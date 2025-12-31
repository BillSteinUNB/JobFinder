import React from 'react';
import { Job } from '../types';
import { MapPin, DollarSign, Clock } from 'lucide-react';

interface JobCardProps {
  job: Job;
  isSelected: boolean;
  onClick: () => void;
}

const JobCard: React.FC<JobCardProps> = ({ job, isSelected, onClick }) => {
  // Format salary
  const salary = job.salaryMin || job.salaryMax 
    ? `$${((job.salaryMin || 0) / 1000).toFixed(0)}k - $${((job.salaryMax || 0) / 1000).toFixed(0)}k`
    : 'Salary not listed';
  
  // Format relative time
  const getRelativeTime = (dateStr: string) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return '1d ago';
    if (diffDays < 7) return `${diffDays}d ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`;
    return `${Math.floor(diffDays / 30)}mo ago`;
  };

  return (
    <div 
        onClick={onClick}
        className={`p-4 rounded-xl border transition-all cursor-pointer relative group
        ${isSelected 
            ? 'bg-primary-50 dark:bg-primary-500/10 border-primary-500 ring-1 ring-primary-500' 
            : 'bg-white dark:bg-[#18181B] border-zinc-200 dark:border-zinc-800 hover:border-primary-300 dark:hover:border-primary-700/50 hover:shadow-md'
        }`}
    >
        <div className="flex items-start justify-between mb-3">
            <div className="flex gap-3">
                <img src={job.company.logo} alt={job.company.name} className="w-10 h-10 rounded-lg object-cover bg-white" />
                <div>
                    <h3 className={`font-semibold text-base ${isSelected ? 'text-primary-700 dark:text-primary-300' : 'text-zinc-900 dark:text-zinc-100'}`}>
                        {job.title}
                    </h3>
                    <p className="text-sm text-zinc-500 dark:text-zinc-400">{job.company.name}</p>
                </div>
            </div>
            <div className="flex flex-col items-end">
                <div className={`text-xs font-bold px-2 py-1 rounded-md mb-1.5 ${
                    job.matchScore >= 90 ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300' :
                    job.matchScore >= 70 ? 'bg-primary-100 text-primary-700 dark:bg-primary-500/20 dark:text-primary-300' :
                    'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300'
                }`}>
                    {job.matchScore}% Match
                </div>
                <span className="text-xs text-zinc-400">{getRelativeTime(job.postedAt)}</span>
            </div>
        </div>

        <div className="flex items-center gap-4 text-xs text-zinc-500 dark:text-zinc-400 mb-4">
            <div className="flex items-center gap-1">
                <MapPin size={14} />
                <span>{job.location}</span>
            </div>
            <div className="flex items-center gap-1">
                <DollarSign size={14} />
                <span className="font-mono">{salary}</span>
            </div>
            <div className="flex items-center gap-1">
                <Clock size={14} />
                <span>{job.type}</span>
            </div>
        </div>

        <div className="flex flex-wrap gap-2">
            {job.skills.slice(0, 4).map(skill => (
                <span key={skill} className="px-2 py-1 bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 text-xs rounded border border-zinc-200 dark:border-zinc-700">
                    {skill}
                </span>
            ))}
            {job.skills.length > 4 && (
                <span className="px-2 py-1 text-xs text-zinc-400">+{job.skills.length - 4}</span>
            )}
        </div>
        
        {/* Hover Actions */}
        <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity hidden sm:block">
            {/* Can add quick actions here */}
        </div>
    </div>
  );
};

export default JobCard;
