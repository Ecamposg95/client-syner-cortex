import { create } from 'zustand';
import apiClient from '../api/client';

interface DiagnosisDimension {
  id: number;
  name: string;
  rating: number;
  findings: string | null;
  recommendations: string | null;
  swot_analysis: {
    strengths: string[];
    weaknesses: string[];
    opportunities: string[];
    threats: string[];
  } | null;
}

interface Diagnosis {
  id: number;
  workspace_id: number;
  status: string;
  created_at: string;
  dimensions: DiagnosisDimension[];
}

interface RoadmapItem {
  id: number;
  roadmap_id: number;
  title: string;
  description: string | null;
  dimension: string;
  phase: number;
  status: 'TODO' | 'IN_PROGRESS' | 'DONE';
  assigned_to: string | null;
  due_date: string | null;
}

interface Roadmap {
  id: number;
  workspace_id: number;
  diagnosis_id: number;
  created_at: string;
  items: RoadmapItem[];
}

interface DiagnosisState {
  currentDiagnosis: Diagnosis | null;
  currentRoadmap: Roadmap | null;
  isLoading: boolean;
  isSubmitting: boolean;
  error: string | null;

  fetchLatestDiagnosis: (workspaceId: number) => Promise<void>;
  submitDiagnosis: (workspaceId: number, answers: { name: string; rating: number; findings: string; challenges: string }[]) => Promise<boolean>;
  fetchLatestRoadmap: (workspaceId: number) => Promise<void>;
  updateRoadmapItem: (itemId: number, patch: { status?: 'TODO' | 'IN_PROGRESS' | 'DONE'; assigned_to?: string; due_date?: string }) => Promise<boolean>;
}

export const useDiagnosisStore = create<DiagnosisState>((set, get) => ({
  currentDiagnosis: null,
  currentRoadmap: null,
  isLoading: false,
  isSubmitting: false,
  error: null,

  fetchLatestDiagnosis: async (workspaceId) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.get('/diagnoses/latest', {
        params: { workspace_id: workspaceId }
      });
      set({ currentDiagnosis: response.data || null, isLoading: false });
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.response?.data?.detail || 'Failed to fetch latest diagnosis.'
      });
    }
  },

  submitDiagnosis: async (workspaceId, answers) => {
    set({ isSubmitting: true, error: null });
    try {
      const response = await apiClient.post('/diagnoses', { dimensions: answers }, {
        params: { workspace_id: workspaceId }
      });
      set({ currentDiagnosis: response.data, isSubmitting: false });
      
      // Fetch the updated roadmap as well
      await get().fetchLatestRoadmap(workspaceId);
      return true;
    } catch (err: any) {
      set({
        isSubmitting: false,
        error: err.response?.data?.detail || 'Failed to submit 360 diagnosis.'
      });
      return false;
    }
  },

  fetchLatestRoadmap: async (workspaceId) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.get('/roadmaps/latest', {
        params: { workspace_id: workspaceId }
      });
      set({ currentRoadmap: response.data || null, isLoading: false });
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.response?.data?.detail || 'Failed to fetch latest roadmap.'
      });
    }
  },

  updateRoadmapItem: async (itemId, patch) => {
    try {
      const response = await apiClient.patch(`/roadmaps/items/${itemId}`, patch);
      const updatedItem = response.data;
      
      // Update in local state
      set((state) => {
        if (!state.currentRoadmap) return {};
        
        const updatedItems = state.currentRoadmap.items.map((item) =>
          item.id === itemId ? { ...item, ...updatedItem } : item
        );
        
        return {
          currentRoadmap: {
            ...state.currentRoadmap,
            items: updatedItems
          }
        };
      });
      
      return true;
    } catch (err: any) {
      console.error('Failed to update roadmap item:', err);
      return false;
    }
  }
}));
