import { useState, useEffect, useCallback } from "react";
import { fetchDevices } from "../api";
import type { Device } from "../types";

const POLL_INTERVAL_MS = 10_000;

export function useDevices() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [newDeviceNames, setNewDeviceNames] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await fetchDevices();
      setDevices(data.devices);
      setNewDeviceNames(data.new_devices);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [refresh]);

  return { devices, newDeviceNames, loading, error, refresh };
}
