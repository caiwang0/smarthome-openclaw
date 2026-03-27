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

      // If targeting a specific entity, validate it exists before proceeding
      if (entity_id && typeof entity_id === "string") {
        const entities = getEntities();
        const entityState = entities[entity_id];

        if (!entityState) {
          // Entity not found in HA at all — return 404 immediately
          return new Response(
            JSON.stringify({
              error: "Entity not found",
              message: `Entity ${entity_id} does not exist in Home Assistant`,
              entity_id,
            }),
            { status: 404, headers: { "Content-Type": "application/json" } }
          );
        }

        // If the entity exists but is unavailable, try reloading its config entry
        // This fixes flaky DLNA devices (like Xiaomi TVs) that drop connections
        if (entityState.state === "unavailable") {
          console.log(`[OPENCLAW API] Entity ${entity_id} is unavailable, attempting config entry reload...`);
          await reloadConfigEntry(entity_id);
          // Give HA a moment to reconnect
          await new Promise((r) => setTimeout(r, 2000));
        }
      }

      await callHAService(domain, service, serviceData, target);

      return { success: true, domain, service, target };
    } catch (error: any) {
      // Distinguish between "service not found" and other HA errors
      const msg = error.message || "";
      if (msg.includes("not found")) {
        return new Response(
          JSON.stringify({
            error: "Service not found",
            message: msg,
            hint: `Check that '${params.domain}.${params.service}' is a valid HA service. Common services: turn_on, turn_off, toggle (for switch domain only).`,
          }),
          { status: 400, headers: { "Content-Type": "application/json" } }
        );
      }
      return new Response(
        JSON.stringify({ error: "Service call failed", message: msg }),
        { status: 502, headers: { "Content-Type": "application/json" } }
      );
    }
  });
