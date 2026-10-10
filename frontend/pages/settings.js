import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Sidebar from "../components/Sidebar";
import { getToken, clearToken, getCurrentUser } from "../lib/api";
import { ui, badge } from "../lib/ui";

const ROLE_NOTE = {
  admin: "Admin: full access, including creating categories.",
  inspector: "Inspector: can upload images and run inspections. Creating categories needs an Admin.",
};

export default function Settings() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    (async () => {
      try {
        setUser(await getCurrentUser());
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  const signOut = () => {
    clearToken();
    router.push("/login");
  };

  const since = user && user.created_at ? new Date(user.created_at).toLocaleDateString() : "-";

  return (
    <div style={ui.shell}>
      <Sidebar />
      <div style={ui.page}>
        <header style={ui.header}>
          <div>
            <div style={ui.eyebrow}>VISIONINSPECT AI - SETTINGS</div>
            <h1 style={ui.title}>Account Settings</h1>
            <div style={ui.subtitle}>Your profile and session.</div>
          </div>
        </header>

        {loading && <div style={ui.msg}>Loading account...</div>}
        {error && <div style={ui.msg}>Error: {error}</div>}

        {!loading && !error && user && (
          <section style={{ ...ui.panel, maxWidth: 560 }}>
            <div style={ui.infoRow}>
              <span style={ui.infoLabel}>Name</span>
              <span>{user.name}</span>
            </div>
            <div style={ui.infoRow}>
              <span style={ui.infoLabel}>Email</span>
              <span>{user.email}</span>
            </div>
            <div style={ui.infoRow}>
              <span style={ui.infoLabel}>Role</span>
              <span style={badge("#f5a623")}>{user.role.toUpperCase()}</span>
            </div>
            <div style={ui.infoRow}>
              <span style={ui.infoLabel}>User ID</span>
              <span>#{user.user_id}</span>
            </div>
            <div style={ui.infoRow}>
              <span style={ui.infoLabel}>Member since</span>
              <span>{since}</span>
            </div>
            <p style={{ color: "#8a94a1", fontSize: 13, margin: "16px 0" }}>
              {ROLE_NOTE[user.role] || ""}
            </p>
            <button style={ui.button} onClick={signOut}>
              Sign out
            </button>
          </section>
        )}
      </div>
    </div>
  );
}
