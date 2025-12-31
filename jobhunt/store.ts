import { create } from 'zustand';
import { ViewState } from './types';

/**
 * UI-only state managed by Zustand.
 * Server data (jobs, applications, resume) is now managed by React Query.
 */
interface AppState {
  // UI State
  currentView: ViewState;
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
}

export const useAppStore = create<AppState>((set) => ({
  // Initial UI State
  currentView: 'dashboard',
  searchQuery: '',
  selectedJobId: null,
  isSidebarCollapsed: false,
  theme: 'light',

  // Actions
  setView: (view) => set({ currentView: view }),
  
  toggleSidebar: () => set((state) => ({ 
    isSidebarCollapsed: !state.isSidebarCollapsed 
  })),
  
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
}));
