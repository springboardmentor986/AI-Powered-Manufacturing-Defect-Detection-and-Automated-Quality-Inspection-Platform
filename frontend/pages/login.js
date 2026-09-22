import { useState } from "react";
import { useRouter } from "next/router";
import Link from "next/link";
import { login } from "../lib/api";

export default function Login() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login({ email, password });
      router.push("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <div style={styles.scanBox}>
          <div style={styles.scanLine} />
          <span style={styles.scanLabel}>SCANNING UNIT</span>
        </div>

        <div style={styles.eyebrow}>VISIONINSPECT AI</div>
        <h1 style={styles.title}>Sign in to inspect</h1>
        <p style={styles.subtitle}>Quality engineers and supervisors only.</p>

        <form onSubmit={handleSubmit} style={styles.form}>
          <label style={styles.label}>
            Email
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={styles.input}
              placeholder="you@plant.com"
            />
          </label>
          <label style={styles.label}>
            Password
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={styles.input}
              placeholder="••••••••"
            />
          </label>

          {error && <div style={styles.error}>{error}</div>}

          <button type="submit" disabled={loading} style={styles.button}>
            {loading ? "Checking credentials…" : "Sign in"}
          </button>
        </form>

        <p style={styles.footerText}>
          No account yet?{" "}
          <Link href="/signup" style={styles.link}>
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "24px",
  },
  card: {
    width: "100%",
    maxWidth: 400,
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: 12,
    padding: "32px",
  },
  scanBox: {
    position: "relative",
    height: 64,
    borderRadius: 8,
    border: "1px dashed var(--border)",
    marginBottom: 24,
    overflow: "hidden",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "var(--surface-2)",
  },
  scanLine: {
    position: "absolute",
    left: 0,
    top: 0,
    width: "3px",
    height: "100%",
    background: "var(--accent)",
    boxShadow: "0 0 12px var(--accent)",
    animation: "scan 2.4s ease-in-out infinite",
  },
  scanLabel: {
    fontFamily: "var(--font-mono)",
    fontSize: 11,
    letterSpacing: "0.12em",
    color: "var(--text-muted)",
  },
  eyebrow: {
    fontFamily: "var(--font-mono)",
    fontSize: 12,
    letterSpacing: "0.14em",
    color: "var(--accent)",
    marginBottom: 8,
  },
  title: {
    fontFamily: "var(--font-display)",
    fontSize: 26,
    margin: "0 0 6px",
  },
  subtitle: {
    color: "var(--text-muted)",
    fontSize: 14,
    margin: "0 0 24px",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: 16,
  },
  label: {
    display: "flex",
    flexDirection: "column",
    gap: 6,
    fontSize: 13,
    color: "var(--text-muted)",
  },
  input: {
    background: "var(--surface-2)",
    border: "1px solid var(--border)",
    borderRadius: 8,
    padding: "10px 12px",
    color: "var(--text)",
    fontSize: 14,
  },
  button: {
    marginTop: 8,
    background: "var(--accent)",
    color: "#14161a",
    border: "none",
    borderRadius: 8,
    padding: "12px",
    fontWeight: 600,
    fontSize: 14,
    cursor: "pointer",
  },
  error: {
    background: "rgba(255,92,92,0.1)",
    border: "1px solid var(--danger)",
    color: "var(--danger)",
    padding: "10px 12px",
    borderRadius: 8,
    fontSize: 13,
  },
  footerText: {
    marginTop: 20,
    fontSize: 13,
    color: "var(--text-muted)",
    textAlign: "center",
  },
  link: {
    color: "var(--accent)",
    textDecoration: "none",
  },
};
