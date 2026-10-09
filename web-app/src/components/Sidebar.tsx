"use client";

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { LayoutDashboard, Camera, History, LogOut, Settings } from 'lucide-react';
import { useEffect, useState } from 'react';

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  // Static initial value so SSR/prerender matches first client render.
  const [userRole, setUserRole] = useState<string | null>(null);

  useEffect(() => {
    const getStoredRole = () => localStorage.getItem('userRole') || localStorage.getItem('role');
    queueMicrotask(() => {
      setUserRole(getStoredRole());
    });
    const syncRole = (e: StorageEvent) => {
      if (e.key === 'role' || e.key === 'userRole') setUserRole(getStoredRole());
    };
    const syncFocus = () => {
      setUserRole(getStoredRole());
    };
    window.addEventListener('storage', syncRole);
    window.addEventListener('focus', syncFocus);
    return () => {
      window.removeEventListener('storage', syncRole);
      window.removeEventListener('focus', syncFocus);
    };
  }, []);

  const handleLogout = () => {
    try {
      localStorage.removeItem('token');
      localStorage.removeItem('access_token');
      localStorage.removeItem('role');
      localStorage.removeItem('userRole');
      localStorage.removeItem('username');
    } finally {
      router.push('/login');
    }
  };

  // Don't show sidebar on login page
  if (pathname === '/login') return null;

  const role = (userRole || '').toLowerCase();
  const navItems = [];

  if (role === 'inspector') {
    navItems.push(
      { label: 'Live Inspection', href: '/inspect', icon: Camera }
    );
  } else if (role === 'supervisor') {
    navItems.push(
      { label: 'Dashboard', href: '/', icon: LayoutDashboard },
      { label: 'Live Inspection', href: '/inspect', icon: Camera },
      { label: 'Analytics / History', href: '/history', icon: History }
    );
  } else if (role === 'admin') {
    navItems.push(
      { label: 'Dashboard', href: '/', icon: LayoutDashboard },
      { label: 'Live Inspection', href: '/inspect', icon: Camera },
      { label: 'Analytics / History', href: '/history', icon: History },
      { label: 'System Settings', href: '/settings', icon: Settings }
    );
  } else {
    // Default fallback prior to role resolution
    navItems.push(
      { label: 'Live Inspection', href: '/inspect', icon: Camera }
    );
  }


  return (
    <aside className="w-64 glass-panel min-h-screen fixed left-0 top-0 hidden md:flex flex-col z-20">
      <div className="p-6 border-b border-[rgba(255,255,255,0.1)] flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center font-bold text-xl shadow-[0_0_15px_rgba(37,99,235,0.5)]">
          V
        </div>
        <div>
          <h1 className="font-bold text-lg leading-tight text-white tracking-wide">VisionInspect</h1>
          <p className="text-xs text-blue-400 font-medium">AI Quality Control</p>
        </div>
      </div>

      <nav className="flex-1 py-6 px-4 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                isActive
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-[inset_0_0_10px_rgba(37,99,235,0.1)]'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Icon size={20} className={isActive ? 'drop-shadow-[0_0_8px_rgba(56,189,248,0.5)]' : ''} />
              <span className="font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-[rgba(255,255,255,0.1)]">
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 px-4 py-3 rounded-xl text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
        >
          <LogOut size={20} />
          <span className="font-medium">Logout</span>
        </button>
      </div>
    </aside>
  );
}
