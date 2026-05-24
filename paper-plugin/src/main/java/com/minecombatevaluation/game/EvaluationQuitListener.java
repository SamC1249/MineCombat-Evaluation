package com.minecombatevaluation.game;

import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerQuitEvent;

/** Logs when the evaluation player leaves mid-episode (TCP client may still be stepping). */
public final class EvaluationQuitListener implements Listener {

    private final EvaluationEngine engine;

    public EvaluationQuitListener(EvaluationEngine engine) {
        this.engine = engine;
    }

    @EventHandler
    public void onQuit(PlayerQuitEvent event) {
        engine.onEvaluationPlayerQuit(event.getPlayer().getUniqueId());
    }
}
