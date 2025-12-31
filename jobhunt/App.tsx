import React, { useEffect } from 'react';
import { useAppStore } from './store';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import Dashboard from './views/Dashboard';
import JobSearch from './views/JobSearch';
import ResumeView from './views/ResumeView';
import Applications from './views/Applications';
import Analytics from './views/Analytics';
import Settings from './views/Settings';
import CommandPalette from './components/CommandPalette';
import { AnimatePresence, motion } from 'framer-motion';

const App: React.FC = () => {
  const { currentView, theme } = useAppStore();

  useEffect(() => {
    // Init theme
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  const renderView = () => {
    switch (currentView) {
      case 'dashboard': return <Dashboard />;
      case 'search': return <JobSearch />;
      case 'resume': return <ResumeView />;
      case 'applications': return <Applications />;
      case 'analytics': return <Analytics />;
      case 'settings': return <Settings />;
      default: return <Dashboard />;
    }
  };

  return (
    <div className={`flex h-screen w-full bg-zinc-50 dark:bg-[#09090B] text-zinc-900 dark:text-zinc-50 font-sans transition-colors duration-200`}>
      <Sidebar />
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">
        <TopBar />
        <main className="flex-1 overflow-hidden relative">
           <AnimatePresence mode="wait">
             <motion.div
                key={currentView}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2, ease: "easeInOut" }}
                className="h-full w-full"
             >
               {renderView()}
             </motion.div>
           </AnimatePresence>
        </main>
      </div>
      <CommandPalette />
    </div>
  );
};

export default App;
