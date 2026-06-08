package com.minecombatevaluation;

import com.minecombatevaluation.game.CombatListener;
import com.minecombatevaluation.game.EnvironmentProtectionListener;
import com.minecombatevaluation.game.EvaluationEngine;
import com.minecombatevaluation.game.EvaluationQuitListener;
import com.minecombatevaluation.game.WorldImmutabilityListener;
import com.minecombatevaluation.net.EvaluationTcpServer;
import net.kyori.adventure.text.Component;
import org.bukkit.Bukkit;
import org.bukkit.plugin.java.JavaPlugin;

public final class MineCombatEvaluationPlugin extends JavaPlugin {

    private EvaluationEngine engine;
    private EvaluationTcpServer tcp;

    @Override
    public void onEnable() {
        saveDefaultConfig();
        engine = new EvaluationEngine(this);
        getServer().getPluginManager().registerEvents(new CombatListener(engine), this);
        getServer().getPluginManager().registerEvents(new EnvironmentProtectionListener(engine), this);
        getServer().getPluginManager().registerEvents(new WorldImmutabilityListener(engine), this);
        getServer().getPluginManager().registerEvents(new EvaluationQuitListener(engine), this);
        tcp = new EvaluationTcpServer(this, engine);
        tcp.start();
        Bukkit.getScheduler()
                .runTask(
                        this,
                        () -> {
                            engine.applyWorldIsolationIfReady();
                        });
        getComponentLogger().info(Component.text("MineCombat-Evaluation: TCP control + combat eval enabled."));
    }

    @Override
    public void onDisable() {
        if (tcp != null) {
            tcp.shutdown();
        }
        getComponentLogger().info(Component.text("MineCombat-Evaluation stopped."));
    }
}
