import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../api/client';

const AuthContext = createContext(null);

export const ROLES = {
  QUALITY_ENGINEER: 'quality_engineer',
  FACTORY_SUPERVISOR: 'factory_supervisor',
  PRODUCTION_MANAGER: 'production_manager',
  ADMIN: 'admin'
};

export const ROLE_DETAILS = {
  quality_engineer: {
    label: 'Quality Engineer',
    personaName: 'Alex Rivera',
    department: 'Station A Quality Inspection',
    badgeColor: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
    lightBadgeColor: 'bg-cyan-50 text-cyan-700 border-cyan-200',
    accentColor: 'cyan',
    description: 'Line level defect acquisition, live camera verification, defect triage & manual sign-offs.'
  },
  factory_supervisor: {
    label: 'Factory Supervisor',
    personaName: 'Sarah Chen',
    department: 'Manufacturing Shift Operations',
    badgeColor: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
    lightBadgeColor: 'bg-amber-50 text-amber-700 border-amber-200',
    accentColor: 'amber',
    description: 'Batch production oversight, line throughput, defect severity monitoring & compliance auditing.'
  },
  production_manager: {
    label: 'Production Manager',
    personaName: 'Marcus Vance',
    department: 'Plant Operations & Quality Strategy',
    badgeColor: 'bg-purple-500/15 text-purple-400 border-purple-500/30',
    lightBadgeColor: 'bg-purple-50 text-purple-700 border-purple-200',
    accentColor: 'purple',
    description: 'Executive yield analytics, cross-category benchmark KPIs, quality cost trends & full system security audit logs.'
  },
  admin: {
    label: 'System Administrator',
    personaName: 'Admin System',
    department: 'Industrial IT Infrastructure',
    badgeColor: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
    lightBadgeColor: 'bg-rose-50 text-rose-700 border-rose-200',
    accentColor: 'rose',
    description: 'Full administrative access and infrastructure controls.'
  }
};

export const ROLE_LABELS = {
  quality_engineer: 'Quality Engineer',
  factory_supervisor: 'Factory Supervisor',
  production_manager: 'Production Manager',
  admin: 'System Administrator'
};

export const ROLE_COLORS = {
  quality_engineer: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30 dark:bg-cyan-500/15 dark:text-cyan-400 dark:border-cyan-500/30 light:bg-cyan-100 light:text-cyan-800',
  factory_supervisor: 'bg-amber-500/15 text-amber-400 border-amber-500/30 dark:bg-amber-500/15 dark:text-amber-400 dark:border-amber-500/30 light:bg-amber-100 light:text-amber-800',
  production_manager: 'bg-purple-500/15 text-purple-400 border-purple-500/30 dark:bg-purple-500/15 dark:text-purple-400 dark:border-purple-500/30 light:bg-purple-100 light:text-purple-800',
  admin: 'bg-rose-500/15 text-rose-400 border-rose-500/30'
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('visioninspect_token'));
  const [loading, setLoading] = useState(true);

  const fetchProfile = async () => {
    try {
      const res = await authAPI.getMe();
      setUser(res.data);
    } catch (err) {
      console.warn('Authentication token expired or invalid');
      logout();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchProfile();
    } else {
      // Default auto-login to Quality Engineer for instant access
      switchToDemoRole(ROLES.QUALITY_ENGINEER);
    }
  }, []);

  const login = async (username, password) => {
    const res = await authAPI.login(username, password);
    const { access_token, user: userData } = res.data;
    localStorage.setItem('visioninspect_token', access_token);
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const register = async (userData) => {
    const res = await authAPI.register(userData);
    const { access_token, user: newUserData } = res.data;
    localStorage.setItem('visioninspect_token', access_token);
    setToken(access_token);
    setUser(newUserData);
    return newUserData;
  };

  const logout = () => {
    localStorage.removeItem('visioninspect_token');
    setToken(null);
    setUser(null);
    setLoading(false);
  };

  const switchToDemoRole = async (roleName) => {
    setLoading(true);
    try {
      const res = await authAPI.switchDemoRole(roleName);
      const { access_token, user: userData } = res.data;
      localStorage.setItem('visioninspect_token', access_token);
      setToken(access_token);
      setUser(userData);
    } catch (err) {
      console.error('Failed to switch demo role', err);
    } finally {
      setLoading(false);
    }
  };

  const hasRole = (allowedRoles) => {
    if (!user) return false;
    if (user.role === ROLES.ADMIN) return true;
    return allowedRoles.includes(user.role);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        register,
        logout,
        switchToDemoRole,
        hasRole,
        currentRoleDetails: user ? ROLE_DETAILS[user.role] || ROLE_DETAILS.quality_engineer : ROLE_DETAILS.quality_engineer,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
