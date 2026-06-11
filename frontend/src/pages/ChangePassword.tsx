import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { AuthLayout } from '../components/layout/AuthLayout';
import apiClient from '../api/client';
import { Loader2, AlertCircle, ShieldCheck } from 'lucide-react';

// ── API shapes ──────────────────────────────────────────────────────────
interface PydanticDetailItem {
  msg?: string;
  loc?: (string | number)[];
}

export const ChangePassword: React.FC = () => {
  const navigate = useNavigate();
  const { fetchUser, logout } = useAuthStore();

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const parseServerError = (data: unknown): string => {
    // Pydantic 422 → { detail: [{ msg, loc }] }
    if (data && typeof data === 'object' && 'detail' in data) {
      const detail = (data as { detail: unknown }).detail;
      if (Array.isArray(detail)) {
        const first = detail[0] as PydanticDetailItem | undefined;
        if (first?.msg) return 'La contraseña no es válida: mínimo 8 caracteres.';
        return 'La contraseña no es válida: mínimo 8 caracteres.';
      }
      if (typeof detail === 'string') return detail;
    }
    return 'No se pudo cambiar la contraseña. Inténtalo de nuevo.';
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (newPassword.length < 8) {
      setError('La contraseña debe tener mínimo 8 caracteres.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Las contraseñas no coinciden.');
      return;
    }

    setSubmitting(true);
    try {
      await apiClient.post('/auth/change-password', { new_password: newPassword });
      await fetchUser();
      navigate('/dashboard');
    } catch (err: any) {
      setError(parseServerError(err.response?.data));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout>
      <div className="flex flex-col items-center mb-6">
        <div
          className="w-11 h-11 rounded-2xl flex items-center justify-center text-white mb-3 shadow-accent"
          style={{ background: 'linear-gradient(135deg, var(--accent-strong), var(--accent))' }}
        >
          <ShieldCheck size={22} />
        </div>
        <h3 className="font-bold text-xl text-white text-center">Cambia tu contraseña</h3>
        <p className="text-xs text-center mt-1.5" style={{ color: 'var(--dark-muted)' }}>
          Por seguridad, debes establecer una nueva contraseña antes de continuar.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 bg-red-950/30 border border-red-500/20 text-red-300 text-xs rounded-xl flex items-start space-x-2">
            <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div>
          <label className="block text-xs font-medium mb-1.5 pl-1" style={{ color: 'var(--dark-muted)' }}>
            Nueva contraseña
          </label>
          <input
            type="password"
            required
            autoComplete="new-password"
            placeholder="••••••••"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className="w-full p-3 rounded-xl text-white text-sm transition-all outline-none"
            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}
          />
        </div>

        <div>
          <label className="block text-xs font-medium mb-1.5 pl-1" style={{ color: 'var(--dark-muted)' }}>
            Confirmar contraseña
          </label>
          <input
            type="password"
            required
            autoComplete="new-password"
            placeholder="••••••••"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="w-full p-3 rounded-xl text-white text-sm transition-all outline-none"
            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}
          />
          <p className="text-[11px] mt-1.5 pl-1" style={{ color: 'var(--dark-muted)' }}>
            Mínimo 8 caracteres.
          </p>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full p-3 rounded-xl font-semibold text-white text-sm transition-all duration-300 active:scale-95 flex items-center justify-center space-x-2 disabled:opacity-60 shadow-accent"
          style={{ background: 'linear-gradient(135deg, var(--accent-strong), var(--accent))' }}
        >
          {submitting ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              <span>Guardando...</span>
            </>
          ) : (
            <span>Guardar y continuar</span>
          )}
        </button>
      </form>

      <div className="mt-6 text-center">
        <button
          type="button"
          onClick={handleLogout}
          className="text-xs font-medium hover:underline"
          style={{ color: 'var(--accent-bright)' }}
        >
          Cerrar sesión
        </button>
      </div>
    </AuthLayout>
  );
};

export default ChangePassword;
