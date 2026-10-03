"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [tab, setTab] = useState<"signin" | "signup">("signin");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");

  async function handleSignin(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api.login(username, password);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Incorrect username or password.");
    }
  }

  async function handleSignup(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (password !== confirm) { setError("Passwords do not match."); return; }
    try {
      await api.signup(username, password);
      await api.login(username, password);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Could not create account.");
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="card w-full max-w-sm p-6">
        <p className="text-amber text-xs tracking-widest font-semibold mb-1">VISIONINSPECT</p>
        <h1 className="text-xl font-bold mb-4">Quality Console</h1>

        <div className="flex border-b border-line mb-5">
          <button onClick={() => setTab("signin")}
            className={`flex-1 pb-2 text-sm ${tab === "signin" ? "text-ink border-b-2 border-amber" : "text-muted"}`}>
            Sign in
          </button>
          <button onClick={() => setTab("signup")}
            className={`flex-1 pb-2 text-sm ${tab === "signup" ? "text-ink border-b-2 border-amber" : "text-muted"}`}>
            Create account
          </button>
        </div>

        {error && <p className="text-critical text-sm mb-3">{error}</p>}

        {tab === "signin" ? (
          <form onSubmit={handleSignin} className="space-y-3">
            <div>
              <label className="text-sm block mb-1">Username</label>
              <input className="w-full bg-bg border border-line rounded-md px-3 py-2 text-sm"
                value={username} onChange={(e) => setUsername(e.target.value)} required />
            </div>
            <div>
              <label className="text-sm block mb-1">Password</label>
              <input type="password" className="w-full bg-bg border border-line rounded-md px-3 py-2 text-sm"
                value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>
            <button type="submit" className="btn-primary w-full">Sign in</button>
          </form>
        ) : (
          <form onSubmit={handleSignup} className="space-y-3">
            <div>
              <label className="text-sm block mb-1">Choose a username</label>
              <input className="w-full bg-bg border border-line rounded-md px-3 py-2 text-sm"
                minLength={3} maxLength={24} value={username} onChange={(e) => setUsername(e.target.value)} required />
            </div>
            <div>
              <label className="text-sm block mb-1">Choose a password</label>
              <input type="password" minLength={6} className="w-full bg-bg border border-line rounded-md px-3 py-2 text-sm"
                value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>
            <div>
              <label className="text-sm block mb-1">Confirm password</label>
              <input type="password" className="w-full bg-bg border border-line rounded-md px-3 py-2 text-sm"
                value={confirm} onChange={(e) => setConfirm(e.target.value)} required />
            </div>
            <button type="submit" className="btn-primary w-full">Create account</button>
          </form>
        )}
      </div>
    </div>
  );
}
