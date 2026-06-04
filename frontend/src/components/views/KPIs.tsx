import React, { useState } from 'react';
import { Card } from '../ui/Card';
import { ProgressBar } from '../ui/ProgressBar';
import { kpiDetails, KPIDetail } from '../../data/mockData';
import { Filter } from 'lucide-react';

type AreaFilter = 'Todos' | 'Finanzas' | 'Operaciones' | 'RRHH';

export const KPIs: React.FC = () => {
  const [filter, setFilter] = useState<AreaFilter>('Todos');

  const filteredData = filter === 'Todos' 
    ? kpiDetails 
    : kpiDetails.filter(kpi => kpi.area === filter);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="font-bold text-2xl">Métricas Detalladas</h2>
          <p className="text-sm text-[var(--muted)] mt-1">Seguimiento de línea base vs. actual</p>
        </div>
        
        <div className="flex items-center gap-2">
          <Filter size={16} className="text-[var(--muted)]" />
          <div className="flex bg-[var(--surface)] border border-[var(--border)] rounded-lg p-1">
            {(['Todos', 'Finanzas', 'Operaciones', 'RRHH'] as AreaFilter[]).map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                  filter === f 
                    ? 'bg-[var(--accent-tint)] text-[var(--accent-strong)]' 
                    : 'text-[var(--muted)] hover:text-[var(--ink)]'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
      </div>

      <Card className="p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-[var(--surface-2)] text-[var(--muted)] border-b border-[var(--border)]">
              <tr>
                <th className="px-6 py-4 font-medium">Indicador</th>
                <th className="px-6 py-4 font-medium">Área</th>
                <th className="px-6 py-4 font-medium">Línea Base</th>
                <th className="px-6 py-4 font-medium">Actual</th>
                <th className="px-6 py-4 font-medium">Meta</th>
                <th className="px-6 py-4 font-medium w-1/4">Progreso</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              {filteredData.map((kpi) => (
                <tr key={kpi.id} className="hover:bg-[var(--surface-2)] transition-colors">
                  <td className="px-6 py-4 font-medium text-[var(--ink)]">{kpi.name}</td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-2 py-1 rounded text-[10px] font-mono uppercase bg-[var(--bg)] text-[var(--muted-2)] border border-[var(--border)]">
                      {kpi.area}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-mono text-xs">{kpi.baseline}</td>
                  <td className="px-6 py-4 font-mono text-xs font-bold text-[var(--ink)]">{kpi.actual}</td>
                  <td className="px-6 py-4 font-mono text-xs">{kpi.meta}</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <ProgressBar percent={kpi.percent} className="flex-1" />
                      <span className="font-mono text-xs text-[var(--muted)] w-8 text-right">{kpi.percent}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filteredData.length === 0 && (
            <div className="p-8 text-center text-[var(--muted)]">
              No hay métricas para esta área.
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};
