import { create } from 'zustand';
import { ViewState, Job, Application, ResumeData } from './types';
import { MOCK_JOBS, MOCK_APPLICATIONS, MOCK_RESUME } from './constants';

interface AppState {
  currentView: ViewState;
  jobs: Job[];
  applications: Application[];
  resume: ResumeData;
  savedJobIds: Set<string>;
  searchQuery: string;
  selectedJobId: string | null;
  isSidebarCollapsed: boolean;
  theme: 'light' | 'dark';
  
  // Actions
  setView: (view: ViewState) => void;
  toggleSidebar: () => void;
  toggleTheme: () => void;
  setSearchQuery: (query: string) => void;
  selectJob: (id: string | null) => void;
  saveJob: (id: string) => void;
  updateApplicationStatus: (id: string, status: Application['status']) => void;
  addApplication: (jobId: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  currentView: 'dashboard',
  jobs: MOCK_JOBS,
  applications: MOCK_APPLICATIONS,
  resume: MOCK_RESUME,
  savedJobIds: new Set(MOCK_APPLICATIONS.filter(a => a.status === 'saved').map(a => a.jobId)),
  searchQuery: '',
  selectedJobId: null,
  isSidebarCollapsed: false,
  theme: 'light', // Initial theme

  setView: (view) => set({ currentView: view }),
  toggleSidebar: () => set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),
  toggleTheme: () => set((state) => {
    const newTheme = state.theme === 'light' ? 'dark' : 'light';
    if (newTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    return { theme: newTheme };
  }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  selectJob: (id) => set({ selectedJobId: id }),
  saveJob: (id) => set((state) => {
    const newSaved = new Set(state.savedJobIds);
    if (newSaved.has(id)) {
      newSaved.delete(id);
    } else {
      newSaved.add(id);
    }
    return { savedJobIds: newSaved };
  }),
  updateApplicationStatus: (id, status) => set((state) => ({
    applications: state.applications.map(app => app.id === id ? { ...app, status } : app)
  })),
  addApplication: (jobId) => set((state) => {
     const job = state.jobs.find(j => j.id === jobId);
     if (!job) return state;
     const newApp: Application = {
         id: `a${Date.now()}`,
         jobId,
         job,
         status: 'applied',
         appliedAt: new Date().toISOString(),
         updatedAt: new Date().toISOString(),
         notes: ''
     };
     return { applications: [...state.applications, newApp] };
  })
}));
