import React, { useEffect, useState } from 'react';
import { MessageSquare, Send, Trash2, Loader2 } from 'lucide-react';
import apiClient from '../api/client';
import { useAuthStore } from '../store/authStore';

/**
 * CommentThread — reusable polymorphic comment thread.
 *
 * Embed inside ANY view (RACI, reports, roadmap, deliverables …) by passing the
 * object's discriminator + id; the component handles its own loading, posting
 * and deletion against /comments. It does NOT mount itself anywhere — the
 * orchestrator decides where to drop it.
 */
export interface CommentThreadProps {
  objectType: string;
  objectId: number;
}

interface Comment {
  id: number;
  object_type: string;
  object_id: number;
  organization_id: number;
  author_id: number;
  author_name: string | null;
  author_email: string | null;
  content: string;
  created_at: string;
}

const formatDate = (iso: string): string => {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
};

export const CommentThread: React.FC<CommentThreadProps> = ({ objectType, objectId }) => {
  const user = useAuthStore((s) => s.user);
  const isCrew = user?.user_type === 'SYNER_CREW';

  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchComments = async () => {
    try {
      const res = await apiClient.get('/comments', {
        params: { object_type: objectType, object_id: objectId },
      });
      setComments(res.data);
      setError(null);
    } catch (e) {
      console.error(e);
      setError('No se pudieron cargar los comentarios.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    fetchComments();
    // Re-fetch whenever the target object changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [objectType, objectId]);

  const handleSend = async () => {
    const content = draft.trim();
    if (!content || sending) return;
    setSending(true);
    try {
      const res = await apiClient.post('/comments', {
        object_type: objectType,
        object_id: objectId,
        content,
      });
      setComments((prev) => [...prev, res.data]);
      setDraft('');
      setError(null);
    } catch (e) {
      console.error(e);
      setError('No se pudo enviar el comentario.');
    } finally {
      setSending(false);
    }
  };

  const handleDelete = async (id: number) => {
    setDeletingId(id);
    try {
      await apiClient.delete(`/comments/${id}`);
      setComments((prev) => prev.filter((c) => c.id !== id));
      setError(null);
    } catch (e) {
      console.error(e);
      setError('No se pudo borrar el comentario.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const canDelete = (c: Comment): boolean => isCrew || c.author_id === user?.id;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
        color: 'var(--text)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <MessageSquare size={16} style={{ color: 'var(--accent)' }} />
        <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>
          Comentarios{comments.length ? ` (${comments.length})` : ''}
        </span>
      </div>

      {error && (
        <div style={{ color: 'var(--neg, #e5484d)', fontSize: '0.8rem' }}>{error}</div>
      )}

      {/* List / loading / empty */}
      {loading ? (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            color: 'var(--muted)',
            fontSize: '0.85rem',
          }}
        >
          <Loader2 size={14} className="animate-spin" /> Cargando…
        </div>
      ) : comments.length === 0 ? (
        <div style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>
          Aún no hay comentarios. Sé el primero en comentar.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {comments.map((c) => (
            <div
              key={c.id}
              style={{
                border: '1px solid var(--border)',
                borderRadius: '0.5rem',
                padding: '0.5rem 0.75rem',
                background: 'var(--surface, transparent)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '0.5rem',
                  marginBottom: '0.25rem',
                }}
              >
                <span style={{ fontWeight: 600, fontSize: '0.8rem' }}>
                  {c.author_name || c.author_email || `Usuario #${c.author_id}`}
                </span>
                <span
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    color: 'var(--muted)',
                    fontSize: '0.72rem',
                  }}
                >
                  {formatDate(c.created_at)}
                  {canDelete(c) && (
                    <button
                      onClick={() => handleDelete(c.id)}
                      disabled={deletingId === c.id}
                      title="Borrar comentario"
                      style={{
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        color: 'var(--muted)',
                        display: 'flex',
                        alignItems: 'center',
                        padding: 0,
                      }}
                    >
                      {deletingId === c.id ? (
                        <Loader2 size={13} className="animate-spin" />
                      ) : (
                        <Trash2 size={13} />
                      )}
                    </button>
                  )}
                </span>
              </div>
              <div style={{ fontSize: '0.85rem', whiteSpace: 'pre-wrap' }}>{c.content}</div>
            </div>
          ))}
        </div>
      )}

      {/* Composer */}
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <input
          type="text"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Escribe un comentario…"
          disabled={sending}
          style={{
            flex: 1,
            padding: '0.5rem 0.75rem',
            borderRadius: '0.5rem',
            border: '1px solid var(--border)',
            background: 'var(--surface, transparent)',
            color: 'var(--text)',
            fontSize: '0.85rem',
            outline: 'none',
          }}
        />
        <button
          onClick={handleSend}
          disabled={sending || !draft.trim()}
          title="Enviar"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            padding: '0.5rem 0.75rem',
            borderRadius: '0.5rem',
            border: 'none',
            cursor: sending || !draft.trim() ? 'not-allowed' : 'pointer',
            background: 'var(--accent)',
            color: 'var(--accent-contrast, #fff)',
            opacity: sending || !draft.trim() ? 0.6 : 1,
            fontSize: '0.85rem',
          }}
        >
          {sending ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
          Enviar
        </button>
      </div>
    </div>
  );
};

export default CommentThread;
