import { useEffect, useState } from "react";
import api from "../services/api";
import Sidebar from "../components/Sidebar";

const sections = [
  {
    id: "profile",
    icon: "👤",
    title: "Profile",
    description: "Manage your account information",
  },
  {
    id: "security",
    icon: "🔐",
    title: "Security",
    description: "Password and account security",
  },
  {
    id: "inspection",
    icon: "🎯",
    title: "Inspection Preferences",
    description: "Configure inspection behaviour",
  },
  {
    id: "notifications",
    icon: "🔔",
    title: "Notifications",
    description: "Manage inspection and system alerts",
  },
  {
    id: "application",
    icon: "⚙️",
    title: "Application Preferences",
    description: "Customize your workspace",
  },
  {
    id: "ai",
    icon: "🤖",
    title: "AI & Models",
    description: "View AI inspection components",
  },
  {
    id: "system",
    icon: "🖥️",
    title: "System Information",
    description: "Platform and system details",
  },
];

function Settings() {
  const [user, setUser] = useState(null);
  const [activeSection, setActiveSection] = useState(null);
  const [editing, setEditing] = useState(false);

  const [theme, setTheme] = useState(
    localStorage.getItem("theme") || "light"
  );

  const [notifications, setNotifications] = useState(
    localStorage.getItem("notifications") !== "off"
  );

  const [passwords, setPasswords] = useState({
    current: "",
    next: "",
    confirm: "",
  });

  const [inspection, setInspection] = useState({
    automatic: true,
    boxes: true,
    confidence: true,
  });

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
  document.documentElement.setAttribute("data-theme", theme);

  api
    .get("/auth/me")
    .then((response) => setUser(response.data.user))
    .catch((requestError) =>
      setError(
        requestError.response?.data?.detail ||
          "Unable to load your profile."
      )
    );
}, []);

  const savePassword = async (event) => {
    event.preventDefault();

    setMessage("");
    setError("");

    if (passwords.next !== passwords.confirm) {
      setError("New password and confirmation do not match.");
      return;
    }

    try {
      await api.post("/auth/change-password", null, {
        params: {
          current_password: passwords.current,
          new_password: passwords.next,
        },
      });

      setMessage("Password updated successfully.");

      setPasswords({
        current: "",
        next: "",
        confirm: "",
      });
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          "Unable to update password."
      );
    }
  };

  const toggleInspection = (key) => {
    setInspection((previous) => ({
      ...previous,
      [key]: !previous[key],
    }));
  };

  const updateTheme = (value) => {
  setTheme(value);
  localStorage.setItem("theme", value);

  document.documentElement.setAttribute("data-theme", value);
};

  const updateNotifications = () => {
    const value = !notifications;
    setNotifications(value);
    localStorage.setItem("notifications", value ? "on" : "off");
  };

  const role =
    user?.role
      ?.replaceAll("_", " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase()) ||
    "Quality Engineer";

  const activeTitle =
    sections.find((section) => section.id === activeSection)?.title || "";

  return (
    <div className="dashboard-layout">
      {/* EXISTING WORKSPACE SIDEBAR */}
      <Sidebar />

      <main className="dashboard-main settings-page">

        {/* HEADER */}
        <header className="dashboard-header">
          <div>
            <div className="dashboard-breadcrumb">
              Workspace / Settings
              {activeSection && ` / ${activeTitle}`}
            </div>

            <h1>
              {activeSection ? activeTitle : "Settings"}
            </h1>

            <p>
              {activeSection
                ? sections.find((s) => s.id === activeSection)?.description
                : "Manage your account, inspection preferences and VisionInspect AI workspace."}
            </p>
          </div>
        </header>

        {message && (
          <div className="settings-success">
            ✓ {message}
          </div>
        )}

        {error && (
          <div className="settings-error">
            ⚠ {error}
          </div>
        )}

        {/* ================================
            SETTINGS HOME
        ================================= */}
        {!activeSection && (
          <div className="settings-section-list">

            {sections.map((section) => (
              <button
                key={section.id}
                className="settings-section-item"
                onClick={() => {
                  setActiveSection(section.id);
                  setMessage("");
                  setError("");
                }}
              >
                <div className="settings-section-icon">
                  {section.icon}
                </div>

                <div className="settings-section-text">
                  <strong>{section.title}</strong>
                  <span>{section.description}</span>
                </div>

                <div className="settings-section-arrow">
                  →
                </div>
              </button>
            ))}

          </div>
        )}

        {/* ================================
            PROFILE
        ================================= */}
        {activeSection === "profile" && (
          <SettingsContent
            onBack={() => setActiveSection(null)}
          >
            <section className="settings-card">
              <div className="settings-card-heading">
                <div>
                  <span className="settings-eyebrow">
                    ACCOUNT
                  </span>

                  <h2>Profile Information</h2>

                  <p>
                    Manage your VisionInspect AI account details.
                  </p>
                </div>

                <button
                  className="settings-primary-btn"
                  onClick={() =>
                    setEditing((previous) => !previous)
                  }
                >
                  {editing ? "Done" : "Edit Profile"}
                </button>
              </div>

              <div className="settings-profile">
                <div className="settings-avatar">
                  {user?.name?.charAt(0)?.toUpperCase() || "U"}
                </div>

                <div className="settings-profile-fields">

                  <label>
                    Full Name
                    <input
                      value={user?.name || ""}
                      readOnly={!editing}
                      onChange={(event) =>
                        setUser({
                          ...user,
                          name: event.target.value,
                        })
                      }
                    />
                  </label>

                  <label>
                    Email Address
                    <input
                      value={user?.email || ""}
                      readOnly
                    />
                  </label>

                  <label>
                    Role
                    <input
                      value={role}
                      readOnly
                    />
                  </label>

                </div>
              </div>
            </section>
          </SettingsContent>
        )}

        {/* ================================
            SECURITY
        ================================= */}
        {activeSection === "security" && (
          <SettingsContent
            onBack={() => setActiveSection(null)}
          >
            <section className="settings-card">
              <div className="settings-card-heading">
                <div>
                  <span className="settings-eyebrow">
                    SECURITY
                  </span>

                  <h2>Change Password</h2>

                  <p>
                    Update your account password securely.
                  </p>
                </div>
              </div>

              <form
                className="settings-form"
                onSubmit={savePassword}
              >
                <label>
                  Current Password
                  <input
                    type="password"
                    required
                    value={passwords.current}
                    onChange={(event) =>
                      setPasswords({
                        ...passwords,
                        current: event.target.value,
                      })
                    }
                  />
                </label>

                <label>
                  New Password
                  <input
                    type="password"
                    required
                    minLength="8"
                    value={passwords.next}
                    onChange={(event) =>
                      setPasswords({
                        ...passwords,
                        next: event.target.value,
                      })
                    }
                  />
                </label>

                <label>
                  Confirm New Password
                  <input
                    type="password"
                    required
                    value={passwords.confirm}
                    onChange={(event) =>
                      setPasswords({
                        ...passwords,
                        confirm: event.target.value,
                      })
                    }
                  />
                </label>

                <button
                  type="submit"
                  className="settings-primary-btn"
                >
                  Update Password
                </button>
              </form>
            </section>

            <section className="settings-card">
              <div className="settings-card-heading">
                <div>
                  <span className="settings-eyebrow">
                    SESSION
                  </span>

                  <h2>Session Security</h2>

                  <p>
                    Your current account session is active.
                  </p>
                </div>
              </div>

              <div className="settings-status-box">
                <span>Current Session</span>
                <strong>● Active</strong>
              </div>
            </section>
          </SettingsContent>
        )}

        {/* ================================
            INSPECTION
        ================================= */}
        {activeSection === "inspection" && (
          <SettingsContent
            onBack={() => setActiveSection(null)}
          >
            <section className="settings-card">

              <div className="settings-card-heading">
                <div>
                  <span className="settings-eyebrow">
                    INSPECTION
                  </span>

                  <h2>Inspection Preferences</h2>

                  <p>
                    Configure how VisionInspect AI handles inspections.
                  </p>
                </div>
              </div>

              <PreferenceToggle
                title="Automatic Inspection"
                description="Automatically process uploaded images."
                enabled={inspection.automatic}
                onChange={() =>
                  toggleInspection("automatic")
                }
              />

              <PreferenceToggle
                title="Defect Bounding Boxes"
                description="Display detected defect locations."
                enabled={inspection.boxes}
                onChange={() =>
                  toggleInspection("boxes")
                }
              />

              <PreferenceToggle
                title="AI Confidence Scores"
                description="Display confidence values for detections."
                enabled={inspection.confidence}
                onChange={() =>
                  toggleInspection("confidence")
                }
              />

            </section>

            <section className="settings-card">

              <div className="settings-card-heading">
                <div>
                  <span className="settings-eyebrow">
                    DEFAULTS
                  </span>

                  <h2>Inspection Defaults</h2>
                </div>
              </div>

              <div className="settings-field">
                <label>
                  Default Product Category
                  <select defaultValue="bottle">
                    <option value="bottle">Bottle</option>
                    <option value="cable">Cable</option>
                    <option value="capsule">Capsule</option>
                    <option value="carpet">Carpet</option>
                    <option value="grid">Grid</option>
                    <option value="hazelnut">Hazelnut</option>
                    <option value="leather">Leather</option>
                    <option value="metal_nut">Metal Nut</option>
                    <option value="pill">Pill</option>
                    <option value="screw">Screw</option>
                    <option value="tile">Tile</option>
                    <option value="toothbrush">Toothbrush</option>
                    <option value="transistor">Transistor</option>
                    <option value="wood">Wood</option>
                    <option value="zipper">Zipper</option>
                  </select>
                </label>
              </div>

            </section>
          </SettingsContent>
        )}

        {/* ================================
            NOTIFICATIONS
        ================================= */}
        {activeSection === "notifications" && (
          <SettingsContent
            onBack={() => setActiveSection(null)}
          >
            <section className="settings-card">

              <div className="settings-card-heading">
                <div>
                  <span className="settings-eyebrow">
                    ALERTS
                  </span>

                  <h2>Notifications</h2>

                  <p>
                    Control inspection and system notifications.
                  </p>
                </div>
              </div>

              <PreferenceToggle
                title="Inspection Notifications"
                description="Receive notifications about inspection results."
                enabled={notifications}
                onChange={updateNotifications}
              />

              <PreferenceToggle
                title="Critical Defect Alerts"
                description="Get notified when critical defects are detected."
                enabled={notifications}
                onChange={updateNotifications}
              />

              <PreferenceToggle
                title="Report Notifications"
                description="Receive notifications when reports are generated."
                enabled={notifications}
                onChange={updateNotifications}
              />

            </section>
          </SettingsContent>
        )}

        {/* ================================
            APPLICATION
        ================================= */}
        {activeSection === "application" && (
          <SettingsContent
            onBack={() => setActiveSection(null)}
          >
            <section className="settings-card">

              <div className="settings-card-heading">
                <div>
                  <span className="settings-eyebrow">
                    APPLICATION
                  </span>

                  <h2>Application Preferences</h2>

                  <p>
                    Customize your VisionInspect AI workspace.
                  </p>
                </div>
              </div>

              <div className="settings-preference">
                <div>
                  <strong>Theme Preference</strong>
                  <span>
                    Choose the application appearance.
                  </span>
                </div>

                <select
                  value={theme}
                  onChange={(event) =>
                    updateTheme(event.target.value)
                  }
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                </select>
              </div>

            </section>
          </SettingsContent>
        )}

        {/* ================================
            AI
        ================================= */}
        {activeSection === "ai" && (
          <SettingsContent
            onBack={() => setActiveSection(null)}
          >
            <section className="settings-card">

              <div className="settings-card-heading">
                <div>
                  <span className="settings-eyebrow">
                    AI ENGINE
                  </span>

                  <h2>AI & Models</h2>

                  <p>
                    AI components powering VisionInspect AI.
                  </p>
                </div>
              </div>

              <ModelRow
                name="Convolutional Autoencoder"
                description="Anomaly detection"
              />

              <ModelRow
                name="YOLO Object Detection"
                description="Defect localization and bounding boxes"
              />

              <ModelRow
                name="ResNet18 Classifier"
                description="Defect type classification"
              />

              <ModelRow
                name="Image Quality Analysis"
                description="Image quality assessment"
              />

            </section>

            <div className="ai-summary">

              <div>
                <strong>15</strong>
                <span>Supported Categories</span>
              </div>

              <div>
                <strong>3</strong>
                <span>AI Models</span>
              </div>

              <div>
                <strong>AI</strong>
                <span>Quality Intelligence</span>
              </div>

            </div>
          </SettingsContent>
        )}

        {/* ================================
            SYSTEM
        ================================= */}
        {activeSection === "system" && (
          <SettingsContent
            onBack={() => setActiveSection(null)}
          >
            <section className="settings-card">

              <div className="settings-card-heading">
                <div>
                  <span className="settings-eyebrow">
                    SYSTEM
                  </span>

                  <h2>System Information</h2>

                  <p>
                    Technical information about the platform.
                  </p>
                </div>
              </div>

              <SystemRow
                label="Application"
                value="VisionInspect AI"
              />

              <SystemRow
                label="Frontend"
                value="React + Vite"
              />

              <SystemRow
                label="Backend"
                value="FastAPI"
              />

              <SystemRow
                label="Database"
                value="PostgreSQL"
              />

              <SystemRow
                label="Authentication"
                value="JWT"
              />

              <SystemRow
                label="Version"
                value="1.0.0"
              />

            </section>

            <section className="settings-card">

              <div className="settings-card-heading">
                <div>
                  <span className="settings-eyebrow">
                    STATUS
                  </span>

                  <h2>System Status</h2>
                </div>
              </div>

              <div className="system-status-grid">

                <StatusCard
                  title="API Server"
                  status="Online"
                />

                <StatusCard
                  title="Database"
                  status="Connected"
                />

                <StatusCard
                  title="AI Engine"
                  status="Ready"
                />

              </div>

            </section>
          </SettingsContent>
        )}

      </main>
    </div>
  );
}

/* ================================
   CONTENT WRAPPER
================================ */

function SettingsContent({ onBack, children }) {
  return (
    <div className="settings-detail">

      <button
        className="settings-back-btn"
        onClick={onBack}
      >
        ← Back to Settings
      </button>

      {children}

    </div>
  );
}

/* ================================
   COMPONENTS
================================ */

function PreferenceToggle({
  title,
  description,
  enabled,
  onChange,
}) {
  return (
    <div className="settings-preference">

      <div>
        <strong>{title}</strong>
        <span>{description}</span>
      </div>

      <button
        type="button"
        className={`settings-toggle ${
          enabled ? "on" : ""
        }`}
        onClick={onChange}
      >
        <span />
      </button>

    </div>
  );
}

function ModelRow({ name, description }) {
  return (
    <div className="settings-model-row">

      <div>
        <strong>{name}</strong>
        <span>{description}</span>
      </div>

      <b className="model-active">
        ● Active
      </b>

    </div>
  );
}

function SystemRow({ label, value }) {
  return (
    <div className="settings-system-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function StatusCard({ title, status }) {
  return (
    <div className="system-status-card">

      <span>{title}</span>

      <strong>
        <i /> {status}
      </strong>

    </div>
  );
}

export default Settings;