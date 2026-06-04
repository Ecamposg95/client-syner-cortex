import { create } from 'zustand';
import apiClient from '../api/client';

interface Workspace {
  id: number;
  name: string;
  description: string;
  organization_id: number;
}

interface Document {
  id: number;
  workspace_id: number;
  name: string;
  file_type: string;
  status: string;
  error_message: string | null;
  created_at: string;
}

interface WorkspaceState {
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  documents: Document[];
  isLoading: boolean;
  isUploading: boolean;
  error: string | null;

  fetchWorkspaces: () => Promise<void>;
  selectWorkspace: (workspaceId: number) => void;
  createWorkspace: (name: string, description?: string) => Promise<boolean>;
  fetchDocuments: () => Promise<void>;
  uploadDocument: (file: File) => Promise<boolean>;
  deleteDocument: (docId: number) => Promise<boolean>;
}

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
  workspaces: [],
  activeWorkspace: null,
  documents: [],
  isLoading: false,
  isUploading: false,
  error: null,

  fetchWorkspaces: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.get('/workspaces');
      const workspaces = response.data;
      set({ workspaces, isLoading: false });

      // Restore active workspace from session storage or select first
      const savedId = sessionStorage.getItem('active_workspace_id');
      if (savedId && workspaces.some((w: any) => w.id === parseInt(savedId))) {
        get().selectWorkspace(parseInt(savedId));
      } else if (workspaces.length > 0) {
        get().selectWorkspace(workspaces[0].id);
      } else {
        set({ activeWorkspace: null, documents: [] });
      }
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.response?.data?.detail || 'Failed to load workspaces.'
      });
    }
  },

  selectWorkspace: (workspaceId) => {
    const { workspaces } = get();
    const active = workspaces.find((w) => w.id === workspaceId) || null;
    if (active) {
      sessionStorage.setItem('active_workspace_id', workspaceId.toString());
      set({ activeWorkspace: active });
      // Fetch documents for the active workspace
      get().fetchDocuments();
    }
  },

  createWorkspace: async (name, description) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.post('/workspaces', { name, description });
      const newWorkspace = response.data;
      set((state) => ({
        workspaces: [...state.workspaces, newWorkspace],
        isLoading: false
      }));
      // Auto-select newly created workspace
      get().selectWorkspace(newWorkspace.id);
      return true;
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.response?.data?.detail || 'Failed to create workspace.'
      });
      return false;
    }
  },

  fetchDocuments: async () => {
    const { activeWorkspace } = get();
    if (!activeWorkspace) return;

    set({ isLoading: true });
    try {
      const response = await apiClient.get('/documents', {
        params: { workspace_id: activeWorkspace.id }
      });
      set({ documents: response.data, isLoading: false });
    } catch (err) {
      set({ isLoading: false });
      console.error('Failed to load documents:', err);
    }
  },

  uploadDocument: async (file) => {
    const { activeWorkspace } = get();
    if (!activeWorkspace) return false;

    set({ isUploading: true, error: null });
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      await apiClient.post('/documents/upload', formData, {
        params: { workspace_id: activeWorkspace.id },
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      set({ isUploading: false });
      // Refresh documents list
      await get().fetchDocuments();
      return true;
    } catch (err: any) {
      set({
        isUploading: false,
        error: err.response?.data?.detail || 'Document upload failed.'
      });
      return false;
    }
  },

  deleteDocument: async (docId) => {
    set({ isLoading: true });
    try {
      await apiClient.delete(`/documents/${docId}`);
      set((state) => ({
        documents: state.documents.filter((d) => d.id !== docId),
        isLoading: false
      }));
      return true;
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.response?.data?.detail || 'Failed to delete document.'
      });
      return false;
    }
  }
}));
