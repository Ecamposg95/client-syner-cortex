import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft, Loader2, Plus, X, Copy, Check, Users, Boxes, LayoutGrid,
  AlertCircle, Save, KeyRound,
} from 'lucide-react';
import apiClient from '../../../api/client';
import { Card } from '../../ui/Card';
import { Badge } from '../../ui/Badge';

// ── API shapes ──────────────────────────────────────────────────────────
interface ClientUser {
  user_id: number;
  email: string;
  full_name: string | null;
  role: string;
  must_change_password: boolean;
  is_active: boolean;
}

interface ClientWorkspace {
  id: number;
  name: string;
  description: string | null;
}

interface ClientModule {
  code: string;
  name: string;
  description: string | null;
  enabled: boolean;
}

interface ClientDetail {
  id: number;
  name: string;
  slug: string;
  organization_type: string;
  created_at: string;
  users: ClientUser[];
  workspaces: ClientWorkspace[];
  modules: ClientModule[];
}

interface CreatedUser {
  user_id: number;
  email: string;
  role: string;
  temp_password: string;
}

const CLIENT_ROLES = [
  { value: 'CLIENT_OWNER', label: 'Owner' },
  { value: 'CLIENT_MANAGER', label: 'Manager' },
  { value: 'CLIENT_VIEWER', label: 'Viewer' },
  { value: 'CLIENT_EXECUTIVE', label: 'Executive' },
];

const inputStyle: React.CSSProperties = {
  background: 'var(--surface-2)',
  border: '1px solid var(--border)',
  color: 'var(--ink)',
};

export const AdminClientDetailView: React.FC = () => {
  const { orgId } = useParams<{ orgId: string }>();
  const navigate = useNavigate();

  const [client, setClient] = useState<ClientDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modules local state
  const [moduleState, setModuleState] = useState<Record<string, boolean>>({});
  const [savingModules, setSavingModules] = useState(false);
  const [modulesSaved, setModulesSaved] = useState(false);

  // User create modal
  const [userModalOpen, setUserModalOpen] = useState(false);
  const [uEmail, setUEmail] = useState('');
  const [uFullName, setUFullName] = useState('');
  const [uRole, setURole] = useState('CLIENT_MANAGER');
  const [uPassword, setUPassword] = useState('');
  const [userSubmitting, setUserSubmitting] = useState(false);
  const [userFormError, setUserFormError] = useState<string | null>(null);
  const [createdUser, setCreatedUser] = useState<CreatedUser | null>(null);
  const [copiedUser, setCopiedUser] = useState(false);

  // Workspace create modal
  const [wsModalOpen, setWsModalOpen] = useState(false);
  const [wsName, setWsName] = useState('');
  const [wsDescription, setWsDescription] = useState('');
  const [wsSubmitting, setWsSubmitting] = useState(false);
  const [wsFormError, setWsFormError] = useState<string | null>(null);

  const loadClient = () =>
    apiClient.get<ClientDetail>(`/admin/clients/${orgId}`).then((res) => {
      setClient(res.data);
      const next: Record<string, boolean> = {};
      res.data.modules.forEach((m) => {
        next[m.code] = m.enabled;
      });
      setModuleState(next);
    });

  useEffect(() => {
    if (!orgId) return;
    setLoading(true);
    setError(null);
    loadClient()
      .catch((e) => {
        console.error(e);
        setError('No se pudo cargar el cliente.');
      })
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId]);

  // ── Modules ─────────────────────────────────────────────────────────────
  const toggleModule = (code: string) => {
    setModulesSaved(false);
    setModuleState((cur) => ({ ...cur, [code]: !cur[code] }));
  };

  const handleSaveModules = async () => {
    if (!client) return;
    setSavingModules(true);
    setModulesSaved(false);
    try {
      const modules = client.modules.map((m) => ({
        code: m.code,
        enabled: !!moduleState[m.code],
      }));
      await apiClient.put(`/admin/clients/${orgId}/modules`, { modules });
      await loadClient();
      setModulesSaved(true);
      window.setTimeout(() => setModulesSaved(false), 2000);
    } catch (e) {
      console.error(e);
    } finally {
      setSavingModules(false);
    }
  };

  // ── User create ─────────────────────────────────────────────────────────
  const openUserModal = () => {
    setUEmail('');
    setUFullName('');
    setURole('CLIENT_MANAGER');
    setUPassword('');
    setUserFormError(null);
    setCreatedUser(null);
    setCopiedUser(false);
    setUserModalOpen(true);
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uEmail.trim()) return;
    setUserSubmitting(true);
    setUserFormError(null);
    try {
      const body: Record<string, unknown> = { email: uEmail.trim(), role: uRole };
      if (uFullName.trim()) body.full_name = uFullName.trim();
      if (uPassword.trim()) body.password = uPassword.trim();

      const res = await apiClient.post<CreatedUser>(`/admin/clients/${orgId}/users`, body);
      await loadClient();
      setCreatedUser(res.data);
    } catch (err: any) {
      setUserFormError(err.response?.data?.detail?.toString() || 'No se pudo crear el usuario.');
    } finally {
      setUserSubmitting(false);
    }
  };

  const handleCopyUserTemp = async () => {
    if (!createdUser) return;
    try {
      await navigator.clipboard.writeText(createdUser.temp_password);
      setCopiedUser(true);
      window.setTimeout(() => setCopiedUser(false), 1800);
    } catch (e) {
      console.error(e);
    }
  };

  // ── Workspace create ─────────────────────────────────────────────────────
  const openWsModal = () => {
    setWsName('');
    setWsDescription('');
    setWsFormError(null);
    setWsModalOpen(true);
  };

  const handleCreateWorkspace = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!wsName.trim()) return;
    setWsSubmitting(true);
    setWsFormError(null);
    try {
      const body: Record<string, unknown> = { name: wsName.trim() };
      if (wsDescription.trim()) body.description = wsDescription.trim();
      await apiClient.post(`/admin/clients/${orgId}/workspaces`, body);
      await loadClient();
      setWsModalOpen(false);
    } catch (err: any) {
      setWsFormError(err.response?.data?.detail?.toString() || 'No se pudo crear el workspace.');
    } finally {
      setWsSubmitting(false);
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="p-12 flex flex-col items-center justify-center gap-4">
        <Loader2 size={36} className="animate-spin text-[var(--accent)]" />
        <p className="text-sm text-[var(--muted)]">Cargando cliente...</p>
      </div>
    );
  }

  if (error || !client) {
    return (
      <div className="space-y-6">
        <button
          type="button"
          onClick={() => navigate('/admin/clients')}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-[var(--muted)] hover:text-[var(--ink)] transition-colors"
        >
          <ArrowLeft size={16} />
          Volver a clientes
        </button>
        <div className="text-center py-16 flex flex-col items-center gap-3">
          <AlertCircle size={32} className="text-[var(--muted-2)]" />
          <p className="text-[var(--muted)]">{error || 'Cliente no encontrado.'}</p>
        </div>
      </div>
    );
  }

  const moduleChanged = client.modules.some((m) => !!moduleState[m.code] !== m.enabled);

  return (
    <div className="space-y-8">
      {/* Back + header */}
      <div className="space-y-4">
        <button
          type="button"
          onClick={() => navigate('/admin/clients')}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-[var(--muted)] hover:text-[var(--ink)] transition-colors"
        >
          <ArrowLeft size={16} />
          Volver a clientes
        </button>

        <div className="flex items-center gap-3">
          <div
            className="p-2.5 rounded-xl text-white"
            style={{ background: 'linear-gradient(135deg, var(--accent-strong), var(--accent))' }}
          >
            <Users size={24} />
          </div>
          <div>
            <h2 className="font-extrabold text-2xl">{client.name}</h2>
            <p className="text-sm text-[var(--muted)]">
              <span className="font-mono">{client.slug}</span> · {client.organization_type}
            </p>
          </div>
        </div>
      </div>

      {/* ── Usuarios ── */}
      <section className="space-y-4">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <h3 className="font-bold text-lg text-[var(--ink)] flex items-center gap-2">
            <Users size={18} className="text-[var(--accent)]" />
            Usuarios
          </h3>
          <button
            type="button"
            onClick={openUserModal}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-white rounded-lg transition-colors"
            style={{ background: 'var(--accent)' }}
          >
            <Plus size={14} />
            Crear usuario
          </button>
        </div>

        {client.users.length === 0 ? (
          <Card>
            <p className="text-sm text-[var(--muted)] text-center py-4">
              No hay usuarios en esta organización.
            </p>
          </Card>
        ) : (
          <div className="space-y-2">
            {client.users.map((u) => (
              <Card key={u.user_id} className="p-4">
                <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-semibold text-sm text-[var(--ink)] truncate">
                        {u.full_name || u.email}
                      </span>
                      {!u.is_active && <Badge variant="risk" label="Inactivo" />}
                    </div>
                    <p className="text-xs text-[var(--muted)] font-mono truncate">{u.email}</p>
                  </div>
                  <div className="flex items-center gap-2 flex-wrap shrink-0">
                    <span className="status-badge status-badge--pending">{u.role}</span>
                    {u.must_change_password && (
                      <span className="status-badge status-badge--risk">
                        <KeyRound size={12} className="inline mr-1 -mt-px" />
                        debe cambiar contraseña
                      </span>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* ── Módulos ── */}
      <section className="space-y-4">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <h3 className="font-bold text-lg text-[var(--ink)] flex items-center gap-2">
            <Boxes size={18} className="text-[var(--accent)]" />
            Módulos
          </h3>
          <button
            type="button"
            onClick={handleSaveModules}
            disabled={savingModules || !moduleChanged}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-white rounded-lg transition-colors disabled:opacity-50"
            style={{ background: 'var(--accent)' }}
          >
            {savingModules ? (
              <Loader2 size={14} className="animate-spin" />
            ) : modulesSaved ? (
              <Check size={14} />
            ) : (
              <Save size={14} />
            )}
            {modulesSaved ? 'Guardado' : 'Guardar módulos'}
          </button>
        </div>

        {client.modules.length === 0 ? (
          <Card>
            <p className="text-sm text-[var(--muted)] text-center py-4">
              No hay módulos disponibles.
            </p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {client.modules.map((m) => {
              const checked = !!moduleState[m.code];
              return (
                <Card key={m.code} className="p-4">
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleModule(m.code)}
                      className="accent-[var(--accent)] w-4 h-4 mt-0.5"
                    />
                    <div className="min-w-0">
                      <p className="font-semibold text-sm text-[var(--ink)] leading-tight">
                        {m.name}
                      </p>
                      <p className="text-[10px] uppercase tracking-wide font-mono text-[var(--muted-2)] mb-1">
                        {m.code}
                      </p>
                      {m.description && (
                        <p className="text-xs text-[var(--muted)] leading-relaxed">
                          {m.description}
                        </p>
                      )}
                    </div>
                  </label>
                </Card>
              );
            })}
          </div>
        )}
      </section>

      {/* ── Workspaces ── */}
      <section className="space-y-4">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <h3 className="font-bold text-lg text-[var(--ink)] flex items-center gap-2">
            <LayoutGrid size={18} className="text-[var(--accent)]" />
            Workspaces
          </h3>
          <button
            type="button"
            onClick={openWsModal}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-white rounded-lg transition-colors"
            style={{ background: 'var(--accent)' }}
          >
            <Plus size={14} />
            Crear workspace
          </button>
        </div>

        {client.workspaces.length === 0 ? (
          <Card>
            <p className="text-sm text-[var(--muted)] text-center py-4">
              No hay workspaces en esta organización.
            </p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {client.workspaces.map((ws) => (
              <Card key={ws.id} className="p-4">
                <p className="font-semibold text-sm text-[var(--ink)] leading-tight mb-1">
                  {ws.name}
                </p>
                <p className="text-xs text-[var(--muted)] leading-relaxed">
                  {ws.description || 'Sin descripción.'}
                </p>
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* ── Crear usuario MODAL ── */}
      {userModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: 'rgba(0,0,0,0.4)' }}
          onClick={() => !userSubmitting && setUserModalOpen(false)}
        >
          <div
            className="w-full max-w-md rounded-xl p-6 shadow-float relative"
            style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => !userSubmitting && setUserModalOpen(false)}
              className="absolute top-4 right-4 transition-colors"
              style={{ color: 'var(--muted)' }}
            >
              <X size={20} />
            </button>

            {createdUser ? (
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Check size={20} className="text-[var(--accent)]" />
                  <h3 className="font-bold text-lg" style={{ color: 'var(--ink)' }}>
                    Usuario creado
                  </h3>
                </div>
                <p className="text-xs text-[var(--muted)] mb-4">
                  Comparte la contraseña temporal con el usuario. Se muestra una sola vez.
                </p>

                <div
                  className="rounded-lg p-4 space-y-3"
                  style={{ background: 'var(--accent-tint)', border: '1px solid var(--border)' }}
                >
                  <div>
                    <p className="text-[10px] uppercase tracking-wide font-semibold text-[var(--muted-2)] mb-0.5">
                      Email
                    </p>
                    <p className="text-sm font-mono text-[var(--ink)] break-all">
                      {createdUser.email}
                    </p>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase tracking-wide font-semibold text-[var(--muted-2)] mb-0.5">
                      Contraseña temporal
                    </p>
                    <div className="flex items-center gap-2">
                      <code
                        className="flex-1 px-2.5 py-1.5 rounded-lg text-sm font-mono break-all"
                        style={inputStyle}
                      >
                        {createdUser.temp_password}
                      </code>
                      <button
                        type="button"
                        onClick={handleCopyUserTemp}
                        className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-semibold rounded-lg transition-colors shrink-0 text-white"
                        style={{ background: 'var(--accent)' }}
                      >
                        {copiedUser ? (
                          <>
                            <Check size={13} />
                            ¡Copiado!
                          </>
                        ) : (
                          <>
                            <Copy size={13} />
                            Copiar
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end mt-5">
                  <button
                    type="button"
                    onClick={() => setUserModalOpen(false)}
                    className="px-4 py-2 text-xs font-semibold text-white rounded-lg"
                    style={{ background: 'var(--accent)' }}
                  >
                    Listo
                  </button>
                </div>
              </div>
            ) : (
              <>
                <h3 className="font-bold text-lg mb-1" style={{ color: 'var(--ink)' }}>
                  Crear usuario
                </h3>
                <p className="text-xs text-[var(--muted)] mb-4">{client.name}</p>

                {userFormError && (
                  <div className="mb-4 p-3 rounded-lg text-xs bg-red-950/20 border border-red-500/20 text-red-400">
                    {userFormError}
                  </div>
                )}

                <form onSubmit={handleCreateUser} className="space-y-4">
                  <div>
                    <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--muted)' }}>
                      Email
                    </label>
                    <input
                      type="email"
                      required
                      placeholder="usuario@cliente.com"
                      value={uEmail}
                      onChange={(e) => setUEmail(e.target.value)}
                      className="w-full p-2.5 rounded-lg text-sm transition-all outline-none"
                      style={inputStyle}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--muted)' }}>
                      Nombre completo
                    </label>
                    <input
                      type="text"
                      placeholder="Opcional"
                      value={uFullName}
                      onChange={(e) => setUFullName(e.target.value)}
                      className="w-full p-2.5 rounded-lg text-sm transition-all outline-none"
                      style={inputStyle}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--muted)' }}>
                      Rol
                    </label>
                    <select
                      value={uRole}
                      onChange={(e) => setURole(e.target.value)}
                      className="w-full p-2.5 rounded-lg text-sm transition-all outline-none"
                      style={inputStyle}
                    >
                      {CLIENT_ROLES.map((r) => (
                        <option key={r.value} value={r.value}>
                          {r.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--muted)' }}>
                      Contraseña
                    </label>
                    <input
                      type="text"
                      placeholder="Dejar en blanco para autogenerar"
                      value={uPassword}
                      onChange={(e) => setUPassword(e.target.value)}
                      className="w-full p-2.5 rounded-lg text-sm transition-all outline-none"
                      style={inputStyle}
                    />
                  </div>

                  <div className="flex justify-end gap-3 pt-2">
                    <button
                      type="button"
                      onClick={() => !userSubmitting && setUserModalOpen(false)}
                      className="px-4 py-2 text-xs font-medium rounded-lg transition-colors"
                      style={{ color: 'var(--muted)', background: 'var(--surface-2)' }}
                    >
                      Cancelar
                    </button>
                    <button
                      type="submit"
                      disabled={userSubmitting || !uEmail.trim()}
                      className="px-4 py-2 text-xs font-semibold text-white rounded-lg flex items-center gap-1 disabled:opacity-50"
                      style={{ background: 'var(--accent)' }}
                    >
                      {userSubmitting ? (
                        <>
                          <Loader2 size={12} className="animate-spin" />
                          <span>Creando...</span>
                        </>
                      ) : (
                        <span>Crear usuario</span>
                      )}
                    </button>
                  </div>
                </form>
              </>
            )}
          </div>
        </div>
      )}

      {/* ── Crear workspace MODAL ── */}
      {wsModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: 'rgba(0,0,0,0.4)' }}
          onClick={() => !wsSubmitting && setWsModalOpen(false)}
        >
          <div
            className="w-full max-w-md rounded-xl p-6 shadow-float relative"
            style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => !wsSubmitting && setWsModalOpen(false)}
              className="absolute top-4 right-4 transition-colors"
              style={{ color: 'var(--muted)' }}
            >
              <X size={20} />
            </button>

            <h3 className="font-bold text-lg mb-1" style={{ color: 'var(--ink)' }}>
              Crear workspace
            </h3>
            <p className="text-xs text-[var(--muted)] mb-4">{client.name}</p>

            {wsFormError && (
              <div className="mb-4 p-3 rounded-lg text-xs bg-red-950/20 border border-red-500/20 text-red-400">
                {wsFormError}
              </div>
            )}

            <form onSubmit={handleCreateWorkspace} className="space-y-4">
              <div>
                <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--muted)' }}>
                  Nombre
                </label>
                <input
                  type="text"
                  required
                  placeholder="Ej. Transformación 2026"
                  value={wsName}
                  onChange={(e) => setWsName(e.target.value)}
                  className="w-full p-2.5 rounded-lg text-sm transition-all outline-none"
                  style={inputStyle}
                />
              </div>

              <div>
                <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--muted)' }}>
                  Descripción
                </label>
                <textarea
                  rows={3}
                  placeholder="Opcional"
                  value={wsDescription}
                  onChange={(e) => setWsDescription(e.target.value)}
                  className="w-full p-2.5 rounded-lg text-sm transition-all outline-none resize-none"
                  style={inputStyle}
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => !wsSubmitting && setWsModalOpen(false)}
                  className="px-4 py-2 text-xs font-medium rounded-lg transition-colors"
                  style={{ color: 'var(--muted)', background: 'var(--surface-2)' }}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={wsSubmitting || !wsName.trim()}
                  className="px-4 py-2 text-xs font-semibold text-white rounded-lg flex items-center gap-1 disabled:opacity-50"
                  style={{ background: 'var(--accent)' }}
                >
                  {wsSubmitting ? (
                    <>
                      <Loader2 size={12} className="animate-spin" />
                      <span>Creando...</span>
                    </>
                  ) : (
                    <span>Crear workspace</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminClientDetailView;
