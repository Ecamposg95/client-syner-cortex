import React, { useEffect, useState } from 'react';
import { Card } from '../ui/Card';
import { Loader2, Inbox, TrendingUp } from 'lucide-react';
import apiClient from '../../api/client';

interface KpiItem {
  id: number;
  name: string;
  value: string | number;
  timestamp: string;
}

const fmtTimestamp = (ts: string): string => {
  if (!ts) return '';
  try {
    return new Date(ts).toLocaleDateString('es-MX', { day: '2-digit', month: 'short', year: 'numeric' });
  } catch {
    return ts;
  }
};

export const KPIs: React.FC = () => {
  const [kpis, setKpis] = useState<KpiItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient
      .get<KpiItem[]>('/kpi')
      .then((res) => setKpis(res.data ?? []))
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-[var(--accent)]" /></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="font-bold text-2xl">Métricas Detalladas</h2>
          <p className="text-sm text-[var(--muted)] mt-1">Indicadores clave de la consultoría</p>
        </div>
      </div>

      {kpis.length === 0 ? (
        <Card className="p-12 flex flex-col items-center justify-center gap-3 text-center">
          <Inbox size={40} className="text-[var(--muted-2)]" />
          <h3 className="font-bold text-lg text-[var(--ink)]">Sin métricas registradas</h3>
          <p className="text-sm text-[var(--muted)] max-w-md">
            Aún no se han capturado KPIs para tu organización.
          </p>
        </Card>
      ) : (
        <Card className="p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-[var(--surface-2)] text-[var(--muted)] border-b border-[var(--border)]">
                <tr>
                  <th className="px-6 py-4 font-medium">Indicador</th>
                  <th className="px-6 py-4 font-medium">Valor</th>
                  <th className="px-6 py-4 font-medium">Actualizado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)]">
                {kpis.map((kpi) => (
                  <tr key={kpi.id} className="hover:bg-[var(--surface-2)] transition-colors">
                    <td className="px-6 py-4 font-medium text-[var(--ink)]">
                      <span className="inline-flex items-center gap-2">
                        <TrendingUp size={14} className="text-[var(--accent)]" />
                        {kpi.name}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-mono text-sm font-bold text-[var(--ink)]">{String(kpi.value)}</td>
                    <td className="px-6 py-4 font-mono text-xs text-[var(--muted)]">{fmtTimestamp(kpi.timestamp)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};
