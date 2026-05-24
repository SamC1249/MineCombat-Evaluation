package com.minecombatevaluation.config;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.regex.Pattern;
import org.bukkit.Material;
import org.bukkit.entity.EntityType;
import org.jetbrains.annotations.Nullable;

/**
 * Applies optional JSON {@code task_spec} on a registered {@link ScenarioSpec}. Sanitizes entity
 * and material names using {@link TaskSpecLimits}.
 */
public final class TaskSpecMerger {

    private static final Pattern VERSION_SAFE = Pattern.compile("[A-Za-z0-9._\\-]{1,32}");

    private static final String[] TASK_SPEC_TOP_KEYS = {
        "level",
        "max_ticks",
        "world_time",
        "time_of_day",
        "entity",
        "baby",
        "scenario_version",
        "gear",
        "entities",
        "hostiles"
    };

    private TaskSpecMerger() {}

    /** Output holder for merge result (mutable). */
    public static final class Result {
        public ScenarioSpec spec;
        public boolean taskSpecApplied;

        public Result() {
            this.spec = null;
            this.taskSpecApplied = false;
        }
    }

    /**
     * @param taskSpec optional object on wire; null / empty → base unchanged.
     * @return error message, or null on success (see outResult).
     */
    public static @Nullable String merge(
            ScenarioSpec base,
            @Nullable JsonObject taskSpec,
            TaskSpecLimits limits,
            Result outResult) {
        if (taskSpec == null || taskSpec.isJsonNull() || taskSpec.entrySet().isEmpty()) {
            outResult.spec = base;
            outResult.taskSpecApplied = false;
            return null;
        }
        if (!hasKnownTaskSpecContent(taskSpec)) {
            outResult.spec = base;
            outResult.taskSpecApplied = false;
            return null;
        }

        int maxTicks = base.maxTicks;
        long worldTime = base.worldTime;
        String timeLabel = base.timeOfDayLabel;
        EntityType hostile = base.hostileEntity;
        boolean baby = base.babyZombie;
        String ver = base.scenarioVersion;
        int level = base.level;
        Material weapon = base.weapon;
        Material helmet = base.helmet;
        Material chest = base.chestplate;
        Material leggings = base.leggings;
        Material boots = base.boots;
        List<HostileSpawnSpec> hostiles = new ArrayList<>(base.hostiles);

        if (taskSpec.has("level") && !taskSpec.get("level").isJsonNull()) {
            try {
                level = taskSpec.get("level").getAsInt();
            } catch (Exception e) {
                return "task_spec.level must be an integer";
            }
            if (level != 1 && level != 2) {
                return "task_spec.level must be 1 or 2";
            }
        }

        if (taskSpec.has("max_ticks") && !taskSpec.get("max_ticks").isJsonNull()) {
            try {
                maxTicks = taskSpec.get("max_ticks").getAsInt();
            } catch (Exception e) {
                return "task_spec.max_ticks must be an integer";
            }
            if (maxTicks < 1) {
                return "task_spec.max_ticks must be >= 1";
            }
            if (maxTicks > limits.maxTicksCap) {
                return "task_spec.max_ticks exceeds cap (" + limits.maxTicksCap + ")";
            }
        }

        boolean setWorldTime = false;
        if (taskSpec.has("world_time") && !taskSpec.get("world_time").isJsonNull()) {
            try {
                worldTime = taskSpec.get("world_time").getAsLong();
            } catch (Exception e) {
                return "task_spec.world_time must be a number";
            }
            if (worldTime < 0 || worldTime > 24000) {
                return "task_spec.world_time must be in [0, 24000]";
            }
            timeLabel = "custom";
            setWorldTime = true;
        }
        if (!setWorldTime && taskSpec.has("time_of_day") && !taskSpec.get("time_of_day").isJsonNull()) {
            try {
                String raw = taskSpec.get("time_of_day").getAsString();
                if (raw == null || raw.isBlank()) {
                    return "task_spec.time_of_day is empty";
                }
                String tod = raw.trim().toLowerCase(Locale.ROOT);
                timeLabel = tod;
                worldTime =
                        switch (tod) {
                            case "day", "morning" -> 1000L;
                            case "noon" -> 6000L;
                            case "night", "evening" -> 13000L;
                            case "midnight" -> 18000L;
                            default -> -1L;
                        };
                if (worldTime < 0) {
                    return "task_spec.time_of_day must be one of: day, morning, noon, night, evening, midnight";
                }
            } catch (Exception e) {
                return "task_spec.time_of_day must be a string";
            }
        }

        if (taskSpec.has("entity") && !taskSpec.get("entity").isJsonNull()) {
            try {
                String raw = taskSpec.get("entity").getAsString();
                if (raw == null || raw.isBlank()) {
                    return "task_spec.entity is empty";
                }
                String name = raw.trim().toUpperCase(Locale.ROOT).replace('-', '_');
                if (!limits.allowedEntities.contains(name)) {
                    return "task_spec.entity not allowed: " + name;
                }
                try {
                    hostile = EntityType.valueOf(name);
                } catch (IllegalArgumentException e) {
                    return "task_spec.entity unknown EntityType: " + name;
                }
                baby = hostile == EntityType.ZOMBIE && baby;
            } catch (Exception e) {
                return "task_spec.entity must be a string";
            }
        }

        if (taskSpec.has("baby") && !taskSpec.get("baby").isJsonNull()) {
            try {
                baby = taskSpec.get("baby").getAsBoolean();
            } catch (Exception e) {
                return "task_spec.baby must be a boolean";
            }
            if (hostile != EntityType.ZOMBIE) {
                baby = false;
            }
        }

        JsonArray multi = null;
        if (taskSpec.has("entities") && !taskSpec.get("entities").isJsonNull()) {
            JsonElement el = taskSpec.get("entities");
            if (!el.isJsonArray()) {
                return "task_spec.entities must be an array";
            }
            multi = el.getAsJsonArray();
        } else if (taskSpec.has("hostiles") && !taskSpec.get("hostiles").isJsonNull()) {
            JsonElement el = taskSpec.get("hostiles");
            if (!el.isJsonArray()) {
                return "task_spec.hostiles must be an array";
            }
            multi = el.getAsJsonArray();
        }
        if (multi != null) {
            List<HostileSpawnSpec> parsed = new ArrayList<>();
            String err = parseHostileArray(multi, limits, parsed);
            if (err != null) {
                return err;
            }
            hostiles = parsed;
            if (!parsed.isEmpty()) {
                hostile = parsed.get(0).entity;
                baby = parsed.get(0).baby;
            }
        }

        if (taskSpec.has("scenario_version") && !taskSpec.get("scenario_version").isJsonNull()) {
            try {
                String sv = taskSpec.get("scenario_version").getAsString();
                if (sv == null) {
                    return "task_spec.scenario_version invalid";
                }
                sv = sv.trim();
                if (!VERSION_SAFE.matcher(sv).matches()) {
                    return "task_spec.scenario_version must match [A-Za-z0-9._-]{1,32}";
                }
                ver = sv;
            } catch (Exception e) {
                return "task_spec.scenario_version must be a string";
            }
        }

        JsonObject gear = null;
        if (taskSpec.has("gear")) {
            JsonElement ge = taskSpec.get("gear");
            if (ge != null && ge.isJsonObject()) {
                gear = ge.getAsJsonObject();
            } else if (!taskSpec.get("gear").isJsonNull()) {
                return "task_spec.gear must be an object";
            }
        }
        if (gear != null) {
            GearResult gr;
            gr = parseGear(gear, "weapon", limits, base.weapon);
            if (gr.error != null) {
                return gr.error;
            }
            weapon = gr.material;
            gr = parseGear(gear, "helmet", limits, base.helmet);
            if (gr.error != null) {
                return gr.error;
            }
            helmet = gr.material;
            gr = parseGear(gear, "chestplate", limits, base.chestplate);
            if (gr.error != null) {
                return gr.error;
            }
            chest = gr.material;
            gr = parseGear(gear, "leggings", limits, base.leggings);
            if (gr.error != null) {
                return gr.error;
            }
            leggings = gr.material;
            gr = parseGear(gear, "boots", limits, base.boots);
            if (gr.error != null) {
                return gr.error;
            }
            boots = gr.material;
        }

        ScenarioSpec merged =
                new ScenarioSpec(
                        base.id,
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
                        leggings,
                        boots,
                        base.environmentId,
                        base.inlineLayout,
                        hostiles);
        outResult.spec = merged;
        outResult.taskSpecApplied = true;
        return null;
    }

    private static @Nullable String parseHostileArray(
            JsonArray arr, TaskSpecLimits limits, List<HostileSpawnSpec> out) {
        for (JsonElement itemEl : arr) {
            if (!itemEl.isJsonObject()) {
                return "task_spec.entities[] entries must be objects";
            }
            JsonObject item = itemEl.getAsJsonObject();
            if (!item.has("entity") || item.get("entity").isJsonNull()) {
                return "task_spec.entities[] missing entity";
            }
            String raw;
            try {
                raw = item.get("entity").getAsString();
            } catch (Exception e) {
                return "task_spec.entities[].entity must be a string";
            }
            if (raw == null || raw.isBlank()) {
                return "task_spec.entities[].entity is empty";
            }
            String name = raw.trim().toUpperCase(Locale.ROOT).replace('-', '_');
            if (!limits.allowedEntities.contains(name)) {
                return "task_spec.entities entity not allowed: " + name;
            }
            EntityType type;
            try {
                type = EntityType.valueOf(name);
            } catch (IllegalArgumentException e) {
                return "task_spec.entities unknown EntityType: " + name;
            }
            boolean baby = false;
            if (item.has("baby") && !item.get("baby").isJsonNull()) {
                try {
                    baby = item.get("baby").getAsBoolean() && type == EntityType.ZOMBIE;
                } catch (Exception e) {
                    return "task_spec.entities[].baby must be a boolean";
                }
            }
            double x = Double.NaN;
            double y = Double.NaN;
            double z = Double.NaN;
            if (item.has("x") && !item.get("x").isJsonNull()) {
                x = item.get("x").getAsDouble();
            }
            if (item.has("y") && !item.get("y").isJsonNull()) {
                y = item.get("y").getAsDouble();
            }
            if (item.has("z") && !item.get("z").isJsonNull()) {
                z = item.get("z").getAsDouble();
            }
            int count = 1;
            if (item.has("count") && !item.get("count").isJsonNull()) {
                try {
                    count = item.get("count").getAsInt();
                } catch (Exception e) {
                    return "task_spec.entities[].count must be an integer";
                }
                if (count < 1) {
                    return "task_spec.entities[].count must be >= 1";
                }
            }
            out.add(new HostileSpawnSpec(type, baby, x, y, z, count));
        }
        if (out.isEmpty()) {
            return "task_spec.entities must not be empty";
        }
        return null;
    }

    private static boolean hasKnownTaskSpecContent(JsonObject taskSpec) {
        for (String k : TASK_SPEC_TOP_KEYS) {
            if (!taskSpec.has(k) || taskSpec.get(k).isJsonNull()) {
                continue;
            }
            if ("gear".equals(k)) {
                JsonElement g = taskSpec.get("gear");
                if (g != null && g.isJsonObject() && !g.getAsJsonObject().entrySet().isEmpty()) {
                    return true;
                }
                continue;
            }
            if ("entities".equals(k) || "hostiles".equals(k)) {
                JsonElement a = taskSpec.get(k);
                if (a != null && a.isJsonArray() && !a.getAsJsonArray().isEmpty()) {
                    return true;
                }
                continue;
            }
            return true;
        }
        return false;
    }

    private static final class GearResult {
        @Nullable final String error;
        final Material material;

        GearResult(@Nullable String error, Material material) {
            this.error = error;
            this.material = material;
        }
    }

    private static GearResult parseGear(
            JsonObject gear, String key, TaskSpecLimits limits, Material baseVal) {
        if (!gear.has(key) || gear.get(key).isJsonNull()) {
            return new GearResult(null, baseVal);
        }
        String raw;
        try {
            raw = gear.get(key).getAsString();
        } catch (Exception e) {
            return new GearResult("task_spec.gear." + key + " must be a string", baseVal);
        }
        if (raw == null) {
            return new GearResult("task_spec.gear." + key + " invalid", baseVal);
        }
        if (raw.isBlank() || "NONE".equalsIgnoreCase(raw) || "AIR".equalsIgnoreCase(raw)) {
            return new GearResult(null, Material.AIR);
        }
        Material m = resolveMaterial(raw.trim(), limits);
        if (m == null) {
            return new GearResult("task_spec.gear." + key + " not an allowed item material: " + raw, baseVal);
        }
        return new GearResult(null, m);
    }

    private static @Nullable Material resolveMaterial(String raw, TaskSpecLimits limits) {
        if (raw == null || raw.isBlank() || "NONE".equalsIgnoreCase(raw) || "AIR".equalsIgnoreCase(raw)) {
            return Material.AIR;
        }
        String t = raw.toUpperCase(Locale.ROOT).replace('-', '_');
        Material m = Material.matchMaterial(t);
        if (m == null || !m.isItem()) {
            return null;
        }
        if (limits.allowAnyGearMaterial) {
            return m;
        }
        if (limits.allowedGearMaterials.isEmpty()) {
            return null;
        }
        if (limits.allowedGearMaterials.contains(m.name())) {
            return m;
        }
        return null;
    }
}
