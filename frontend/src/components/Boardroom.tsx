import React from 'react';
import { CommandCenterView } from './views/CommandCenterView';

/**
 * Boardroom — crew Command Center entry point. The portfolio dashboard now lives
 * in CommandCenterView (wired to real data via GET /portfolio/summary); this
 * thin wrapper keeps the existing Boardroom export/route working.
 */
export const Boardroom: React.FC = () => {
  return <CommandCenterView />;
};
