import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../services/api";

function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("quality_engineer");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();

    setError("");
    setLoading(true);

    try {
      await api.post("/auth/register", {
        name,
        email,
        password,
        role,
      });

      navigate("/login");

    } catch (error) {
      setError(
        error.response?.data?.detail ||
        "Unable to create your account."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">

      <section className="login-brand">

        <div className="brand-header">

          <div className="brand-logo">
            V
          </div>

          <div>
            <h2>VisionInspect AI</h2>
            <span>QUALITY INTELLIGENCE</span>
          </div>

        </div>


        <div className="brand-content">

          <div className="eyebrow">
            JOIN THE PLATFORM
          </div>

          <h1>
            Build
            <br />
            <span>Better Quality.</span>
          </h1>

          <p>
            Create your account and access
            intelligent manufacturing inspection
            tools.
          </p>

          <div className="feature-list">

            <div className="feature">
              <div className="feature-icon">
                ✓
              </div>

              <div>
                <strong>Secure Access</strong>
                <span>
                  Role-based authentication
                </span>
              </div>
            </div>

            <div className="feature">
              <div className="feature-icon">
                ◉
              </div>

              <div>
                <strong>AI Inspection</strong>
                <span>
                  Computer vision quality control
                </span>
              </div>
            </div>

          </div>

        </div>

      </section>


      <section className="login-form-section">

        <div className="login-form-container">

          <div className="form-heading">

            <span className="form-label">
              GET STARTED
            </span>

            <h2>Create account</h2>

            <p>
              Set up your VisionInspect workspace.
            </p>

          </div>


          <form onSubmit={handleRegister}>

            <div className="form-group">

              <label>Full name</label>

              <div className="input-wrapper">

                <span>●</span>

                <input
                  type="text"
                  placeholder="Your full name"
                  value={name}
                  onChange={(e) =>
                    setName(e.target.value)
                  }
                  required
                />

              </div>

            </div>


            <div className="form-group">

              <label>Email address</label>

              <div className="input-wrapper">

                <span>✉</span>

                <input
                  type="email"
                  placeholder="you@company.com"
                  value={email}
                  onChange={(e) =>
                    setEmail(e.target.value)
                  }
                  required
                />

              </div>

            </div>


            <div className="form-group">

              <label>Password</label>

              <div className="input-wrapper">
  <span>◆</span>

  <input
    type={showPassword ? "text" : "password"}
    placeholder="Create a password"
    value={password}
    onChange={(e) =>
      setPassword(e.target.value)
    }
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


            <div className="form-group">

              <label>Account role</label>

              <select
                value={role}
                onChange={(e) =>
                  setRole(e.target.value)
                }
              >

                <option value="quality_engineer">
                  Quality Engineer
                </option>

                <option value="factory_supervisor">
                  Factory Supervisor
                </option>

              </select>

            </div>


            {error && (
              <div className="login-error">
                <span>!</span>
                {error}
              </div>
            )}


            <button
              type="submit"
              className="login-button"
              disabled={loading}
            >
              {loading
                ? "Creating account..."
                : "Create account"}
            </button>

          </form>


          <div className="register-prompt">

            Already have an account?

            <Link to="/login">
              Sign in
            </Link>

          </div>

        </div>

      </section>

    </div>
  );
}

export default Register;