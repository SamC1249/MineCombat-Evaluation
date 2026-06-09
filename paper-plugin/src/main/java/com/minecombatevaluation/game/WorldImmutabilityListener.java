package com.minecombatevaluation.game;

import com.minecombatevaluation.config.PluginSettings;
import org.bukkit.World;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.block.BlockBurnEvent;
import org.bukkit.event.block.BlockExplodeEvent;
import org.bukkit.event.block.BlockFadeEvent;
import org.bukkit.event.block.BlockFormEvent;
import org.bukkit.event.block.BlockFromToEvent;
import org.bukkit.event.block.BlockPlaceEvent;
import org.bukkit.event.block.BlockSpreadEvent;
import org.bukkit.event.block.LeavesDecayEvent;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.event.player.PlayerBucketEmptyEvent;
import org.bukkit.event.player.PlayerBucketFillEvent;
import org.bukkit.event.world.StructureGrowEvent;

/**
 * Keeps the evaluation world's blocks immutable so a run cannot corrupt the arena.
 *
 * <p>Covers everything except mob-caused changes (creeper/enderman/blaze), which stay in
 * {@link EnvironmentProtectionListener} because they keep combat damage while dropping block
 * edits. Here we cancel: player block break/place, bucket use, fire burning, fire/liquid spread,
 * block fade/form, liquid flow, leaves decay, sapling growth, and non-entity (bed/anchor)
 * explosions. Gated on {@link PluginSettings#protectWorldBlocks} and the configured world only.
 */
public final class WorldImmutabilityListener implements Listener {

    private final EvaluationEngine engine;

    public WorldImmutabilityListener(EvaluationEngine engine) {
        this.engine = engine;
    }

    private boolean protect(World world) {
        if (world == null) {
            return false;
        }
        PluginSettings s = engine.settings();
        if (!s.protectWorldBlocks) {
            return false;
        }
        return s.worldName.equals(world.getName());
    }

    @EventHandler(ignoreCancelled = true, priority = EventPriority.HIGHEST)
    public void onBlockBreak(BlockBreakEvent event) {
        if (protect(event.getBlock().getWorld())) {
            event.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true, priority = EventPriority.HIGHEST)
    public void onBlockPlace(BlockPlaceEvent event) {
        if (protect(event.getBlock().getWorld())) {
            event.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true, priority = EventPriority.HIGHEST)
    public void onBucketEmpty(PlayerBucketEmptyEvent event) {
        if (protect(event.getBlockClicked().getWorld())) {
            event.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true, priority = EventPriority.HIGHEST)
    public void onBucketFill(PlayerBucketFillEvent event) {
        if (protect(event.getBlockClicked().getWorld())) {
            event.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true, priority = EventPriority.HIGHEST)
    public void onBlockBurn(BlockBurnEvent event) {
        if (protect(event.getBlock().getWorld())) {
            event.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true, priority = EventPriority.HIGHEST)
    public void onBlockSpread(BlockSpreadEvent event) {
        if (protect(event.getBlock().getWorld())) {
            event.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true, priority = EventPriority.HIGHEST)
    public void onBlockFade(BlockFadeEvent event) {
        if (protect(event.getBlock().getWorld())) {
            event.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true, priority = EventPriority.HIGHEST)
    public void onBlockForm(BlockFormEvent event) {
        if (protect(event.getBlock().getWorld())) {
            event.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true, priority = EventPriority.HIGHEST)
    public void onBlockFromTo(BlockFromToEvent event) {
        if (protect(event.getBlock().getWorld())) {
            event.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true, priority = EventPriority.HIGHEST)
    public void onLeavesDecay(LeavesDecayEvent event) {
        if (protect(event.getBlock().getWorld())) {
            event.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true, priority = EventPriority.HIGHEST)
    public void onStructureGrow(StructureGrowEvent event) {
        if (protect(event.getWorld())) {
            event.setCancelled(true);
        }
    }

    /** Bed / respawn-anchor style explosions (no source entity): keep effect, drop block breaks. */
    @EventHandler(ignoreCancelled = true, priority = EventPriority.HIGHEST)
    public void onBlockExplode(BlockExplodeEvent event) {
        if (protect(event.getBlock().getWorld())) {
            event.blockList().clear();
            event.setYield(0.0f);
        }
    }
}
