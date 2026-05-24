package com.minecombatevaluation.config;

import org.bukkit.Location;
import org.bukkit.World;

/** Per-environment or per-scenario spawn and arena bounds (Level 2). */
public final class SpawnLayout {

    public final double playerX;
    public final double playerY;
    public final double playerZ;
    public final float playerYaw;
    public final float playerPitch;
    public final double hostileAnchorX;
    public final double hostileAnchorY;
    public final double hostileAnchorZ;
    public final double arenaCenterX;
    public final double arenaCenterY;
    public final double arenaCenterZ;
    public final double halfSize;
    public final double mobClearHalfSize;
    public final double minYDelta;
    public final double maxYDelta;

    public SpawnLayout(
            double playerX,
            double playerY,
            double playerZ,
            float playerYaw,
            float playerPitch,
            double hostileAnchorX,
            double hostileAnchorY,
            double hostileAnchorZ,
            double arenaCenterX,
            double arenaCenterY,
            double arenaCenterZ,
            double halfSize,
            double mobClearHalfSize,
            double minYDelta,
            double maxYDelta) {
        this.playerX = playerX;
        this.playerY = playerY;
        this.playerZ = playerZ;
        this.playerYaw = playerYaw;
        this.playerPitch = playerPitch;
        this.hostileAnchorX = hostileAnchorX;
        this.hostileAnchorY = hostileAnchorY;
        this.hostileAnchorZ = hostileAnchorZ;
        this.arenaCenterX = arenaCenterX;
        this.arenaCenterY = arenaCenterY;
        this.arenaCenterZ = arenaCenterZ;
        this.halfSize = halfSize;
        this.mobClearHalfSize = mobClearHalfSize;
        this.minYDelta = minYDelta;
        this.maxYDelta = maxYDelta;
    }

    public Location playerSpawn(World world) {
        return new Location(world, playerX, playerY, playerZ, playerYaw, playerPitch);
    }

    public Location arenaCenter(World world) {
        return new Location(world, arenaCenterX, arenaCenterY, arenaCenterZ);
    }
}
