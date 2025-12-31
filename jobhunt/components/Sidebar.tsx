import React from 'react';
import { useAppStore } from '../store';
import { useApplications } from '../hooks';
import { LayoutDashboard, Search, FileText, Briefcase, BarChart2, Settings, ChevronLeft, ChevronRight, HelpCircle } from 'lucide-react';
import { ViewState } from '../types';
import { CURRENT_USER } from '../constants';

const Sidebar: React.FC = () => {
  const { currentView, setView, isSidebarCollapsed, toggleSidebar } = useAppStore();
  const { data: appsData } = useApplications();
  
  const applications = appsData?.applications || [];
  const activeCount = applications.filter(a => ['applied', 'screening', 'interview'].includes(a.status)).length;

  const NavItem = ({ view, icon: Icon, label, badge }: { view: ViewState, icon: any, label: string, badge?: number }) => {
    const isActive = currentView === view;
    return (
      <button
        onClick={() => setView(view)}
        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 group
          ${isActive 
            ? 'bg-primary-500 text-white shadow-md shadow-primary-500/20 font-medium' 
            : 'text-zinc-500 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800 hover:text-zinc-900 dark:hover:text-zinc-100'
          }`}
      >
        <Icon size={20} strokeWidth={1.5} className={isActive ? 'text-white' : ''} />
        {!isSidebarCollapsed && (
          <span className="flex-1 text-left">{label}</span>
        )}
        {!isSidebarCollapsed && badge && (
          <span className={`text-xs px-2 py-0.5 rounded-full ${isActive ? 'bg-white/20 text-white' : 'bg-zinc-200 dark:bg-zinc-700 text-zinc-600 dark:text-zinc-300'}`}>
            {badge}
          </span>
        )}
      </button>
    );
  };

  return (
    <div 
      className={`h-screen bg-white dark:bg-[#09090B] border-r border-zinc-200 dark:border-zinc-800 flex flex-col transition-all duration-300 z-20
        ${isSidebarCollapsed ? 'w-20 items-center' : 'w-64'}
      `}
    >
      <div className="h-16 flex items-center px-6 border-b border-zinc-100 dark:border-zinc-800/50">
        <div className="h-8 w-8 bg-gradient-to-br from-primary-500 to-indigo-600 rounded-lg flex items-center justify-center shrink-0 shadow-lg shadow-indigo-500/20">
            <span className="text-white font-bold text-lg">J</span>
        </div>
        {!isSidebarCollapsed && (
             <span className="ml-3 font-bold text-xl tracking-tight text-zinc-900 dark:text-white">JobHunt</span>
        )}
      </div>

      <div className="flex-1 py-6 px-3 space-y-1 overflow-y-auto">
        <div className={`px-3 mb-2 text-xs font-semibold text-zinc-400 uppercase tracking-wider ${isSidebarCollapsed ? 'hidden' : 'block'}`}>
            Menu
        </div>
        <NavItem view="dashboard" icon={LayoutDashboard} label="Dashboard" />
        <NavItem view="search" icon={Search} label="Job Search" />
        <NavItem view="resume" icon={FileText} label="My Resume" />
        <NavItem view="applications" icon={Briefcase} label="Applications" badge={activeCount} />
        <NavItem view="analytics" icon={BarChart2} label="Analytics" />
      </div>

      <div className="p-3 border-t border-zinc-100 dark:border-zinc-800/50 space-y-1">
         <NavItem view="settings" icon={Settings} label="Settings" />
         <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-zinc-500 hover:text-zinc-900 dark:hover:text-white transition-colors">
            <HelpCircle size={20} strokeWidth={1.5} />
            {!isSidebarCollapsed && <span>Help & Support</span>}
         </button>
      </div>

      <div className={`p-4 border-t border-zinc-100 dark:border-zinc-800/50 flex items-center ${isSidebarCollapsed ? 'justify-center' : 'gap-3'}`}>
          <img src={CURRENT_USER.avatar} alt="User" className="w-9 h-9 rounded-full object-cover ring-2 ring-white dark:ring-zinc-800" />
          {!isSidebarCollapsed && (
              <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-zinc-900 dark:text-white truncate">{CURRENT_USER.name}</p>
                  <p className="text-xs text-zinc-500 truncate">{CURRENT_USER.plan} Plan</p>
              </div>
          )}
          <button 
            onClick={toggleSidebar}
            className={`p-1.5 rounded-md hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-400 transition-colors ${isSidebarCollapsed ? 'absolute -right-3 top-20 bg-white dark:bg-zinc-800 border dark:border-zinc-700 shadow-sm' : ''}`}
          >
            {isSidebarCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={16} />}
          </button>
      </div>
    </div>
  );
};

export default Sidebar;
