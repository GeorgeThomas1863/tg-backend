import { useEffect, useState } from "react";
import { fetchVideos } from "../api/client";

// Fetches the list of videos once on mount and exposes loading/error state.
// Components call this and just render — no fetch logic in the JSX.
export function useVideos(limit = 50) {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    fetchVideos(limit)
      .then((data) => {
        if (!cancelled) {
          setVideos(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message);
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [limit]);

  return { videos, loading, error };
}
