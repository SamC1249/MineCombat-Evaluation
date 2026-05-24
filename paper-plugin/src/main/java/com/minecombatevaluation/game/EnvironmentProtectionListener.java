package com.minecombatevaluation.game;

import com.minecombatevaluation.config.PluginSettings;
import org.bukkit.World;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.block.BlockIgniteEvent;
import org.bukkit.event.entity.EntityChangeBlockEvent;
import org.bukkit.event.entity.EntityExplodeEvent;

/** Prevents mobs from modifying blocks in the evaluation world (creepers, endermen, doors, fire). */
public final class EnvironmentProtectionListener implements Listener {

    private final EvaluationEngine engine;

    public EnvironmentProtectionListener(EvaluationEngine engine) {
        this.engine = engine;
    }

    private boolean protect(World world) {
        if (world == null) {
            return false;
        }
        PluginSettings s = engine.settings();
        if (!s.disableMobGriefing) {
            return false;
        }
        return s.worldName.equals(world.getName());
    }

    /** Creeper / ghast / wither-style explosions: keep damage, remove block breaks. */
    @EventHandler(ignoreCancelled = true, priority = EventPriority.HIGHEST)
    public void onEntityExplode(EntityExplodeEvent event) {
        if (!protect(event.getLocation().getWorld())) {
            return;
        }
        event.blockList().clear();
        event.setYield(0.0f);
    }

    /** Endermen picking up blocks, silverfish, etc. */
    @EventHandler(ignoreCancelled = true, priority = EventPriority.HIGHEST)
    public void onEntityChangeBlock(EntityChangeBlockEvent event) {
        if (!protect(event.getBlock().getWorld())) {
            return;
        }
        Entity entity = event.getEntity();
        if (entity instanceof Player) {
            return;
        }
        event.setCancelled(true);
    }

    /** Blaze fireballs and other mob-started fires. */
    @EventHandler(ignoreCancelled = true, priority = EventPriority.HIGHEST)
    public void onBlockIgnite(BlockIgniteEvent event) {
        if (!protect(event.getBlock().getWorld())) {
            return;
        }
        Entity igniter = event.getIgnitingEntity();
        if (igniter != null && !(igniter instanceof Player)) {
            event.setCancelled(true);
        }
    }
}
