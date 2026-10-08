import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  ShieldCheck, 
  Clock, 
  RefreshCw, 
  User, 
  Activity,
  Layers
} from 'lucide-react';
import { auditAPI } from '../api/client';
import { useAuth, ROLES } from '../context/AuthContext';

export const AuditLogsPage = () => {
  const { user, hasRole } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAction, setSelectedAction] = useState('all');

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params = {
        action: selectedAction !== 'all' ? selectedAction : undefined,
        limit: 100
      };
      const res = await auditAPI.getLogs(params);
      setLogs(res.data);
    } catch (err) {
      console.error('Failed to fetch audit logs', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [selectedAction]);

  if (!hasRole([ROLES.FACTORY_SUPERVISOR, ROLES.PRODUCTION_MANAGER, ROLES.ADMIN])) {
    return (
      <div className="glass-panel rounded-2xl p-12 text-center space-y-3">
        <ShieldAlert className="w-10 h-10 mx-auto text-amber-500" />
        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">Restricted Security Console</h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto">
          Audit logs are restricted to Factory Supervisors and Production Managers. Please switch your active role to view compliance trails.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-enter">
      {/* Header */}
      <div className="glass-panel p-5 sm:p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-amber-500" />
            Security & System Audit Trails
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Tamper-evident logs of authentications, quality overrides, uploads, and batch runs.
          </p>
        </div>

        <div className="flex items-center space-x-2.5">
          <button
            onClick={fetchLogs}
            className="p-2 rounded-xl bg-slate-100 dark:bg-industrial-900 hover:bg-slate-200 dark:hover:bg-industrial-800 border border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-cyan-500' : ''}`} />
          </button>
        </div>
      </div>

      {/* Action Filter */}
      <div className="glass-panel p-4 flex items-center justify-between">
        <div className="flex items-center space-x-2 text-xs font-mono">
          <span className="text-slate-500 dark:text-slate-400">Filter Event:</span>
          <select
            value={selectedAction}
            onChange={(e) => setSelectedAction(e.target.value)}
            className="px-3 py-1.5 rounded-xl bg-slate-50 dark:bg-industrial-900 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200 text-xs font-medium"
          >
            <option value="all">All System Events</option>
            <option value="USER_LOGIN">USER_LOGIN</option>
            <option value="IMAGE_UPLOAD">IMAGE_UPLOAD</option>
            <option value="DECISION_OVERRIDE">DECISION_OVERRIDE</option>
            <option value="BATCH_CREATED">BATCH_CREATED</option>
            <option value="DATASET_SEEDED">DATASET_SEEDED</option>
            <option value="INSPECTION_DELETED">INSPECTION_DELETED</option>
          </select>
        </div>

        <span className="text-xs font-mono text-slate-500 dark:text-slate-400">
          Showing {logs.length} logged events
        </span>
      </div>

      {/* Logs Table */}
      <div className="glass-panel overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left data-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Event Action</th>
                <th>Operator / User</th>
                <th>Resource Type</th>
                <th>Status</th>
                <th>Event Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-mono text-xs text-slate-700 dark:text-slate-300">
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400">
                    No audit records match the current filter.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-100/50 dark:hover:bg-industrial-900/40 transition-colors">
                    <td className="py-3 px-4 text-slate-500 dark:text-slate-400 text-[11px]">
                      {log.timestamp ? new Date(log.timestamp).toLocaleString() : 'N/A'}
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[11px] bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-cyan-600 dark:text-cyan-400 font-semibold">
                        {log.action}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-800 dark:text-slate-200">
                      {log.user_email || 'System'}
                    </td>
                    <td className="py-3 px-4 text-slate-500 dark:text-slate-400 capitalize">
                      {log.resource_type || '-'}
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-emerald-600 dark:text-emerald-400 font-semibold text-[11px]">
                        {log.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-[11px] text-slate-500 dark:text-slate-400 max-w-xs truncate">
                      {JSON.stringify(log.details)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
