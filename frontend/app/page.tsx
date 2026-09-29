"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const API = "http://127.0.0.1:8000";

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("visioninspect_token");

    if (token) {
      router.replace("/engineer");
    }
  }, [router]);

  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setLoading(true);
    setError("");

    try {
      // Step 1: Login
      const response = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Invalid email or password"
        );
      }

      // Save JWT
      localStorage.setItem(
        "visioninspect_token",
        data.access_token
      );

      localStorage.setItem(
        "visioninspect_token_type",
        data.token_type || "bearer"
      );

      // Step 2: Get logged-in user
      const meResponse = await fetch(`${API}/auth/me`, {
        headers: {
          Authorization: `Bearer ${data.access_token}`,
        },
      });

      if (!meResponse.ok) {
        throw new Error(
          "Unable to retrieve user information"
        );
      }

      const user = await meResponse.json();

      // Save user information
      localStorage.setItem(
        "visioninspect_user",
        JSON.stringify(user)
      );

      // Step 3: Temporary role routing
      // We will verify the actual role IDs
      // from PostgreSQL before finalizing this.
      if (user.role_id === 2) {
  router.replace("/engineer");
} else if (user.role_id === 3) {
  router.replace("/supervisor");
} else if (user.role_id === 1) {
  // Admin currently uses the engineer workspace
  // until the admin management UI is completed.
  router.replace("/engineer");
} else {
  throw new Error("Unknown user role");
}

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Login failed"
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">

      <div className="login-shell">

        {/* BRAND */}
        <div className="login-brand">

          <div className="brand-mark">
            VI
          </div>

          <div>
            <h1>VisionInspect AI</h1>

            <p>
              Manufacturing Defect Detection &
              Quality Inspection System
            </p>
          </div>

        </div>

        {/* LOGIN CARD */}
        <div className="login-card">

          <div className="login-heading">

            <span>
              SECURE ACCESS
            </span>

            <h2>
              Sign in to VisionInspect
            </h2>

            <p>
              Access the manufacturing quality
              inspection platform.
            </p>

          </div>

          <form onSubmit={login}>

            {/* EMAIL */}
            <div className="login-field">

              <label>
                Email
              </label>

              <input
                type="email"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                placeholder="Enter your email"
                required
              />

            </div>

            {/* PASSWORD */}
            <div className="login-field">

              <label>
                Password
              </label>

              <input
                type="password"
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                placeholder="Enter your password"
                required
              />

            </div>

            {/* ERROR */}
            {error && (
              <div className="login-error">
                ⚠ {error}
              </div>
            )}

            {/* LOGIN BUTTON */}
            <button
              type="submit"
              className="login-button"
              disabled={loading}
            >
              {loading
                ? "AUTHENTICATING..."
                : "SIGN IN"}
            </button>

          </form>

          {/* STATUS */}
          <div className="login-status">

            <span className="status-dot"></span>

            VisionInspect AI Backend

          </div>

        </div>

        {/* FOOTER */}
        <div className="login-footer">

          <span>
            VISIONINSPECT AI
          </span>

          <span>
            AI QUALITY INSPECTION PLATFORM
          </span>

        </div>

      </div>

    </main>
  );
}