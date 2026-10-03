"use client";
import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { api } from "@/lib/api";

export default function UsersPage() {
  const [users, setUsers] = useState<any[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.listUsers().then(setUsers).catch((e) => setError(e.message));
  }, []);

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8">
        <h1 className="text-2xl font-bold mb-6">Users</h1>
        {error && <p className="text-muted text-sm">{error} (Admin or Factory Supervisor role required.)</p>}
        <table className="w-full text-sm">
          <thead className="text-muted text-left border-b border-line">
            <tr><th className="py-2">Name</th><th>Username</th><th>Role</th><th>Status</th></tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-b border-line">
                <td className="py-2">{u.full_name}</td>
                <td className="font-mono text-xs">{u.username}</td>
                <td className="capitalize">{u.role.replace(/_/g, " ")}</td>
                <td>{u.is_active ? "Active" : "Deactivated"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </main>
    </div>
  );
}
