package com.minecombatevaluation.config;

import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.FileConfiguration;

/** Bounds and whitelists for {@code task_spec} on wire {@code reset} (see TaskSpecMerger). */
public final class TaskSpecLimits {

    /** Default Level-1 hostiles matching shipped scenario rows; merged with config. */
    private static final String[] DEFAULT_ALLOWED_ENTITIES = {
        "ZOMBIE", "CREEPER", "SKELETON", "ENDERMAN", "SPIDER", "WITCH",
        "MAGMA_CUBE", "SLIME", "HOGLIN", "SILVERFISH", "BLAZE", "SHULKER",
        "DROWNED", "HUSK", "STRAY", "CAVE_SPIDER", "PILLAGER", "VINDICATOR",
        "VEX", "EVOKER", "RAVAGER", "PHANTOM", "PIGLIN", "PIGLIN_BRUTE",
        "ZOMBIFIED_PIGLIN", "ZOGLIN", "GUARDIAN", "ELDER_GUARDIAN"
    };

    public final int maxTicksCap;
    public final Set<String> allowedEntities;
    public final boolean allowAnyGearMaterial;
    public final Set<String> allowedGearMaterials;

    public TaskSpecLimits(
            int maxTicksCap,
            Set<String> allowedEntities,
            boolean allowAnyGearMaterial,
            Set<String> allowedGearMaterials) {
        this.maxTicksCap = maxTicksCap;
        this.allowedEntities = allowedEntities;
        this.allowAnyGearMaterial = allowAnyGearMaterial;
        this.allowedGearMaterials = allowedGearMaterials;
    }

    public static TaskSpecLimits from(FileConfiguration c, int defaultMaxTicks) {
        ConfigurationSection root = c.getConfigurationSection("evaluation.task-spec");
        int cap;
        if (root != null && root.contains("max-ticks-cap")) {
            cap = root.getInt("max-ticks-cap", 12_000);
        } else {
            cap = Math.max(12_000, defaultMaxTicks * 5);
        }
        cap = Math.max(1, cap);
        Set<String> entities = new HashSet<>();
        for (String d : DEFAULT_ALLOWED_ENTITIES) {
            entities.add(d);
        }
        if (root != null) {
            List<String> extra = root.getStringList("allowed-entities");
            for (String s : extra) {
                if (s != null && !s.isBlank()) {
                    entities.add(s.trim().toUpperCase(Locale.ROOT).replace('-', '_'));
                }
            }
        }
        boolean allowAny = true;
        Set<String> mats = new HashSet<>();
        if (root != null) {
            allowAny = root.getBoolean("allow-any-gear-material", true);
            for (String s : root.getStringList("allowed-gear-materials")) {
                if (s != null && !s.isBlank()) {
                    mats.add(s.trim().toUpperCase(Locale.ROOT).replace('-', '_'));
                }
            }
        }
        return new TaskSpecLimits(cap, Collections.unmodifiableSet(entities), allowAny, Collections.unmodifiableSet(mats));
    }
}
