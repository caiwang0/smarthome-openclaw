import { useState, useEffect } from "react";
import { fetchAreas } from "../api";
import type { Area } from "../types";

export function useAreas() {
  const [areas, setAreas] = useState<Area[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAreas()
      .then((data) => setAreas(data.areas))
      .catch(() => {}) // Areas are non-critical
      .finally(() => setLoading(false));
  }, []);

  return { areas, loading };
}
