import React, { useEffect, useState } from 'react';
import { Card } from '../ui/Card';
import {
  Lightbulb, Loader2, Plus, Share2, Pencil, GitBranch,
  Eye, EyeOff, Lock, ListTree, X,
} from 'lucide-react';
import apiClient from '../../api/client';
import { useAuthStore } from '../../store/authStore';
import { useWorkspaceStore } from '../../store/workspaceStore';

type Visibility = 'INTERNAL' | 'SHARED' | 'EXECUTIVE_ONLY' | 'TASK_VISIBLE';

interface Recommendation {
  id: number;
  workspace_id: number;
  organization_id: number;
  dimension: string | null;
  text: string;
  visibility: Visibility;
  impact: string | null;
  effort: string | null;
  linked_roadmap_item_id: number | null;
  created_at: string;
  updated_at: string;
}

const VISIBILITY_META: Record<Visibility, { label: string; icon: any; color: string }> = {
  INTERNAL:       { label: 'Interno',     icon: EyeOff, color: 'var(--muted)' },
  SHARED:         { label: 'Compartido',  icon: Eye,    color: 'var(--pos, #22c55e)' },
  EXECUTIVE_ONLY: { label: 'Ejecutivo',   icon: Lock,   color: 'var(--accent)' },
  TASK_VISIBLE:   { label: 'En tarea',    icon: ListTree, color: 'var(--warn, #eab308)' },
};

const LEVEL_COLOR: Record<string, string> = {
  HIGH:   'text-red-500 bg-red-500/10',
  MEDIUM: 'text-yellow-500 bg-yellow-500/10',
  LOW:    'text-blue-500 bg-blue-500/10',
};

const LEVELS = ['LOW', 'MEDIUM', 'HIGH'];

interface FormState {
  text: string;
  dimension: string;
  impact: string;
  effort: string;
}

const EMPTY_FORM: FormState = { text: '', dimension: '', impact: 'MEDIUM', effort: 'MEDIUM' };

export const RecommendationsView: React.FC = () => {
  const user = useAuthStore((s) => s.user);
  const isCrew = user?.user_type === 'SYNER_CREW';
  const activeWorkspace = useWorkspaceStore((s) => s.activeWorkspace);

  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [dimensionFilter, setDimensionFilter] = useState<string>('');

  // Modal state: when editingId is null we are creating, otherwise editing.
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  const fetchRecs = async () => {
    const params = dimensionFilter ? { dimension: dimensionFilter } : undefined;
    const res = await apiClient.get('/recommendations', { params });
    setRecs(res.data);
  };

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        await fetchRecs();
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dimensionFilter]);

  const openCreate = () => {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setError(null);
    setModalOpen(true);
  };

  const openEdit = (r: Recommendation) => {
    setEditingId(r.id);
    setForm({
      text: r.text,
      dimension: r.dimension || '',
      impact: r.impact || 'MEDIUM',
      effort: r.effort || 'MEDIUM',
    });
    setError(null);
    setModalOpen(true);
  };

  const handleSave = async () => {
    if (!form.text.trim()) {
      setError('El texto de la recomendación es obligatorio');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      if (editingId === null) {
        if (!activeWorkspace) {
          setError('Selecciona un workspace antes de crear una recomendación');
          setSaving(false);
          return;
        }
        await apiClient.post('/recommendations', {
          workspace_id: activeWorkspace.id,
          organization_id: activeWorkspace.organization_id,
          text: form.text,
          dimension: form.dimension || null,
          impact: form.impact,
          effort: form.effort,
          visibility: 'INTERNAL',
        });
      } else {
        await apiClient.patch(`/recommendations/${editingId}`, {
          text: form.text,
          dimension: form.dimension || null,
          impact: form.impact,
          effort: form.effort,
        });
      }
      setModalOpen(false);
      await fetchRecs();
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'No se pudo guardar la recomendación');
    } finally {
      setSaving(false);
    }
  };

  const handleShare = async (id: number) => {
    setBusyId(id);
    try {
      await apiClient.patch(`/recommendations/${id}`, { visibility: 'SHARED' });
      await fetchRecs();
    } catch (e) {
      console.error(e);
    } finally {
      setBusyId(null);
    }
  };

  const handleConvert = async (id: number) => {
    setBusyId(id);
    setError(null);
    try {
      await apiClient.post(`/recommendations/${id}/convert-to-roadmap`);
      await fetchRecs();
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'No se pudo convertir a roadmap');
    } finally {
      setBusyId(null);
    }
  };

  if (loading) {
    return (
      <div className="p-8 flex justify-center">
        <Loader2 className="animate-spin text-[var(--accent)]" />
      </div>
    );
  }

  const dimensions = Array.from(
    new Set(recs.map((r) => r.dimension).filter((d): d is string => !!d)),
  );

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="font-bold text-2xl flex items-center gap-2">
            <Lightbulb className="text-[var(--accent)]" /> Recomendaciones
          </h2>
          <p className="text-sm text-[var(--muted)]">
            Recomendaciones priorizadas que el crew comparte y vincula al roadmap
          </p>
        </div>
        {isCrew && (
          <button
            type="button"
            onClick={openCreate}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md text-sm font-semibold text-white transition-colors"
            style={{ background: 'var(--accent)' }}
          >
            <Plus size={16} /> Nueva
          </button>
        )}
      </div>

      {error && !modalOpen && (
        <div
          className="px-4 py-3 rounded-lg text-sm"
          style={{ background: 'var(--neg-tint, rgba(239,68,68,0.1))', color: 'var(--neg, #ef4444)' }}
        >
          {error}
        </div>
      )}

      {/* Dimension filter */}
      {dimensions.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-[var(--muted-2)] uppercase tracking-wide">Dimensión</span>
          <button
            type="button"
            onClick={() => setDimensionFilter('')}
            className={`px-3 py-1 rounded-md text-xs font-medium border transition-colors ${
              dimensionFilter === ''
                ? 'border-[var(--accent)] text-[var(--accent)]'
                : 'border-[var(--border)] text-[var(--muted)] hover:bg-[var(--surface-2)]'
            }`}
          >
            Todas
          </button>
          {dimensions.map((d) => (
            <button
              key={d}
              type="button"
              onClick={() => setDimensionFilter(d)}
              className={`px-3 py-1 rounded-md text-xs font-medium border transition-colors ${
                dimensionFilter === d
                  ? 'border-[var(--accent)] text-[var(--accent)]'
                  : 'border-[var(--border)] text-[var(--muted)] hover:bg-[var(--surface-2)]'
              }`}
            >
              {d}
            </button>
          ))}
        </div>
      )}

      {/* List */}
      <div className="space-y-4">
        {recs.length === 0 && (
          <Card className="p-8 text-center">
            <Lightbulb className="mx-auto mb-3 text-[var(--muted-2)]" size={28} />
            <p className="text-sm text-[var(--muted)]">
              No hay recomendaciones todavía.
              {isCrew ? ' Usa "Nueva" para crear la primera.' : ''}
            </p>
          </Card>
        )}

        {recs.map((r) => {
          const vis = VISIBILITY_META[r.visibility];
          const VisIcon = vis.icon;
          const busy = busyId === r.id;
          return (
            <Card key={r.id} className="p-5">
              <div className="flex items-start justify-between gap-4 mb-3">
                <div className="flex items-start gap-3">
                  <Lightbulb size={20} className="mt-0.5 flex-shrink-0 text-[var(--accent)]" />
                  <div>
                    <p className="font-medium text-[var(--ink)]">{r.text}</p>
                    {r.dimension && (
                      <p className="text-xs text-[var(--muted-2)] mt-0.5">{r.dimension}</p>
                    )}
                  </div>
                </div>
                <span
                  className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-bold uppercase whitespace-nowrap"
                  style={{ background: 'var(--surface-2)', color: vis.color }}
                >
                  <VisIcon size={11} /> {vis.label}
                </span>
              </div>

              <div className="flex flex-wrap items-center gap-2 mb-3">
                {r.impact && (
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${LEVEL_COLOR[r.impact] || 'bg-[var(--surface-2)] text-[var(--muted)]'}`}>
                    Impacto: {r.impact}
                  </span>
                )}
                {r.effort && (
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${LEVEL_COLOR[r.effort] || 'bg-[var(--surface-2)] text-[var(--muted)]'}`}>
                    Esfuerzo: {r.effort}
                  </span>
                )}
                {r.linked_roadmap_item_id != null && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-[var(--surface-2)] text-[var(--accent-strong, var(--accent))]">
                    <GitBranch size={10} /> En roadmap
                  </span>
                )}
              </div>

              {isCrew && (
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => openEdit(r)}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium border border-[var(--border)] text-[var(--ink-2)] hover:bg-[var(--surface-2)] transition-colors disabled:opacity-50"
                  >
                    <Pencil size={12} /> Editar
                  </button>
                  {r.visibility !== 'SHARED' && (
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => handleShare(r.id)}
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium border border-[var(--border)] text-[var(--ink-2)] hover:bg-[var(--surface-2)] transition-colors disabled:opacity-50"
                    >
                      {busy ? <Loader2 size={12} className="animate-spin" /> : <Share2 size={12} />}
                      Compartir
                    </button>
                  )}
                  {r.linked_roadmap_item_id == null && (
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => handleConvert(r.id)}
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium border border-[var(--border)] text-[var(--ink-2)] hover:bg-[var(--surface-2)] transition-colors disabled:opacity-50"
                    >
                      {busy ? <Loader2 size={12} className="animate-spin" /> : <GitBranch size={12} />}
                      Convertir a roadmap
                    </button>
                  )}
                </div>
              )}
            </Card>
          );
        })}
      </div>

      {/* Create / Edit modal (crew only) */}
      {isCrew && modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: 'rgba(0,0,0,0.5)' }}>
          <Card className="w-full max-w-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-lg flex items-center gap-2">
                <Lightbulb size={18} className="text-[var(--accent)]" />
                {editingId === null ? 'Nueva recomendación' : 'Editar recomendación'}
              </h3>
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="p-1 rounded-md text-[var(--muted)] hover:bg-[var(--surface-2)]"
              >
                <X size={18} />
              </button>
            </div>

            {error && (
              <div
                className="px-3 py-2 rounded-lg text-sm mb-3"
                style={{ background: 'var(--neg-tint, rgba(239,68,68,0.1))', color: 'var(--neg, #ef4444)' }}
              >
                {error}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[var(--muted)] uppercase tracking-wide mb-1">
                  Recomendación
                </label>
                <textarea
                  value={form.text}
                  onChange={(e) => setForm({ ...form, text: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 rounded-md bg-[var(--surface-2)] border border-[var(--border)] text-sm text-[var(--ink)] focus:outline-none focus:border-[var(--accent)]"
                  placeholder="Describe la recomendación accionable..."
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[var(--muted)] uppercase tracking-wide mb-1">
                  Dimensión
                </label>
                <input
                  type="text"
                  value={form.dimension}
                  onChange={(e) => setForm({ ...form, dimension: e.target.value })}
                  className="w-full px-3 py-2 rounded-md bg-[var(--surface-2)] border border-[var(--border)] text-sm text-[var(--ink)] focus:outline-none focus:border-[var(--accent)]"
                  placeholder="Ventas, Operaciones, RH..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-[var(--muted)] uppercase tracking-wide mb-1">
                    Impacto
                  </label>
                  <select
                    value={form.impact}
                    onChange={(e) => setForm({ ...form, impact: e.target.value })}
                    className="w-full px-3 py-2 rounded-md bg-[var(--surface-2)] border border-[var(--border)] text-sm text-[var(--ink)] focus:outline-none focus:border-[var(--accent)]"
                  >
                    {LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[var(--muted)] uppercase tracking-wide mb-1">
                    Esfuerzo
                  </label>
                  <select
                    value={form.effort}
                    onChange={(e) => setForm({ ...form, effort: e.target.value })}
                    className="w-full px-3 py-2 rounded-md bg-[var(--surface-2)] border border-[var(--border)] text-sm text-[var(--ink)] focus:outline-none focus:border-[var(--accent)]"
                  >
                    {LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
                  </select>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button
                type="button"
                onClick={() => setModalOpen(false)}
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
                {editingId === null ? 'Crear' : 'Guardar'}
              </button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
