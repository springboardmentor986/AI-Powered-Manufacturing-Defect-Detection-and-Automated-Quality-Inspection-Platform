import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register, ApiError } from "../services/api";

function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [roleId, setRoleId] = useState(1); // 1 = Quality Engineer, 2 = Factory Supervisor
  const [supervisorCode, setSupervisorCode] = useState("");
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});

  const navigate = useNavigate();

  const validateClientSide = () => {
    const errors = {};

    if (!name.trim()) {
      errors.name = "Full name is required.";
    }

    if (!email.trim()) {
      errors.email = "Email address is required.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errors.email = "Please enter a valid email address.";
    }

    if (!password) {
      errors.password = "Password is required.";
    } else {
      if (password.length < 8) {
        errors.password = "Password must be at least 8 characters long.";
      } else if (!/[A-Z]/.test(password)) {
        errors.password = "Must contain at least one uppercase letter.";
      } else if (!/[a-z]/.test(password)) {
        errors.password = "Must contain at least one lowercase letter.";
      } else if (!/[0-9]/.test(password)) {
        errors.password = "Must contain at least one digit.";
      } else if (!/[^A-Za-z0-9]/.test(password)) {
        errors.password = "Must contain at least one special character.";
      }
    }

    if (password !== confirmPassword) {
      errors.confirmPassword = "Passwords do not match.";
    }

    if (roleId === 2 && !supervisorCode.trim()) {
      errors.supervisorCode = "Supervisor registration code is required.";
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleRegister = async (event) => {
    event.preventDefault();
    setError("");

    if (!validateClientSide()) {
      return;
    }

    setLoading(true);

    try {
      const payload = {
        name: name.trim(),
        email: email.trim(),
        password: password,
        role_id: Number(roleId),
      };

      if (roleId === 2) {
        payload.supervisor_registration_code = supervisorCode.trim();
      }

      await register(payload);

      // Navigate to login with success state
      navigate("/login", {
        state: {
          successMessage: "Account created successfully! Please sign in with your credentials.",
          prefilledEmail: email.trim(),
        },
      });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Unable to connect to the authentication service.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-logo">VI</div>
          <h1 className="auth-title">Create Account</h1>
          <p className="auth-subtitle">
            Register for VisionInspect AI industrial inspection platform
          </p>
        </div>

        {error && (
          <div className="alert alert-error">
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleRegister}>
          {/* Full Name */}
          <div className="form-group">
            <label className="form-label" htmlFor="name">
              Full Name
            </label>
            <input
              id="name"
              type="text"
              className="form-input"
              placeholder="e.g. John Doe"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                if (fieldErrors.name) setFieldErrors({ ...fieldErrors, name: null });
              }}
              disabled={loading}
              autoComplete="name"
            />
            {fieldErrors.name && (
              <span className="form-hint" style={{ color: "var(--danger)" }}>
                {fieldErrors.name}
              </span>
            )}
          </div>

          {/* Email */}
          <div className="form-group">
            <label className="form-label" htmlFor="email">
              Work Email Address
            </label>
            <input
              id="email"
              type="email"
              className="form-input"
              placeholder="name@plant.company.com"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (fieldErrors.email) setFieldErrors({ ...fieldErrors, email: null });
              }}
              disabled={loading}
              autoComplete="email"
            />
            {fieldErrors.email && (
              <span className="form-hint" style={{ color: "var(--danger)" }}>
                {fieldErrors.email}
              </span>
            )}
          </div>

          <div className="form-group">
            <label className="form-label">Select Role</label>
            <div className="role-select-grid">
              <div
                className={`role-card ${roleId === 1 ? "active" : ""}`}
                onClick={() => setRoleId(1)}
              >
                <div className="role-card-header">
                  <span className="role-card-title">Quality Engineer</span>
                  {roleId === 1 && <span className="badge badge-approved">Selected</span>}
                </div>
                <p className="role-card-desc">
                  Upload and inspect image records
                </p>
              </div>

              <div
                className={`role-card ${roleId === 2 ? "active" : ""}`}
                onClick={() => setRoleId(2)}
              >
                <div className="role-card-header">
                  <span className="role-card-title">Factory Supervisor</span>
                  {roleId === 2 && <span className="badge badge-approved">Selected</span>}
                </div>
                <p className="role-card-desc">
                  Review queue, approve or reject images
                </p>
              </div>
            </div>
          </div>

          {roleId === 2 && (
            <div className="form-group">
              <label className="form-label" htmlFor="supervisorCode">
                Supervisor Access Code
              </label>
              <input
                id="supervisorCode"
                type="password"
                className="form-input"
                placeholder="Enter supervisor code"
                value={supervisorCode}
                onChange={(e) => {
                  setSupervisorCode(e.target.value);
                  if (fieldErrors.supervisorCode) {
                    setFieldErrors({ ...fieldErrors, supervisorCode: null });
                  }
                }}
                disabled={loading}
              />
              <span className="form-hint">
                Authorization code required for supervisor registration.
              </span>
              {fieldErrors.supervisorCode && (
                <span className="form-hint" style={{ color: "var(--danger)" }}>
                  {fieldErrors.supervisorCode}
                </span>
              )}
            </div>
          )}

          <div className="form-row">
            <div className="form-group">
              <label className="form-label" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                className="form-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (fieldErrors.password) setFieldErrors({ ...fieldErrors, password: null });
                }}
                disabled={loading}
                autoComplete="new-password"
              />
              {fieldErrors.password && (
                <span className="form-hint" style={{ color: "var(--danger)" }}>
                  {fieldErrors.password}
                </span>
              )}
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="confirmPassword">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                className="form-input"
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => {
                  setConfirmPassword(e.target.value);
                  if (fieldErrors.confirmPassword) {
                    setFieldErrors({ ...fieldErrors, confirmPassword: null });
                  }
                }}
                disabled={loading}
                autoComplete="new-password"
              />
              {fieldErrors.confirmPassword && (
                <span className="form-hint" style={{ color: "var(--danger)" }}>
                  {fieldErrors.confirmPassword}
                </span>
              )}
            </div>
          </div>

          <p className="form-hint" style={{ marginBottom: "1.25rem" }}>
            Must be 8+ characters with uppercase, lowercase, digit, and special character.
          </p>

          <button
            type="submit"
            className="btn btn-primary btn-block btn-lg"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner" style={{ width: "16px", height: "16px" }} />
                <span>Registering Account...</span>
              </>
            ) : (
              "Complete Registration"
            )}
          </button>
        </form>

        <div className="auth-footer">
          Already have an account? <Link to="/login">Sign in here</Link>
        </div>
      </div>
    </div>
  );
}

export default Register;
