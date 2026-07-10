import { useState } from "react";
import { postLogin } from "../api/client";

// Password form shown when the backend answers 401. Posts the password;
// on success the session cookie is set and onSuccess() tells the caller
// to refetch. Knows nothing about videos.
export function PasswordGate({ onSuccess }) {
  const [pw, setPw] = useState("");
  const [message, setMessage] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function submitPassword(event) {
    event.preventDefault();
    if (!pw || submitting) return;

    setSubmitting(true);
    setMessage(null);
    const result = await postLogin(pw);
    setSubmitting(false);

    if (!result.success) {
      setMessage(result.message);
      return;
    }

    onSuccess();
  }

  return (
    <form style={styles.form} onSubmit={submitPassword}>
      <label style={styles.label} htmlFor="pw-input">
        Enter the site password
      </label>
      <input
        id="pw-input"
        type="password"
        value={pw}
        onChange={(event) => setPw(event.target.value)}
        style={styles.input}
        autoFocus
      />
      <button style={styles.button} type="submit" disabled={submitting}>
        {submitting ? "Checking…" : "Submit"}
      </button>
      {message && <div style={styles.message}>{message}</div>}
    </form>
  );
}

const styles = {
  form: {
    display: "flex",
    flexDirection: "column",
    gap: 12,
    maxWidth: 320,
    margin: "80px auto 0",
  },
  label: { fontSize: 18, fontWeight: 600 },
  input: {
    padding: "10px 12px",
    fontSize: 16,
    border: "1px solid #ccc",
    borderRadius: 6,
  },
  button: {
    padding: "10px 12px",
    fontSize: 16,
    fontWeight: 600,
    border: "none",
    borderRadius: 6,
    background: "#222",
    color: "#fff",
    cursor: "pointer",
  },
  message: { color: "#c00", fontSize: 14 },
};
