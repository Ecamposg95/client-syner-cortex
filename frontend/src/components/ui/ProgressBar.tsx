import React from 'react';

interface ProgressBarProps {
  percent: number;
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ percent, className = '' }) => {
  const clamped = Math.max(0, Math.min(100, percent));
  return (
    <div className={`progress-track ${className}`}>
      <div className="progress-fill" style={{ width: `${clamped}%` }} />
    </div>
  );
};
