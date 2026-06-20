import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../ui/Card';
import {
  LayoutDashboard, Loader2, Building2, Users, FolderKanban, Boxes,
  Briefcase, Lightbulb, AlertTriangle, GitPullRequestArrow, ChevronRight,
} from 'lucide-react';
import apiClient from '../../api/client';

interface ClientCard {
  id: number;
  name: string;
  slug: string;
  created_at: string | null;
  user_count: number;
  workspace_count: number;
  enabled_module_count: number;
  engagement_count: number;
  insight_count: number;
  finding_count: number;
  pending_decision_count: number;
}

interface Totals {
  client_count: number;
  user_count: number;
  workspace_count: number;
  enabled_module_count: number;
  engagement_count: number;
  insight_count: number;
  finding_count: number;
  pending_decision_count: number;
}

interface PortfolioSummary {
  totals: Totals;
  clients: ClientCard[];
}

const TOTAL_TILES: { key: keyof Totals; label: string; icon: any }[] = [
  { key: 'client_count', label: 'Clientes', icon: Building2 },
  { key: 'user_count', label: 'Usuarios', icon: Users },
  { key: 'workspace_count', label: 'Workspaces', icon: FolderKanban },
  { key: 'enabled_module_count', label: 'Módulos activos', icon: Boxes },
  { key: 'engagement_count', label: 'Engagements', icon: Briefcase },
  { key: 'insight_count', label: 'Insights', icon: Lightbulb },
  { key: 'finding_count', label: 'Hallazgos', icon: AlertTriangle },
  { key: 'pending_decision_count', label: 'Decisiones pendientes', icon: GitPullRequestArrow },
];

const CLIENT_METRICS: { key: keyof ClientCard; label: string; icon: any }[] = [
  { key: 'user_count', label: 'Usuarios', icon: Users },
  { key: 'workspace_count', label: 'Workspaces', icon: FolderKanban },
  { key: 'enabled_module_count', label: 'Módulos', icon: Boxes },
  { key: 'engagement_count', label: 'Engagements', icon: Briefcase },
  { key: 'insight_count', label: 'Insights', icon: Lightbulb },
  { key: 'finding_count', label: 'Hallazgos', icon: AlertTriangle },
  { key: 'pending_decision_count', label: 'Decisiones', icon: GitPullRequestArrow },
];

export const CommandCenterView: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await apiClient.get('/portfolio/summary');
        setData(res.data);
      } catch (e: any) {
        setError(e?.response?.data?.detail || 'No se pudo cargar el portafolio');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

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
      <div className="flex flex-col gap-1">
        <h2 className="font-bold text-2xl flex items-center gap-2">
          <LayoutDashboard className="text-[var(--accent)]" /> Command Center
        </h2>
        <p className="text-sm text-[var(--muted)]">
          Salud del portafolio completo — visión cruzada de todos los clientes
        </p>
      </div>

      {error && (
        <div
          className="px-4 py-3 rounded-lg text-sm"
          style={{ background: 'var(--neg-tint, rgba(239,68,68,0.1))', color: 'var(--neg, #ef4444)' }}
        >
          {error}
        </div>
      )}

      {/* Totals row */}
      {data && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
          {TOTAL_TILES.map((t) => {
            const Icon = t.icon;
            return (
              <Card key={t.key} className="p-4">
                <div className="flex items-center gap-2 mb-2 text-[var(--muted)]">
                  <Icon size={16} className="text-[var(--accent)]" />
                  <span className="text-[10px] uppercase tracking-wide truncate">{t.label}</span>
                </div>
                <p className="text-2xl font-bold text-[var(--ink)]">{data.totals[t.key]}</p>
              </Card>
            );
          })}
        </div>
      )}

      {/* Clients grid */}
      <div className="space-y-4">
        <h3 className="font-bold text-lg">Clientes</h3>

        {data && data.clients.length === 0 && (
          <Card className="p-8 text-center">
            <Building2 className="mx-auto mb-3 text-[var(--muted-2)]" size={28} />
            <p className="text-sm text-[var(--muted)]">
              Aún no hay clientes dados de alta.
            </p>
          </Card>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {data?.clients.map((c) => (
            <div
              key={c.id}
              role="button"
              tabIndex={0}
              onClick={() => navigate(`/admin/clients/${c.id}`)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') navigate(`/admin/clients/${c.id}`);
              }}
              className="cursor-pointer outline-none"
            >
            <Card className="p-5 hover:border-[var(--accent)]">
              <div className="flex items-start justify-between gap-2 mb-4">
                <div className="flex items-start gap-3">
                  <div
                    className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                    style={{ background: 'var(--surface-2)' }}
                  >
                    <Building2 size={18} className="text-[var(--accent)]" />
                  </div>
                  <div>
                    <h4 className="font-bold text-[var(--ink)] leading-tight">{c.name}</h4>
                    <p className="text-xs text-[var(--muted-2)] mt-0.5">{c.slug}</p>
                  </div>
                </div>
                <ChevronRight size={16} className="text-[var(--muted-2)] flex-shrink-0 mt-1" />
              </div>

              <div className="grid grid-cols-2 gap-2">
                {CLIENT_METRICS.map((m) => {
                  const Icon = m.icon;
                  const value = c[m.key] as number;
                  const isAlert =
                    (m.key === 'pending_decision_count' || m.key === 'finding_count') && value > 0;
                  return (
                    <div
                      key={m.key}
                      className="flex items-center gap-2 px-2 py-1.5 rounded-md"
                      style={{ background: 'var(--surface-2)' }}
                    >
                      <Icon
                        size={14}
                        className="flex-shrink-0"
                        style={{ color: isAlert ? 'var(--warn, #f59e0b)' : 'var(--muted)' }}
                      />
                      <span className="text-xs text-[var(--muted)] truncate">{m.label}</span>
                      <span
                        className="ml-auto text-sm font-bold"
                        style={{ color: isAlert ? 'var(--warn, #f59e0b)' : 'var(--ink)' }}
                      >
                        {value}
                      </span>
                    </div>
                  );
                })}
              </div>
            </Card>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CommandCenterView;
