import React, { useEffect, useMemo, useState } from 'react';
import { Card } from '../ui/Card';
import { CheckCircle2, Circle, Clock, Loader2, Inbox } from 'lucide-react';
import apiClient from '../../api/client';

type ItemStatus = 'TODO' | 'IN_PROGRESS' | 'DONE';
type ItemPhase = 30 | 60 | 90;

interface RoadmapItem {
  id?: number;
  phase: ItemPhase;
  status: ItemStatus;
  title: string;
  dimension?: string;
  assigned_to?: string | null;
  due_date?: string | null;
}

interface Roadmap {
  id?: number;
  items: RoadmapItem[];
}

interface Workspace {
  id: number;
  name: string;
}

const STATUS_LABEL: Record<ItemStatus, string> = {
  TODO: 'Pendiente',
  IN_PROGRESS: 'En Curso',
  DONE: 'Completado',
};

const PHASES: ItemPhase[] = [30, 60, 90];

export const RoadmapView: React.FC = () => {
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const wsRes = await apiClient.get<Workspace[]>('/workspaces');
        const workspaces = wsRes.data;
        if (!workspaces || workspaces.length === 0) {
          setRoadmap(null);
          return;
        }
        const res = await apiClient.get<Roadmap>(`/roadmaps/latest?workspace_id=${workspaces[0].id}`);
        setRoadmap(res.data);
      } catch (e) {
        console.error(e);
        setRoadmap(null);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const itemsByPhase = useMemo(() => {
    const grouped: Record<ItemPhase, RoadmapItem[]> = { 30: [], 60: [], 90: [] };
    (roadmap?.items ?? []).forEach((item) => {
      if (grouped[item.phase]) grouped[item.phase].push(item);
    });
    return grouped;
  }, [roadmap]);

  if (loading) {
    return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-[var(--accent)]" /></div>;
  }

  const hasItems = (roadmap?.items ?? []).length > 0;

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h2 className="font-bold text-2xl">Roadmap de Ejecución</h2>
        <p className="text-sm text-[var(--muted)] mt-1">Plan de acción por horizonte (30 / 60 / 90 días)</p>
      </div>

      {!hasItems ? (
        <Card className="p-12 flex flex-col items-center justify-center gap-3 text-center">
          <Inbox size={40} className="text-[var(--muted-2)]" />
          <h3 className="font-bold text-lg text-[var(--ink)]">Aún no hay roadmap</h3>
          <p className="text-sm text-[var(--muted)] max-w-md">
            El equipo de Syner aún no ha publicado un plan de acción para tu organización.
          </p>
        </Card>
      ) : (
        <div className="space-y-8">
          {PHASES.map((phase) => {
            const items = itemsByPhase[phase];
            if (items.length === 0) return null;
            return (
              <section key={phase} className="space-y-3">
                <div className="flex items-center gap-3">
                  <span className="px-3 py-1 rounded-lg text-sm font-bold text-white" style={{ background: 'linear-gradient(135deg, var(--accent-strong), var(--accent))' }}>
                    {phase} días
                  </span>
                  <span className="text-xs text-[var(--muted)] font-mono">{items.length} {items.length === 1 ? 'iniciativa' : 'iniciativas'}</span>
                </div>
                <div className="grid grid-cols-1 gap-3">
                  {items.map((item, idx) => {
                    const isCompleted = item.status === 'DONE';
                    const isActive = item.status === 'IN_PROGRESS';
                    return (
                      <Card
                        key={item.id ?? `${phase}-${idx}`}
                        className={`p-4 border ${isActive ? 'border-[var(--accent)] bg-[var(--accent-tint)]' : 'border-[var(--border)]'}`}
                      >
                        <div className="flex items-start gap-3">
                          <div className="mt-0.5 shrink-0">
                            {isCompleted ? (
                              <CheckCircle2 size={20} className="text-[var(--accent)]" />
                            ) : isActive ? (
                              <div className="w-5 h-5 rounded-full border-2 border-[var(--accent)] flex items-center justify-center">
                                <div className="w-2 h-2 rounded-full bg-[var(--accent)]" />
                              </div>
                            ) : (
                              <Circle size={20} className="text-[var(--border-strong)]" />
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <h3 className={`font-bold ${isActive ? 'text-[var(--accent-strong)]' : 'text-[var(--ink)]'}`}>{item.title}</h3>
                              <span className={`px-2 py-1 rounded text-[10px] uppercase font-bold tracking-wider ${
                                isCompleted ? 'bg-[var(--bg)] text-[var(--muted-2)]' :
                                isActive ? 'bg-[var(--accent)] text-white' :
                                'bg-[var(--surface-2)] text-[var(--muted)]'
                              }`}>
                                {STATUS_LABEL[item.status]}
                              </span>
                            </div>
                            <div className="flex flex-wrap items-center gap-4 mt-2 text-xs text-[var(--muted)]">
                              {item.dimension && (
                                <span className="font-mono uppercase text-[var(--muted-2)]">{item.dimension}</span>
                              )}
                              {item.assigned_to && (
                                <span>Responsable: <strong className="text-[var(--ink)]">{item.assigned_to}</strong></span>
                              )}
                              {item.due_date && (
                                <span className="flex items-center gap-1.5"><Clock size={12} />{item.due_date}</span>
                              )}
                            </div>
                          </div>
                        </div>
                      </Card>
                    );
                  })}
                </div>
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
};
