import { Elysia } from "elysia";
import { getAreas } from "../device-aggregator";

export const areaRoutes = new Elysia()
  .get("/api/areas", async () => {
    try {
      const areas = await getAreas();
      return { areas };
    } catch (error: any) {
      return new Response(
        JSON.stringify({ error: "Failed to fetch areas", message: error.message }),
        { status: 502, headers: { "Content-Type": "application/json" } }
      );
    }
  });
