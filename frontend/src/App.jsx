import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { UploadModal } from './components/UploadModal';
import { InspectionDetail } from './components/InspectionDetail';

import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { InspectionsPage } from './pages/InspectionsPage';
import { DatasetPage } from './pages/DatasetPage';
import { SimulatorPage } from './pages/SimulatorPage';
import { AuditLogsPage } from './pages/AuditLogsPage';

function MainApp() {
  const { isAuthenticated, loading } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-industrial-950 flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 border-4 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin" />
        <span className="text-xs font-mono text-cyan-600 dark:text-cyan-400 tracking-wider">
          INITIALIZING VISIONINSPECT PLATFORM...
        </span>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage onLoginSuccess={() => setActiveTab('dashboard')} />;
  }

  const handleUploadSuccess = () => {
    setRefreshTrigger(prev => prev + 1);
    setActiveTab('inspections');
  };

  const handleImportSuccess = (newRec) => {
    setSelectedRecord(newRec);
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-industrial-950 text-slate-900 dark:text-slate-100 flex flex-col selection:bg-cyan-500 selection:text-white transition-colors duration-200">
      {/* Top Navbar */}
      <Navbar 
        onOpenUpload={() => setUploadModalOpen(true)}
        onOpenSimulator={() => setActiveTab('simulator')}
      />

      {/* Main Layout Area */}
      <div className="flex-1 flex">
        {/* Sidebar */}
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

        {/* Content Container */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full overflow-x-hidden">
          {activeTab === 'dashboard' && (
            <DashboardPage
              key={refreshTrigger}
              onSelectRecord={(rec) => setSelectedRecord(rec)}
              onOpenUpload={() => setUploadModalOpen(true)}
              onOpenSimulator={() => setActiveTab('simulator')}
              onOpenDataset={() => setActiveTab('dataset')}
              setActiveTab={setActiveTab}
            />
          )}

          {activeTab === 'inspections' && (
            <InspectionsPage
              key={refreshTrigger}
              onSelectRecord={(rec) => setSelectedRecord(rec)}
              onOpenUpload={() => setUploadModalOpen(true)}
              onOpenSimulator={() => setActiveTab('simulator')}
            />
          )}

          {activeTab === 'dataset' && (
            <DatasetPage onImportSuccess={handleImportSuccess} />
          )}

          {activeTab === 'simulator' && (
            <SimulatorPage 
              onNewInspection={() => setRefreshTrigger(prev => prev + 1)} 
            />
          )}

          {activeTab === 'audit' && (
            <AuditLogsPage />
          )}
        </main>
      </div>

      {/* Upload Modal */}
      <UploadModal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />

      {/* Inspection Detail Modal */}
      {selectedRecord && (
        <InspectionDetail
          record={selectedRecord}
          onClose={() => setSelectedRecord(null)}
          onUpdate={(updated) => {
            setSelectedRecord(updated);
            setRefreshTrigger(prev => prev + 1);
          }}
          onDelete={() => {
            setSelectedRecord(null);
            setRefreshTrigger(prev => prev + 1);
          }}
        />
      )}
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <MainApp />
      </AuthProvider>
    </ThemeProvider>
  );
}
