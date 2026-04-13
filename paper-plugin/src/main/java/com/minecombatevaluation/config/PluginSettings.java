package com.minecombatevaluation.config;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.World;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.plugin.java.JavaPlugin;

public final class PluginSettings {

    public final String bindHost;
    public final int port;
    public final String playerName;
    public final String worldName;
    public final int maxTicks;
    public final double centerX;
    public final double centerY;
    public final double centerZ;
    public final double halfSize;
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
    public final Material weapon;
    public final double moveBaseSpeed;
    public final double sprintMultiplier;

    private PluginSettings(
            String bindHost,
            int port,
            String playerName,
            String worldName,
            int maxTicks,
            double centerX,
            double centerY,
            double centerZ,
            double halfSize,
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
            Material weapon,
            double moveBaseSpeed,
            double sprintMultiplier) {
        this.bindHost = bindHost;
        this.port = port;
        this.playerName = playerName;
        this.worldName = worldName;
        this.maxTicks = maxTicks;
        this.centerX = centerX;
        this.centerY = centerY;
        this.centerZ = centerZ;
        this.halfSize = halfSize;
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
        this.weapon = weapon;
        this.moveBaseSpeed = moveBaseSpeed;
        this.sprintMultiplier = sprintMultiplier;
    }

    public static PluginSettings from(JavaPlugin plugin) {
        FileConfiguration c = plugin.getConfig();
        String bind = c.getString("network.bind", "127.0.0.1");
        int port = c.getInt("network.port", 8765);
        String pname = Objects.toString(c.getString("evaluation.player-name", ""), "").trim();
        String world = c.getString("evaluation.world", "world");
        int maxTicks = c.getInt("evaluation.max-ticks", 2400);
        double cx = c.getDouble("evaluation.arena.center-x");
        double cy = c.getDouble("evaluation.arena.center-y");
        double cz = c.getDouble("evaluation.arena.center-z");
        double hs = c.getDouble("evaluation.arena.half-size", 16);
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
        String weaponName = c.getString("evaluation.gear.weapon", "WOODEN_SWORD");
        Material mat = Material.matchMaterial(weaponName.toUpperCase(Locale.ROOT));
        if (mat == null || !mat.isItem()) {
            mat = Material.WOODEN_SWORD;
        }
        double base = c.getDouble("evaluation.move.base-speed", 0.22);
        double sprint = c.getDouble("evaluation.move.sprint-multiplier", 1.3);
        return new PluginSettings(
                bind,
                port,
                pname,
                world,
                maxTicks,
                cx,
                cy,
                cz,
                hs,
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
                mat,
                base,
                sprint);
    }

    public Location arenaCenter(World world) {
        return new Location(world, centerX, centerY, centerZ);
    }

    public Location playerSpawn(World world) {
        return new Location(world, playerSpawnX, playerSpawnY, playerSpawnZ, playerYaw, playerPitch);
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
