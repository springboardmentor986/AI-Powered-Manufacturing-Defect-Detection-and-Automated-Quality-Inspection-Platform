import React from 'react';

export const StatCard = ({ title, value, unit = '', subtext, icon: Icon, color = 'cyan', badge }) => {
  const colorMap = {
    cyan:    { border: 'accent-border-cyan',    icon: 'bg-cyan-500/12 text-cyan-400 border border-cyan-500/25',    tint: 'from-cyan-500/5 to-transparent',    num: 'text-cyan-400' },
    emerald: { border: 'accent-border-emerald', icon: 'bg-emerald-500/12 text-emerald-400 border border-emerald-500/25', tint: 'from-emerald-500/5 to-transparent', num: 'text-emerald-400' },
    rose:    { border: 'accent-border-rose',    icon: 'bg-rose-500/12 text-rose-400 border border-rose-500/25',    tint: 'from-rose-500/5 to-transparent',    num: 'text-rose-400' },
    amber:   { border: 'accent-border-amber',   icon: 'bg-amber-500/12 text-amber-400 border border-amber-500/25',  tint: 'from-amber-500/5 to-transparent',   num: 'text-amber-400' },
    purple:  { border: 'accent-border-purple',  icon: 'bg-purple-500/12 text-purple-400 border border-purple-500/25', tint: 'from-purple-500/5 to-transparent', num: 'text-purple-400' },
  };

  const c = colorMap[color] || colorMap.cyan;

  return (
    <div className={`glass-panel glass-panel-hover overflow-hidden relative ${c.border}`}>
      {/* Subtle gradient tint wash */}
      <div className={`absolute inset-0 bg-gradient-to-br ${c.tint} pointer-events-none`} />

      <div className="relative p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-3 min-w-0 flex-1">
            <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider font-mono block leading-none">
              {title}
            </span>
            <div className="flex items-baseline gap-1.5">
              <span className={`text-3xl sm:text-4xl font-black tracking-tight tabular-nums leading-none ${c.num}`}>
                {value}
              </span>
              {unit && <span className="text-sm font-semibold text-slate-400">{unit}</span>}
            </div>
          </div>

          {Icon && (
            <div className={`p-2.5 rounded-xl flex-shrink-0 ${c.icon}`}>
              <Icon className="w-5 h-5" />
            </div>
          )}
        </div>

        {(subtext || badge) && (
          <div className="mt-4 pt-3 flex items-center justify-between gap-2 border-t border-slate-100/60 dark:border-slate-800/60">
            <span className="text-[11px] text-slate-500 dark:text-slate-400 font-medium truncate leading-snug">
              {subtext}
            </span>
            {badge && (
              <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-industrial-950 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-800 flex-shrink-0">
                {badge}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
