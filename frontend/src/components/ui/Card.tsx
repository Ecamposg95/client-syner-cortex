import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export const Card: React.FC<CardProps> = ({ children, className = '' }) => {
  return (
    <div
      className={`bg-[var(--surface)] border border-[var(--border)] rounded-lg p-5 transition-all duration-200 hover:shadow-card ${className}`}
    >
      {children}
    </div>
  );
};
