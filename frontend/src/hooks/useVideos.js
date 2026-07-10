import { useEffect, useState } from "react";
import { fetchVideos } from "../api/client";

// Fetches the list of videos and exposes loading/error/auth state.
// A 401 surfaces as `unauthorized` (the password gate), not as an error.
// `refetch` re-runs the fetch — called after a successful login.
export function useVideos(limit = 50) {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [unauthorized, setUnauthorized] = useState(false);
  const [fetchCount, setFetchCount] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setUnauthorized(false);

    fetchVideos(limit)
      .then((data) => {
        if (cancelled) return;
        setVideos(data);
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err.status === 401) setUnauthorized(true);
        else setError(err.message);
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [limit, fetchCount]);

  const refetch = () => setFetchCount((count) => count + 1);

  return { videos, loading, error, unauthorized, refetch };
}
