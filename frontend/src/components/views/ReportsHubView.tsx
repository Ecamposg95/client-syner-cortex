import React, { useEffect, useState } from 'react';
import {
  FileText, Loader2, Plus, X, CheckCircle2, Share2, Download, Sparkles,
} from 'lucide-react';
import apiClient from '../../api/client';
import { Card } from '../ui/Card';
import { useAuthStore } from '../../store/authStore';

// ── API shapes ──────────────────────────────────────────────────────────
interface Report {
  id: number;
  organization_id: number;
  workspace_id: number | null;
  created_by: number | null;
  title: string;
  report_type: string | null;
  status: string;
  visibility: string;
  content: Record<string, any> | null;
  approved_by: number | null;
  shared_at: string | null;
  created_at: string;
  updated_at: string;
}

interface ToolRunOption {
  id: number;
  tool_name: string;
  status: string;
}

const inputStyle: React.CSSProperties = {
  background: 'var(--surface-2)',
  border: '1px solid var(--border)',
  color: 'var(--ink)',
};

// Status → badge class (reuses the global status-badge palette).
const STATUS_BADGE: Record<string, string> = {
  DRAFT_INTERNAL: 'status-badge--pending',
  CONSULTANT_REVIEW: 'status-badge--pending',
  APPROVED: 'status-badge--active',
  CLIENT_SHARED: 'status-badge--completed',
  ARCHIVED: 'status-badge--muted',
};

const STATUS_LABEL: Record<string, string> = {
  DRAFT_INTERNAL: 'Borrador interno',
  CONSULTANT_REVIEW: 'En revisión',
  APPROVED: 'Aprobado',
  CLIENT_SHARED: 'Compartido con cliente',
  ARCHIVED: 'Archivado',
};

export const ReportsHubView: React.FC = () => {
  const user = useAuthStore((s) => s.user);
  const isCrew = user?.user_type === 'SYNER_CREW';

  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  // Create modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [reportType, setReportType] = useState('');
  const [toolRuns, setToolRuns] = useState<ToolRunOption[]>([]);
  const [selectedRunIds, setSelectedRunIds] = useState<number[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const loadReports = () =>
    apiClient.get<Report[]>('/reports').then((res) => setReports(res.data));

  useEffect(() => {
    loadReports()
      .catch((e) => setError(e?.response?.data?.detail || 'No se pudieron cargar los reportes'))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const openModal = async () => {
    setTitle('');
    setReportType('');
    setSelectedRunIds([]);
    setFormError(null);
    setModalOpen(true);
    // Best-effort: load shareable tool runs to optionally compose from. The
    // endpoint may not list runs for every deployment, so failures are silent.
    try {
      const res = await apiClient.get<ToolRunOption[]>('/tool-runs');
      setToolRuns(Array.isArray(res.data) ? res.data : []);
    } catch {
      setToolRuns([]);
    }
  };

  const toggleRun = (id: number) =>
    setSelectedRunIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );

  const handleCreate = async () => {
    if (!title.trim()) {
      setFormError('El título es obligatorio');
      return;
    }
    setSubmitting(true);
    setFormError(null);
    try {
      await apiClient.post('/reports', {
        title: title.trim(),
        report_type: reportType.trim() || null,
        tool_run_ids: selectedRunIds.length ? selectedRunIds : null,
      });
      setModalOpen(false);
      await loadReports();
    } catch (e: any) {
      setFormError(e?.response?.data?.detail || 'No se pudo crear el reporte');
    } finally {
      setSubmitting(false);
    }
  };

  const patchStatus = async (id: number, status: string) => {
    setBusyId(id);
    setError(null);
    try {
      await apiClient.patch(`/reports/${id}`, { status });
      await loadReports();
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'No se pudo actualizar el reporte');
    } finally {
      setBusyId(null);
    }
  };

  const exportMarkdown = async (report: Report) => {
    setBusyId(report.id);
    setError(null);
    try {
      const res = await apiClient.post(`/reports/${report.id}/export-markdown`);
      const blob = new Blob([res.data.markdown], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${report.title.replace(/\s+/g, '_')}.md`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'No se pudo exportar el reporte');
    } finally {
      setBusyId(null);
    }
  };

  if (loading)
    return (
      <div className="p-8 flex justify-center">
        <Loader2 className="animate-spin text-[var(--accent)]" />
      </div>
    );

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="font-bold text-2xl flex items-center gap-2">
            <FileText className="text-[var(--accent)]" /> Reportes
          </h2>
          <p className="text-sm text-[var(--muted)]">
            {isCrew
              ? 'Reportes de consultoría con ciclo borrador → aprobado → compartido'
              : 'Reportes compartidos contigo por el equipo de consultoría'}
          </p>
        </div>
        {isCrew && (
          <button
            type="button"
            onClick={openModal}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md text-sm font-semibold text-white transition-colors"
            style={{ background: 'var(--accent)' }}
          >
            <Plus size={16} /> Nuevo reporte
          </button>
        )}
      </div>

      {error && (
        <div
          className="px-4 py-3 rounded-lg text-sm"
          style={{ background: 'var(--neg-tint, rgba(239,68,68,0.1))', color: 'var(--neg, #ef4444)' }}
        >
          {error}
        </div>
      )}

      {/* List */}
      {reports.length === 0 ? (
        <Card className="p-8 text-center">
          <FileText className="mx-auto mb-3 text-[var(--muted-2)]" size={28} />
          <p className="text-sm text-[var(--muted)]">
            No hay reportes todavía.
            {isCrew ? ' Usa "Nuevo reporte" para crear uno.' : ''}
          </p>
        </Card>
      ) : (
        <div className="space-y-4">
          {reports.map((r) => (
            <Card key={r.id} className="p-5">
              <div className="flex items-start justify-between gap-4 mb-3">
                <div className="flex items-start gap-3">
                  <FileText size={20} className="mt-0.5 flex-shrink-0 text-[var(--accent)]" />
                  <div>
                    <h4 className="font-bold text-[var(--ink)]">{r.title}</h4>
                    {r.report_type && (
                      <p className="text-xs text-[var(--muted-2)] mt-0.5">{r.report_type}</p>
                    )}
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <span className={`status-badge ${STATUS_BADGE[r.status] || 'status-badge--pending'}`}>
                    {STATUS_LABEL[r.status] || r.status}
                  </span>
                  <span className="text-[10px] uppercase tracking-wide text-[var(--muted-2)]">
                    {r.visibility}
                  </span>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                {isCrew && r.status !== 'APPROVED' && r.status !== 'CLIENT_SHARED' && (
                  <button
                    type="button"
                    disabled={busyId === r.id}
                    onClick={() => patchStatus(r.id, 'APPROVED')}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium border border-[var(--border)] text-[var(--ink-2)] hover:bg-[var(--surface-2)] transition-colors disabled:opacity-50"
                  >
                    {busyId === r.id ? <Loader2 size={12} className="animate-spin" /> : <CheckCircle2 size={12} />}
                    Aprobar
                  </button>
                )}
                {isCrew && r.status !== 'CLIENT_SHARED' && (
                  <button
                    type="button"
                    disabled={busyId === r.id}
                    onClick={() => patchStatus(r.id, 'CLIENT_SHARED')}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium border border-[var(--border)] text-[var(--ink-2)] hover:bg-[var(--surface-2)] transition-colors disabled:opacity-50"
                  >
                    {busyId === r.id ? <Loader2 size={12} className="animate-spin" /> : <Share2 size={12} />}
                    Compartir con cliente
                  </button>
                )}
                {isCrew && (
                  <button
                    type="button"
                    disabled={busyId === r.id}
                    onClick={() => exportMarkdown(r)}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium border border-[var(--border)] text-[var(--ink-2)] hover:bg-[var(--surface-2)] transition-colors disabled:opacity-50"
                  >
                    {busyId === r.id ? <Loader2 size={12} className="animate-spin" /> : <Download size={12} />}
                    Exportar Markdown
                  </button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create modal */}
      {modalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: 'rgba(0,0,0,0.5)' }}
          onClick={() => setModalOpen(false)}
        >
          <Card
            className="w-full max-w-lg p-6"
            onClick={(e: React.MouseEvent) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-lg flex items-center gap-2">
                <Sparkles size={18} className="text-[var(--accent)]" /> Nuevo reporte
              </h3>
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="p-1 rounded-md hover:bg-[var(--surface-2)] text-[var(--muted)]"
              >
                <X size={18} />
              </button>
            </div>

            {formError && (
              <div
                className="px-3 py-2 rounded-md text-sm mb-3"
                style={{ background: 'var(--neg-tint, rgba(239,68,68,0.1))', color: 'var(--neg, #ef4444)' }}
              >
                {formError}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[var(--muted)] mb-1">Título</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-md text-sm"
                  style={inputStyle}
                  placeholder="Reporte de diagnóstico ejecutivo"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[var(--muted)] mb-1">Tipo (opcional)</label>
                <input
                  type="text"
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value)}
                  className="w-full px-3 py-2 rounded-md text-sm"
                  style={inputStyle}
                  placeholder="DIAGNÓSTICO, ROADMAP, ..."
                />
              </div>

              {toolRuns.length > 0 && (
                <div>
                  <label className="block text-xs font-semibold text-[var(--muted)] mb-1">
                    Componer desde tool runs (opcional)
                  </label>
                  <div className="space-y-1.5 max-h-40 overflow-y-auto border border-[var(--border)] rounded-md p-2">
                    {toolRuns.map((run) => (
                      <label key={run.id} className="flex items-center gap-2 text-sm text-[var(--ink-2)] cursor-pointer">
                        <input
                          type="checkbox"
                          checked={selectedRunIds.includes(run.id)}
                          onChange={() => toggleRun(run.id)}
                        />
                        <span className="truncate">
                          #{run.id} · {run.tool_name}
                          <span className="text-[var(--muted-2)] text-xs"> ({run.status})</span>
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              )}
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
                disabled={submitting}
                onClick={handleCreate}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-md text-sm font-semibold text-white transition-colors disabled:opacity-50"
                style={{ background: 'var(--accent)' }}
              >
                {submitting && <Loader2 size={14} className="animate-spin" />}
                Crear reporte
              </button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default ReportsHubView;
