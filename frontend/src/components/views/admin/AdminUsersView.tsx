import React, { useEffect, useMemo, useState } from 'react';
import {
  Users, Loader2, Search, Shield, ShieldCheck, Building2, CircleDot, CircleSlash,
} from 'lucide-react';
import apiClient from '../../../api/client';
import { Card } from '../../ui/Card';

// ── API shapes ──────────────────────────────────────────────────────────
interface UserOrg {
  organization_id: number;
  org_name: string;
  organization_type: string;
  role: string;
}

interface FirmUser {
  id: number;
  email: string;
  full_name: string | null;
  user_type: string;
  is_active: boolean;
  is_superadmin: boolean;
  orgs: UserOrg[];
}

const inputStyle: React.CSSProperties = {
  background: 'var(--surface-2)',
  border: '1px solid var(--border)',
  color: 'var(--ink)',
};

export const AdminUsersView: React.FC = () => {
  const [users, setUsers] = useState<FirmUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');

  useEffect(() => {
    apiClient
      .get<FirmUser[]>('/admin/users')
      .then((res) => setUsers(res.data))
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return users;
    return users.filter(
      (u) =>
        u.email.toLowerCase().includes(q) ||
        (u.full_name ?? '').toLowerCase().includes(q),
    );
  }, [users, query]);

  if (loading) {
    return (
      <div className="p-12 flex flex-col items-center justify-center gap-4">
        <Loader2 size={36} className="animate-spin text-[var(--accent)]" />
        <p className="text-sm text-[var(--muted)]">Cargando usuarios...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-3">
          <div
            className="p-2.5 rounded-xl text-white"
            style={{ background: 'linear-gradient(135deg, var(--accent-strong), var(--accent))' }}
          >
            <Users size={24} />
          </div>
          <div>
            <h2 className="font-extrabold text-2xl">Usuarios de la firma</h2>
            <p className="text-sm text-[var(--muted)]">
              {users.length} {users.length === 1 ? 'usuario' : 'usuarios'} en todas las organizaciones
            </p>
          </div>
        </div>
        <div className="relative">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]"
          />
          <input
            type="text"
            placeholder="Buscar por email o nombre..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="pl-9 pr-3 py-2.5 rounded-lg text-sm outline-none w-72"
            style={inputStyle}
          />
        </div>
      </div>

      {/* Table */}
      {filtered.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-[var(--muted)]">
            {users.length === 0
              ? 'Aún no hay usuarios registrados.'
              : 'Ningún usuario coincide con la búsqueda.'}
          </p>
        </div>
      ) : (
        <Card className="p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr
                  className="text-left text-[10px] uppercase tracking-wide font-semibold text-[var(--muted-2)]"
                  style={{ borderBottom: '1px solid var(--border)' }}
                >
                  <th className="px-5 py-3">Usuario</th>
                  <th className="px-5 py-3">Tipo</th>
                  <th className="px-5 py-3">Estado</th>
                  <th className="px-5 py-3">Organizaciones / Rol</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((u) => (
                  <tr
                    key={u.id}
                    style={{ borderBottom: '1px solid var(--border)' }}
                    className="hover:bg-[var(--accent-tint)] transition-colors"
                  >
                    <td className="px-5 py-3 align-top">
                      <div className="font-semibold text-[var(--ink)]">
                        {u.full_name || '—'}
                      </div>
                      <div className="text-xs font-mono text-[var(--muted-2)] break-all">
                        {u.email}
                      </div>
                    </td>
                    <td className="px-5 py-3 align-top">
                      <span className="inline-flex items-center gap-1 text-xs font-medium text-[var(--ink)]">
                        {u.is_superadmin ? (
                          <ShieldCheck size={13} className="text-[var(--accent)]" />
                        ) : (
                          <Shield size={13} className="text-[var(--muted)]" />
                        )}
                        {u.is_superadmin ? 'SUPERADMIN' : u.user_type}
                      </span>
                    </td>
                    <td className="px-5 py-3 align-top">
                      {u.is_active ? (
                        <span className="status-badge status-badge--active inline-flex items-center gap-1">
                          <CircleDot size={11} /> Activo
                        </span>
                      ) : (
                        <span className="status-badge status-badge--pending inline-flex items-center gap-1">
                          <CircleSlash size={11} /> Inactivo
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-3 align-top">
                      {u.orgs.length === 0 ? (
                        <span className="text-xs text-[var(--muted-2)]">Sin organización</span>
                      ) : (
                        <div className="flex flex-col gap-1.5">
                          {u.orgs.map((o) => (
                            <div
                              key={o.organization_id}
                              className="flex items-center gap-2 text-xs"
                            >
                              <Building2 size={12} className="text-[var(--muted)] shrink-0" />
                              <span className="font-medium text-[var(--ink)]">{o.org_name}</span>
                              <span
                                className="text-[10px] font-semibold uppercase tracking-wide px-1.5 py-0.5 rounded"
                                style={{ background: 'var(--accent-tint)', color: 'var(--accent-strong)' }}
                              >
                                {o.role}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </td>
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

export default AdminUsersView;
