import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../../ui/Card';
import {
  History, Loader2, PenTool, Clock, ChevronRight, Filter,
} from 'lucide-react';
import apiClient from '../../../api/client';
import { useAuthStore } from '../../../store/authStore';

interface ToolRunSummary {
  id: number;
  tool_id: number;
  tool_name: string;
  status: string;
  visibility: string;
  workspace_id: number | null;
  created_at: string;
}

const STATUS_BADGE: Record<string, string> = {
  DRAFT: 'bg-[var(--surface-2)] text-[var(--muted)]',
  AI_GENERATED: 'bg-yellow-500/10 text-yellow-500',
  APPROVED: 'bg-green-500/10 text-green-500',
  CLIENT_SHARED: 'bg-blue-500/10 text-blue-500',
};

const VISIBILITY_BADGE: Record<string, string> = {
  INTERNAL: 'bg-[var(--surface-2)] text-[var(--muted-2)]',
  CLIENT_SHARED: 'bg-blue-500/10 text-blue-500',
};

// Status chips offered as filters (value sent to the backend via ?status=).
const STATUS_FILTERS: { value: string; label: string }[] = [
  { value: '', label: 'Todos' },
  { value: 'DRAFT', label: 'Borrador' },
  { value: 'AI_GENERATED', label: 'Generado' },
  { value: 'APPROVED', label: 'Aprobado' },
  { value: 'CLIENT_SHARED', label: 'Compartido' },
];

const formatDate = (iso: string): string => {
  if (!iso) return '';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleString();
};

export const ToolRunHistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const isCrew = user?.user_type === 'SYNER_CREW';

  const [runs, setRuns] = useState<ToolRunSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const fetchRuns = async (status: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get('/tool-runs', {
        params: status ? { status } : undefined,
      });
      setRuns(Array.isArray(res.data) ? res.data : []);
    } catch (e: any) {
      console.error(e);
      setError(e?.response?.data?.detail || 'No se pudo cargar el historial de ejecuciones.');
      setRuns([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns(statusFilter);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-[var(--border)] pb-4">
        <div className="flex flex-col gap-1">
          <h2 className="font-extrabold text-2xl flex items-center gap-2">
            <History className="text-[var(--accent)]" /> Historial de Ejecuciones
          </h2>
          <p className="text-sm text-[var(--muted)]">
            {isCrew
              ? 'Todas las ejecuciones del Consulting Toolkit'
              : 'Entregables compartidos contigo'}
          </p>
        </div>
      </div>

      {/* Status filter chips */}
      <div className="flex flex-wrap items-center gap-2">
        <Filter size={14} className="text-[var(--muted-2)]" />
        {STATUS_FILTERS.map((f) => (
          <button
            key={f.value || 'all'}
            type="button"
            onClick={() => setStatusFilter(f.value)}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold border transition-colors ${
              statusFilter === f.value
                ? 'bg-[var(--accent)] text-white border-[var(--accent)]'
                : 'border-[var(--border)] text-[var(--ink-2)] hover:bg-[var(--surface-2)]'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 text-red-500 border border-red-500/20 rounded-lg text-sm font-semibold">
          {error}
        </div>
      )}

      {/* Content */}
      {loading ? (
        <div className="p-12 flex justify-center">
          <Loader2 size={36} className="animate-spin text-[var(--accent)]" />
        </div>
      ) : runs.length === 0 ? (
        <Card className="p-10 text-center">
          <History className="mx-auto mb-3 text-[var(--muted-2)]" size={28} />
          <p className="text-sm text-[var(--muted)]">
            No hay ejecuciones{statusFilter ? ' con este estado' : ''} todavía.
          </p>
        </Card>
      ) : (
        <div className="space-y-3">
          {runs.map((run) => (
            <Card
              key={run.id}
              className="p-4 cursor-pointer hover:border-[var(--accent)]"
            >
              <button
                type="button"
                onClick={() => navigate(`/runs/${run.id}/review`)}
                className="w-full flex items-center justify-between gap-4 text-left"
              >
                <div className="flex items-start gap-3 min-w-0">
                  <PenTool size={20} className="mt-0.5 flex-shrink-0 text-[var(--accent)]" />
                  <div className="min-w-0">
                    <h4 className="font-bold text-[var(--ink)] truncate">{run.tool_name}</h4>
                    <div className="flex items-center gap-2 mt-1 text-xs text-[var(--muted-2)]">
                      <Clock size={12} />
                      <span>{formatDate(run.created_at)}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      STATUS_BADGE[run.status] || 'bg-[var(--surface-2)] text-[var(--muted)]'
                    }`}
                  >
                    {run.status}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      VISIBILITY_BADGE[run.visibility] || 'bg-[var(--surface-2)] text-[var(--muted-2)]'
                    }`}
                  >
                    {run.visibility}
                  </span>
                  <ChevronRight size={16} className="text-[var(--muted-2)]" />
                </div>
              </button>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
