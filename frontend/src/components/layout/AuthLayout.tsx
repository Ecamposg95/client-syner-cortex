import React from 'react';

interface AuthLayoutProps {
  children: React.ReactNode;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative font-sans overflow-hidden"
         style={{ background: 'var(--dark-bg)', color: 'var(--dark-fg)' }}>
      
      {/* GLOW DECORATIONS */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full blur-[100px] -z-10 pointer-events-none"
           style={{ background: 'var(--accent-glow)' }} />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full blur-[100px] -z-10 pointer-events-none"
           style={{ background: 'rgba(44, 154, 166, 0.05)' }} />

      {/* CORE FRAME CARD */}
      <div className="w-full max-w-md atlas-glass rounded-3xl p-8 relative">
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-2xl flex items-center justify-center font-bold text-white text-lg mb-3 shadow-accent"
               style={{ background: 'linear-gradient(135deg, var(--accent-strong), var(--accent))' }}>
            SH
          </div>
          <h2 className="font-extrabold text-2xl tracking-wider text-white">
            Syner Hub
          </h2>
          <p className="font-mono text-[10px] mt-1 uppercase tracking-widest font-semibold"
             style={{ color: 'var(--dark-muted)' }}>
            Transformación con trazabilidad
          </p>
        </div>
        
        {children}
      </div>
    </div>
  );
};
