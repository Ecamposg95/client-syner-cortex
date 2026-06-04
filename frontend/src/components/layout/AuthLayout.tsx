import React from 'react';

interface AuthLayoutProps {
  children: React.ReactNode;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-[#080B11] text-[#F8FAFC] flex items-center justify-center p-4 relative font-sans overflow-hidden">
      
      {/* GLOW DECORATIONS */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-violet-600/10 rounded-full blur-3xl -z-10" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl -z-10" />

      {/* CORE FRAME CARD */}
      <div className="w-full max-w-md bg-[#0C1220]/50 backdrop-blur-xl border border-white/5 rounded-3xl p-8 shadow-2xl relative">
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-violet-600 via-indigo-500 to-pink-500 flex items-center justify-center font-bold text-white text-lg shadow-glow mb-3">
            SC
          </div>
          <h2 className="font-display font-extrabold text-2xl tracking-wider text-white">
            Syner Cortex
          </h2>
          <p className="text-xs text-slate-400 mt-1 uppercase tracking-widest font-semibold">
            AI consulting operating system
          </p>
        </div>
        
        {children}
      </div>
    </div>
  );
};
