import React, { useEffect, useState } from 'react';
import { Card } from '../ui/Card';
import { Milestone, Loader2, DollarSign, Target } from 'lucide-react';
import apiClient from '../../api/client';

interface Initiative {
  id: number;
  title: string;
  objective: string;
  area: string;
  status: string;
  priority: string;
  estimated_budget: number;
}

export const InitiativesView: React.FC = () => {
  const [initiatives, setInitiatives] = useState<Initiative[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchInitiatives = async () => {
      try {
        const engRes = await apiClient.get('/clevel/engagements');
        if (engRes.data.length > 0) {
          const res = await apiClient.get(`/clevel/engagements/${engRes.data[0].id}/initiatives`);
          setInitiatives(res.data);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchInitiatives();
  }, []);

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
  };

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-[var(--accent)]" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <h2 className="font-bold text-2xl">Strategic Initiatives</h2>
        <p className="text-sm text-[var(--muted)]">Roadmap de proyectos y acciones de mejora</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {initiatives.map((ini) => (
          <Card key={ini.id} className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-[var(--surface-2)] rounded-lg text-[var(--accent)]">
                <Milestone size={24} />
              </div>
              <div>
                <h3 className="font-bold text-lg text-[var(--ink)] leading-tight">{ini.title}</h3>
                <span className="text-xs font-mono text-[var(--muted-2)] uppercase">{ini.area}</span>
              </div>
            </div>

            <div className="space-y-4 text-sm">
              <div className="p-3 bg-[var(--surface-2)] rounded-lg">
                <p className="font-semibold flex items-center gap-2 mb-1"><Target size={14}/> Objetivo</p>
                <p className="text-[var(--muted)]">{ini.objective}</p>
              </div>

              <div className="flex items-center justify-between border-t border-[var(--border)] pt-4">
                <div className="flex flex-col">
                  <span className="text-[10px] uppercase font-bold text-[var(--muted)]">Estado</span>
                  <span className="font-semibold text-[var(--ink)]">{ini.status}</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[10px] uppercase font-bold text-[var(--muted)]">Prioridad</span>
                  <span className="font-semibold text-[var(--ink)]">{ini.priority}</span>
                </div>
                <div className="flex flex-col items-end">
                  <span className="text-[10px] uppercase font-bold text-[var(--muted)]">Presupuesto</span>
                  <span className="font-semibold flex items-center text-[var(--accent-strong)]">
                    <DollarSign size={14}/> {ini.estimated_budget ? formatCurrency(ini.estimated_budget).replace('$', '') : 'TBD'}
                  </span>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
