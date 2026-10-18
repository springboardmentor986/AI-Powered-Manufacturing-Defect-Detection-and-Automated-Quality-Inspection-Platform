import React, { useState } from 'react';
import { 
  ScanEye, 
  ShieldCheck, 
  ChevronDown, 
  LogOut, 
  Zap,
  Sun,
  Moon
} from 'lucide-react';
import { useAuth, ROLES, ROLE_DETAILS } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';

export const Navbar = ({ onOpenUpload, onOpenSimulator }) => {
  const { user, logout, switchToDemoRole, isAuthenticated } = useAuth();
  const { toggleTheme, isDark } = useTheme();
  const [roleDropdownOpen, setRoleDropdownOpen] = useState(false);

  const currentRole = user?.role || ROLES.QUALITY_ENGINEER;
  const currentDetails = ROLE_DETAILS[currentRole] || ROLE_DETAILS.quality_engineer;

  const roleStyles = {
    quality_engineer:  'bg-cyan-500/10 text-cyan-600 dark:text-cyan-300 border-cyan-500/30',
    factory_supervisor:'bg-amber-500/10 text-amber-600 dark:text-amber-300 border-amber-500/30',
    production_manager:'bg-purple-500/10 text-purple-600 dark:text-purple-300 border-purple-500/30',
    admin:             'bg-rose-500/10 text-rose-600 dark:text-rose-300 border-rose-500/30'
  };

  return (
    <header className="h-14 border-b border-slate-200/80 dark:border-slate-800/60 bg-white/85 dark:bg-industrial-950/85 backdrop-blur-xl px-4 sm:px-6 flex items-center justify-between sticky top-0 z-40 transition-colors duration-200">
      {/* Brand */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-[10px] bg-gradient-to-br from-cyan-500 to-emerald-500 p-[1.5px] shadow-md shadow-cyan-500/20">
            <div className="w-full h-full bg-white dark:bg-industrial-950 rounded-[8px] flex items-center justify-center">
              <ScanEye className="w-4.5 h-4.5 text-cyan-500 dark:text-cyan-400" style={{ width: 18, height: 18 }} />
            </div>
          </div>
          <div>
            <span className="font-bold text-[15px] text-slate-900 dark:text-slate-50 tracking-tight leading-none">
              VisionInspect
            </span>
          </div>
        </div>

        {/* Live heartbeat */}
        <div className="hidden xl:flex items-center gap-2 pl-4 border-l border-slate-200 dark:border-slate-800">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
          <span className="text-[11px] font-mono text-emerald-600 dark:text-emerald-400 font-semibold tracking-wide">ONLINE</span>
        </div>
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-2">
        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          aria-label={`Switch to ${isDark ? 'Light' : 'Dark'} mode`}
          className="p-2 rounded-[10px] bg-slate-100 hover:bg-slate-200 dark:bg-industrial-900 dark:hover:bg-industrial-800 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700/80 transition-all hover:scale-105 active:scale-95"
        >
          {isDark
            ? <Sun className="w-4 h-4 text-amber-400" />
            : <Moon className="w-4 h-4 text-slate-600" />
          }
        </button>

        {/* Upload CTA */}
        {onOpenUpload && (
          <button
            onClick={onOpenUpload}
            className="hidden sm:flex items-center gap-1.5 px-3.5 py-2 rounded-[10px] bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 text-white text-[12px] font-semibold shadow-md shadow-cyan-600/20 transition-all hover:scale-[1.02] active:scale-[0.97]"
          >
            <Zap className="w-3.5 h-3.5" />
            <span>Upload</span>
          </button>
        )}

        {/* Role switcher */}
        {isAuthenticated && user && (
          <div className="relative">
            <button
              onClick={() => setRoleDropdownOpen(!roleDropdownOpen)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-[10px] border text-[12px] font-semibold transition-all ${
                roleStyles[currentRole] || 'bg-slate-100 dark:bg-slate-800 text-slate-600 border-slate-200'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{currentDetails.label}</span>
              <ChevronDown className="w-3 h-3 opacity-60" />
            </button>

            {roleDropdownOpen && (
              <div
                className="absolute right-0 mt-2 w-60 rounded-2xl bg-white dark:bg-industrial-900 border border-slate-200 dark:border-slate-700/80 shadow-2xl p-2 z-50"
                style={{ animation: 'fadeSlideUp 0.15s ease both' }}
                onClick={() => setRoleDropdownOpen(false)}
              >
                <div className="px-3 py-2 text-[10px] font-mono text-slate-400 uppercase tracking-wider border-b border-slate-100 dark:border-slate-800 mb-1">
                  Switch Role View
                </div>

                {[
                  { role: ROLES.QUALITY_ENGINEER,  label: 'Quality Engineer',  sub: 'Alex Rivera · Line Station',    color: 'text-cyan-600 dark:text-cyan-400' },
                  { role: ROLES.FACTORY_SUPERVISOR, label: 'Factory Supervisor', sub: 'Sarah Chen · Shift Ops',        color: 'text-amber-600 dark:text-amber-400' },
                  { role: ROLES.PRODUCTION_MANAGER, label: 'Production Manager', sub: 'Marcus Vance · Plant Exec',     color: 'text-purple-600 dark:text-purple-400' },
                ].map(({ role, label, sub, color }) => (
                  <button
                    key={role}
                    onClick={() => switchToDemoRole(role)}
                    className="w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-50 dark:hover:bg-industrial-800 flex items-center justify-between text-[12px] transition-colors"
                  >
                    <div>
                      <div className={`font-semibold ${color}`}>{label}</div>
                      <div className="text-[10px] text-slate-400 dark:text-slate-500 font-mono mt-0.5">{sub}</div>
                    </div>
                    {user.role === role && <div className="w-2 h-2 rounded-full bg-emerald-400" />}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Logout */}
        {isAuthenticated && user && (
          <button
            onClick={logout}
            title="Log out"
            className="p-2 rounded-[10px] hover:bg-slate-100 dark:hover:bg-industrial-800 text-slate-400 hover:text-rose-500 dark:hover:text-rose-400 transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        )}
      </div>
    </header>
  );
};
