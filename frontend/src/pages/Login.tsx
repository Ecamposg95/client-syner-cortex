import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { AuthLayout } from '../components/layout/AuthLayout';
import { Loader2, AlertCircle } from 'lucide-react';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login, isLoading, error } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;

    const success = await login(email, password);
    if (success) {
      navigate('/dashboard');
    }
  };

  return (
    <AuthLayout>
      <h3 className="font-bold text-xl text-white text-center mb-6">
        Acceso a Syner Hub
      </h3>

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 bg-red-950/30 border border-red-500/20 text-red-300 text-xs rounded-xl flex items-start space-x-2">
            <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div>
          <label className="block text-xs font-medium mb-1.5 pl-1" style={{ color: 'var(--dark-muted)' }}>
            Correo electrónico
          </label>
          <input
            type="email"
            required
            autoComplete="email"
            placeholder="name@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full p-3 rounded-xl text-white text-sm transition-all outline-none"
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)',
            }}
          />
        </div>

        <div>
          <label className="block text-xs font-medium mb-1.5 pl-1" style={{ color: 'var(--dark-muted)' }}>
            Contraseña
          </label>
          <input
            type="password"
            required
            autoComplete="current-password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full p-3 rounded-xl text-white text-sm transition-all outline-none"
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)',
            }}
          />
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full p-3 rounded-xl font-semibold text-white text-sm transition-all duration-300 active:scale-95 flex items-center justify-center space-x-2 disabled:opacity-60 shadow-accent"
          style={{ background: 'linear-gradient(135deg, var(--accent-strong), var(--accent))' }}
        >
          {isLoading ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              <span>Iniciando sesión...</span>
            </>
          ) : (
            <span>Entrar a plataforma</span>
          )}
        </button>
      </form>

      <div className="mt-6 text-center">
        <p className="text-xs" style={{ color: 'var(--dark-muted)' }}>
          ¿No tienes acceso?{' '}
          <Link to="/register" className="font-medium hover:underline" style={{ color: 'var(--accent-bright)' }}>
            Crear cuenta
          </Link>
        </p>
      </div>
    </AuthLayout>
  );
};
export default Login;
