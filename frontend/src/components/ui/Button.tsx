import React from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'danger';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  children: React.ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:   'bg-brand-accent text-white hover:bg-brand-accentHover shadow-accent active:scale-[0.97]',
  secondary: 'bg-transparent text-brand-muted border border-brand-border hover:border-brand-borderStrong hover:text-brand-ink2',
  danger:    'bg-brand-neg/10 text-brand-neg border border-brand-neg/20 hover:bg-brand-neg/20',
};

export const Button: React.FC<ButtonProps> = ({ variant = 'primary', children, className = '', ...props }) => {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200 disabled:opacity-50 disabled:pointer-events-none ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};
