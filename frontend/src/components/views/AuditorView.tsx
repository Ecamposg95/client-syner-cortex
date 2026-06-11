import React from 'react';
import { Card } from '../ui/Card';
import { ClipboardCheck, AlertTriangle, CheckCircle, Clock } from 'lucide-react';

const mockAudits = [
  { id: 1, area: 'Taller Principal', score: 85, status: 'COMPLETED', findings: 3, date: '2026-05-15' },
  { id: 2, area: 'Almacén de Refacciones', score: 62, status: 'IN_PROGRESS', findings: 7, date: '2026-05-28' },
  { id: 3, area: 'Recepción y Caja', score: 0, status: 'PENDING', findings: 0, date: '2026-06-10' },
];

export const AuditorView: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <h2 className="font-bold text-2xl">Auditoría Operativa</h2>
        <p className="text-sm text-[var(--muted)]">Seguimiento de auditorías y hallazgos por área</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {mockAudits.map((audit) => (
          <Card key={audit.id} className="p-6 space-y-4">
            <div className="flex justify-between items-start">
              <div className="bg-[var(--surface-2)] p-3 rounded-lg">
                <ClipboardCheck size={24} className="text-[var(--ink)]" />
              </div>
              {audit.status === 'COMPLETED' ? (
                <CheckCircle size={20} className="text-green-500" />
              ) : audit.status === 'IN_PROGRESS' ? (
                <Clock size={20} className="text-yellow-500" />
              ) : (
                <Clock size={20} className="text-[var(--muted)]" />
              )}
            </div>

            <div>
              <h3 className="font-semibold text-[var(--ink)]">{audit.area}</h3>
              <p className="text-xs text-[var(--muted)] mt-1">Programada: {audit.date}</p>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-[var(--border)]">
              <div className="flex flex-col">
                <span className="text-[10px] uppercase font-bold text-[var(--muted)]">Score</span>
                <span className="font-extrabold text-lg" style={{ color: audit.score >= 80 ? 'var(--pos)' : audit.score >= 50 ? 'var(--warn)' : 'var(--muted)' }}>
                  {audit.score > 0 ? `${audit.score}%` : '—'}
                </span>
              </div>
              <div className="flex flex-col items-end">
                <span className="text-[10px] uppercase font-bold text-[var(--muted)]">Hallazgos</span>
                <span className="font-bold text-lg flex items-center gap-1">
                  {audit.findings > 0 && <AlertTriangle size={14} className="text-yellow-500" />}
                  {audit.findings}
                </span>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};