"use client";

import { useState } from "react";
import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState("engineer@visioninspect.ai");
  const [password, setPassword] = useState("Engineer@12345");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(email, password);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Login failed. Check your credentials.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center p-6 bg-graphite"
      style={{
        backgroundImage:
          "radial-gradient(circle at 15% 20%, rgba(245,166,35,0.06), transparent 40%)",
      }}
    >
      <div className="card w-full max-w-sm px-8 py-9">
        <p className="eyebrow mb-1">VisionInspect AI</p>
        <h1 className="font-display text-xl font-semibold mb-1">Quality Console Login</h1>
        <p className="text-sm text-muted mb-7">
          Manufacturing defect detection &amp; quality inspection platform
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-muted mb-1.5">Email</label>
            <input
              type="email"
              required
              className="input-field"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs text-muted mb-1.5">Password</label>
            <input
              type="password"
              required
              className="input-field"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error && <p className="text-sm text-critical">{error}</p>}
          <button type="submit" disabled={busy} className="btn-primary w-full">
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <div className="mt-6 pt-5 border-t border-line text-xs text-muted font-mono leading-relaxed">
          Demo accounts (seeded by backend/seed.py):
          <br />
          admin@visioninspect.ai / Admin@12345
          <br />
          engineer@visioninspect.ai / Engineer@12345
          <br />
          supervisor@visioninspect.ai / Supervisor@12345
          <br />
          manager@visioninspect.ai / Manager@12345
        </div>
      </div>
    </div>
  );
}
