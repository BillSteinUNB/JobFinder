import React from 'react';
import { useApplications, useUpdateApplication } from '../hooks';
import { Application, ApplicationStatus } from '../types';
import { MoreHorizontal, Plus, Loader2, AlertCircle, Inbox } from 'lucide-react';
import { motion } from 'framer-motion';

const STATUS_COLUMNS: { id: ApplicationStatus; label: string; color: string }[] = [
  { id: 'saved', label: 'Saved', color: 'bg-zinc-500' },
  { id: 'applied', label: 'Applied', color: 'bg-primary-500' },
  { id: 'screening', label: 'Screening', color: 'bg-amber-500' },
  { id: 'interview', label: 'Interview', color: 'bg-purple-500' },
  { id: 'offer', label: 'Offer', color: 'bg-emerald-500' },
];

const Applications: React.FC = () => {
  const { data, isLoading, error } = useApplications();
  const updateMutation = useUpdateApplication();

  const applications = data?.applications || [];

  const getAppsByStatus = (status: ApplicationStatus) => 
    applications.filter(a => a.status === status);

  const handleDragStart = (e: React.DragEvent, id: string) => {
    e.dataTransfer.setData('applicationId', id);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent, status: ApplicationStatus) => {
    e.preventDefault();
    const id = e.dataTransfer.getData('applicationId');
    if (id) {
      updateMutation.mutate({ 
        applicationId: id, 
        data: { status } 
      });
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="h-full flex flex-col p-6 overflow-hidden">
        <div className="flex items-center justify-between mb-6 shrink-0">
          <div className="h-8 w-32 bg-zinc-200 dark:bg-zinc-800 rounded animate-pulse" />
          <div className="h-10 w-40 bg-zinc-200 dark:bg-zinc-800 rounded animate-pulse" />
        </div>
        <div className="flex-1 flex gap-6 overflow-hidden">
          {STATUS_COLUMNS.map(col => (
            <div 
              key={col.id}
              className="w-80 h-full rounded-xl bg-zinc-50 dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800 animate-pulse"
            />
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center p-8">
          <div className="w-16 h-16 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle size={32} className="text-red-500" />
          </div>
          <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-2">Failed to Load Applications</h3>
          <p className="text-zinc-500 max-w-sm">
            {error.message || 'An error occurred while fetching applications.'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col p-6 overflow-hidden">
      <div className="flex items-center justify-between mb-6 shrink-0">
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-white flex items-center gap-2">
          Pipeline
          {updateMutation.isPending && (
            <Loader2 size={18} className="animate-spin text-primary-500" />
          )}
        </h1>
        <button className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2">
          <Plus size={16} /> Add Application
        </button>
      </div>

      {applications.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center p-8">
            <div className="w-16 h-16 bg-zinc-100 dark:bg-zinc-800 rounded-full flex items-center justify-center mx-auto mb-4">
              <Inbox size={32} className="text-zinc-400" />
            </div>
            <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-2">No Applications Yet</h3>
            <p className="text-zinc-500 max-w-sm">
              Start by searching for jobs and saving the ones you're interested in.
            </p>
          </div>
        </div>
      ) : (
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
                      <div className={`w-2 h-2 rounded-full ${col.color}`} />
                      <span className="font-semibold text-sm text-zinc-700 dark:text-zinc-200">{col.label}</span>
                      <span className="bg-white dark:bg-zinc-800 text-zinc-500 text-xs px-2 py-0.5 rounded-full border border-zinc-200 dark:border-zinc-700">
                        {apps.length}
                      </span>
                    </div>
                    <button className="text-zinc-400 hover:text-zinc-600">
                      <MoreHorizontal size={16} />
                    </button>
                  </div>

                  <div className="flex-1 overflow-y-auto p-3 space-y-3 custom-scrollbar">
                    {apps.map(app => (
                      <ApplicationCard 
                        key={app.id} 
                        app={app} 
                        onDragStart={handleDragStart}
                      />
                    ))}
                    
                    {apps.length === 0 && (
                      <div className="text-center py-8 text-zinc-400 text-sm">
                        Drop applications here
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

interface ApplicationCardProps {
  app: Application;
  onDragStart: (e: React.DragEvent, id: string) => void;
}

const ApplicationCard: React.FC<ApplicationCardProps> = ({ app, onDragStart }) => {
  // Format relative time
  const getRelativeTime = (dateStr: string) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return '1d';
    if (diffDays < 7) return `${diffDays}d`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)}w`;
    return `${Math.floor(diffDays / 30)}mo`;
  };

  return (
    <motion.div 
      layoutId={app.id}
      draggable
      onDragStart={(e) => onDragStart(e as unknown as React.DragEvent, app.id)}
      className="bg-white dark:bg-[#18181B] p-4 rounded-lg border border-zinc-200 dark:border-zinc-800 shadow-sm hover:shadow-md cursor-move group"
    >
      <div className="flex justify-between items-start mb-2">
        <div className="flex gap-2">
          {app.job.company.logo ? (
            <img src={app.job.company.logo} className="w-6 h-6 rounded bg-zinc-50" alt="" />
          ) : (
            <div className="w-6 h-6 rounded bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center">
              <span className="text-xs font-medium text-zinc-500">
                {app.job.company.name.charAt(0)}
              </span>
            </div>
          )}
          <span className="text-xs font-semibold text-zinc-900 dark:text-white truncate max-w-[120px]">
            {app.job.company.name}
          </span>
        </div>
        <span className="text-[10px] text-zinc-400">
          {getRelativeTime(app.updatedAt)}
        </span>
      </div>
      <h4 className="font-medium text-sm text-zinc-900 dark:text-white mb-1 line-clamp-1">
        {app.job.title}
      </h4>
      <p className="font-mono text-xs text-zinc-500 dark:text-zinc-400 mb-3">
        ${((app.job.salaryMin || 0) / 1000).toFixed(0)}k
      </p>
      
      {app.nextStep && (
        <div className="bg-primary-50 dark:bg-primary-900/10 text-primary-700 dark:text-primary-300 text-xs p-2 rounded flex items-center gap-2">
          <div className="w-1.5 h-1.5 bg-primary-500 rounded-full animate-pulse" />
          {app.nextStep}
        </div>
      )}
      
      {app.notes && !app.nextStep && (
        <p className="text-xs text-zinc-400 line-clamp-2 mt-2">{app.notes}</p>
      )}
    </motion.div>
  );
};

export default Applications;
