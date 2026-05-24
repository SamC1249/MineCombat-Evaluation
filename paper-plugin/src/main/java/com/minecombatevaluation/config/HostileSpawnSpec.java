package com.minecombatevaluation.config;

import org.bukkit.entity.EntityType;

/** One hostile spawn entry (entity type, optional position, count). */
public final class HostileSpawnSpec {

    public final EntityType entity;
    public final boolean baby;
    /** NaN = use environment default hostile anchor. */
    public final double x;
    public final double y;
    public final double z;
    public final int count;

    public HostileSpawnSpec(EntityType entity, boolean baby, double x, double y, double z, int count) {
        this.entity = entity;
        this.baby = baby;
        this.x = x;
        this.y = y;
        this.z = z;
        this.count = Math.max(1, count);
    }

    public boolean hasPosition() {
        return !Double.isNaN(x) && !Double.isNaN(y) && !Double.isNaN(z);
    }

    public HostileSpawnSpec withPosition(double px, double py, double pz) {
        return new HostileSpawnSpec(entity, baby, px, py, pz, count);
    }

    public HostileSpawnSpec withEntity(EntityType t, boolean b) {
        return new HostileSpawnSpec(t, b, x, y, z, count);
    }

    public HostileSpawnSpec withCount(int c) {
        return new HostileSpawnSpec(entity, baby, x, y, z, c);
    }
}
