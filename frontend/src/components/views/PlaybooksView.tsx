import React, { useEffect, useState } from 'react';
import { Card } from '../ui/Card';
import {
  BookOpen, Loader2, Plus, Pencil, Trash2, X, Tag,
} from 'lucide-react';
import apiClient from '../../api/client';

interface Playbook {
  id: number;
  organization_id: number | null;
  created_by: number | null;
  title: string;
  category: string | null;
  content: string;
  tags: string[] | null;
  visibility: string;
  created_at: string;
  updated_at: string;
}

interface FormState {
  title: string;
  category: string;
  content: string;
}

const EMPTY_FORM: FormState = { title: '', category: '', content: '' };

export const PlaybooksView: React.FC = () => {
  const [playbooks, setPlaybooks] = useState<Playbook[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const fetchPlaybooks = async () => {
    const res = await apiClient.get('/playbooks');
    setPlaybooks(res.data);
  };

  useEffect(() => {
    (async () => {
      try {
        await fetchPlaybooks();
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const openCreate = () => {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setError(null);
    setModalOpen(true);
  };

  const openEdit = (p: Playbook) => {
    setEditingId(p.id);
    setForm({ title: p.title, category: p.category || '', content: p.content || '' });
    setError(null);
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setEditingId(null);
    setForm(EMPTY_FORM);
  };

  const handleSave = async () => {
    if (!form.title.trim()) {
      setError('El título es obligatorio');
      return;
    }
    setSaving(true);
    setError(null);
    const body = {
      title: form.title.trim(),
      category: form.category.trim() || null,
      content: form.content,
    };
    try {
      if (editingId == null) {
        await apiClient.post('/playbooks', body);
      } else {
        await apiClient.put(`/playbooks/${editingId}`, body);
      }
      await fetchPlaybooks();
      closeModal();
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'No se pudo guardar el playbook');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('¿Eliminar este playbook? Esta acción no se puede deshacer.')) return;
    setDeletingId(id);
    try {
      await apiClient.delete(`/playbooks/${id}`);
      await fetchPlaybooks();
    } catch (e) {
      console.error(e);
    } finally {
      setDeletingId(null);
    }
  };

  if (loading) {
    return (
      <div className="p-8 flex justify-center">
        <Loader2 className="animate-spin text-[var(--accent)]" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="font-bold text-2xl flex items-center gap-2">
            <BookOpen className="text-[var(--accent)]" /> Playbooks internos
          </h2>
          <p className="text-sm text-[var(--muted)]">
            Biblioteca de metodologías de Syner · uso interno (crew), nunca visible para clientes
          </p>
        </div>
        <button
          type="button"
          onClick={openCreate}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-md text-sm font-semibold text-white transition-colors disabled:opacity-50"
          style={{ background: 'var(--accent)' }}
        >
          <Plus size={16} /> Nuevo playbook
        </button>
      </div>

      {/* List */}
      <div className="space-y-4">
        {playbooks.length === 0 && (
          <Card className="p-8 text-center">
            <BookOpen className="mx-auto mb-3 text-[var(--muted-2)]" size={28} />
            <p className="text-sm text-[var(--muted)]">
              No hay playbooks todavía. Usa "Nuevo playbook" para documentar una metodología.
            </p>
          </Card>
        )}

        {playbooks.map((p) => (
          <Card key={p.id} className="p-5">
            <div className="flex items-start justify-between gap-4 mb-3">
              <div className="flex items-start gap-3">
                <BookOpen size={20} className="mt-0.5 flex-shrink-0 text-[var(--accent)]" />
                <div>
                  <h4 className="font-bold text-[var(--ink)]">{p.title}</h4>
                  {p.category && (
                    <p className="text-xs text-[var(--muted-2)] mt-0.5">{p.category}</p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => openEdit(p)}
                  className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-medium border border-[var(--border)] text-[var(--ink-2)] hover:bg-[var(--surface-2)] transition-colors"
                >
                  <Pencil size={12} /> Editar
                </button>
                <button
                  type="button"
                  disabled={deletingId === p.id}
                  onClick={() => handleDelete(p.id)}
                  className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-medium border border-[var(--border)] text-red-500 hover:bg-red-500/10 transition-colors disabled:opacity-50"
                >
                  {deletingId === p.id ? <Loader2 size={12} className="animate-spin" /> : <Trash2 size={12} />}
                  Eliminar
                </button>
              </div>
            </div>

            {p.content && (
              <p className="text-sm text-[var(--muted)] whitespace-pre-wrap mb-3">{p.content}</p>
            )}

            {p.tags && p.tags.length > 0 && (
              <div className="flex flex-wrap items-center gap-1.5">
                {p.tags.map((t) => (
                  <span
                    key={t}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium bg-[var(--surface-2)] text-[var(--muted)]"
                  >
                    <Tag size={10} /> {t}
                  </span>
                ))}
              </div>
            )}
          </Card>
        ))}
      </div>

      {/* Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <Card className="w-full max-w-lg p-6 relative">
            <button
              type="button"
              onClick={closeModal}
              className="absolute top-4 right-4 text-[var(--muted)] hover:text-[var(--ink)]"
            >
              <X size={18} />
            </button>
            <h3 className="font-bold text-lg mb-4">
              {editingId == null ? 'Nuevo playbook' : 'Editar playbook'}
            </h3>

            {error && (
              <div
                className="px-3 py-2 rounded-md text-sm mb-4"
                style={{ background: 'var(--neg-tint, rgba(239,68,68,0.1))', color: 'var(--neg, #ef4444)' }}
              >
                {error}
              </div>
            )}

            <div className="space-y-4">
              <div className="flex flex-col gap-1">
                <label className="text-xs font-medium text-[var(--muted)]">Título</label>
                <input
                  type="text"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  className="px-3 py-2 rounded-md text-sm bg-[var(--surface-2)] border border-[var(--border)] text-[var(--ink)] focus:outline-none focus:border-[var(--accent)]"
                  placeholder="Ej. Metodología de diagnóstico 360"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs font-medium text-[var(--muted)]">Categoría</label>
                <input
                  type="text"
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                  className="px-3 py-2 rounded-md text-sm bg-[var(--surface-2)] border border-[var(--border)] text-[var(--ink)] focus:outline-none focus:border-[var(--accent)]"
                  placeholder="Ej. Diagnóstico, Ventas, Operaciones"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs font-medium text-[var(--muted)]">Contenido</label>
                <textarea
                  value={form.content}
                  onChange={(e) => setForm({ ...form, content: e.target.value })}
                  rows={8}
                  className="px-3 py-2 rounded-md text-sm bg-[var(--surface-2)] border border-[var(--border)] text-[var(--ink)] focus:outline-none focus:border-[var(--accent)] resize-y"
                  placeholder="Describe los pasos, frameworks y mejores prácticas de esta metodología..."
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 mt-6">
              <button
                type="button"
                onClick={closeModal}
                className="px-4 py-2 rounded-md text-sm font-medium border border-[var(--border)] text-[var(--ink-2)] hover:bg-[var(--surface-2)] transition-colors"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={handleSave}
                disabled={saving}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-md text-sm font-semibold text-white transition-colors disabled:opacity-50"
                style={{ background: 'var(--accent)' }}
              >
                {saving && <Loader2 size={14} className="animate-spin" />}
                {editingId == null ? 'Crear' : 'Guardar'}
              </button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
