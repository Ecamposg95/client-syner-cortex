import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { AuthLayout } from '../components/layout/AuthLayout';
import { Loader2, AlertCircle, CheckCircle } from 'lucide-react';

export const Register: React.FC = () => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSuccess, setIsSuccess] = useState(false);
  const { signup, isLoading, error } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName || !email || !password) return;

    const success = await signup(email, fullName, password);
    if (success) {
      setIsSuccess(true);
      setTimeout(() => {
        navigate('/login');
      }, 2500);
    }
  };

  return (
    <AuthLayout>
      <h3 className="font-bold text-xl text-white text-center mb-6">
        Crear cuenta en Syner Hub
      </h3>

      {isSuccess ? (
        <div className="text-center py-6 space-y-3">
          <div className="w-12 h-12 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center mx-auto text-emerald-400">
            <CheckCircle size={24} />
          </div>
          <h4 className="font-semibold text-white">¡Registro exitoso!</h4>
          <p className="text-xs" style={{ color: 'var(--dark-muted)' }}>Redirigiendo al acceso...</p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 bg-red-950/30 border border-red-500/20 text-red-300 text-xs rounded-xl flex items-start space-x-2">
              <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium mb-1.5 pl-1" style={{ color: 'var(--dark-muted)' }}>
              Nombre completo
            </label>
            <input
              type="text"
              required
              placeholder="Humberto Villanueva"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full p-3 rounded-xl text-white text-sm transition-all outline-none"
              style={{
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
              }}
            />
          </div>

          <div>
            <label className="block text-xs font-medium mb-1.5 pl-1" style={{ color: 'var(--dark-muted)' }}>
              Correo electrónico
            </label>
            <input
              type="email"
              required
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
              placeholder="Min. 8 characters"
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
                <span>Creando cuenta...</span>
              </>
            ) : (
              <span>Crear cuenta</span>
            )}
          </button>
        </form>
      )}

      {!isSuccess && (
        <div className="mt-6 text-center">
          <p className="text-xs" style={{ color: 'var(--dark-muted)' }}>
            ¿Ya tienes cuenta?{' '}
            <Link to="/login" className="font-medium hover:underline" style={{ color: 'var(--accent-bright)' }}>
              Iniciar sesión
            </Link>
          </p>
        </div>
      )}
    </AuthLayout>
  );
};
export default Register;
