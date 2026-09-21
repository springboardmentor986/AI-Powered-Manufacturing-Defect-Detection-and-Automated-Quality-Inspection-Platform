"use client";

import { useEffect, useState } from "react";
import ProtectedPage from "@/components/ProtectedPage";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import { User, UserRole } from "@/lib/types";

const ROLES: UserRole[] = ["admin", "quality_engineer", "factory_supervisor", "production_manager"];

function UsersContent() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setLoading(true);
    api
      .get("/api/users")
      .then((res) => setUsers(res.data))
      .catch((err) => setError(err?.response?.data?.detail || "Failed to load users"))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function changeRole(userId: number, role: UserRole) {
    try {
      await api.patch(`/api/users/${userId}/role`, null, { params: { role } });
      load();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Could not update role (admin only)");
    }
  }

  async function deactivate(userId: number) {
    try {
      await api.patch(`/api/users/${userId}/deactivate`);
      load();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Could not deactivate user (admin only)");
    }
  }

  return (
    <div>
      <div className="mb-7">
        <p className="eyebrow mb-1">User Management</p>
        <h1 className="font-display text-2xl font-semibold">Accounts &amp; Roles</h1>
        <p className="text-sm text-muted mt-1">
          Quality engineer, factory supervisor, production manager, and admin accounts with role-based access control.
        </p>
      </div>

      {error && <p className="text-sm text-critical mb-4">{error}</p>}

      <div className="card px-5 py-4">
        {loading ? (
          <p className="text-sm text-muted">Loading…</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-muted text-xs uppercase border-b border-line">
                <th className="pb-2 font-medium">Name</th>
                <th className="pb-2 font-medium">Email</th>
                <th className="pb-2 font-medium">Role</th>
                <th className="pb-2 font-medium">Status</th>
                <th className="pb-2 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-line/50 last:border-0">
                  <td className="py-2">{u.full_name}</td>
                  <td className="py-2 font-mono text-xs">{u.email}</td>
                  <td className="py-2">
                    {currentUser?.role === "admin" ? (
                      <select
                        className="input-field py-1 text-xs"
                        value={u.role}
                        onChange={(e) => changeRole(u.id, e.target.value as UserRole)}
                      >
                        {ROLES.map((r) => (
                          <option key={r} value={r}>
                            {r.replace(/_/g, " ")}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <span className="capitalize">{u.role.replace(/_/g, " ")}</span>
                    )}
                  </td>
                  <td className="py-2">
                    <span className={u.is_active ? "text-pass" : "text-muted"}>
                      {u.is_active ? "Active" : "Deactivated"}
                    </span>
                  </td>
                  <td className="py-2 text-right">
                    {currentUser?.role === "admin" && u.is_active && u.id !== currentUser.id && (
                      <button
                        onClick={() => deactivate(u.id)}
                        className="text-xs text-critical hover:underline"
                      >
                        Deactivate
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default function UsersPage() {
  return (
    <ProtectedPage>
      <UsersContent />
    </ProtectedPage>
  );
}
