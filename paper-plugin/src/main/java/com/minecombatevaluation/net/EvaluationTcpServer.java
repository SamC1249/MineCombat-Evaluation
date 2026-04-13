package com.minecombatevaluation.net;

import com.minecombatevaluation.game.EvaluationEngine;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.logging.Level;
import org.bukkit.Bukkit;
import org.bukkit.plugin.java.JavaPlugin;

public final class EvaluationTcpServer implements Runnable {

    private static final int SYNC_TIMEOUT_SEC = 120;

    private final JavaPlugin plugin;
    private final EvaluationEngine engine;
    private volatile boolean running;
    private volatile ServerSocket serverSocket;
    private Thread thread;

    public EvaluationTcpServer(JavaPlugin plugin, EvaluationEngine engine) {
        this.plugin = plugin;
        this.engine = engine;
    }

    public void start() {
        running = true;
        thread = new Thread(this, "minecombat-tcp");
        thread.setDaemon(true);
        thread.start();
    }

    public void shutdown() {
        running = false;
        ServerSocket ss = this.serverSocket;
        if (ss != null && !ss.isClosed()) {
            try {
                ss.close();
            } catch (IOException ignored) {
            }
        }
        if (thread != null) {
            thread.interrupt();
        }
    }

    @Override
    public void run() {
        String bind = plugin.getConfig().getString("network.bind", "127.0.0.1");
        int port = plugin.getConfig().getInt("network.port", 8765);
        try {
            InetAddress addr = InetAddress.getByName(bind);
            ServerSocket ss = new ServerSocket(port, 16, addr);
            this.serverSocket = ss;
            plugin.getLogger().info("Evaluation TCP listening on " + bind + ":" + port);
            while (running) {
                Socket client;
                try {
                    client = ss.accept();
                } catch (IOException e) {
                    if (!running) {
                        break;
                    }
                    plugin.getLogger().log(Level.WARNING, "accept failed", e);
                    continue;
                }
                client.setTcpNoDelay(true);
                handleClient(client);
            }
        } catch (IOException e) {
            if (running) {
                plugin.getLogger().log(Level.SEVERE, "TCP server failed", e);
            }
        }
    }

    private void handleClient(Socket client) {
        try (Socket c = client;
                BufferedReader in =
                        new BufferedReader(
                                new InputStreamReader(c.getInputStream(), StandardCharsets.UTF_8));
                PrintWriter out =
                        new PrintWriter(
                                new OutputStreamWriter(c.getOutputStream(), StandardCharsets.UTF_8),
                                true)) {
            String line;
            while (running && (line = in.readLine()) != null) {
                String response = submitSync(line);
                out.println(response);
            }
        } catch (IOException e) {
            plugin.getLogger().log(Level.FINE, "client io end", e);
        }
    }

    private String submitSync(String line) {
        CompletableFuture<String> done = new CompletableFuture<>();
        Bukkit.getScheduler()
                .runTask(
                        plugin,
                        () -> {
                            try {
                                done.complete(engine.handleIncomingJson(line));
                            } catch (Throwable t) {
                                plugin.getLogger().log(Level.SEVERE, "eval handler", t);
                                done.complete(engine.error(t.getMessage()));
                            }
                        });
        try {
            return done.get(SYNC_TIMEOUT_SEC, TimeUnit.SECONDS);
        } catch (TimeoutException e) {
            return engine.error("server tick did not run (timeout)");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return engine.error("interrupted");
        } catch (ExecutionException e) {
            return engine.error(e.getCause() != null ? e.getCause().getMessage() : "error");
        }
    }
}
