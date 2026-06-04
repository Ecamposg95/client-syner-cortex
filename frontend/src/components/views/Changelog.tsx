import React from 'react';
import { Card } from '../ui/Card';
import { changelog } from '../../data/mockData';
import { Clock } from 'lucide-react';

export const Changelog: React.FC = () => {
  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h2 className="font-bold text-2xl">Bitácora de Decisiones</h2>
        <p className="text-sm text-[var(--muted)] mt-1">Registro auditable de cambios y acuerdos del proyecto</p>
      </div>

      <Card className="p-0 overflow-hidden">
        <div className="max-h-[600px] overflow-y-auto">
          <div className="divide-y divide-[var(--border)]">
            {changelog.map((entry) => (
              <div key={entry.id} className="p-5 flex gap-4 hover:bg-[var(--surface-2)] transition-colors">
                <div className="w-10 h-10 shrink-0 rounded-full bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center font-bold text-xs text-[var(--ink)]">
                  {entry.initials}
                </div>
                <div className="flex-1 min-w-0 pt-0.5">
                  <p className="text-sm text-[var(--ink)] font-medium leading-relaxed">
                    {entry.description}
                  </p>
                  <div className="flex items-center gap-3 mt-2 text-xs font-mono">
                    <span className="text-[var(--ink-2)] font-semibold">{entry.user}</span>
                    <span className="text-[var(--border-strong)]">•</span>
                    <span className="text-[var(--muted)]">{entry.timestamp}</span>
                    <span className="text-[var(--border-strong)]">•</span>
                    <span className="flex items-center gap-1 text-[var(--accent)] font-bold">
                      <Clock size={12} />
                      {entry.relative}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>
    </div>
  );
};
