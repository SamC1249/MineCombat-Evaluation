package com.minecombatevaluation.game;

import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.EntityDeathEvent;

public final class CombatListener implements Listener {

    private final EvaluationEngine engine;

    public CombatListener(EvaluationEngine engine) {
        this.engine = engine;
    }

    @EventHandler
    public void onEntityDeath(EntityDeathEvent event) {
        engine.onEntityDeath(event.getEntity());
    }
}
