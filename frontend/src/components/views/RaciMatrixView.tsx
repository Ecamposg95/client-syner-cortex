import React, { useEffect, useMemo, useState } from 'react';
import { Card } from '../ui/Card';
import {
  Grid3x3, Loader2, AlertTriangle, CheckCircle2, Info, ShieldAlert,
  Download, X, Filter,
} from 'lucide-react';
import apiClient from '../../api/client';
import { useAuthStore } from '../../store/authStore';

interface Role {
  id: number; name: string; order: number;
  charter_decides: string | null;
  charter_blocks: string | null;
  charter_escalates: string | null;
}
interface Process {
  id: number; name: string; order: number;
  evidence_min: string | null; handoff_owner: string | null;
}
interface Validation {
  process_id: number; accountable_count: number; responsible_count: number;
  golden_rule_ok: boolean; missing_responsible: boolean; issues: string[];
}
interface MatrixDetail {
  id: number; name: string; description: string | null; version: string;
  roles: Role[]; processes: Process[];
  cells: Record<string, string[]>;
  validation: Validation[];
  valid: boolean;
}
interface MatrixSummary {
  id: number; name: string; version: string; role_count: number;
  process_count: number; violations: number;
}

const VALUES = ['R', 'A', 'C', 'I'] as const;
const VALUE_META: Record<string, { label: string; color: string; bg: string }> = {
  R: { label: 'Responsible — ejecuta', color: 'var(--pos, #16a34a)', bg: 'rgba(22,163,74,0.14)' },
  A: { label: 'Accountable — único dueño', color: 'var(--accent, #2563eb)', bg: 'rgba(37,99,235,0.14)' },
  C: { label: 'Consulted — se le consulta', color: 'var(--warn, #d97706)', bg: 'rgba(217,119,6,0.14)' },
  I: { label: 'Informed — se le informa', color: 'var(--muted, #6b7280)', bg: 'rgba(107,114,128,0.14)' },
};

const CLIENT_EDIT_ROLES = ['CLIENT_OWNER', 'CLIENT_EXECUTIVE', 'CLIENT_MANAGER'];

export const RaciMatrixView: React.FC = () => {
  const user = useAuthStore((s) => s.user);
  const orgRelation = useAuthStore((s) => s.currentOrgRelation);
  const isCrew = user?.user_type === 'SYNER_CREW';
  const canEdit = isCrew || CLIENT_EDIT_ROLES.includes(orgRelation?.role || '');

  const [summaries, setSummaries] = useState<MatrixSummary[]>([]);
  const [matrixId, setMatrixId] = useState<number | null>(null);
  const [detail, setDetail] = useState<MatrixDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeCell, setActiveCell] = useState<string | null>(null);   // "pid:rid"
  const [charterRole, setCharterRole] = useState<Role | null>(null);
  const [highlightRole, setHighlightRole] = useState<number | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await apiClient.get('/raci/matrices');
        setSummaries(res.data);
        if (res.data.length) setMatrixId(res.data[0].id);
      } catch (e) { console.error(e); }
      finally { setLoading(false); }
    })();
  }, []);

  useEffect(() => {
    if (matrixId == null) { setDetail(null); return; }
    (async () => {
      try {
        const res = await apiClient.get(`/raci/matrices/${matrixId}`);
        setDetail(res.data);
      } catch (e) { console.error(e); }
    })();
  }, [matrixId]);

  const validationByProcess = useMemo(() => {
    const m: Record<number, Validation> = {};
    detail?.validation.forEach((v) => { m[v.process_id] = v; });
    return m;
  }, [detail]);

  const allIssues = useMemo(
    () => detail?.validation.flatMap((v) => v.issues) ?? [],
    [detail],
  );

  const toggleValue = async (processId: number, roleId: number, value: string, present: boolean) => {
    if (!canEdit || !detail) return;
    setSaving(true);
    try {
      const res = await apiClient.patch(`/raci/matrices/${detail.id}/cell`, {
        process_id: processId, role_id: roleId, value, present,
      });
      setDetail(res.data);
    } catch (e) { console.error(e); }
    finally { setSaving(false); }
  };

  const exportMarkdown = () => {
    if (!detail) return;
    const header = `| Proceso | ${detail.roles.map((r) => r.name).join(' | ')} |`;
    const sep = `|${' --- |'.repeat(detail.roles.length + 1)}`;
    const rows = detail.processes.map((p) => {
      const cells = detail.roles.map((r) => (detail.cells[`${p.id}:${r.id}`] || []).join('/') || '–');
      return `| ${p.name} | ${cells.join(' | ')} |`;
    });
    const md = [`# ${detail.name} (v${detail.version})`, '', header, sep, ...rows, '',
      `> Regla: un solo Accountable (A) por proceso. Estado: ${detail.valid ? 'OK' : 'con observaciones'}.`,
    ].join('\n');
    const blob = new Blob([md], { type: 'text/markdown' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `${detail.name.replace(/[^a-z0-9]+/gi, '_')}.md`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-[var(--accent)]" /></div>;

  if (!detail) {
    return (
      <Card className="p-8 text-center">
        <Grid3x3 className="mx-auto mb-3 text-[var(--muted-2)]" size={28} />
        <p className="text-sm text-[var(--muted)]">No hay matrices RACI para esta organización todavía.</p>
      </Card>
    );
  }

  return (
    <div className="space-y-6" onClick={() => setActiveCell(null)}>
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="font-bold text-2xl flex items-center gap-2">
            <Grid3x3 className="text-[var(--accent)]" /> Matriz RACI
          </h2>
          <p className="text-sm text-[var(--muted)]">
            Responsabilidad por proceso y rol. {canEdit ? 'Haz clic en una celda para editar.' : 'Vista de solo lectura.'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {summaries.length > 1 && (
            <select
              value={matrixId ?? ''}
              onChange={(e) => setMatrixId(Number(e.target.value))}
              className="px-3 py-2 rounded-md text-sm border border-[var(--border)] bg-[var(--surface)] text-[var(--ink-2)]"
            >
              {summaries.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          )}
          <button
            type="button" onClick={exportMarkdown}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium border border-[var(--border)] text-[var(--ink-2)] hover:bg-[var(--surface-2)] transition-colors"
          >
            <Download size={15} /> Exportar
          </button>
        </div>
      </div>

      {/* Validation banner — golden rule */}
      <Card className="p-4 border-l-4" style={{ borderLeftColor: detail.valid ? 'var(--pos, #16a34a)' : 'var(--neg, #ef4444)' }}>
        <div className="flex items-center gap-2 mb-1">
          {detail.valid
            ? <CheckCircle2 size={18} className="text-[var(--pos,#16a34a)]" />
            : <AlertTriangle size={18} className="text-[var(--neg,#ef4444)]" />}
          <span className="font-bold text-sm">
            {detail.valid ? 'Matriz consistente' : `${allIssues.length} observación(es) de diseño`}
          </span>
          {saving && <Loader2 size={14} className="animate-spin text-[var(--muted)]" />}
        </div>
        <p className="text-xs text-[var(--muted)] ml-7">
          Regla de oro: <strong>un solo Accountable (A) por proceso</strong>. Si hay dos aprobadores, el proceso no está bien cerrado.
        </p>
        {!detail.valid && (
          <ul className="mt-2 ml-7 space-y-1">
            {allIssues.map((iss, k) => (
              <li key={k} className="text-xs text-[var(--neg,#ef4444)] flex items-start gap-1.5">
                <ShieldAlert size={12} className="mt-0.5 flex-shrink-0" /> {iss}
              </li>
            ))}
          </ul>
        )}
      </Card>

      {/* Role highlight filter */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-[var(--muted-2)] flex items-center gap-1"><Filter size={12} /> Resaltar rol:</span>
        <button
          onClick={() => setHighlightRole(null)}
          className={`px-2.5 py-1 rounded-full text-xs border transition-colors ${highlightRole === null ? 'border-[var(--accent)] text-[var(--accent-strong)] bg-[var(--accent-tint,rgba(37,99,235,0.08))]' : 'border-[var(--border)] text-[var(--muted)]'}`}
        >Todos</button>
        {detail.roles.map((r) => (
          <button
            key={r.id}
            onClick={() => setHighlightRole(highlightRole === r.id ? null : r.id)}
            className={`px-2.5 py-1 rounded-full text-xs border transition-colors ${highlightRole === r.id ? 'border-[var(--accent)] text-[var(--accent-strong)] bg-[var(--accent-tint,rgba(37,99,235,0.08))]' : 'border-[var(--border)] text-[var(--muted)]'}`}
          >{r.name}</button>
        ))}
      </div>

      {/* Matrix grid */}
      <Card className="p-0 overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr>
              <th className="sticky left-0 z-10 bg-[var(--surface)] text-left p-3 font-bold text-[var(--ink)] min-w-[220px] border-b border-[var(--border)]">
                Proceso
              </th>
              {detail.roles.map((r) => (
                <th
                  key={r.id}
                  onClick={() => setCharterRole(r)}
                  title="Ver charter de autoridad"
                  className={`p-2 text-center font-semibold cursor-pointer align-bottom border-b border-[var(--border)] transition-colors hover:bg-[var(--surface-2)] ${highlightRole === r.id ? 'bg-[var(--accent-tint,rgba(37,99,235,0.08))]' : ''}`}
                  style={{ minWidth: 92 }}
                >
                  <span className="block text-[11px] leading-tight text-[var(--ink-2)]">{r.name}</span>
                  <Info size={11} className="inline mt-1 text-[var(--muted-2)]" />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {detail.processes.map((p) => {
              const v = validationByProcess[p.id];
              const rowBad = v && v.issues.length > 0;
              return (
                <tr key={p.id} className="border-b border-[var(--border)] last:border-0">
                  <td
                    className="sticky left-0 z-10 bg-[var(--surface)] p-3 align-top border-r border-[var(--border)]"
                    style={rowBad ? { boxShadow: 'inset 3px 0 0 var(--neg, #ef4444)' } : undefined}
                    title={[p.evidence_min ? `Evidencia mínima: ${p.evidence_min}` : '', p.handoff_owner ? `Owner del handoff: ${p.handoff_owner}` : ''].filter(Boolean).join('\n')}
                  >
                    <div className="font-medium text-[var(--ink)] text-[13px]">{p.name}</div>
                    {p.handoff_owner && (
                      <div className="text-[10px] text-[var(--muted-2)] mt-0.5">Owner: {p.handoff_owner}</div>
                    )}
                    {rowBad && (
                      <div className="text-[10px] text-[var(--neg,#ef4444)] mt-0.5 flex items-center gap-1">
                        <AlertTriangle size={10} /> {v!.accountable_count !== 1 ? `${v!.accountable_count} A` : 'sin R'}
                      </div>
                    )}
                  </td>
                  {detail.roles.map((r) => {
                    const key = `${p.id}:${r.id}`;
                    const vals = detail.cells[key] || [];
                    const isActive = activeCell === key;
                    const dim = highlightRole !== null && highlightRole !== r.id;
                    return (
                      <td
                        key={r.id}
                        className={`relative p-1.5 text-center transition-colors ${dim ? 'opacity-30' : ''} ${highlightRole === r.id ? 'bg-[var(--accent-tint,rgba(37,99,235,0.06))]' : ''}`}
                        onClick={(e) => { e.stopPropagation(); if (canEdit) setActiveCell(isActive ? null : key); }}
                        style={{ cursor: canEdit ? 'pointer' : 'default' }}
                      >
                        <div className="flex items-center justify-center gap-0.5 min-h-[26px]">
                          {vals.length === 0 && <span className="text-[var(--muted-2)] text-xs">·</span>}
                          {vals.map((val) => (
                            <span
                              key={val}
                              className="inline-flex items-center justify-center w-5 h-5 rounded text-[11px] font-bold"
                              style={{ color: VALUE_META[val]?.color, background: VALUE_META[val]?.bg }}
                            >{val}</span>
                          ))}
                        </div>

                        {/* Edit popover */}
                        {isActive && canEdit && (
                          <div
                            className="absolute z-20 top-full left-1/2 -translate-x-1/2 mt-1 p-1.5 rounded-lg shadow-float flex gap-1"
                            style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
                            onClick={(e) => e.stopPropagation()}
                          >
                            {VALUES.map((val) => {
                              const on = vals.includes(val);
                              return (
                                <button
                                  key={val}
                                  title={VALUE_META[val].label}
                                  onClick={() => toggleValue(p.id, r.id, val, !on)}
                                  className="w-7 h-7 rounded text-xs font-bold transition-all"
                                  style={{
                                    color: on ? '#fff' : VALUE_META[val].color,
                                    background: on ? VALUE_META[val].color : VALUE_META[val].bg,
                                    outline: on ? '2px solid var(--ink)' : 'none',
                                  }}
                                >{val}</button>
                              );
                            })}
                          </div>
                        )}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </Card>

      {/* Legend */}
      <div className="flex flex-wrap gap-4">
        {VALUES.map((val) => (
          <div key={val} className="flex items-center gap-1.5 text-xs text-[var(--muted)]">
            <span className="inline-flex items-center justify-center w-5 h-5 rounded font-bold" style={{ color: VALUE_META[val].color, background: VALUE_META[val].bg }}>{val}</span>
            {VALUE_META[val].label}
          </div>
        ))}
      </div>

      {/* Charter drawer */}
      {charterRole && (
        <div className="fixed inset-0 z-50 flex justify-end" style={{ background: 'rgba(0,0,0,0.4)' }} onClick={() => setCharterRole(null)}>
          <div className="w-full max-w-sm h-full p-6 overflow-y-auto" style={{ background: 'var(--surface)' }} onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="text-[10px] uppercase tracking-widest text-[var(--muted-2)]">Charter de autoridad</p>
                <h3 className="font-bold text-lg text-[var(--ink)]">{charterRole.name}</h3>
              </div>
              <button onClick={() => setCharterRole(null)} className="text-[var(--muted)]"><X size={20} /></button>
            </div>
            {[
              { t: 'Qué decide', v: charterRole.charter_decides, c: 'var(--accent)' },
              { t: 'Qué bloquea / veta', v: charterRole.charter_blocks, c: 'var(--neg, #ef4444)' },
              { t: 'Qué escala', v: charterRole.charter_escalates, c: 'var(--warn, #d97706)' },
            ].map((sec) => (
              <div key={sec.t} className="mb-4">
                <p className="font-semibold text-sm mb-1" style={{ color: sec.c }}>{sec.t}</p>
                <p className="text-sm text-[var(--ink-2)]">{sec.v || <span className="text-[var(--muted-2)] italic">No definido</span>}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
