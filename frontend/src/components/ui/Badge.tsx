import React from 'react';

type BadgeVariant = 'active' | 'completed' | 'pending' | 'risk';

interface BadgeProps {
  variant: BadgeVariant;
  label: string;
}

const variantClass: Record<BadgeVariant, string> = {
  active:    'status-badge--active',
  completed: 'status-badge--completed',
  pending:   'status-badge--pending',
  risk:      'status-badge--risk',
};

export const Badge: React.FC<BadgeProps> = ({ variant, label }) => {
  return (
    <span className={`status-badge ${variantClass[variant]}`}>
      {variant === 'active' && <span className="pulse-dot" />}
      {label}
    </span>
  );
};
