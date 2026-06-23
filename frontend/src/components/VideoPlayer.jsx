import { streamUrl, thumbUrl } from "../api/client";

// Renders a single video with native controls. Takes one video object;
// knows nothing about fetching.
export function VideoPlayer({ video }) {
  return (
    <div style={styles.wrap}>
      <h1 style={styles.title}>{video.name}</h1>
      <video style={styles.video} src={streamUrl(video.id)} poster={thumbUrl(video.id)} controls preload="metadata" />
      <div style={styles.meta}>
        {video.width && video.height ? `${video.width}×${video.height} · ` : ""}
        {video.duration ? `${Math.round(video.duration)}s · ` : ""}
        {(video.size / (1024 * 1024)).toFixed(1)} MB
      </div>
    </div>
  );
}

const styles = {
  wrap: {},
  title: { fontSize: 20, fontWeight: 600, marginBottom: 16 },
  video: { width: "100%", borderRadius: 8, background: "#000" },
  meta: { marginTop: 12, color: "#666", fontSize: 14 },
};
