import { Elysia } from "elysia";

const OPENCLAW_URL = process.env.OPENCLAW_URL || "http://localhost:18790";
const OPENCLAW_TOKEN = process.env.OPENCLAW_TOKEN || "smarthub-local-token-2026";

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

      return new Response(response.body, {
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
