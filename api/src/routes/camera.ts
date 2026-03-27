import { Elysia } from "elysia";
import { getHAUrl, getHAToken } from "../ha-client";

export const cameraRoutes = new Elysia()
  .get("/api/camera/:entity_id/snapshot", async ({ params }) => {
    try {
      const { entity_id } = params;
      const haUrl = getHAUrl();
      const token = getHAToken();
      const timestamp = Date.now();

      const response = await fetch(
        `${haUrl}/api/camera_proxy/${entity_id}?time=${timestamp}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (!response.ok) {
        return new Response(
          JSON.stringify({ error: "Camera snapshot failed", status: response.status }),
          { status: response.status, headers: { "Content-Type": "application/json" } }
        );
      }

      const imageBuffer = await response.arrayBuffer();
      return new Response(imageBuffer, {
        headers: {
          "Content-Type": response.headers.get("Content-Type") || "image/jpeg",
          "Cache-Control": "no-cache",
        },
      });
    } catch (error: any) {
      return new Response(
        JSON.stringify({ error: "Camera proxy failed", message: error.message }),
        { status: 502, headers: { "Content-Type": "application/json" } }
      );
    }
  });
