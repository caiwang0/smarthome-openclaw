import { Elysia } from "elysia";
import { connectToHA } from "./ha-client";
import { deviceRoutes } from "./routes/devices";
import { areaRoutes } from "./routes/areas";
import { serviceRoutes } from "./routes/services";
import { cameraRoutes } from "./routes/camera";
import { chatRoutes } from "./routes/chat";

const app = new Elysia()
  .get("/api/health", () => ({ status: "ok" }))
  .use(deviceRoutes)
  .use(areaRoutes)
  .use(serviceRoutes)
  .use(cameraRoutes)
  .use(chatRoutes)
  .listen(Number(process.env.API_PORT) || 3001);

console.log(`API running on port ${app.server?.port}`);

connectToHA()
  .then(() => console.log("HA connection established"))
  .catch((err) => {
    console.error("Failed to connect to HA:", err.message);
    console.error("Make sure HA is running and HA_TOKEN is set in .env");
  });
