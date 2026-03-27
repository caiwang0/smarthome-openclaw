import { Elysia } from "elysia";
import { getAggregatedDevices, getNewDeviceNames } from "../device-aggregator";

export const deviceRoutes = new Elysia()
  .get("/api/devices", async () => {
    try {
      const devices = await getAggregatedDevices();
      const newDevices = getNewDeviceNames(devices);
      return {
        devices,
        new_devices: newDevices,
        count: devices.length,
      };
    } catch (error: any) {
      return new Response(
        JSON.stringify({ error: "Failed to fetch devices", message: error.message }),
        { status: 502, headers: { "Content-Type": "application/json" } }
      );
    }
  })
  .get("/api/devices/:id", async ({ params }) => {
    try {
      const devices = await getAggregatedDevices();
      const device = devices.find((d) => d.id === params.id);
      if (!device) {
        return new Response(
          JSON.stringify({ error: "Device not found" }),
          { status: 404, headers: { "Content-Type": "application/json" } }
        );
      }
      return device;
    } catch (error: any) {
      return new Response(
        JSON.stringify({ error: "Failed to fetch device", message: error.message }),
        { status: 502, headers: { "Content-Type": "application/json" } }
      );
    }
  });
