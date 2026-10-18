import React from 'react';
import { 
  LayoutDashboard, 
  Scan, 
  FolderArchive, 
  Video, 
  ShieldAlert, 
  Cpu,
  CheckCircle2,
  Circle
} from 'lucide-react';
import { useAuth, ROLES } from '../context/AuthContext';

export const Sidebar = ({ activeTab, setActiveTab }) => {
  const { user, hasRole } = useAuth();

  const navItems = [
    {
      id: 'dashboard',
      label: 'Role Dashboard',
      icon: LayoutDashboard,
      roles: [ROLES.QUALITY_ENGINEER, ROLES.FACTORY_SUPERVISOR, ROLES.PRODUCTION_MANAGER, ROLES.ADMIN],
      badge: 'Live'
    },
    {
      id: 'inspections',
      label: 'Inspection Records',
      icon: Scan,
      roles: [ROLES.QUALITY_ENGINEER, ROLES.FACTORY_SUPERVISOR, ROLES.PRODUCTION_MANAGER, ROLES.ADMIN],
    },
    {
      id: 'simulator',
      label: 'Camera Simulator',
      icon: Video,
      roles: [ROLES.QUALITY_ENGINEER, ROLES.FACTORY_SUPERVISOR, ROLES.PRODUCTION_MANAGER, ROLES.ADMIN],
    },
    {
      id: 'audit',
      label: 'Security & Audit',
      icon: ShieldAlert,
      roles: [ROLES.FACTORY_SUPERVISOR, ROLES.PRODUCTION_MANAGER, ROLES.ADMIN],
      badge: 'Sec'
    },
  ];

  return (
    <aside className="w-60 border-r border-slate-200/80 dark:border-slate-800/60 bg-white/70 dark:bg-industrial-950/80 backdrop-blur-xl flex flex-col justify-between py-5 px-3 hidden md:flex min-h-[calc(100vh-4rem)] transition-colors duration-200">
      <div className="space-y-1">
        {navItems.map((item) => {
          const isAllowed = !item.roles || (user && hasRole(item.roles));
          if (!isAllowed) return null;
          const Icon = item.icon;
          const isActive = activeTab === item.id;

          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-[13px] font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-cyan-500/12 dark:bg-cyan-500/15 text-cyan-600 dark:text-cyan-300 border border-cyan-500/25 shadow-sm font-semibold'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100/80 dark:hover:bg-industrial-900/60 border border-transparent'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-cyan-500 dark:text-cyan-400' : 'text-slate-400 dark:text-slate-500'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded-full ${
                  isActive
                    ? 'bg-cyan-500/20 text-cyan-600 dark:text-cyan-300'
                    : 'bg-slate-100 dark:bg-industrial-900 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-800'
                }`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </aside>
  );
};
