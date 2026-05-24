package com.minecombatevaluation.config;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import org.bukkit.Material;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.entity.EntityType;
import org.bukkit.plugin.java.JavaPlugin;

/** Loads scenarios (Level 1 template + Level 2 custom environments). */
public final class ScenarioRegistry {

    private final Map<String, ScenarioSpec> byId;

    private ScenarioRegistry(Map<String, ScenarioSpec> byId) {
        this.byId = byId;
    }

    public ScenarioSpec get(String id) {
        return byId.get(id);
    }

    public Set<String> ids() {
        return Collections.unmodifiableSet(byId.keySet());
    }

    public static ScenarioRegistry from(JavaPlugin plugin) {
        FileConfiguration c = plugin.getConfig();
        int defaultMaxTicks = c.getInt("evaluation.max-ticks", 2400);
        ConfigurationSection scenariosRoot = c.getConfigurationSection("evaluation.scenarios");
        Map<String, ScenarioSpec> map = new LinkedHashMap<>();
        if (scenariosRoot != null) {
            for (String key : scenariosRoot.getKeys(false)) {
                ConfigurationSection sec = scenariosRoot.getConfigurationSection(key);
                if (sec == null) {
                    continue;
                }
                ScenarioSpec spec = parseScenario(key, sec, defaultMaxTicks, c);
                map.put(key, spec);
            }
        }
        if (map.isEmpty()) {
            String w = c.getString("evaluation.gear.weapon", "WOODEN_SWORD");
            Material weapon = ScenarioSpec.parseMaterial(w, Material.WOODEN_SWORD);
            map.put(
                    "ZombieRoom-v0",
                    new ScenarioSpec(
                            "ZombieRoom-v0",
                            1,
                            "1",
                            defaultMaxTicks,
                            1000L,
                            "day",
                            EntityType.ZOMBIE,
                            false,
                            weapon,
                            Material.AIR,
                            Material.AIR,
                            Material.AIR,
                            Material.AIR,
                            null,
                            null,
                            List.of()));
        }
        return new ScenarioRegistry(map);
    }

    private static ScenarioSpec parseScenario(
            String id, ConfigurationSection sec, int defaultMaxTicks, FileConfiguration c) {
        int level = sec.getInt("level", 1);
        String ver = sec.getString("scenario-version", "1");
        int maxTicks = sec.getInt("max-ticks", defaultMaxTicks);
        long worldTime;
        String timeLabel;
        if (sec.contains("world-time")) {
            worldTime = sec.getLong("world-time");
            timeLabel = "custom";
        } else {
            String rawTod = sec.getString("time-of-day", "day");
            String tod = (rawTod != null ? rawTod : "day").toLowerCase(Locale.ROOT);
            timeLabel = tod;
            worldTime =
                    switch (tod) {
                        case "day", "morning" -> 1000L;
                        case "noon" -> 6000L;
                        case "night", "evening" -> 13000L;
                        case "midnight" -> 18000L;
                        default -> 1000L;
                    };
        }
        ConfigurationSection gear = sec.getConfigurationSection("gear");
        if (gear == null) {
            gear = sec.createSection("gear");
        }
        Material weapon = ScenarioSpec.parseMaterial(gear.getString("weapon"), Material.WOODEN_SWORD);
        Material helmet = ScenarioSpec.parseMaterial(gear.getString("helmet"), Material.AIR);
        Material chest = ScenarioSpec.parseMaterial(gear.getString("chestplate"), Material.AIR);
        Material legs = ScenarioSpec.parseMaterial(gear.getString("leggings"), Material.AIR);
        Material boots = ScenarioSpec.parseMaterial(gear.getString("boots"), Material.AIR);
        EntityType hostile = ScenarioSpec.parseHostileEntity(sec.getString("entity"));
        boolean baby = sec.getBoolean("baby", false);
        if (hostile != EntityType.ZOMBIE) {
            baby = false;
        }
        String environmentId = sec.getString("environment");
        if (environmentId != null && environmentId.isBlank()) {
            environmentId = null;
        }
        SpawnLayout inlineLayout = null;
        if (sec.contains("spawn") || sec.contains("arena")) {
            inlineLayout = parseInlineLayout(sec, c);
        }
        List<HostileSpawnSpec> hostiles = parseHostiles(sec);
        return new ScenarioSpec(
                id,
                level,
                ver,
                maxTicks,
                worldTime,
                timeLabel,
                hostile,
                baby,
                weapon,
                helmet,
                chest,
                legs,
                boots,
                environmentId,
                inlineLayout,
                hostiles);
    }

    private static SpawnLayout parseInlineLayout(ConfigurationSection sec, FileConfiguration c) {
        ConfigurationSection spawn = sec.getConfigurationSection("spawn");
        ConfigurationSection arena = sec.getConfigurationSection("arena");
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

        ConfigurationSection player = spawn != null ? spawn.getConfigurationSection("player") : null;
        ConfigurationSection hostile = spawn != null ? spawn.getConfigurationSection("hostile") : null;
        double px = player != null ? player.getDouble("x", dpsx) : dpsx;
        double py = player != null ? player.getDouble("y", dpsy) : dpsy;
        double pz = player != null ? player.getDouble("z", dpsz) : dpsz;
        float yaw = player != null ? (float) player.getDouble("yaw", dyaw) : dyaw;
        float pitch = player != null ? (float) player.getDouble("pitch", dpitch) : dpitch;
        double hx = hostile != null ? hostile.getDouble("x", dhx) : dhx;
        double hy = hostile != null ? hostile.getDouble("y", dhy) : dhy;
        double hz = hostile != null ? hostile.getDouble("z", dhz) : dhz;
        double cx = arena != null ? arena.getDouble("center-x", dcx) : dcx;
        double cy = arena != null ? arena.getDouble("center-y", dcy) : dcy;
        double cz = arena != null ? arena.getDouble("center-z", dcz) : dcz;
        double hs = arena != null ? arena.getDouble("half-size", dhs) : dhs;
        double mchRaw = arena != null ? arena.getDouble("mob-clear-half-size", -1.0) : -1.0;
        double mch = mchRaw > 0 ? mchRaw : Math.max(hs, dmch);
        double minY = arena != null ? arena.getDouble("min-y-delta", dminY) : dminY;
        double maxY = arena != null ? arena.getDouble("max-y-delta", dmaxY) : dmaxY;
        return new SpawnLayout(
                px, py, pz, yaw, pitch, hx, hy, hz, cx, cy, cz, hs, mch, minY, maxY);
    }

    private static List<HostileSpawnSpec> parseHostiles(ConfigurationSection sec) {
        List<?> list = sec.getList("hostiles");
        if (list == null || list.isEmpty()) {
            return List.of();
        }
        List<HostileSpawnSpec> out = new ArrayList<>();
        for (Object item : list) {
            if (!(item instanceof Map<?, ?> raw)) {
                continue;
            }
            @SuppressWarnings("unchecked")
            Map<String, Object> m = (Map<String, Object>) raw;
            EntityType entity =
                    ScenarioSpec.parseHostileEntity(
                            m.get("entity") != null ? String.valueOf(m.get("entity")) : null);
            boolean baby =
                    Boolean.TRUE.equals(m.get("baby")) && entity == EntityType.ZOMBIE;
            double x = m.containsKey("x") ? asDouble(m.get("x"), Double.NaN) : Double.NaN;
            double y = m.containsKey("y") ? asDouble(m.get("y"), Double.NaN) : Double.NaN;
            double z = m.containsKey("z") ? asDouble(m.get("z"), Double.NaN) : Double.NaN;
            int count = m.containsKey("count") ? (int) Math.round(asDouble(m.get("count"), 1)) : 1;
            out.add(new HostileSpawnSpec(entity, baby, x, y, z, count));
        }
        return out;
    }

    private static double asDouble(Object o, double fallback) {
        if (o instanceof Number n) {
            return n.doubleValue();
        }
        try {
            return Double.parseDouble(String.valueOf(o));
        } catch (Exception e) {
            return fallback;
        }
    }
}
