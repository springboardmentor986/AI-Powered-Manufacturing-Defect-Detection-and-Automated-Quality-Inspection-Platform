import React from 'react';
import { 
  ShieldCheck, 
  Zap, 
  Activity, 
  Layers, 
  ShieldAlert,
  TrendingUp
} from 'lucide-react';
import { useAuth, ROLES, ROLE_DETAILS } from '../context/AuthContext';

export const RoleHeaderBanner = ({ 
  onOpenUpload, 
  onOpenSimulator, 
  onOpenDataset, 
  setActiveTab 
}) => {
  const { user, switchToDemoRole } = useAuth();
  const role = user?.role || ROLES.QUALITY_ENGINEER;
  const details = ROLE_DETAILS[role] || ROLE_DETAILS.quality_engineer;

  const roleConfig = {
    quality_engineer: {
      accentBorder: 'border-l-4 border-cyan-500',
      badge:        'bg-cyan-500/12 text-cyan-400 border border-cyan-500/25',
      accent:       'text-cyan-500 dark:text-cyan-400',
      btnPrimary:   'bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 text-white shadow-cyan-600/20',
      btnSecondary: 'bg-slate-100 hover:bg-slate-200 dark:bg-industrial-800 dark:hover:bg-industrial-700 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700',
      roleTab:      (active) => active ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 font-semibold' : '',
    },
    factory_supervisor: {
      accentBorder: 'border-l-4 border-amber-500',
      badge:        'bg-amber-500/12 text-amber-400 border border-amber-500/25',
      accent:       'text-amber-500 dark:text-amber-400',
      btnPrimary:   'bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-white shadow-amber-600/20',
      btnSecondary: 'bg-slate-100 hover:bg-slate-200 dark:bg-industrial-800 dark:hover:bg-industrial-700 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700',
      roleTab:      (active) => active ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30 font-semibold' : '',
    },
    production_manager: {
      accentBorder: 'border-l-4 border-purple-500',
      badge:        'bg-purple-500/12 text-purple-400 border border-purple-500/25',
      accent:       'text-purple-500 dark:text-purple-400',
      btnPrimary:   'bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400 text-white shadow-purple-600/20',
      btnSecondary: 'bg-slate-100 hover:bg-slate-200 dark:bg-industrial-800 dark:hover:bg-industrial-700 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700',
      roleTab:      (active) => active ? 'bg-purple-500/15 text-purple-300 border border-purple-500/30 font-semibold' : '',
    },
  };

  const cfg = roleConfig[role] || roleConfig.quality_engineer;

  const headlines = {
    [ROLES.QUALITY_ENGINEER]:  'Inspection Station & Defect Triage',
    [ROLES.FACTORY_SUPERVISOR]:'Shift Operations & Batch Control',
    [ROLES.PRODUCTION_MANAGER]:'Plant Quality Intelligence',
  };

  const descriptions = {
    [ROLES.QUALITY_ENGINEER]:  'Inspect images, triage defects, and submit quality sign-offs.',
    [ROLES.FACTORY_SUPERVISOR]:'Monitor production line batches and shift security alerts.',
    [ROLES.PRODUCTION_MANAGER]:'Plant-wide compliance analytics and audit trail access.',
  };

  return (
    <div className={`glass-panel overflow-hidden relative pl-0 ${cfg.accentBorder}`}>
      <div className="p-5 sm:p-6">
        {/* Top row */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono font-bold uppercase tracking-wider ${cfg.badge}`}>
              <ShieldCheck className="w-3 h-3" />
              {details.label}
            </span>
            <h1 className="text-xl sm:text-2xl font-black text-slate-900 dark:text-white tracking-tight leading-tight">
              {headlines[role]}
            </h1>
            <p className="text-[13px] text-slate-500 dark:text-slate-400 leading-snug max-w-lg">
              {descriptions[role]}
            </p>
          </div>

          {/* Role switcher pill */}
          <div className="flex-shrink-0">
            <div className="bg-slate-100 dark:bg-industrial-950 p-1 rounded-xl border border-slate-200 dark:border-slate-800 flex items-center gap-0.5 text-[12px]">
              {[
                { r: ROLES.QUALITY_ENGINEER,  label: 'Engineer' },
                { r: ROLES.FACTORY_SUPERVISOR, label: 'Supervisor' },
                { r: ROLES.PRODUCTION_MANAGER, label: 'Manager' },
              ].map(({ r, label }) => (
                <button
                  key={r}
                  onClick={() => switchToDemoRole(r)}
                  className={`px-3.5 py-1.5 rounded-[9px] transition-all ${
                    role === r
                      ? cfg.roleTab(true)
                      : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Action row */}
        <div className="mt-4 pt-4 border-t border-slate-200/60 dark:border-slate-800/60 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            {role === ROLES.QUALITY_ENGINEER && (
              <>
                <button
                  onClick={onOpenUpload}
                  className={`px-4 py-2 rounded-[10px] font-semibold text-[12px] transition-all flex items-center gap-1.5 shadow-md ${cfg.btnPrimary}`}
                >
                  <Zap className="w-3.5 h-3.5" /> Inspect Image
                </button>
                <button
                  onClick={onOpenSimulator}
                  className={`px-4 py-2 rounded-[10px] font-semibold text-[12px] transition-all flex items-center gap-1.5 ${cfg.btnSecondary}`}
                >
                  <Activity className="w-3.5 h-3.5" /> Live Feed
                </button>
              </>
            )}

            {role === ROLES.FACTORY_SUPERVISOR && (
              <>
                <button
                  onClick={onOpenUpload}
                  className={`px-4 py-2 rounded-[10px] font-semibold text-[12px] transition-all flex items-center gap-1.5 shadow-md ${cfg.btnPrimary}`}
                >
                  <Layers className="w-3.5 h-3.5" /> New Batch
                </button>
                <button
                  onClick={() => setActiveTab('audit')}
                  className={`px-4 py-2 rounded-[10px] font-semibold text-[12px] transition-all flex items-center gap-1.5 ${cfg.btnSecondary}`}
                >
                  <ShieldAlert className="w-3.5 h-3.5" /> Audit Logs
                </button>
              </>
            )}

            {role === ROLES.PRODUCTION_MANAGER && (
              <>
                <button
                  onClick={() => setActiveTab('audit')}
                  className={`px-4 py-2 rounded-[10px] font-semibold text-[12px] transition-all flex items-center gap-1.5 shadow-md ${cfg.btnPrimary}`}
                >
                  <ShieldAlert className="w-3.5 h-3.5" /> Audit Trail
                </button>
                <button
                  onClick={() => setActiveTab('inspections')}
                  className={`px-4 py-2 rounded-[10px] font-semibold text-[12px] transition-all flex items-center gap-1.5 ${cfg.btnSecondary}`}
                >
                  <Layers className="w-3.5 h-3.5" /> Inspection Records
                </button>
              </>
            )}
          </div>

          {/* Status dot */}
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span className="text-[11px] font-mono text-emerald-600 dark:text-emerald-400 font-semibold">Station Sync: 100%</span>
          </div>
        </div>
      </div>
    </div>
  );
};
