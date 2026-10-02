import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../services/api";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();

    setError("");
    setLoading(true);

    try {
      const response = await api.post("/auth/login", {
        email,
        password,
      });

      localStorage.setItem("token", response.data.access_token);
      localStorage.setItem("refresh_token", response.data.refresh_token);
      localStorage.setItem("role", response.data.role);

      navigate("/dashboard");
    } catch (error) {
      setError(
        error.response?.data?.detail ||
          "Unable to sign in. Please check your credentials."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      {/* LEFT BRAND PANEL */}
      <section className="login-brand">
        <div className="brand-header">
          <div className="brand-logo">V</div>

          <div>
            <h2>VisionInspect AI</h2>
            <span>QUALITY INTELLIGENCE</span>
          </div>
        </div>

        <div className="brand-content">
          <div className="eyebrow">AI-POWERED MANUFACTURING</div>

          <h1>
            Smarter
            <br />
            <span>Quality Inspection.</span>
          </h1>

          <p>
            Transform visual inspection with intelligent computer vision and
            automated defect detection.
          </p>

          <div className="feature-list">
            <div className="feature">
              <div className="feature-icon">✓</div>
              <div>
                <strong>Automated Inspection</strong>
                <span>Reduce manual quality checks</span>
              </div>
            </div>

            <div className="feature">
              <div className="feature-icon">◉</div>
              <div>
                <strong>AI-Based Detection</strong>
                <span>Identify manufacturing anomalies</span>
              </div>
            </div>

            <div className="feature">
              <div className="feature-icon">▦</div>
              <div>
                <strong>Quality Analytics</strong>
                <span>Track inspection performance</span>
              </div>
            </div>
          </div>
        </div>

        <div className="brand-footer">
          VisionInspect AI · Intelligent Quality Control
        </div>
      </section>

      {/* LOGIN PANEL */}
      <section className="login-form-section">
        <div className="login-form-container">
          <div className="mobile-logo">
            <div className="brand-logo">V</div>
            <strong>VisionInspect AI</strong>
          </div>

          <div className="form-heading">
            <span className="form-label">SECURE ACCESS</span>

            <h2>Welcome back</h2>

            <p>Sign in to access your inspection workspace.</p>
          </div>

          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label htmlFor="login-email">Email address</label>

              <div className="input-wrapper">
                <span className="input-icon">✉</span>

                <input
                  id="login-email"
                  type="email"
                  placeholder="you@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="login-password">Password</label>

              <div className="input-wrapper">
                <span className="input-icon">◆</span>

                <input
                  id="login-password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                />

                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <svg
                      viewBox="0 0 24 24"
                      width="19"
                      height="19"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  ) : (
                    <svg
                      viewBox="0 0 24 24"
                      width="19"
                      height="19"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M3 3l18 18" />
                      <path d="M10.6 10.6a2 2 0 0 0 2.8 2.8" />
                      <path d="M9.9 5.2A10.7 10.7 0 0 1 12 5c6.5 0 10 7 10 7a17.2 17.2 0 0 1-3.2 4.2" />
                      <path d="M6.6 6.6C3.8 8.4 2 12 2 12s3.5 7 10 7c1.5 0 2.8-.3 4-.8" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {error && (
              <div className="login-error" role="alert">
                <span>!</span>
                {error}
              </div>
            )}

            <button
              type="submit"
              className="login-button"
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="login-spinner" />
                  Signing in...
                </>
              ) : (
                <>
                  Sign in
                  <span className="login-arrow">→</span>
                </>
              )}
            </button>
          </form>

          <div className="register-prompt">
            <span>Don't have an account?</span>
            <Link to="/register">Create account</Link>
          </div>

          <div className="security-note">
            <span>🔒</span>
            Secure authentication powered by JWT
          </div>
        </div>
      </section>
    </div>
  );
}

export default Login;
