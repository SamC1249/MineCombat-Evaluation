package com.minecombatevaluation.config;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.plugin.java.JavaPlugin;

/** Level 2 environment templates (spawn + arena). */
public final class EnvironmentRegistry {

    private final Map<String, SpawnLayout> byId;

    private EnvironmentRegistry(Map<String, SpawnLayout> byId) {
        this.byId = byId;
    }

    public SpawnLayout get(String id) {
        return byId.get(id);
    }

    public static EnvironmentRegistry from(JavaPlugin plugin) {
        FileConfiguration c = plugin.getConfig();
        ConfigurationSection root = c.getConfigurationSection("evaluation.environments");
        Map<String, SpawnLayout> map = new LinkedHashMap<>();
        if (root != null) {
            for (String key : root.getKeys(false)) {
                ConfigurationSection sec = root.getConfigurationSection(key);
                if (sec != null) {
                    SpawnLayout layout = parseLayout(sec, c);
                    if (layout != null) {
                        map.put(key, layout);
                    }
                }
            }
        }
        return new EnvironmentRegistry(Collections.unmodifiableMap(map));
    }

    private static SpawnLayout parseLayout(ConfigurationSection sec, FileConfiguration c) {
        ConfigurationSection spawn = sec.getConfigurationSection("spawn");
        ConfigurationSection arena = sec.getConfigurationSection("arena");
        if (spawn == null) {
            return null;
        }
        ConfigurationSection player = spawn.getConfigurationSection("player");
        ConfigurationSection hostile = spawn.getConfigurationSection("hostile");
        if (player == null) {
            return null;
        }
        double dpsx = c.getDouble("evaluation.spawn.player.x");
        double dpsy = c.getDouble("evaluation.spawn.player.y");
        double dpsz = c.getDouble("evaluation.spawn.player.z");
        float dyaw = (float) c.getDouble("evaluation.spawn.player.yaw");
        float dpitch = (float) c.getDouble("evaluation.spawn.player.pitch");
        double dhx = c.getDouble("evaluation.spawn.zombie.x");
        double dhy = c.getDouble("evaluation.spawn.zombie.y");
        double dhz = c.getDouble("evaluation.spawn.zombie.z");
        double dcx = c.getDouble("evaluation.arena.center-x");
        double dcy = c.getDouble("evaluation.arena.center-y");
        double dcz = c.getDouble("evaluation.arena.center-z");
        double dhs = c.getDouble("evaluation.arena.half-size", 16);
        double dmch = c.getDouble("evaluation.arena.mob-clear-half-size", 48);
        double dminY = c.getDouble("evaluation.arena.min-y-delta", 2);
        double dmaxY = c.getDouble("evaluation.arena.max-y-delta", 8);

        double px = player.getDouble("x", dpsx);
        double py = player.getDouble("y", dpsy);
        double pz = player.getDouble("z", dpsz);
        float yaw = (float) player.getDouble("yaw", dyaw);
        float pitch = (float) player.getDouble("pitch", dpitch);
        double hx = hostile != null ? hostile.getDouble("x", px + 8) : px + 8;
        double hy = hostile != null ? hostile.getDouble("y", py) : py;
        double hz = hostile != null ? hostile.getDouble("z", pz) : pz;
        double cx = arena != null ? arena.getDouble("center-x", px) : px;
        double cy = arena != null ? arena.getDouble("center-y", py) : py;
        double cz = arena != null ? arena.getDouble("center-z", pz) : pz;
        double hs = arena != null ? arena.getDouble("half-size", dhs) : dhs;
        double mchRaw = arena != null ? arena.getDouble("mob-clear-half-size", -1.0) : -1.0;
        double mch = mchRaw > 0 ? mchRaw : Math.max(hs, dmch);
        double minY = arena != null ? arena.getDouble("min-y-delta", dminY) : dminY;
        double maxY = arena != null ? arena.getDouble("max-y-delta", dmaxY) : dmaxY;
        return new SpawnLayout(
                px, py, pz, yaw, pitch, hx, hy, hz, cx, cy, cz, hs, mch, minY, maxY);
    }
}
