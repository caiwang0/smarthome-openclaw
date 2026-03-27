import { Elysia } from "elysia";
import { callHAService, getEntities, reloadConfigEntry } from "../ha-client";

export const serviceRoutes = new Elysia()
  .post("/api/services/:domain/:service", async ({ params, body }) => {
    try {
      const { domain, service } = params;
      const { entity_id, area_id, ...serviceData } = body as any;

      const target: Record<string, any> = {};
      if (entity_id) target.entity_id = entity_id;
      if (area_id) target.area_id = area_id;

      // If the target entity is unavailable, try reloading its config entry first
      // This fixes flaky DLNA devices (like Xiaomi TVs) that drop connections
      if (entity_id && typeof entity_id === "string") {
        const entities = getEntities();
        const entityState = entities[entity_id];
        if (!entityState || entityState.state === "unavailable") {
          console.log(`Entity ${entity_id} is unavailable, reloading config entry...`);
          await reloadConfigEntry(entity_id);
          // Give HA a moment to reconnect
          await new Promise((r) => setTimeout(r, 2000));
        }
      }

      await callHAService(domain, service, serviceData, target);

      return { success: true, domain, service, target };
    } catch (error: any) {
      return new Response(
        JSON.stringify({ error: "Service call failed", message: error.message }),
        { status: 502, headers: { "Content-Type": "application/json" } }
      );
    }
  });
