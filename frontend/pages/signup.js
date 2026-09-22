import { useState } from "react";
import { useRouter } from "next/router";
import Link from "next/link";
import { signup } from "../lib/api";

export default function Signup() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("inspector");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await signup({ name, email, password, role });
      router.push("/login");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <div style={styles.eyebrow}>VISIONINSPECT AI</div>
        <h1 style={styles.title}>Create an account</h1>
        <p style={styles.subtitle}>Register as a quality engineer or supervisor.</p>

        <form onSubmit={handleSubmit} style={styles.form}>
          <label style={styles.label}>
            Full name
            <input
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              style={styles.input}
              placeholder="Parvatha"
            />
          </label>
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
              placeholder="At least 8 characters"
            />
          </label>
          <label style={styles.label}>
            Role
            <select value={role} onChange={(e) => setRole(e.target.value)} style={styles.input}>
              <option value="inspector">Quality Engineer (Inspector)</option>
              <option value="admin">Factory Supervisor (Admin)</option>
            </select>
          </label>

          {error && <div style={styles.error}>{error}</div>}

          <button type="submit" disabled={loading} style={styles.button}>
            {loading ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p style={styles.footerText}>
          Already registered?{" "}
          <Link href="/login" style={styles.link}>
            Sign in
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
