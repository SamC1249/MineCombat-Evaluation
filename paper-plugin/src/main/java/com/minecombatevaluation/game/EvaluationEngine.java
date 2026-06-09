package com.minecombatevaluation.game;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.google.gson.JsonElement;
import com.minecombatevaluation.config.HostileSpawnSpec;
import com.minecombatevaluation.config.PluginSettings;
import com.minecombatevaluation.config.ScenarioSpec;
import com.minecombatevaluation.config.SpawnLayout;
import com.minecombatevaluation.config.TaskSpecMerger;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.World;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.ArmorStand;
import org.bukkit.entity.Enderman;
import org.bukkit.entity.Entity;
import org.bukkit.entity.EntityType;
import org.bukkit.entity.Hoglin;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Monster;
import org.bukkit.entity.Player;
import org.bukkit.entity.Shulker;
import org.bukkit.entity.Slime;
import org.bukkit.entity.Zombie;
import org.bukkit.inventory.ItemStack;
import org.bukkit.Material;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.util.BoundingBox;
import org.bukkit.util.Vector;
import org.jetbrains.annotations.Nullable;

public final class EvaluationEngine {

    /** Backward-compatible default id (Level 1 wood / day). */
    public static final String SCENARIO_ZOMBIE_ROOM_V0 = "ZombieRoom-v0";

    private final JavaPlugin plugin;
    private PluginSettings settings;
    private @Nullable Episode episode;

    public EvaluationEngine(JavaPlugin plugin) {
        this.plugin = plugin;
        this.settings = PluginSettings.from(plugin);
    }

    public void reloadSettings() {
        this.settings = PluginSettings.from(plugin);
        applyWorldIsolationIfReady();
    }

    public PluginSettings settings() {
        return settings;
    }

    /** Re-applies isolation rules when the evaluation world is loaded (gamerule + border). */
    public void applyWorldIsolationIfReady() {
        World w = Bukkit.getWorld(settings.worldName);
        if (w != null) {
            settings.applyIsolation(w);
        }
    }

    /**
     * Called when a player quits: logs if that player was the evaluation subject (episode cleared so
     * a new {@code reset} is required after rejoin).
     */
    public void onEvaluationPlayerQuit(UUID playerId) {
        Episode ep = this.episode;
        if (ep == null || ep.ended) {
            return;
        }
        if (!Objects.equals(ep.player.getUniqueId(), playerId)) {
            return;
        }
        ep.ended = true;
        this.episode = null;
        plugin.getLogger()
                .severe(
                        "[MineCombat-Evaluation] evaluation player left the game during an active episode; "
                                + "rejoin the server, then run_eval / reset can start a new episode.");
    }

    public void onEntityDeath(Entity entity) {
        Episode ep = this.episode;
        if (ep == null || ep.ended) {
            return;
        }
        if (entity instanceof Player p && p.getUniqueId().equals(ep.player.getUniqueId())) {
            ep.playerDead = true;
        }
        if (ep.hostileIds.remove(entity.getUniqueId()) && ep.hostileIds.isEmpty()) {
            ep.hostileDead = true;
        }
    }

    public String handleIncomingJson(String line) {
        JsonObject root;
        try {
            root = JsonParser.parseString(line).getAsJsonObject();
        } catch (Exception e) {
            return error("invalid json: " + e.getMessage());
        }
        if (!root.has("type")) {
            return error("missing type");
        }
        String type = root.get("type").getAsString();
        return switch (type) {
            case "reset" -> onReset(root);
            case "step" -> onStep(root);
            default -> error("unknown type: " + type);
        };
    }

    private String onReset(JsonObject in) {
        if (!in.has("protocol") || in.get("protocol").getAsInt() != 1) {
            return error("unsupported protocol (expected 1)");
        }
        String scenarioId = in.has("scenario_id") ? in.get("scenario_id").getAsString() : "";
        ScenarioSpec base = settings.scenarios.get(scenarioId);
        if (base == null) {
            return error("unsupported scenario_id: " + scenarioId);
        }
        if (base.level < 1 || base.level > 2) {
            return error("unsupported scenario level: " + base.level);
        }
        com.google.gson.JsonObject taskJson = null;
        if (in.has("task_spec") && !in.get("task_spec").isJsonNull()) {
            JsonElement te = in.get("task_spec");
            if (!te.isJsonObject()) {
                return error("task_spec must be a JSON object");
            }
            taskJson = te.getAsJsonObject();
        } else if (in.has("task") && !in.get("task").isJsonNull()) {
            JsonElement te = in.get("task");
            if (!te.isJsonObject()) {
                return error("task must be a JSON object");
            }
            taskJson = te.getAsJsonObject();
        }
        TaskSpecMerger.Result merged = new TaskSpecMerger.Result();
        String mergeErr = TaskSpecMerger.merge(base, taskJson, settings.taskSpecLimits, merged);
        if (mergeErr != null) {
            return error(mergeErr);
        }
        ScenarioSpec spec = merged.spec;
        boolean taskSpecApplied = merged.taskSpecApplied;
        SpawnLayout layout = settings.layoutFor(spec);
        Player player = settings.resolvePlayer();
        if (player == null || !player.isOnline()) {
            return error("no online player (join the server or set evaluation.player-name)");
        }
        World world = Bukkit.getWorld(settings.worldName);
        if (world == null) {
            return error("world not found: " + settings.worldName);
        }
        settings.applyIsolation(world, layout);
        episode = Episode.begin(player, spec, layout, taskSpecApplied);
        clearHostiles(world, layout);
        world.setTime(spec.worldTime);
        // A player killed in the previous episode is on the death screen; teleport/setHealth are
        // no-ops until they respawn, so force it before repositioning for the new episode.
        if (player.isDead()) {
            player.spigot().respawn();
        }
        Location ps = settings.playerSpawn(world, layout);
        player.teleport(ps);
        applyGear(player, spec);
        player.setHealth(player.getAttribute(Attribute.MAX_HEALTH).getValue());
        player.setFoodLevel(20);
        spawnHostiles(world, layout, spec, episode);
        episode.tick = 0;
        JsonObject obs = buildObservation(episode, world);
        JsonObject out = new JsonObject();
        out.addProperty("type", "reset_ok");
        out.addProperty("protocol", 1);
        out.addProperty("episode_id", episode.id.toString());
        out.addProperty("tick", episode.tick);
        out.add("observation", obs);
        out.addProperty("truncated", false);
        out.addProperty("terminated", false);
        return out.toString();
    }

    private static void applyGear(Player player, ScenarioSpec spec) {
        player.getInventory().clear();
        player.getInventory().setItemInMainHand(new ItemStack(spec.weapon));
        player.getInventory().setHelmet(stackOrNull(spec.helmet));
        player.getInventory().setChestplate(stackOrNull(spec.chestplate));
        player.getInventory().setLeggings(stackOrNull(spec.leggings));
        player.getInventory().setBoots(stackOrNull(spec.boots));
    }

    private static ItemStack stackOrNull(Material m) {
        if (m == null || m == Material.AIR) {
            return null;
        }
        return new ItemStack(m);
    }

    private String onStep(JsonObject in) {
        if (!in.has("protocol") || in.get("protocol").getAsInt() != 1) {
            return error("unsupported protocol (expected 1)");
        }
        Episode ep = this.episode;
        if (ep == null || ep.ended) {
            return error("no active episode; send reset first");
        }
        if (!in.has("episode_id")) {
            return error("missing episode_id");
        }
        UUID id;
        try {
            id = UUID.fromString(in.get("episode_id").getAsString());
        } catch (Exception e) {
            return error("bad episode_id");
        }
        if (!ep.id.equals(id)) {
            return error("episode_id mismatch");
        }
        if (!ep.player.isOnline()) {
            return abortEpisodePlayerDisconnected("step: evaluation player is offline");
        }
        World world = ep.player.getWorld();
        ep.tick += 1;
        JsonObject action = in.has("action") ? in.getAsJsonObject("action") : new JsonObject();
        applyAction(ep.player, action);

        String outcome = null;
        String reason = null;
        boolean terminated = false;
        if (ep.playerDead) {
            terminated = true;
            outcome = "failure";
            reason = "player_died";
            ep.ended = true;
        } else if (ep.hostileDead) {
            terminated = true;
            outcome = "success";
            reason = "all_hostiles_defeated";
            ep.ended = true;
        } else if (ep.tick >= ep.scenario.maxTicks) {
            terminated = true;
            outcome = "timeout";
            reason = "max_ticks";
            ep.ended = true;
        }

        JsonObject obs = buildObservation(ep, world);
        JsonObject out = new JsonObject();
        out.addProperty("type", "step_result");
        out.addProperty("protocol", 1);
        out.addProperty("episode_id", ep.id.toString());
        out.addProperty("tick", ep.tick);
        out.addProperty("reward", 0.0);
        out.addProperty("truncated", "timeout".equals(outcome));
        out.addProperty("terminated", terminated);
        if (terminated) {
            out.addProperty("outcome", outcome);
            out.addProperty("reason", reason);
        }
        out.add("observation", obs);
        return out.toString();
    }

    private String abortEpisodePlayerDisconnected(String context) {
        Episode ep = this.episode;
        if (ep != null) {
            ep.ended = true;
        }
        this.episode = null;
        plugin.getLogger()
                .severe("[MineCombat-Evaluation] " + context + " — evaluation aborted; rejoin, then send reset.");
        return error("player disconnected");
    }

    private void clearHostiles(World world, SpawnLayout layout) {
        Location c = layout.arenaCenter(world);
        double hs = layout.mobClearHalfSize;
        double yMin = c.getY() - layout.minYDelta;
        double yMax = c.getY() + layout.maxYDelta;
        BoundingBox bb =
                BoundingBox.of(
                        new Vector(c.getX() - hs, yMin, c.getZ() - hs),
                        new Vector(c.getX() + hs, yMax, c.getZ() + hs));
        for (Entity e : world.getNearbyEntities(bb, EvaluationEngine::isArenaHostile)) {
            e.remove();
        }
    }

    /**
     * Level 1 arena uses {@link Monster} plus mobs that are hostile but do not implement {@link
     * Monster} (e.g. enderman, slimes, shulker).
     */
    private static boolean isArenaHostile(Entity e) {
        if (e instanceof Player || e instanceof ArmorStand) {
            return false;
        }
        if (e instanceof Monster) {
            return true;
        }
        if (e instanceof Enderman) {
            return true;
        }
        if (e instanceof Slime) {
            return true;
        }
        if (e instanceof Shulker) {
            return true;
        }
        return false;
    }

    private static void spawnHostiles(
            World world, SpawnLayout layout, ScenarioSpec spec, Episode episode) {
        List<HostileSpawnSpec> plans = spec.resolvedHostiles(layout);
        int spreadIndex = 0;
        for (HostileSpawnSpec plan : plans) {
            double bx = plan.hasPosition() ? plan.x : layout.hostileAnchorX;
            double by = plan.hasPosition() ? plan.y : layout.hostileAnchorY;
            double bz = plan.hasPosition() ? plan.z : layout.hostileAnchorZ;
            for (int i = 0; i < plan.count; i++) {
                double[] off = spreadOffset(spreadIndex, plan.count);
                Location loc = new Location(world, bx + off[0], by, bz + off[1]);
                Entity hostile = spawnHostile(world, loc, plan.entity, plan.baby);
                episode.hostileIds.add(hostile.getUniqueId());
                spreadIndex++;
            }
        }
    }

    /** Small horizontal offsets so multiple mobs do not overlap. */
    private static double[] spreadOffset(int index, int groupSize) {
        if (groupSize <= 1) {
            return new double[] {0.0, 0.0};
        }
        double angle = (2.0 * Math.PI * index) / groupSize;
        double r = 1.5 + (index % 2) * 0.5;
        return new double[] {Math.cos(angle) * r, Math.sin(angle) * r};
    }

    private static Entity spawnHostile(World world, Location loc, EntityType type, boolean baby) {
        EntityType t = type != null ? type : EntityType.ZOMBIE;
        Entity e = world.spawnEntity(loc, t);
        if (e instanceof Zombie z) {
            z.setBaby(baby);
        }
        if (e instanceof Hoglin h) {
            h.setImmuneToZombification(true);
        }
        if (e instanceof Slime s) {
            s.setSize(1);
        }
        if (e instanceof LivingEntity le) {
            le.setRemoveWhenFarAway(false);
            le.setPersistent(true);
        }
        return e;
    }

    private void applyAction(Player player, JsonObject a) {
        double forward = getDouble(a, "forward", 0.0);
        double strafe = getDouble(a, "strafe", 0.0);
        double yawD = getDouble(a, "yaw_delta", 0.0);
        double pitchD = getDouble(a, "pitch_delta", 0.0);
        boolean jump = getBool(a, "jump", false);
        boolean attack = getBool(a, "attack", false);
        boolean sprint = getBool(a, "sprint", false);
        int hotbar = (int) Math.round(getDouble(a, "hotbar_slot", 0.0));
        hotbar = Math.max(0, Math.min(8, hotbar));
        player.getInventory().setHeldItemSlot(hotbar);

        Location loc = player.getLocation();
        float ny = loc.getYaw() + (float) yawD;
        float np = loc.getPitch() + (float) pitchD;
        np = Math.max(-90f, Math.min(90f, np));
        loc.setYaw(ny);
        loc.setPitch(np);
        player.teleport(loc);

        double f = clamp(forward, -1.0, 1.0);
        double s = clamp(strafe, -1.0, 1.0);
        double yawRad = Math.toRadians(loc.getYaw());
        Vector forwardV = new Vector(-Math.sin(yawRad), 0, Math.cos(yawRad)).normalize();
        Vector rightV = new Vector(Math.cos(yawRad), 0, Math.sin(yawRad)).normalize();
        double mag = Math.min(1.0, Math.sqrt(f * f + s * s));
        double spd = settings.moveBaseSpeed * (sprint ? settings.sprintMultiplier : 1.0) * mag;
        Vector horiz = forwardV.multiply(f).add(rightV.multiply(s));
        if (horiz.lengthSquared() > 1e-8) {
            horiz.normalize().multiply(spd);
        } else {
            horiz = new Vector(0, 0, 0);
        }
        Vector vel = player.getVelocity();
        player.setVelocity(new Vector(horiz.getX(), vel.getY(), horiz.getZ()));

        if (jump && player.isOnGround()) {
            player.setVelocity(player.getVelocity().add(new Vector(0, 0.42, 0)));
        }

        if (attack) {
            melee(player);
        }
    }

    private static void melee(Player player) {
        Location eye = player.getEyeLocation();
        Vector dir = eye.getDirection();
        List<Entity> nearby = player.getNearbyEntities(4.0, 4.0, 4.0);
        nearby.sort(Comparator.comparingDouble(e -> e.getLocation().distanceSquared(eye)));
        for (Entity e : nearby) {
            if (!(e instanceof LivingEntity target)) {
                continue;
            }
            if (target.equals(player)) {
                continue;
            }
            if (!isArenaHostile(target)) {
                continue;
            }
            if (!player.hasLineOfSight(target)) {
                continue;
            }
            double reach = 3.2;
            Vector to = target.getEyeLocation().toVector().subtract(eye.toVector());
            if (to.lengthSquared() > reach * reach) {
                continue;
            }
            double cos = dir.dot(to.normalize());
            if (cos < 0.35) {
                continue;
            }
            player.swingMainHand();
            double dmg =
                    player.getAttribute(Attribute.ATTACK_DAMAGE) != null
                            ? player.getAttribute(Attribute.ATTACK_DAMAGE).getValue()
                            : 1.0;
            target.damage(dmg, player);
            return;
        }
    }

    private JsonObject buildObservation(Episode ep, World world) {
        Player p = ep.player;
        ScenarioSpec sc = ep.scenario;
        boolean taskSpecApplied = ep.taskSpecApplied;
        JsonObject obs = new JsonObject();
        obs.addProperty("tick", ep.tick);
        JsonObject pj = new JsonObject();
        pj.addProperty("health", p.getHealth());
        pj.addProperty(
                "max_health",
                p.getAttribute(Attribute.MAX_HEALTH) != null
                        ? p.getAttribute(Attribute.MAX_HEALTH).getValue()
                        : 20.0);
        pj.addProperty("food", p.getFoodLevel());
        Location pl = p.getLocation();
        pj.addProperty("x", pl.getX());
        pj.addProperty("y", pl.getY());
        pj.addProperty("z", pl.getZ());
        pj.addProperty("yaw", pl.getYaw());
        pj.addProperty("pitch", pl.getPitch());
        pj.addProperty("on_ground", p.isOnGround());
        obs.add("player", pj);

        JsonArray mobs = new JsonArray();
        Location center = ep.layout.arenaCenter(world);
        for (Entity e : world.getNearbyEntities(center, 48.0, 48.0, 48.0)) {
            if (!(e instanceof LivingEntity le)) {
                continue;
            }
            if (!isArenaHostile(le)) {
                continue;
            }
            Location el = le.getLocation();
            JsonObject mj = new JsonObject();
            mj.addProperty("kind", le.getType().name());
            mj.addProperty("uuid", le.getUniqueId().toString());
            mj.addProperty("x", el.getX());
            mj.addProperty("y", el.getY());
            mj.addProperty("z", el.getZ());
            mj.addProperty("health", le.getHealth());
            mj.addProperty("distance", pl.distance(el));
            mobs.add(mj);
        }
        obs.add("mobs", mobs);

        JsonObject meta = new JsonObject();
        meta.addProperty("plugin_version", plugin.getPluginMeta().getVersion());
        meta.addProperty("paper_minecraft", Bukkit.getVersion());
        meta.addProperty("scenario_id", sc.id);
        meta.addProperty("scenario_version", sc.scenarioVersion);
        meta.addProperty("scenario_level", sc.level);
        meta.addProperty("time_of_day", sc.timeOfDayLabel);
        meta.addProperty("world_time", sc.worldTime);
        meta.addProperty("hostile_entity", sc.hostileEntity.name());
        meta.addProperty("hostile_count", ep.hostileIds.size());
        if (sc.environmentId != null && !sc.environmentId.isBlank()) {
            meta.addProperty("environment_id", sc.environmentId);
        }
        if (sc.babyZombie) {
            meta.addProperty("baby_zombie", true);
        }
        if (taskSpecApplied) {
            meta.addProperty("task_spec_applied", true);
        }
        obs.add("meta", meta);
        return obs;
    }

    public String error(String message) {
        JsonObject out = new JsonObject();
        out.addProperty("type", "error");
        out.addProperty("protocol", 1);
        out.addProperty("message", message);
        return out.toString();
    }

    private static double getDouble(JsonObject o, String key, double def) {
        if (o == null || !o.has(key) || o.get(key).isJsonNull()) {
            return def;
        }
        try {
            return o.get(key).getAsDouble();
        } catch (Exception e) {
            return def;
        }
    }

    private static boolean getBool(JsonObject o, String key, boolean def) {
        if (o == null || !o.has(key) || o.get(key).isJsonNull()) {
            return def;
        }
        try {
            return o.get(key).getAsBoolean();
        } catch (Exception e) {
            return false;
        }
    }

    private static double clamp(double v, double lo, double hi) {
        return Math.max(lo, Math.min(hi, v));
    }

    private static final class Episode {
        final UUID id = UUID.randomUUID();
        int tick;
        final Player player;
        final ScenarioSpec scenario;
        final SpawnLayout layout;
        final boolean taskSpecApplied;
        final Set<UUID> hostileIds = new HashSet<>();
        volatile boolean hostileDead;
        volatile boolean playerDead;
        boolean ended;

        private Episode(Player player, ScenarioSpec scenario, SpawnLayout layout, boolean taskSpecApplied) {
            this.player = player;
            this.scenario = scenario;
            this.layout = layout;
            this.taskSpecApplied = taskSpecApplied;
        }

        static Episode begin(
                Player player, ScenarioSpec scenario, SpawnLayout layout, boolean taskSpecApplied) {
            return new Episode(player, scenario, layout, taskSpecApplied);
        }
    }
}
