import React from 'react';
import { PortalDashboard } from './PortalDashboard';

export const Overview: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="font-bold text-2xl">Dashboard Ejecutivo</h2>
      </div>
      <PortalDashboard />
    </div>
  );
};
