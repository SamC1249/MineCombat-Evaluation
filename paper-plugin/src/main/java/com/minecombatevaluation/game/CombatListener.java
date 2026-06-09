package com.minecombatevaluation.game;

import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.EntityDeathEvent;
import org.bukkit.event.entity.PlayerDeathEvent;

public final class CombatListener implements Listener {

    private final EvaluationEngine engine;

    public CombatListener(EvaluationEngine engine) {
        this.engine = engine;
    }

    /** Hostile deaths. Player deaths fire {@link PlayerDeathEvent}, handled below. */
    @EventHandler
    public void onEntityDeath(EntityDeathEvent event) {
        engine.onEntityDeath(event.getEntity());
    }

    /**
     * Player deaths fire {@link PlayerDeathEvent}, which has its own handler list and is NOT
     * delivered to {@link #onEntityDeath}. Without this, a player death is never detected and the
     * episode runs to max_ticks instead of ending as failure/player_died.
     */
    @EventHandler
    public void onPlayerDeath(PlayerDeathEvent event) {
        engine.onEntityDeath(event.getEntity());
    }
}
