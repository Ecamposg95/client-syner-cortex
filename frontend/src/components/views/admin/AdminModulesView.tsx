import React, { useEffect, useState } from 'react';
import { Boxes, Loader2, Plus, X } from 'lucide-react';
import apiClient from '../../../api/client';
import { Card } from '../../ui/Card';

// ── API shapes ──────────────────────────────────────────────────────────
interface ModuleItem {
  id: number;
  code: string;
  name: string;
  description: string | null;
}

const inputStyle: React.CSSProperties = {
  background: 'var(--surface-2)',
  border: '1px solid var(--border)',
  color: 'var(--ink)',
};

export const AdminModulesView: React.FC = () => {
  const [modules, setModules] = useState<ModuleItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const loadModules = () =>
    apiClient.get<ModuleItem[]>('/admin/modules').then((res) => setModules(res.data));

  useEffect(() => {
    loadModules()
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const openModal = () => {
    setCode('');
    setName('');
    setDescription('');
    setFormError(null);
    setModalOpen(true);
  };

  const closeModal = () => {
    if (submitting) return;
    setModalOpen(false);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim() || !name.trim()) return;
    setSubmitting(true);
    setFormError(null);
    try {
      await apiClient.post<ModuleItem>('/admin/modules', {
        code: code.trim(),
        name: name.trim(),
        description: description.trim() || null,
      });
      await loadModules();
      setModalOpen(false);
    } catch (err: any) {
      setFormError(err.response?.data?.detail?.toString() || 'No se pudo crear el módulo.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 flex flex-col items-center justify-center gap-4">
        <Loader2 size={36} className="animate-spin text-[var(--accent)]" />
        <p className="text-sm text-[var(--muted)]">Cargando módulos...</p>
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
            <Boxes size={24} />
          </div>
          <div>
            <h2 className="font-extrabold text-2xl">Catálogo de Módulos</h2>
            <p className="text-sm text-[var(--muted)]">
              {modules.length} {modules.length === 1 ? 'módulo' : 'módulos'} en el catálogo
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
          Nuevo módulo
        </button>
      </div>

      {/* Grid / empty */}
      {modules.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-[var(--muted)]">Aún no hay módulos en el catálogo. Crea el primero.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {modules.map((m) => (
            <Card key={m.id} className="p-5">
              <div className="flex items-start gap-3 mb-3">
                <div
                  className="p-2 rounded-lg text-white shrink-0"
                  style={{ background: 'linear-gradient(135deg, var(--accent-strong), var(--accent))' }}
                >
                  <Boxes size={18} />
                </div>
                <div className="min-w-0">
                  <h3 className="font-bold text-base text-[var(--ink)] leading-tight">
                    {m.name}
                  </h3>
                  <p className="text-xs text-[var(--muted-2)] font-mono break-all">{m.code}</p>
                </div>
              </div>
              {m.description && (
                <p className="text-sm text-[var(--muted)] leading-snug">{m.description}</p>
              )}
            </Card>
          ))}
        </div>
      )}

      {/* ── Nuevo módulo MODAL ── */}
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

            <h3 className="font-bold text-lg mb-1" style={{ color: 'var(--ink)' }}>
              Nuevo módulo
            </h3>
            <p className="text-xs text-[var(--muted)] mb-4">
              Registra un módulo en el catálogo global de la plataforma.
            </p>

            {formError && (
              <div className="mb-4 p-3 rounded-lg text-xs bg-red-950/20 border border-red-500/20 text-red-400">
                {formError}
              </div>
            )}

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--muted)' }}>
                  Código
                </label>
                <input
                  type="text"
                  required
                  placeholder="Ej. cortex_vault"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  className="w-full p-2.5 rounded-lg text-sm font-mono outline-none"
                  style={inputStyle}
                />
              </div>

              <div>
                <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--muted)' }}>
                  Nombre
                </label>
                <input
                  type="text"
                  required
                  placeholder="Ej. Cortex Vault"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full p-2.5 rounded-lg text-sm outline-none"
                  style={inputStyle}
                />
              </div>

              <div>
                <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--muted)' }}>
                  Descripción
                </label>
                <textarea
                  rows={3}
                  placeholder="Descripción del módulo (opcional)"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full p-2.5 rounded-lg text-sm outline-none resize-none"
                  style={inputStyle}
                />
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
                  disabled={submitting || !code.trim() || !name.trim()}
                  className="px-4 py-2 text-xs font-semibold text-white rounded-lg flex items-center gap-1 disabled:opacity-50"
                  style={{ background: 'var(--accent)' }}
                >
                  {submitting ? (
                    <>
                      <Loader2 size={12} className="animate-spin" />
                      <span>Creando...</span>
                    </>
                  ) : (
                    <span>Crear módulo</span>
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

export default AdminModulesView;
