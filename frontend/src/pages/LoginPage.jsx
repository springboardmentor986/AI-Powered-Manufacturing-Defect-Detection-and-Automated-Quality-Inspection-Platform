import React, { useState } from 'react';
import { 
  ScanEye, 
  ShieldCheck, 
  User, 
  Lock, 
  Mail, 
  ArrowRight, 
  AlertCircle,
  Sun,
  Moon
} from 'lucide-react';
import { useAuth, ROLES } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';

const InputField = ({ icon: Icon, ...props }) => (
  <div className="relative">
    {Icon && (
      <Icon className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
    )}
    <input
      {...props}
      className={`w-full ${Icon ? 'pl-9' : 'px-3'} pr-3 py-2.5 rounded-[10px] bg-slate-50 dark:bg-industrial-900 border border-slate-200 dark:border-slate-700/80 text-slate-800 dark:text-slate-100 text-[13px] placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/15 transition-all`}
    />
  </div>
);

export const LoginPage = ({ onLoginSuccess }) => {
  const { login, register, switchToDemoRole } = useAuth();
  const { toggleTheme, isDark } = useTheme();
  const [isRegister, setIsRegister] = useState(false);

  const [username, setUsername]   = useState('');
  const [email, setEmail]         = useState('');
  const [password, setPassword]   = useState('');
  const [fullName, setFullName]   = useState('');
  const [role, setRole]           = useState(ROLES.QUALITY_ENGINEER);
  const [department, setDepartment] = useState('Manufacturing Quality Control');
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (isRegister) {
        await register({ username, email, password, full_name: fullName, role, department });
      } else {
        await login(username || email, password);
      }
      onLoginSuccess?.();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async (roleName) => {
    setError(null);
    setLoading(true);
    try {
      await switchToDemoRole(roleName);
      onLoginSuccess?.();
    } catch {
      setError('Demo login failed. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const demoRoles = [
    { role: ROLES.QUALITY_ENGINEER,   label: 'Engineer',   name: 'Alex Rivera',   color: 'border-cyan-500/30 bg-cyan-500/8 hover:bg-cyan-500/15 text-cyan-600 dark:text-cyan-300' },
    { role: ROLES.FACTORY_SUPERVISOR, label: 'Supervisor', name: 'Sarah Chen',    color: 'border-amber-500/30 bg-amber-500/8 hover:bg-amber-500/15 text-amber-600 dark:text-amber-300' },
    { role: ROLES.PRODUCTION_MANAGER, label: 'Manager',    name: 'Marcus Vance',  color: 'border-purple-500/30 bg-purple-500/8 hover:bg-purple-500/15 text-purple-600 dark:text-purple-300' },
  ];

  return (
    <div className="min-h-[100dvh] flex overflow-hidden bg-slate-50 dark:bg-industrial-950 transition-colors duration-200">

      {/* ── Left Panel (brand / visual) — hidden on mobile ── */}
      <div className="hidden lg:flex lg:w-1/2 xl:w-[55%] flex-col justify-between p-12 bg-industrial-950 relative overflow-hidden">
        {/* Grid texture overlay */}
        <div
          className="absolute inset-0 opacity-[0.04] pointer-events-none"
          style={{
            backgroundImage: 'linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)',
            backgroundSize: '40px 40px'
          }}
        />
        {/* Radial glow */}
        <div className="absolute -top-32 -left-32 w-[500px] h-[500px] bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-emerald-500/6 rounded-full blur-3xl pointer-events-none" />

        {/* Brand mark */}
        <div className="relative z-10 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-emerald-500 p-[2px] shadow-lg shadow-cyan-500/25">
            <div className="w-full h-full bg-industrial-950 rounded-[10px] flex items-center justify-center">
              <ScanEye style={{ width: 22, height: 22 }} className="text-cyan-400" />
            </div>
          </div>
          <div>
            <span className="font-black text-lg text-white tracking-tight">VisionInspect AI</span>
            <span className="block text-[10px] font-mono text-slate-500 tracking-wider uppercase mt-0.5">Enterprise Edition</span>
          </div>
        </div>

        {/* Central content */}
        <div className="relative z-10 space-y-8">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-cyan-500/25 bg-cyan-500/10 text-cyan-400 text-[11px] font-mono font-semibold uppercase tracking-wider">
              <span className="relative flex h-1.5 w-1.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-70" />
                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-cyan-400" />
              </span>
              Pipeline Online
            </div>
            <h2 className="text-4xl xl:text-5xl font-black text-white leading-tight tracking-tight">
              Manufacturing<br />
              Defect Detection
              <span className="block text-cyan-400">at Line Speed.</span>
            </h2>
            <p className="text-slate-400 text-[15px] leading-relaxed max-w-sm">
              AI-powered quality control across 15 MVTec AD industrial categories. Real-time inspection, role-based access, tamper-evident audit logs.
            </p>
          </div>

          {/* Feature bullets */}
          <div className="space-y-3">
            {[
              { icon: ShieldCheck, text: 'Role-based access: Engineer, Supervisor, Manager' },
              { icon: ScanEye,    text: '15 MVTec AD categories · sub-40ms inference' },
              { icon: ShieldCheck, text: 'Tamper-evident audit trail & compliance logs' },
            ].map(({ icon: Icon, text }, i) => (
              <div key={i} className="flex items-center gap-3 text-[13px] text-slate-400">
                <Icon className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                <span>{text}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="relative z-10 text-[10px] font-mono text-slate-600 uppercase tracking-wider">
          FastAPI · SQLite · MVTec AD · PyTorch
        </div>
      </div>

      {/* ── Right Panel (form) ── */}
      <div className="flex-1 flex flex-col items-center justify-center p-6 sm:p-10 relative">
        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="absolute top-5 right-5 p-2 rounded-[10px] bg-white dark:bg-industrial-900 border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 shadow-sm hover:scale-105 active:scale-95 transition-all"
          aria-label="Toggle theme"
        >
          {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-600" />}
        </button>

        {/* Mobile brand (shown only on mobile) */}
        <div className="lg:hidden flex items-center gap-2.5 mb-8 self-start">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-cyan-500 to-emerald-500 p-[1.5px]">
            <div className="w-full h-full bg-white dark:bg-industrial-950 rounded-[9px] flex items-center justify-center">
              <ScanEye style={{ width: 16, height: 16 }} className="text-cyan-500 dark:text-cyan-400" />
            </div>
          </div>
          <span className="font-black text-slate-900 dark:text-white text-[16px] tracking-tight">VisionInspect AI</span>
        </div>

        <div className="w-full max-w-sm space-y-6 animate-enter">
          {/* Form header */}
          <div className="space-y-1">
            <h1 className="text-[22px] font-black text-slate-900 dark:text-white tracking-tight">
              {isRegister ? 'Create Operator Account' : 'Sign In'}
            </h1>
            <p className="text-[13px] text-slate-500 dark:text-slate-400">
              {isRegister ? 'Register your role to access the platform.' : 'Use your credentials or a demo role below.'}
            </p>
          </div>

          {/* Demo 1-click logins */}
          {!isRegister && (
            <div className="space-y-2">
              <span className="text-[11px] font-mono text-slate-400 dark:text-slate-500 uppercase tracking-wider font-semibold">Demo — 1-click login</span>
              <div className="grid grid-cols-3 gap-2">
                {demoRoles.map(({ role: r, label, name, color }) => (
                  <button
                    key={r}
                    type="button"
                    onClick={() => handleDemoLogin(r)}
                    disabled={loading}
                    className={`p-3 rounded-xl border text-center transition-all disabled:opacity-50 ${color}`}
                  >
                    <div className="text-[12px] font-bold leading-none">{label}</div>
                    <div className="text-[10px] font-mono text-slate-400 dark:text-slate-500 mt-1 leading-none">{name}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Divider */}
          {!isRegister && (
            <div className="relative flex items-center">
              <div className="flex-1 border-t border-slate-200 dark:border-slate-800" />
              <span className="px-3 text-[11px] font-mono text-slate-400 uppercase tracking-wider bg-slate-50 dark:bg-industrial-950">
                or credentials
              </span>
              <div className="flex-1 border-t border-slate-200 dark:border-slate-800" />
            </div>
          )}

          {/* Error message */}
          {error && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/25 text-rose-600 dark:text-rose-400 text-[12px] flex items-start gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <>
                <div className="space-y-1.5">
                  <label className="block text-[12px] font-semibold text-slate-600 dark:text-slate-400">Full Name</label>
                  <InputField icon={User} type="text" required value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Alex Rivera" />
                </div>
                <div className="space-y-1.5">
                  <label className="block text-[12px] font-semibold text-slate-600 dark:text-slate-400">Email Address</label>
                  <InputField icon={Mail} type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="engineer@plant.com" />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <label className="block text-[12px] font-semibold text-slate-600 dark:text-slate-400">Role</label>
                    <select
                      value={role}
                      onChange={(e) => setRole(e.target.value)}
                      className="w-full px-3 py-2.5 rounded-[10px] bg-slate-50 dark:bg-industrial-900 border border-slate-200 dark:border-slate-700/80 text-slate-800 dark:text-slate-100 text-[13px] focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/15 transition-all"
                    >
                      <option value={ROLES.QUALITY_ENGINEER}>Quality Engineer</option>
                      <option value={ROLES.FACTORY_SUPERVISOR}>Factory Supervisor</option>
                      <option value={ROLES.PRODUCTION_MANAGER}>Production Manager</option>
                    </select>
                  </div>
                  <div className="space-y-1.5">
                    <label className="block text-[12px] font-semibold text-slate-600 dark:text-slate-400">Department</label>
                    <InputField type="text" value={department} onChange={(e) => setDepartment(e.target.value)} placeholder="Line A" />
                  </div>
                </div>
              </>
            )}

            <div className="space-y-1.5">
              <label className="block text-[12px] font-semibold text-slate-600 dark:text-slate-400">
                {isRegister ? 'Username' : 'Username or Email'}
              </label>
              <InputField
                icon={User}
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder={isRegister ? 'quality.engineer' : 'engineer@visioninspect.ai'}
              />
            </div>

            <div className="space-y-1.5">
              <label className="block text-[12px] font-semibold text-slate-600 dark:text-slate-400">Password</label>
              <InputField icon={Lock} type="password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-[10px] bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 text-white text-[13px] font-bold shadow-lg shadow-cyan-600/20 transition-all hover:scale-[1.01] active:scale-[0.98] flex items-center justify-center gap-2 disabled:opacity-60"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <span>{isRegister ? 'Create Account' : 'Sign In'}</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Toggle register / login */}
          <div className="text-center text-[12px] text-slate-500 dark:text-slate-400">
            {isRegister ? 'Already registered? ' : "Don't have an account? "}
            <button
              type="button"
              onClick={() => { setIsRegister(!isRegister); setError(null); }}
              className="text-cyan-600 dark:text-cyan-400 font-semibold hover:underline"
            >
              {isRegister ? 'Sign In' : 'Register'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
