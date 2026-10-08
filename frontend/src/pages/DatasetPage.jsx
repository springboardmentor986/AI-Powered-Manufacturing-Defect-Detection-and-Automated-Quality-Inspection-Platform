import React from 'react';
import { DatasetBrowser } from '../components/DatasetBrowser';

export const DatasetPage = ({ onImportSuccess }) => {
  return (
    <div className="space-y-6">
      <DatasetBrowser onImportSuccess={onImportSuccess} />
    </div>
  );
};
