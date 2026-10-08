import React from 'react';
import { CameraSimulator } from '../components/CameraSimulator';

export const SimulatorPage = ({ onNewInspection }) => {
  return (
    <div className="space-y-6">
      <CameraSimulator onNewInspection={onNewInspection} />
    </div>
  );
};
