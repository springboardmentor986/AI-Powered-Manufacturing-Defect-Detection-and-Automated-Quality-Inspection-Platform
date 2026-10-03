"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { api } from "@/lib/api";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/upload", label: "Upload & Inspect" },
  { href: "/inspections", label: "Inspections" },
  { href: "/analytics", label: "Analytics" },
  { href: "/validation", label: "Validation & Testing" },
  { href: "/documentation", label: "Documentation" },
  { href: "/users", label: "Users" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  function handleLogout() {
    api.logout();
    router.push("/login");
  }

  return (
    <aside className="w-56 shrink-0 border-r border-line min-h-screen p-4 flex flex-col">
      <div className="mb-6">
        <p className="text-amber text-xs tracking-widest font-semibold">VISIONINSPECT</p>
        <p className="text-lg font-bold">Quality Console</p>
      </div>
      <nav className="flex-1 space-y-1">
        {NAV.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`block px-3 py-2 rounded-md text-sm ${
              pathname === item.href ? "bg-panel text-amber" : "text-muted hover:text-ink"
            }`}
          >
            {item.label}
          </Link>
        ))}
      </nav>
      <button onClick={handleLogout} className="btn-secondary mt-4 text-sm">
        Sign out
      </button>
    </aside>
  );
}
