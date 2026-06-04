import { create } from 'zustand';
import apiClient from '../api/client';

interface ChatMessage {
  id: number;
  session_id: number;
  sender: 'user' | 'assistant';
  content: string;
  sources: { document_id: number; document_name: string; snippet: string }[] | null;
  created_at: string;
}

interface ChatSession {
  id: number;
  workspace_id: number;
  title: string;
  created_at: string;
}

interface ChatState {
  sessions: ChatSession[];
  activeSession: ChatSession | null;
  messages: ChatMessage[];
  isLoading: boolean;
  isSending: boolean;
  error: string | null;

  fetchSessions: (workspaceId: number) => Promise<void>;
  selectSession: (session: ChatSession | null) => Promise<void>;
  createSession: (workspaceId: number, title: string) => Promise<ChatSession | null>;
  sendMessage: (content: string) => Promise<boolean>;
}

export const useChatStore = create<ChatState>((set, get) => ({
  sessions: [],
  activeSession: null,
  messages: [],
  isLoading: false,
  isSending: false,
  error: null,

  fetchSessions: async (workspaceId) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.get('/chat/sessions', {
        params: { workspace_id: workspaceId }
      });
      set({ sessions: response.data, isLoading: false });
      
      // Auto-select first session if none selected
      const { activeSession } = get();
      if (!activeSession && response.data.length > 0) {
        get().selectSession(response.data[0]);
      }
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.response?.data?.detail || 'Failed to fetch sessions.'
      });
    }
  },

  selectSession: async (session) => {
    set({ activeSession: session, error: null });
    if (!session) {
      set({ messages: [] });
      return;
    }

    set({ isLoading: true });
    try {
      const response = await apiClient.get(`/chat/sessions/${session.id}/messages`);
      set({ messages: response.data, isLoading: false });
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.response?.data?.detail || 'Failed to load messages.'
      });
    }
  },

  createSession: async (workspaceId, title) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.post('/chat/sessions', { title }, {
        params: { workspace_id: workspaceId }
      });
      const newSession = response.data;
      set((state) => ({
        sessions: [newSession, ...state.sessions],
        isLoading: false
      }));
      await get().selectSession(newSession);
      return newSession;
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.response?.data?.detail || 'Failed to create chat session.'
      });
      return null;
    }
  },

  sendMessage: async (content) => {
    const { activeSession } = get();
    if (!activeSession) return false;

    set({ isSending: true, error: null });

    // Optimistically insert user message in UI
    const tempUserMsg: ChatMessage = {
      id: Date.now(), // temporary id
      session_id: activeSession.id,
      sender: 'user',
      content,
      sources: null,
      created_at: new Date().toISOString()
    };
    
    set((state) => ({
      messages: [...state.messages, tempUserMsg]
    }));

    try {
      const response = await apiClient.post(`/chat/sessions/${activeSession.id}/messages`, { content });
      const assistantMsg = response.data;
      
      // Replace optimistic messages with actual list from server (which ensures stable IDs)
      set((state) => {
        // filter out temp message and append server-verified messages
        const filtered = state.messages.filter((m) => m.id !== tempUserMsg.id);
        return {
          messages: [...filtered, assistantMsg],
          isSending: false
        };
      });
      return true;
    } catch (err: any) {
      set((state) => ({
        // remove temp message on error
        messages: state.messages.filter((m) => m.id !== tempUserMsg.id),
        isSending: false,
        error: err.response?.data?.detail || 'Failed to send message.'
      }));
      return false;
    }
  }
}));
