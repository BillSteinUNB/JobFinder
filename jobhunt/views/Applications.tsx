import React from 'react';
import { useAppStore } from '../store';
import { Application, ApplicationStatus } from '../types';
import { MoreHorizontal, Plus } from 'lucide-react';
import { motion } from 'framer-motion';

const STATUS_COLUMNS: { id: ApplicationStatus; label: string; color: string }[] = [
  { id: 'saved', label: 'Saved', color: 'bg-zinc-500' },
  { id: 'applied', label: 'Applied', color: 'bg-primary-500' },
  { id: 'screening', label: 'Screening', color: 'bg-amber-500' },
  { id: 'interview', label: 'Interview', color: 'bg-purple-500' },
  { id: 'offer', label: 'Offer', color: 'bg-emerald-500' },
];

const Applications: React.FC = () => {
  const { applications, updateApplicationStatus } = useAppStore();

  const getAppsByStatus = (status: ApplicationStatus) => applications.filter(a => a.status === status);

  const handleDragStart = (e: React.DragEvent, id: string) => {
      e.dataTransfer.setData('applicationId', id);
  };

  const handleDragOver = (e: React.DragEvent) => {
      e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent, status: ApplicationStatus) => {
      const id = e.dataTransfer.getData('applicationId');
      if (id) {
          updateApplicationStatus(id, status);
      }
  };

  return (
    <div className="h-full flex flex-col p-6 overflow-hidden">
      <div className="flex items-center justify-between mb-6 shrink-0">
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">Pipeline</h1>
          <button className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2">
              <Plus size={16} /> Add Application
          </button>
      </div>

      <div className="flex-1 overflow-x-auto overflow-y-hidden pb-4">
          <div className="flex gap-6 h-full min-w-max">
              {STATUS_COLUMNS.map(col => {
                  const apps = getAppsByStatus(col.id);
                  return (
                      <div 
                        key={col.id} 
                        className="w-80 flex flex-col h-full rounded-xl bg-zinc-50 dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800"
                        onDragOver={handleDragOver}
                        onDrop={(e) => handleDrop(e, col.id)}
                      >
                          <div className="p-3 flex items-center justify-between border-b border-zinc-200 dark:border-zinc-800 bg-zinc-100 dark:bg-zinc-900 rounded-t-xl">
                              <div className="flex items-center gap-2">
                                  <div className={`w-2 h-2 rounded-full ${col.color}`}></div>
                                  <span className="font-semibold text-sm text-zinc-700 dark:text-zinc-200">{col.label}</span>
                                  <span className="bg-white dark:bg-zinc-800 text-zinc-500 text-xs px-2 py-0.5 rounded-full border border-zinc-200 dark:border-zinc-700">{apps.length}</span>
                              </div>
                              <button className="text-zinc-400 hover:text-zinc-600"><MoreHorizontal size={16} /></button>
                          </div>

                          <div className="flex-1 overflow-y-auto p-3 space-y-3 custom-scrollbar">
                              {apps.map(app => (
                                  <motion.div 
                                    layoutId={app.id}
                                    key={app.id}
                                    draggable
                                    onDragStart={(e) => handleDragStart(e as any, app.id)}
                                    className="bg-white dark:bg-[#18181B] p-4 rounded-lg border border-zinc-200 dark:border-zinc-800 shadow-sm hover:shadow-md cursor-move group"
                                  >
                                      <div className="flex justify-between items-start mb-2">
                                          <div className="flex gap-2">
                                              <img src={app.job.company.logo} className="w-6 h-6 rounded bg-zinc-50" />
                                              <span className="text-xs font-semibold text-zinc-900 dark:text-white truncate max-w-[120px]">{app.job.company.name}</span>
                                          </div>
                                          <span className="text-[10px] text-zinc-400">2d</span>
                                      </div>
                                      <h4 className="font-medium text-sm text-zinc-900 dark:text-white mb-1 line-clamp-1">{app.job.title}</h4>
                                      <p className="font-mono text-xs text-zinc-500 dark:text-zinc-400 mb-3">${(app.job.salaryMin/1000).toFixed(0)}k</p>
                                      
                                      {app.nextStep && (
                                          <div className="bg-primary-50 dark:bg-primary-900/10 text-primary-700 dark:text-primary-300 text-xs p-2 rounded flex items-center gap-2">
                                              <div className="w-1.5 h-1.5 bg-primary-500 rounded-full animate-pulse"></div>
                                              {app.nextStep}
                                          </div>
                                      )}
                                  </motion.div>
                              ))}
                          </div>
                      </div>
                  );
              })}
          </div>
      </div>
    </div>
  );
};

export default Applications;
