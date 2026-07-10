// Single source of truth for the backend URL and how we talk to it.
// VITE_API_BASE is injected by vite.config.js from the repo-root .env:
// an explicit VITE_API_BASE wins, else http://localhost:<BACKEND_PORT>.

const BASE = import.meta.env.VITE_API_BASE;

export async function fetchVideos(limit = 50) {
  const res = await fetch(`${BASE}/api/videos?limit=${limit}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// URL builders for media the <video>/<img> elements load directly.
export function streamUrl(id) {
  return `${BASE}/stream/${id}`;
}

export function thumbUrl(id) {
  return `${BASE}/thumb/${id}`;
}
