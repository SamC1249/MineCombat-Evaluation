package com.minecombatevaluation.config;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;
import org.bukkit.Bukkit;
import org.bukkit.GameRule;
import org.bukkit.Location;
import org.bukkit.World;
import org.bukkit.WorldBorder;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.plugin.java.JavaPlugin;

public final class PluginSettings {

    public final String bindHost;
    public final int port;
    public final String playerName;
    public final String worldName;
    public final double centerX;
    public final double centerY;
    public final double centerZ;
    public final double halfSize;
    /**
     * Horizontal half-extent (blocks) for mob removal on reset; can exceed {@link #halfSize} to
     * clear stragglers outside the nominal arena.
     */
    public final double mobClearHalfSize;
    public final double minYDelta;
    public final double maxYDelta;
    public final double playerSpawnX;
    public final double playerSpawnY;
    public final double playerSpawnZ;
    public final float playerYaw;
    public final float playerPitch;
    public final double zombieSpawnX;
    public final double zombieSpawnY;
    public final double zombieSpawnZ;
    public final double moveBaseSpeed;
    public final double sprintMultiplier;
    /**
     * When true, natural mob spawning is disabled in the eval world (plugin applies on reset /
     * enable; does not affect plugin spawns).
     */
    public final boolean disableNaturalSpawn;
    /**
     * Diameter in blocks for {@link WorldBorder}, centered on the arena, or 0.0 to leave the
     * current border unchanged.
     */
    public final double worldBorderDiameter;
    /**
     * When true, sets doMobGriefing = false on the eval world and blocks mob block changes via
     * {@link com.minecombatevaluation.game.EnvironmentProtectionListener}.
     */
    public final boolean disableMobGriefing;
    /**
     * When true, sets {@link org.bukkit.GameRule#DO_DAYLIGHT_CYCLE} false on the eval world so
     * {@code setTime} for night/day is not overridden by tick progression.
     */
    public final boolean freezeDaylightCycle;
    /**
     * When true, the eval world's blocks are immutable: player block break/place, bucket use,
     * fire/liquid spread, decay, and non-entity explosions are cancelled via
     * {@link com.minecombatevaluation.game.WorldImmutabilityListener}. Mob-caused block changes
     * are handled separately by {@link #disableMobGriefing}.
     */
    public final boolean protectWorldBlocks;
    public final ScenarioRegistry scenarios;
    public final EnvironmentRegistry environments;
    public final TaskSpecLimits taskSpecLimits;

    private PluginSettings(
            String bindHost,
            int port,
            String playerName,
            String worldName,
            double centerX,
            double centerY,
            double centerZ,
            double halfSize,
            double mobClearHalfSize,
            double minYDelta,
            double maxYDelta,
            double playerSpawnX,
            double playerSpawnY,
            double playerSpawnZ,
            float playerYaw,
            float playerPitch,
            double zombieSpawnX,
            double zombieSpawnY,
            double zombieSpawnZ,
            double moveBaseSpeed,
            double sprintMultiplier,
            boolean disableNaturalSpawn,
            double worldBorderDiameter,
            boolean disableMobGriefing,
            boolean freezeDaylightCycle,
            boolean protectWorldBlocks,
            ScenarioRegistry scenarios,
            EnvironmentRegistry environments,
            TaskSpecLimits taskSpecLimits) {
        this.bindHost = bindHost;
        this.port = port;
        this.playerName = playerName;
        this.worldName = worldName;
        this.centerX = centerX;
        this.centerY = centerY;
        this.centerZ = centerZ;
        this.halfSize = halfSize;
        this.mobClearHalfSize = mobClearHalfSize;
        this.minYDelta = minYDelta;
        this.maxYDelta = maxYDelta;
        this.playerSpawnX = playerSpawnX;
        this.playerSpawnY = playerSpawnY;
        this.playerSpawnZ = playerSpawnZ;
        this.playerYaw = playerYaw;
        this.playerPitch = playerPitch;
        this.zombieSpawnX = zombieSpawnX;
        this.zombieSpawnY = zombieSpawnY;
        this.zombieSpawnZ = zombieSpawnZ;
        this.moveBaseSpeed = moveBaseSpeed;
        this.sprintMultiplier = sprintMultiplier;
        this.disableNaturalSpawn = disableNaturalSpawn;
        this.worldBorderDiameter = worldBorderDiameter;
        this.disableMobGriefing = disableMobGriefing;
        this.freezeDaylightCycle = freezeDaylightCycle;
        this.protectWorldBlocks = protectWorldBlocks;
        this.scenarios = scenarios;
        this.environments = environments;
        this.taskSpecLimits = taskSpecLimits;
    }

    public static PluginSettings from(JavaPlugin plugin) {
        FileConfiguration c = plugin.getConfig();
        String bind = c.getString("network.bind", "127.0.0.1");
        int port = c.getInt("network.port", 8765);
        String pname = Objects.toString(c.getString("evaluation.player-name", ""), "").trim();
        String world = c.getString("evaluation.world", "mcbench_flat");
        double cx = c.getDouble("evaluation.arena.center-x");
        double cy = c.getDouble("evaluation.arena.center-y");
        double cz = c.getDouble("evaluation.arena.center-z");
        double hs = c.getDouble("evaluation.arena.half-size", 16);
        double mchRaw = c.getDouble("evaluation.arena.mob-clear-half-size", -1.0);
        double mch = mchRaw > 0 ? mchRaw : Math.max(hs, 48.0);
        double minYd = c.getDouble("evaluation.arena.min-y-delta", 2);
        double maxYd = c.getDouble("evaluation.arena.max-y-delta", 8);
        double psx = c.getDouble("evaluation.spawn.player.x");
        double psy = c.getDouble("evaluation.spawn.player.y");
        double psz = c.getDouble("evaluation.spawn.player.z");
        float yaw = (float) c.getDouble("evaluation.spawn.player.yaw");
        float pitch = (float) c.getDouble("evaluation.spawn.player.pitch");
        double zx = c.getDouble("evaluation.spawn.zombie.x");
        double zy = c.getDouble("evaluation.spawn.zombie.y");
        double zz = c.getDouble("evaluation.spawn.zombie.z");
        double base = c.getDouble("evaluation.move.base-speed", 0.22);
        double sprint = c.getDouble("evaluation.move.sprint-multiplier", 1.3);
        ConfigurationSection isolation = c.getConfigurationSection("evaluation.isolation");
        boolean dms = true;
        double wbd = 128.0;
        boolean dmg = true;
        boolean fdc = true;
        boolean pwb = true;
        if (isolation != null) {
            dms = isolation.getBoolean("disable-natural-spawn", true);
            wbd = isolation.getDouble("world-border-diameter", 128.0);
            dmg = isolation.getBoolean("disable-mob-griefing", true);
            fdc = isolation.getBoolean("freeze-daylight-cycle", true);
            pwb = isolation.getBoolean("protect-world-blocks", true);
        }
        ScenarioRegistry registry = ScenarioRegistry.from(plugin);
        EnvironmentRegistry environments = EnvironmentRegistry.from(plugin);
        int defaultMaxTicks = c.getInt("evaluation.max-ticks", 2400);
        TaskSpecLimits taskLimits = TaskSpecLimits.from(c, defaultMaxTicks);
        return new PluginSettings(
                bind,
                port,
                pname,
                world,
                cx,
                cy,
                cz,
                hs,
                mch,
                minYd,
                maxYd,
                psx,
                psy,
                psz,
                yaw,
                pitch,
                zx,
                zy,
                zz,
                base,
                sprint,
                dms,
                wbd,
                dmg,
                fdc,
                pwb,
                registry,
                environments,
                taskLimits);
    }

    public SpawnLayout defaultLayout() {
        return new SpawnLayout(
                playerSpawnX,
                playerSpawnY,
                playerSpawnZ,
                playerYaw,
                playerPitch,
                zombieSpawnX,
                zombieSpawnY,
                zombieSpawnZ,
                centerX,
                centerY,
                centerZ,
                halfSize,
                mobClearHalfSize,
                minYDelta,
                maxYDelta);
    }

    public SpawnLayout layoutFor(ScenarioSpec spec) {
        return spec.resolveLayout(environments, this);
    }

    public Location arenaCenter(World world) {
        return new Location(world, centerX, centerY, centerZ);
    }

    public Location arenaCenter(World world, SpawnLayout layout) {
        return layout.arenaCenter(world);
    }

    /**
     * Applies world gamerules and world border for the eval arena. Safe to call whenever the
     * evaluation world is loaded.
     */
    public void applyIsolation(World world) {
        applyIsolation(world, defaultLayout());
    }

    public void applyIsolation(World world, SpawnLayout layout) {
        if (world == null) {
            return;
        }
        if (disableNaturalSpawn) {
            world.setGameRule(GameRule.DO_MOB_SPAWNING, false);
        }
        if (disableMobGriefing) {
            @SuppressWarnings("removal")
            GameRule<Boolean> mobGriefing = GameRule.MOB_GRIEFING;
            world.setGameRule(mobGriefing, false);
        }
        if (worldBorderDiameter > 0) {
            WorldBorder border = world.getWorldBorder();
            border.setCenter(layout.arenaCenterX, layout.arenaCenterZ);
            border.setSize(worldBorderDiameter);
            border.setDamageAmount(0.0);
        }
        if (freezeDaylightCycle) {
            world.setGameRule(GameRule.DO_DAYLIGHT_CYCLE, false);
        }
    }

    public Location playerSpawn(World world) {
        return new Location(world, playerSpawnX, playerSpawnY, playerSpawnZ, playerYaw, playerPitch);
    }

    public Location playerSpawn(World world, SpawnLayout layout) {
        return layout.playerSpawn(world);
    }

    public Location zombieSpawn(World world) {
        return new Location(world, zombieSpawnX, zombieSpawnY, zombieSpawnZ);
    }

    public Player resolvePlayer() {
        if (!playerName.isEmpty()) {
            return Bukkit.getPlayerExact(playerName);
        }
        List<Player> online = new ArrayList<>(Bukkit.getOnlinePlayers());
        if (online.isEmpty()) {
            return null;
        }
        online.sort(Comparator.comparing(Player::getName, String.CASE_INSENSITIVE_ORDER));
        return online.get(0);
    }
}
