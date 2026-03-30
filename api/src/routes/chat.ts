import { Elysia } from "elysia";

const OPENCLAW_URL = process.env.OPENCLAW_URL || "http://localhost:18790";
const OPENCLAW_TOKEN = process.env.OPENCLAW_TOKEN || "smarthub-local-token-2026";
const KEEPALIVE_MS = 5_000;
const UPSTREAM_IDLE_TIMEOUT_MS = 300_000; // 5 min — tool use can be slow

export const chatRoutes = new Elysia()
  .post("/api/chat", async ({ body }) => {
    const { message } = body as { message?: string };

    if (!message || typeof message !== "string" || !message.trim()) {
      return new Response(
        JSON.stringify({ error: "Message is required" }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    try {
      const response = await fetch(`${OPENCLAW_URL}/v1/chat/completions`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${OPENCLAW_TOKEN}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: "openclaw:main",
          messages: [{ role: "user", content: message.trim() }],
          stream: true,
        }),
      });

      if (!response.ok || !response.body) {
        return new Response(
          JSON.stringify({ error: "OpenClaw is offline or returned an error" }),
          { status: 502, headers: { "Content-Type": "application/json" } }
        );
      }

      const upstream = response.body.getReader();
      const enc = new TextEncoder();
      const keepaliveBytes = enc.encode(": keepalive\n\n");
      const doneBytes = enc.encode("data: [DONE]\n\n");
      let closed = false;

      const stream = new ReadableStream({
        start(controller) {
          // Keepalive: send SSE comments every 5s to prevent connection drop
          const keepaliveTimer = setInterval(() => {
            if (!closed) {
              try { controller.enqueue(keepaliveBytes); } catch {}
            }
          }, KEEPALIVE_MS);

          // Idle timeout: if upstream goes completely silent, close gracefully
          let idleTimer = setTimeout(() => closeStream("timeout"), UPSTREAM_IDLE_TIMEOUT_MS);

          function resetIdle() {
            clearTimeout(idleTimer);
            idleTimer = setTimeout(() => closeStream("timeout"), UPSTREAM_IDLE_TIMEOUT_MS);
          }

          function closeStream(reason?: string) {
            if (closed) return;
            closed = true;
            clearInterval(keepaliveTimer);
            clearTimeout(idleTimer);
            try {
              // Always send [DONE] so the frontend resets
              controller.enqueue(doneBytes);
              controller.close();
            } catch {}
            upstream.cancel().catch(() => {});
          }

          // Read loop runs independently of pull()
          (async () => {
            try {
              while (!closed) {
                const { done, value } = await upstream.read();
                if (done) { closeStream(); return; }
                resetIdle();
                try { controller.enqueue(value); } catch { return; }
              }
            } catch {
              closeStream("error");
            }
          })();
        },
        cancel() {
          closed = true;
          upstream.cancel().catch(() => {});
        },
      });

      return new Response(stream, {
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          "Connection": "keep-alive",
        },
      });
    } catch (err: any) {
      console.error("OpenClaw proxy error:", err.message);
      return new Response(
        JSON.stringify({ error: "OpenClaw is offline. Check that the gateway is running." }),
        { status: 502, headers: { "Content-Type": "application/json" } }
      );
    }
  });
