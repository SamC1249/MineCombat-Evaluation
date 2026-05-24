package com.minecombatevaluation.config;

import java.util.Collections;
import java.util.List;
import java.util.Locale;
import org.bukkit.Material;
import org.bukkit.entity.EntityType;

/** One registered scenario. Level 1 = global template arena; Level 2 = custom environment. */
public final class ScenarioSpec {

    public final String id;
    /** 1 = template arena; 2 = custom environment spawn/arena. */
    public final int level;
    public final String scenarioVersion;
    public final int maxTicks;
    /** Minecraft world time tick (0–24000). */
    public final long worldTime;
    /** Label for observation meta, e.g. day, night. */
    public final String timeOfDayLabel;
    /** Primary hostile (used when {@link #hostiles} is empty). */
    public final EntityType hostileEntity;
    /** If true, {@link EntityType#ZOMBIE} is spawned as a baby. */
    public final boolean babyZombie;
    public final Material weapon;
    public final Material helmet;
    public final Material chestplate;
    public final Material leggings;
    public final Material boots;
    /** Level 2 environment template id (e.g. cave, beach). Null for Level 1. */
    public final String environmentId;
    /** Optional inline spawn/arena override on this scenario row. */
    public final SpawnLayout inlineLayout;
    /** Explicit hostile spawn list; empty → single {@link #hostileEntity} at hostile anchor. */
    public final List<HostileSpawnSpec> hostiles;

    public ScenarioSpec(
            String id,
            int level,
            String scenarioVersion,
            int maxTicks,
            long worldTime,
            String timeOfDayLabel,
            EntityType hostileEntity,
            boolean babyZombie,
            Material weapon,
            Material helmet,
            Material chestplate,
            Material leggings,
            Material boots,
            String environmentId,
            SpawnLayout inlineLayout,
            List<HostileSpawnSpec> hostiles) {
        this.id = id;
        this.level = level;
        this.scenarioVersion = scenarioVersion;
        this.maxTicks = maxTicks;
        this.worldTime = worldTime;
        this.timeOfDayLabel = timeOfDayLabel;
        this.hostileEntity = hostileEntity;
        this.babyZombie = babyZombie;
        this.weapon = weapon;
        this.helmet = helmet;
        this.chestplate = chestplate;
        this.leggings = leggings;
        this.boots = boots;
        this.environmentId = environmentId;
        this.inlineLayout = inlineLayout;
        this.hostiles = hostiles == null ? List.of() : List.copyOf(hostiles);
    }

    public SpawnLayout resolveLayout(EnvironmentRegistry environments, PluginSettings global) {
        if (inlineLayout != null) {
            return inlineLayout;
        }
        if (environmentId != null && !environmentId.isBlank()) {
            SpawnLayout env = environments.get(environmentId);
            if (env != null) {
                return env;
            }
        }
        return global.defaultLayout();
    }

    public List<HostileSpawnSpec> resolvedHostiles(SpawnLayout layout) {
        if (!hostiles.isEmpty()) {
            return hostiles;
        }
        double x = layout.hostileAnchorX;
        double y = layout.hostileAnchorY;
        double z = layout.hostileAnchorZ;
        return List.of(new HostileSpawnSpec(hostileEntity, babyZombie, x, y, z, 1));
    }

    public ScenarioSpec withHostiles(List<HostileSpawnSpec> next) {
        return new ScenarioSpec(
                id,
                level,
                scenarioVersion,
                maxTicks,
                worldTime,
                timeOfDayLabel,
                hostileEntity,
                babyZombie,
                weapon,
                helmet,
                chestplate,
                leggings,
                boots,
                environmentId,
                inlineLayout,
                next);
    }

    public ScenarioSpec withLevel(int nextLevel) {
        return new ScenarioSpec(
                id,
                nextLevel,
                scenarioVersion,
                maxTicks,
                worldTime,
                timeOfDayLabel,
                hostileEntity,
                babyZombie,
                weapon,
                helmet,
                chestplate,
                leggings,
                boots,
                environmentId,
                inlineLayout,
                hostiles);
    }

    public static Material parseMaterial(String raw, Material fallback) {
        if (raw == null || raw.isBlank()) {
            return fallback;
        }
        String t = raw.trim().toUpperCase(Locale.ROOT);
        if ("NONE".equals(t) || "AIR".equals(t)) {
            return Material.AIR;
        }
        Material m = Material.matchMaterial(t);
        if (m == null || !m.isItem()) {
            return fallback;
        }
        return m;
    }

    public static EntityType parseHostileEntity(String raw) {
        if (raw == null || raw.isBlank()) {
            return EntityType.ZOMBIE;
        }
        String t = raw.trim().toUpperCase(Locale.ROOT).replace('-', '_');
        try {
            return EntityType.valueOf(t);
        } catch (IllegalArgumentException e) {
            return EntityType.ZOMBIE;
        }
    }
}
