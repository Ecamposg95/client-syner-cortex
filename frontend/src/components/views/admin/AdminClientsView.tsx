import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Building2, Loader2, Plus, X, Copy, Check, Users, Boxes, LayoutGrid, ChevronRight,
} from 'lucide-react';
import apiClient from '../../../api/client';
import { Card } from '../../ui/Card';

// ── API shapes ──────────────────────────────────────────────────────────
interface ClientSummary {
  id: number;
  name: string;
  slug: string;
  organization_type: string;
  created_at: string;
  user_count: number;
  workspace_count: number;
  enabled_module_count: number;
}

interface CreatedOwner {
  user_id: number;
  email: string;
  role: string;
  temp_password: string;
}

interface CreateClientResponse {
  id: number;
  name: string;
  slug: string;
  organization_type: string;
  created_at: string;
  owner?: CreatedOwner | null;
}

const inputStyle: React.CSSProperties = {
  background: 'var(--surface-2)',
  border: '1px solid var(--border)',
  color: 'var(--ink)',
};

export const AdminClientsView: React.FC = () => {
  const navigate = useNavigate();

  const [clients, setClients] = useState<ClientSummary[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [name, setName] = useState('');
  const [ownerEmail, setOwnerEmail] = useState('');
  const [ownerFullName, setOwnerFullName] = useState('');
  const [ownerPassword, setOwnerPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Success / temp-password panel
  const [createdOwner, setCreatedOwner] = useState<CreatedOwner | null>(null);
  const [copied, setCopied] = useState(false);

  const loadClients = () =>
    apiClient.get<ClientSummary[]>('/admin/clients').then((res) => setClients(res.data));

  useEffect(() => {
    loadClients()
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const openModal = () => {
    setName('');
    setOwnerEmail('');
    setOwnerFullName('');
    setOwnerPassword('');
    setFormError(null);
    setCreatedOwner(null);
    setCopied(false);
    setModalOpen(true);
  };

  const closeModal = () => {
    if (submitting) return;
    setModalOpen(false);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setSubmitting(true);
    setFormError(null);
    try {
      const body: Record<string, unknown> = { name: name.trim() };
      if (ownerEmail.trim()) body.owner_email = ownerEmail.trim();
      if (ownerFullName.trim()) body.owner_full_name = ownerFullName.trim();
      if (ownerPassword.trim()) body.owner_password = ownerPassword.trim();

      const res = await apiClient.post<CreateClientResponse>('/admin/clients', body);
      await loadClients();

      if (res.data.owner?.temp_password) {
        setCreatedOwner(res.data.owner);
      } else {
        setModalOpen(false);
      }
    } catch (err: any) {
      setFormError(err.response?.data?.detail?.toString() || 'No se pudo crear el cliente.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCopyTemp = async () => {
    if (!createdOwner) return;
    try {
      await navigator.clipboard.writeText(createdOwner.temp_password);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) {
    return (
      <div className="p-12 flex flex-col items-center justify-center gap-4">
        <Loader2 size={36} className="animate-spin text-[var(--accent)]" />
        <p className="text-sm text-[var(--muted)]">Cargando clientes...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-3">
          <div
            className="p-2.5 rounded-xl text-white"
            style={{ background: 'linear-gradient(135deg, var(--accent-strong), var(--accent))' }}
          >
            <Building2 size={24} />
          </div>
          <div>
            <h2 className="font-extrabold text-2xl">Administración de Clientes</h2>
            <p className="text-sm text-[var(--muted)]">
              {clients.length} {clients.length === 1 ? 'organización cliente' : 'organizaciones cliente'}
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={openModal}
          className="inline-flex items-center gap-1.5 px-4 py-2.5 text-sm font-semibold text-white rounded-lg transition-colors"
          style={{ background: 'var(--accent)' }}
        >
          <Plus size={16} />
          Nuevo cliente
        </button>
      </div>

      {/* Grid / empty */}
      {clients.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-[var(--muted)]">Aún no hay clientes registrados. Crea el primero.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {clients.map((client) => (
            <Card
              key={client.id}
              className="p-0 overflow-hidden cursor-pointer group hover:shadow-lg transition-all duration-300 hover:-translate-y-0.5"
              onClick={() => navigate('/admin/clients/' + client.id)}
            >
              <div
                className="h-1.5 w-full"
                style={{ background: 'linear-gradient(135deg, var(--accent-strong), var(--accent))' }}
              />
              <div className="p-5">
                <div className="flex items-start justify-between mb-3">
                  <div
                    className="p-2.5 rounded-xl text-white"
                    style={{ background: 'linear-gradient(135deg, var(--accent-strong), var(--accent))' }}
                  >
                    <Building2 size={22} />
                  </div>
                  <ChevronRight
                    size={20}
                    className="text-[var(--muted-2)] group-hover:text-[var(--accent)] group-hover:translate-x-1 transition-all"
                  />
                </div>

                <h3 className="font-bold text-base text-[var(--ink)] leading-tight mb-0.5">
                  {client.name}
                </h3>
                <p className="text-xs text-[var(--muted-2)] font-mono mb-4">{client.slug}</p>

                <div className="flex flex-wrap gap-1.5">
                  <span className="status-badge status-badge--active">
                    <Users size={12} className="inline mr-1 -mt-px" />
                    {client.user_count} usuarios
                  </span>
                  <span className="status-badge status-badge--pending">
                    <LayoutGrid size={12} className="inline mr-1 -mt-px" />
                    {client.workspace_count} workspaces
                  </span>
                  <span className="status-badge status-badge--completed">
                    <Boxes size={12} className="inline mr-1 -mt-px" />
                    {client.enabled_module_count} módulos
                  </span>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* ── Nuevo cliente MODAL ── */}
      {modalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: 'rgba(0,0,0,0.4)' }}
          onClick={closeModal}
        >
          <div
            className="w-full max-w-md rounded-xl p-6 shadow-float relative"
            style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={closeModal}
              className="absolute top-4 right-4 transition-colors"
              style={{ color: 'var(--muted)' }}
            >
              <X size={20} />
            </button>

            {createdOwner ? (
              // ── Success / temp password panel ──
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Check size={20} className="text-[var(--accent)]" />
                  <h3 className="font-bold text-lg" style={{ color: 'var(--ink)' }}>
                    Cliente creado
                  </h3>
                </div>
                <p className="text-xs text-[var(--muted)] mb-4">
                  Comparte estas credenciales con el cliente. La contraseña temporal se muestra
                  una sola vez.
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
                      {createdOwner.email}
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
                        {createdOwner.temp_password}
                      </code>
                      <button
                        type="button"
                        onClick={handleCopyTemp}
                        className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-semibold rounded-lg transition-colors shrink-0 text-white"
                        style={{ background: 'var(--accent)' }}
                      >
                        {copied ? (
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
                    onClick={() => setModalOpen(false)}
                    className="px-4 py-2 text-xs font-semibold text-white rounded-lg"
                    style={{ background: 'var(--accent)' }}
                  >
                    Listo
                  </button>
                </div>
              </div>
            ) : (
              // ── Create form ──
              <>
                <h3 className="font-bold text-lg mb-1" style={{ color: 'var(--ink)' }}>
                  Nuevo cliente
                </h3>
                <p className="text-xs text-[var(--muted)] mb-4">
                  Crea una organización cliente y, opcionalmente, su usuario propietario.
                </p>

                {formError && (
                  <div className="mb-4 p-3 rounded-lg text-xs bg-red-950/20 border border-red-500/20 text-red-400">
                    {formError}
                  </div>
                )}

                <form onSubmit={handleCreate} className="space-y-4">
                  <div>
                    <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--muted)' }}>
                      Nombre del cliente
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="Ej. Acme Corp"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="w-full p-2.5 rounded-lg text-sm transition-all outline-none"
                      style={inputStyle}
                    />
                  </div>

                  <div className="pt-1 border-t border-[var(--border)]" />
                  <p className="text-[11px] text-[var(--muted-2)] -mt-1">
                    Usuario propietario (opcional)
                  </p>

                  <div>
                    <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--muted)' }}>
                      Email del propietario
                    </label>
                    <input
                      type="email"
                      placeholder="owner@cliente.com"
                      value={ownerEmail}
                      onChange={(e) => setOwnerEmail(e.target.value)}
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
                      placeholder="Nombre del propietario"
                      value={ownerFullName}
                      onChange={(e) => setOwnerFullName(e.target.value)}
                      className="w-full p-2.5 rounded-lg text-sm transition-all outline-none"
                      style={inputStyle}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--muted)' }}>
                      Contraseña
                    </label>
                    <input
                      type="text"
                      placeholder="Dejar en blanco para autogenerar"
                      value={ownerPassword}
                      onChange={(e) => setOwnerPassword(e.target.value)}
                      className="w-full p-2.5 rounded-lg text-sm transition-all outline-none"
                      style={inputStyle}
                    />
                    <p className="text-[11px] text-[var(--muted-2)] mt-1">
                      Si lo dejas vacío, se generará una contraseña temporal automáticamente.
                    </p>
                  </div>

                  <div className="flex justify-end gap-3 pt-2">
                    <button
                      type="button"
                      onClick={closeModal}
                      className="px-4 py-2 text-xs font-medium rounded-lg transition-colors"
                      style={{ color: 'var(--muted)', background: 'var(--surface-2)' }}
                    >
                      Cancelar
                    </button>
                    <button
                      type="submit"
                      disabled={submitting || !name.trim()}
                      className="px-4 py-2 text-xs font-semibold text-white rounded-lg flex items-center gap-1 disabled:opacity-50"
                      style={{ background: 'var(--accent)' }}
                    >
                      {submitting ? (
                        <>
                          <Loader2 size={12} className="animate-spin" />
                          <span>Creando...</span>
                        </>
                      ) : (
                        <span>Crear cliente</span>
                      )}
                    </button>
                  </div>
                </form>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminClientsView;
