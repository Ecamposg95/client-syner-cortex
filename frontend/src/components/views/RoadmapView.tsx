import React from 'react';
import { Card } from '../ui/Card';
import { phases } from '../../data/mockData';
import { CheckCircle2, Circle, Clock } from 'lucide-react';

export const RoadmapView: React.FC = () => {
  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h2 className="font-bold text-2xl">Roadmap de Ejecución</h2>
        <p className="text-sm text-[var(--muted)] mt-1">Línea de tiempo de fases del proyecto</p>
      </div>

      <Card className="p-8">
        <div className="relative border-l-2 border-[var(--border)] ml-4 space-y-10">
          {phases.map((phase, index) => {
            const isCompleted = phase.status === 'Completado';
            const isActive = phase.status === 'En Curso';
            
            return (
              <div key={phase.id} className="relative pl-8">
                {/* Timeline Dot */}
                <div className={`absolute -left-[11px] top-1 w-5 h-5 rounded-full flex items-center justify-center bg-[var(--surface)] ${
                  isActive ? 'ring-2 ring-[var(--accent)] ring-offset-2 ring-offset-[var(--surface)]' : ''
                }`}>
                  {isCompleted ? (
                    <CheckCircle2 size={20} className="text-[var(--accent)] bg-[var(--surface)] rounded-full" />
                  ) : isActive ? (
                    <div className="w-3 h-3 rounded-full bg-[var(--accent)]" />
                  ) : (
                    <Circle size={20} className="text-[var(--border-strong)] bg-[var(--surface)] rounded-full" />
                  )}
                </div>

                <div className={`p-5 rounded-xl border transition-all ${
                  isActive 
                    ? 'border-[var(--accent)] bg-[var(--accent-tint)] shadow-accent' 
                    : 'border-[var(--border)] hover:border-[var(--border-strong)] bg-[var(--surface)]'
                }`}>
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-2">
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-[10px] text-[var(--muted-2)] uppercase">
                        Fase 0{phase.id}
                      </span>
                      <h3 className={`font-bold text-lg ${isActive ? 'text-[var(--accent-strong)]' : 'text-[var(--ink)]'}`}>
                        {phase.title}
                      </h3>
                    </div>
                    <div className="flex items-center gap-4 text-xs font-mono">
                      <div className="flex items-center gap-1.5 text-[var(--muted)]">
                        <Clock size={12} />
                        <span>{phase.date}</span>
                      </div>
                      <span className={`px-2 py-1 rounded text-[10px] uppercase font-bold tracking-wider ${
                        isCompleted ? 'bg-[var(--bg)] text-[var(--muted-2)]' :
                        isActive ? 'bg-[var(--accent)] text-white' :
                        'bg-[var(--surface-2)] text-[var(--muted)]'
                      }`}>
                        {phase.status}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2 mt-4 text-sm">
                    <span className="text-[var(--muted)]">Responsable:</span>
                    <span className="font-medium text-[var(--ink)]">{phase.responsible}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
};
