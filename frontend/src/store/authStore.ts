import { create } from 'zustand';
import apiClient from '../api/client';

interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superadmin: boolean;
  user_type: 'SYNER_CREW' | 'CLIENT_USER';
  must_change_password?: boolean;
}

interface Organization {
  id: number;
  name: string;
  slug: string;
}

interface OrgUserRelation {
  id: number;
  role: string;
  organization: Organization;
}

interface AuthState {
  user: User | null;
  organizations: OrgUserRelation[];
  currentOrgRelation: OrgUserRelation | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  login: (email: string, password: string) => Promise<boolean>;
  signup: (email: string, fullName: string, password: string) => Promise<boolean>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  fetchOrganizations: () => Promise<void>;
  selectOrganization: (orgId: number) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  organizations: [],
  currentOrgRelation: null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.post('/auth/login-json', { email, password });
      const { access_token } = response.data;
      localStorage.setItem('access_token', access_token);
      set({ isAuthenticated: true });
      
      // Fetch user profile immediately
      await get().fetchUser();
      // Fetch user organizations
      await get().fetchOrganizations();
      
      set({ isLoading: false });
      return true;
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.response?.data?.detail || 'Authentication failed. Please check your credentials.'
      });
      return false;
    }
  },

  signup: async (email, fullName, password) => {
    set({ isLoading: true, error: null });
    try {
      await apiClient.post('/auth/signup', { email, full_name: fullName, password });
      set({ isLoading: false });
      return true;
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.response?.data?.detail || 'Registration failed. User may already exist.'
      });
      return false;
    }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('active_organization_id');
    set({
      user: null,
      organizations: [],
      currentOrgRelation: null,
      isAuthenticated: false,
      error: null
    });
  },

  fetchUser: async () => {
    try {
      const response = await apiClient.get('/auth/me');
      set({ user: response.data, isAuthenticated: true });
    } catch (err) {
      get().logout();
    }
  },

  fetchOrganizations: async () => {
    try {
      const response = await apiClient.get('/organizations');
      const relations = response.data;
      set({ organizations: relations });

      // Auto-select first org or restore previous selection
      const savedOrgId = localStorage.getItem('active_organization_id');
      if (savedOrgId && relations.some((r: any) => r.organization_id === parseInt(savedOrgId))) {
        get().selectOrganization(parseInt(savedOrgId));
      } else if (relations.length > 0) {
        get().selectOrganization(relations[0].organization_id);
      }
    } catch (err) {
      console.error('Failed to fetch organizations:', err);
    }
  },

  selectOrganization: (orgId) => {
    const { organizations } = get();
    const selected = organizations.find((r) => r.organization_id === orgId) || null;
    
    if (selected) {
      localStorage.setItem('active_organization_id', orgId.toString());
      set({ currentOrgRelation: selected });
      // Trigger a page reload to reset headers/state cleanly
      // window.location.reload(); (handled by routing layout instead for UX)
    } else {
      localStorage.removeItem('active_organization_id');
      set({ currentOrgRelation: null });
    }
  }
}));
