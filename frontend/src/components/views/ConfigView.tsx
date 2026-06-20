import React, { useEffect, useMemo, useState } from 'react';
import { Card } from '../ui/Card';
import {
  Settings, Loader2, ShieldAlert, Save, Check, Lock,
  Cpu, Database, Gauge, Plug, KeyRound,
} from 'lucide-react';
import apiClient from '../../api/client';
import { useAuthStore } from '../../store/authStore';

interface AppSetting {
  id: number;
  key: string;
  value: string | null;
  category: string | null;
  description: string | null;
  updated_by: number | null;
  created_at: string;
  updated_at: string;
}

const MASK = '****';

const CATEGORY_META: Record<string, { label: string; icon: any }> = {
  AI: { label: 'Inteligencia Artificial', icon: Cpu },
  RAG: { label: 'RAG / Recuperación', icon: Database },
  LIMITS: { label: 'Límites', icon: Gauge },
  INTEGRATIONS: { label: 'Integraciones', icon: Plug },
  OTHER: { label: 'Otros', icon: Settings },
};

const SECRET_HINTS = ['KEY', 'SECRET', 'TOKEN', 'PASSWORD'];
const isSecret = (key: string) => SECRET_HINTS.some((h) => key.toUpperCase().includes(h));

export const ConfigView: React.FC = () => {
  const user = useAuthStore((s) => s.user);

  const [settings, setSettings] = useState<AppSetting[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Local edits keyed by setting key (only fields the user has touched).
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [savingKey, setSavingKey] = useState<string | null>(null);
  const [savedKey, setSavedKey] = useState<string | null>(null);

  const fetchSettings = async () => {
    const res = await apiClient.get('/settings');
    setSettings(res.data);
  };

  useEffect(() => {
    if (!user?.is_superadmin) {
      setLoading(false);
      return;
    }
    (async () => {
      try {
        await fetchSettings();
      } catch (e: any) {
        setError(e?.response?.data?.detail || 'No se pudieron cargar las configuraciones');
      } finally {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.is_superadmin]);

  const grouped = useMemo(() => {
    const buckets: Record<string, AppSetting[]> = {};
    for (const s of settings) {
      const cat = s.category && CATEGORY_META[s.category] ? s.category : 'OTHER';
      (buckets[cat] ||= []).push(s);
    }
    return buckets;
  }, [settings]);

  if (!user?.is_superadmin) {
    return (
      <Card className="p-8 text-center max-w-md mx-auto mt-8">
        <ShieldAlert className="mx-auto mb-3 text-[var(--neg,#ef4444)]" size={32} />
        <h3 className="font-bold text-lg text-[var(--ink)]">Acceso restringido</h3>
        <p className="text-sm text-[var(--muted)] mt-1">
          Esta sección es exclusiva para superadministradores de la plataforma.
        </p>
      </Card>
    );
  }

  if (loading) {
    return (
      <div className="p-8 flex justify-center">
        <Loader2 className="animate-spin text-[var(--accent)]" />
      </div>
    );
  }

  const handleSave = async (s: AppSetting) => {
    const draft = drafts[s.key];
    if (draft === undefined) return;
    setSavingKey(s.key);
    setError(null);
    try {
      await apiClient.put(`/settings/${encodeURIComponent(s.key)}`, {
        key: s.key,
        value: draft,
        category: s.category,
        description: s.description,
      });
      await fetchSettings();
      setDrafts((d) => {
        const next = { ...d };
        delete next[s.key];
        return next;
      });
      setSavedKey(s.key);
      setTimeout(() => setSavedKey((k) => (k === s.key ? null : k)), 1500);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'No se pudo guardar la configuración');
    } finally {
      setSavingKey(null);
    }
  };

  const categories = Object.keys(grouped).sort((a, b) => {
    const order = ['AI', 'RAG', 'LIMITS', 'INTEGRATIONS', 'OTHER'];
    return order.indexOf(a) - order.indexOf(b);
  });

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-1">
        <h2 className="font-bold text-2xl flex items-center gap-2">
          <Settings className="text-[var(--accent)]" /> Configuración de plataforma
        </h2>
        <p className="text-sm text-[var(--muted)]">
          Ajustes globales de IA, RAG, límites e integraciones. Solo superadministradores.
        </p>
      </div>

      {error && (
        <div
          className="px-4 py-3 rounded-lg text-sm"
          style={{ background: 'var(--neg-tint, rgba(239,68,68,0.1))', color: 'var(--neg, #ef4444)' }}
        >
          {error}
        </div>
      )}

      {settings.length === 0 && (
        <Card className="p-8 text-center">
          <Settings className="mx-auto mb-3 text-[var(--muted-2)]" size={28} />
          <p className="text-sm text-[var(--muted)]">
            No hay configuraciones guardadas todavía.
          </p>
        </Card>
      )}

      {categories.map((cat) => {
        const meta = CATEGORY_META[cat] || CATEGORY_META.OTHER;
        const Icon = meta.icon;
        return (
          <div key={cat}>
            <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
              <Icon size={18} className="text-[var(--accent)]" /> {meta.label}
            </h3>
            <Card className="p-0 overflow-hidden">
              <div className="divide-y divide-[var(--border)]">
                {grouped[cat].map((s) => {
                  const secret = isSecret(s.key);
                  const masked = secret && s.value === MASK;
                  const draft = drafts[s.key];
                  const inputValue =
                    draft !== undefined ? draft : masked ? '' : (s.value ?? '');
                  const dirty = draft !== undefined;
                  return (
                    <div key={s.id} className="p-4 flex flex-col gap-2">
                      <div className="flex items-center gap-2">
                        <code className="text-sm font-semibold text-[var(--ink)]">{s.key}</code>
                        {secret && (
                          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold text-[var(--muted)] bg-[var(--surface-2)]">
                            <KeyRound size={10} /> SECRETO
                          </span>
                        )}
                      </div>
                      {s.description && (
                        <p className="text-xs text-[var(--muted)]">{s.description}</p>
                      )}
                      <div className="flex items-center gap-2">
                        <div className="relative flex-1">
                          {masked && draft === undefined && (
                            <Lock
                              size={14}
                              className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted-2)]"
                            />
                          )}
                          <input
                            type={secret ? 'password' : 'text'}
                            value={inputValue}
                            placeholder={masked ? 'Valor oculto · escribe para reemplazar' : ''}
                            onChange={(e) =>
                              setDrafts((d) => ({ ...d, [s.key]: e.target.value }))
                            }
                            className={`w-full rounded-md border border-[var(--border)] bg-[var(--surface-2)] text-sm text-[var(--ink)] py-2 ${
                              masked && draft === undefined ? 'pl-8' : 'pl-3'
                            } pr-3 focus:outline-none focus:border-[var(--accent)]`}
                          />
                        </div>
                        <button
                          type="button"
                          disabled={!dirty || savingKey === s.key}
                          onClick={() => handleSave(s)}
                          className="inline-flex items-center gap-1.5 px-3 py-2 rounded-md text-xs font-semibold text-white transition-colors disabled:opacity-40"
                          style={{ background: 'var(--accent)' }}
                        >
                          {savingKey === s.key ? (
                            <Loader2 size={14} className="animate-spin" />
                          ) : savedKey === s.key ? (
                            <Check size={14} />
                          ) : (
                            <Save size={14} />
                          )}
                          {savedKey === s.key ? 'Guardado' : 'Guardar'}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>
          </div>
        );
      })}
    </div>
  );
};
