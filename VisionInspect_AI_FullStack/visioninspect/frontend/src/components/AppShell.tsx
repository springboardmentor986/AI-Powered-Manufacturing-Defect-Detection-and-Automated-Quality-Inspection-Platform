"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: "◧" },
  { href: "/upload", label: "Upload & Inspect", icon: "⬆" },
  { href: "/inspections", label: "Inspections", icon: "☰" },
  { href: "/analytics", label: "Analytics", icon: "▤" },
  { href: "/users", label: "Users", icon: "◍", roles: ["admin", "factory_supervisor"] },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen flex bg-graphite text-ink">
      <aside className="w-60 shrink-0 border-r border-line bg-panel flex flex-col">
        <div className="px-5 py-5 border-b border-line">
          <p className="eyebrow">VisionInspect</p>
          <p className="font-display text-lg font-semibold">Quality Console</p>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV_ITEMS.filter(
            (item) => !item.roles || (user && item.roles.includes(user.role))
          ).map((item) => {
            const active = pathname?.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2 rounded text-sm font-medium transition-colors ${
                  active
                    ? "bg-panel-2 text-amber border border-line"
                    : "text-muted hover:text-ink hover:bg-panel-2"
                }`}
              >
                <span aria-hidden>{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="px-5 py-4 border-t border-line">
          {user && (
            <div className="mb-3">
              <p className="text-sm font-medium">{user.full_name}</p>
              <p className="text-xs text-muted capitalize">
                {user.role.replace(/_/g, " ")}
              </p>
            </div>
          )}
          <button onClick={logout} className="btn-secondary w-full text-sm">
            Sign out
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-6xl mx-auto px-8 py-8">{children}</div>
      </main>
    </div>
  );
}
