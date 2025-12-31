import React, { useEffect, useState } from 'react';
import { useAppStore } from '../store';
import { Search, Briefcase, FileText, LayoutDashboard, X } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';

const CommandPalette: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const { setView } = useAppStore();

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setIsOpen((open) => !open);
      }
      if (e.key === 'Escape') {
          setIsOpen(false);
      }
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  const handleNav = (view: any) => {
      setView(view);
      setIsOpen(false);
      setQuery('');
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh] px-4">
            <motion.div 
                initial={{ opacity: 0 }} 
                animate={{ opacity: 1 }} 
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/50 backdrop-blur-sm" 
                onClick={() => setIsOpen(false)}
            />
            
            <motion.div 
                initial={{ opacity: 0, scale: 0.95 }} 
                animate={{ opacity: 1, scale: 1 }} 
                exit={{ opacity: 0, scale: 0.95 }}
                className="w-full max-w-lg bg-white dark:bg-[#18181B] rounded-xl shadow-2xl border border-zinc-200 dark:border-zinc-800 overflow-hidden relative z-50"
            >
                <div className="flex items-center px-4 py-3 border-b border-zinc-100 dark:border-zinc-800">
                    <Search className="text-zinc-400" size={20} />
                    <input 
                        className="flex-1 bg-transparent border-none outline-none px-3 text-zinc-900 dark:text-white placeholder-zinc-400"
                        placeholder="Type a command or search..."
                        autoFocus
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                    />
                    <button onClick={() => setIsOpen(false)} className="text-zinc-400 hover:text-zinc-600">
                        <X size={16} />
                    </button>
                </div>
                
                <div className="max-h-[300px] overflow-y-auto p-2">
                    <div className="text-xs font-semibold text-zinc-400 px-2 py-1 mb-1">Navigation</div>
                    <button onClick={() => handleNav('dashboard')} className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-700 dark:text-zinc-200 text-sm">
                        <LayoutDashboard size={18} /> Dashboard
                    </button>
                    <button onClick={() => handleNav('search')} className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-700 dark:text-zinc-200 text-sm">
                        <Search size={18} /> Search Jobs
                    </button>
                    <button onClick={() => handleNav('resume')} className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-700 dark:text-zinc-200 text-sm">
                        <FileText size={18} /> My Resume
                    </button>
                    <button onClick={() => handleNav('applications')} className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-700 dark:text-zinc-200 text-sm">
                        <Briefcase size={18} /> Applications
                    </button>
                </div>
                
                <div className="px-4 py-2 bg-zinc-50 dark:bg-zinc-900 border-t border-zinc-100 dark:border-zinc-800 flex justify-between text-xs text-zinc-400">
                    <span>Pro Tip: Use arrows to navigate</span>
                    <span>ESC to close</span>
                </div>
            </motion.div>
        </div>
    </AnimatePresence>
  );
};

export default CommandPalette;
