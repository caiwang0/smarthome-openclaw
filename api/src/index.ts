import { Elysia } from "elysia";
import { connectToHA, isConnectionReady } from "./ha-client";
import { deviceRoutes } from "./routes/devices";
import { areaRoutes } from "./routes/areas";
import { serviceRoutes } from "./routes/services";
import { cameraRoutes } from "./routes/camera";
import { chatRoutes } from "./routes/chat";
import { xiaomiRoutes } from "./routes/xiaomi";

const app = new Elysia()
  .onBeforeHandle(({ request }) => {
    const url = new URL(request.url);
    console.log(`[OPENCLAW API] --> ${request.method} ${url.pathname}`);

    // Allow health endpoint without HA connection
    if (url.pathname === "/api/health") return;

    // Block data endpoints until HA connection is ready
    if (!isConnectionReady()) {
      return new Response(
        JSON.stringify({
          error: "API is starting",
          message: "Home Assistant connection is not established yet. Please retry in a few seconds.",
        }),
        { status: 503, headers: { "Content-Type": "application/json", "Retry-After": "5" } }
      );
    }
  })
  .onAfterHandle(({ request, response }) => {
    const url = new URL(request.url);
    const status = response instanceof Response ? response.status : 200;
    console.log(`[OPENCLAW API] <-- ${request.method} ${url.pathname} ${status}`);
  })
  .onError(({ request, error }) => {
    const url = new URL(request.url);
    console.error(`[OPENCLAW API] ERR ${request.method} ${url.pathname}`, error.message);
  })
  .get("/api/health", () => ({
    status: "ok",
    ha_connected: isConnectionReady(),
  }))
  .use(deviceRoutes)
  .use(areaRoutes)
  .use(serviceRoutes)
  .use(cameraRoutes)
  .use(chatRoutes)
  .use(xiaomiRoutes)
  .listen(Number(process.env.API_PORT) || 3001);

console.log(`[OPENCLAW API] Server running on port ${app.server?.port}`);

connectToHA()
  .then(() => console.log("[OPENCLAW API] HA connection established"))
  .catch((err) => {
    console.error("[OPENCLAW API] FAILED to connect to HA:", err.message);
    console.error("[OPENCLAW API] Make sure HA is running and HA_TOKEN is set in .env");
  });
