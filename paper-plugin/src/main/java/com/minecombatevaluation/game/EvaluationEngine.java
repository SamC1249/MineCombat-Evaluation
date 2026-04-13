package com.minecombatevaluation.game;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.minecombatevaluation.config.PluginSettings;
import java.util.Comparator;
import java.util.List;
import java.util.UUID;
import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.World;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Entity;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Monster;
import org.bukkit.entity.Player;
import org.bukkit.entity.Zombie;
import org.bukkit.inventory.ItemStack;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.util.BoundingBox;
import org.bukkit.util.Vector;
import org.jetbrains.annotations.Nullable;

public final class EvaluationEngine {

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
    }

    public void onEntityDeath(Entity entity) {
        Episode ep = this.episode;
        if (ep == null || ep.ended) {
            return;
        }
        if (entity instanceof Player p && p.getUniqueId().equals(ep.player.getUniqueId())) {
            ep.playerDead = true;
        }
        if (ep.zombieId != null && entity.getUniqueId().equals(ep.zombieId)) {
            ep.zombieDead = true;
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
        String scenario = in.has("scenario_id") ? in.get("scenario_id").getAsString() : "";
        if (!SCENARIO_ZOMBIE_ROOM_V0.equals(scenario)) {
            return error("unsupported scenario_id: " + scenario);
        }
        Player player = settings.resolvePlayer();
        if (player == null || !player.isOnline()) {
            return error("no online player (join the server or set evaluation.player-name)");
        }
        World world = Bukkit.getWorld(settings.worldName);
        if (world == null) {
            return error("world not found: " + settings.worldName);
        }
        episode = Episode.begin(player);
        clearHostiles(world);
        Location ps = settings.playerSpawn(world);
        player.teleport(ps);
        player.getInventory().clear();
        player.getInventory().setItemInMainHand(new ItemStack(settings.weapon));
        player.setHealth(player.getAttribute(Attribute.MAX_HEALTH).getValue());
        player.setFoodLevel(20);
        Location zs = settings.zombieSpawn(world);
        Zombie z = world.spawn(zs, Zombie.class);
        z.setRemoveWhenFarAway(false);
        z.setPersistent(true);
        episode.zombieId = z.getUniqueId();
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
        } else if (ep.zombieDead) {
            terminated = true;
            outcome = "success";
            reason = "all_hostiles_defeated";
            ep.ended = true;
        } else if (ep.tick >= settings.maxTicks) {
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

    private void clearHostiles(World world) {
        Location c = settings.arenaCenter(world);
        double hs = settings.halfSize;
        double yMin = c.getY() - settings.minYDelta;
        double yMax = c.getY() + settings.maxYDelta;
        BoundingBox bb =
                BoundingBox.of(
                        new Vector(c.getX() - hs, yMin, c.getZ() - hs),
                        new Vector(c.getX() + hs, yMax, c.getZ() + hs));
        for (Entity e : world.getNearbyEntities(bb, e -> e instanceof Monster)) {
            e.remove();
        }
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
            if (!(target instanceof Monster)) {
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
        Location center = settings.arenaCenter(world);
        for (Entity e : world.getNearbyEntities(center, 48.0, 48.0, 48.0)) {
            if (!(e instanceof Monster)) {
                continue;
            }
            if (!(e instanceof LivingEntity le)) {
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
        @Nullable UUID zombieId;
        volatile boolean zombieDead;
        volatile boolean playerDead;
        boolean ended;

        private Episode(Player player) {
            this.player = player;
        }

        static Episode begin(Player player) {
            return new Episode(player);
        }
    }
}
