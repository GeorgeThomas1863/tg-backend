import { useVideos } from "./hooks/useVideos";
import { VideoPlayer } from "./components/VideoPlayer";

// Root component. Composes data (useVideos) with presentation (VideoPlayer).
// For now it shows a single video — the most recent one.
export default function App() {
  const { videos, loading, error } = useVideos(1);

  if (loading) return <div style={styles.page}>Loading…</div>;
  if (error) return <div style={styles.page}>Error loading videos: {error}</div>;
  if (videos.length === 0) return <div style={styles.page}>No videos found.</div>;

  return (
    <div style={styles.page}>
      <VideoPlayer video={videos[0]} />
    </div>
  );
}

const styles = {
  page: {
    maxWidth: 900,
    margin: "40px auto",
    padding: "0 16px",
    fontFamily: "system-ui, sans-serif",
    color: "#222",
  },
};
