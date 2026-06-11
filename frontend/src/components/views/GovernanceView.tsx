import React from 'react';
import { Card } from '../ui/Card';
import { Landmark, Users, FileText, Shield } from 'lucide-react';

const mockPolicies = [
  { id: 1, name: 'Código de Ética y Conducta', status: 'VIGENTE', lastReview: '2026-01-15', owner: 'Dirección General' },
  { id: 2, name: 'Política de Seguridad Laboral (EHS)', status: 'VIGENTE', lastReview: '2026-03-01', owner: 'Operaciones' },
  { id: 3, name: 'Política de Protección de Datos', status: 'EN REVISIÓN', lastReview: '2025-12-10', owner: 'Legal' },
  { id: 4, name: 'Reglamento Interno de Trabajo', status: 'VIGENTE', lastReview: '2026-02-20', owner: 'RRHH' },
];

const mockCommittees = [
  { id: 1, name: 'Comité de Dirección', members: 4, nextMeeting: '2026-06-15' },
  { id: 2, name: 'Comité de Seguridad', members: 6, nextMeeting: '2026-06-08' },
  { id: 3, name: 'Comité de Calidad', members: 5, nextMeeting: '2026-06-22' },
];

export const GovernanceView: React.FC = () => {
  return (
    <div className="space-y-8">
      {/* Policies Section */}
      <div className="space-y-4">
        <div className="flex flex-col gap-1">
          <h2 className="font-bold text-2xl flex items-center gap-2">
            <Landmark className="text-[var(--accent)]" /> Gobernanza Corporativa
          </h2>
          <p className="text-sm text-[var(--muted)]">Políticas, comités y estructura de gobierno</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {mockPolicies.map((policy) => (
            <Card key={policy.id} className="p-5">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-[var(--surface-2)] rounded-lg">
                    <FileText size={20} className="text-[var(--ink)]" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm text-[var(--ink)]">{policy.name}</h3>
                    <span className="text-[10px] text-[var(--muted)]">Responsable: {policy.owner}</span>
                  </div>
                </div>
                <span className={`px-2 py-1 text-[10px] uppercase font-bold rounded-md ${
                  policy.status === 'VIGENTE' ? 'bg-green-500/10 text-green-500' : 'bg-yellow-500/10 text-yellow-500'
                }`}>
                  {policy.status}
                </span>
              </div>
              <p className="text-xs text-[var(--muted)]">Última revisión: {policy.lastReview}</p>
            </Card>
          ))}
        </div>
      </div>

      {/* Committees Section */}
      <div className="space-y-4 pt-4 border-t border-[var(--border)]">
        <h3 className="font-bold text-lg flex items-center gap-2">
          <Users className="text-[var(--accent)]" size={20} /> Comités Activos
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {mockCommittees.map((c) => (
            <Card key={c.id} className="p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-[var(--surface-2)] rounded-lg">
                  <Shield size={20} className="text-[var(--accent)]" />
                </div>
                <h4 className="font-semibold text-[var(--ink)]">{c.name}</h4>
              </div>
              <div className="flex justify-between text-xs text-[var(--muted)]">
                <span>{c.members} miembros</span>
                <span>Próx: {c.nextMeeting}</span>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};