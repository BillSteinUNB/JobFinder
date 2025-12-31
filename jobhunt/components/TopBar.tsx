import React from 'react';
import { useAppStore } from '../store';
import { Search, Bell, Moon, Sun, Command } from 'lucide-react';

const TopBar: React.FC = () => {
  const { toggleTheme, theme } = useAppStore();

  return (
    <header className="h-16 px-6 bg-white/80 dark:bg-[#09090B]/80 backdrop-blur-md border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between sticky top-0 z-10">
      
      {/* Search Trigger */}
      <div className="flex-1 max-w-xl">
        <button 
            onClick={() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }))}
            className="w-full flex items-center gap-3 px-4 py-2 bg-zinc-50 dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800 rounded-lg text-sm text-zinc-400 hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors group cursor-text"
        >
            <Search size={16} className="text-zinc-400 group-hover:text-zinc-500" />
            <span className="flex-1 text-left">Search jobs, companies, skills...</span>
            <div className="flex items-center gap-1 text-xs text-zinc-400 bg-zinc-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded border border-zinc-200 dark:border-zinc-700 font-mono">
                <Command size={10} />
                <span>K</span>
            </div>
        </button>
      </div>

      <div className="flex items-center gap-2 ml-4">
        <button 
            className="p-2 text-zinc-400 hover:text-zinc-900 dark:hover:text-white hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-full transition-all relative"
            aria-label="Notifications"
        >
            <Bell size={20} strokeWidth={1.5} />
            <span className="absolute top-2 right-2.5 w-2 h-2 bg-red-500 rounded-full border-2 border-white dark:border-zinc-900"></span>
        </button>

        <div className="h-6 w-px bg-zinc-200 dark:bg-zinc-800 mx-2"></div>

        <button 
            onClick={toggleTheme}
            className="p-2 text-zinc-400 hover:text-zinc-900 dark:hover:text-white hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-full transition-all"
        >
            {theme === 'light' ? <Moon size={20} strokeWidth={1.5} /> : <Sun size={20} strokeWidth={1.5} />}
        </button>
      </div>
    </header>
  );
};

export default TopBar;
