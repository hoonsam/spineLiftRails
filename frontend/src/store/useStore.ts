import { create } from 'zustand';
import type { Project, Layer, User } from '../types/index';

interface AppState {
  // Auth
  user: User | null;
  token: string | null;
  setAuth: (user: User | null, token: string | null) => void;
  
  // Projects
  projects: Project[];
  currentProject: Project | null;
  setProjects: (projects: Project[]) => void;
  setCurrentProject: (project: Project | null) => void;
  addProject: (project: Project) => void;
  updateProject: (id: string, updates: Partial<Project>) => void;
  
  // Layers
  layers: Layer[];
  currentLayer: Layer | null;
  setLayers: (layers: Layer[]) => void;
  setCurrentLayer: (layer: Layer | null) => void;
  updateLayer: (id: string, updates: Partial<Layer>) => void;
  
  // UI State
  isLoading: boolean;
  setLoading: (loading: boolean) => void;
}

export const useStore = create<AppState>((set) => ({
  // Auth
  user: null,
  token: localStorage.getItem('token'),
  setAuth: (user, token) => {
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
    set({ user, token });
  },
  
  // Projects
  projects: [],
  currentProject: null,
  setProjects: (projects) => set({ projects }),
  setCurrentProject: (project) => set({ currentProject: project }),
  addProject: (project) => set((state) => ({ 
    projects: [...state.projects, project] 
  })),
  updateProject: (id, updates) => set((state) => ({
    projects: state.projects.map(p => p.id === id ? { ...p, ...updates } : p),
    currentProject: state.currentProject?.id === id 
      ? { ...state.currentProject, ...updates } 
      : state.currentProject
  })),
  
  // Layers
  layers: [],
  currentLayer: null,
  setLayers: (layers) => set({ layers }),
  setCurrentLayer: (layer) => set({ currentLayer: layer }),
  updateLayer: (id, updates) => set((state) => ({
    layers: state.layers.map(l => l.id === id ? { ...l, ...updates } : l),
    currentLayer: state.currentLayer?.id === id 
      ? { ...state.currentLayer, ...updates } 
      : state.currentLayer
  })),
  
  // UI State
  isLoading: false,
  setLoading: (loading) => set({ isLoading: loading }),
}));