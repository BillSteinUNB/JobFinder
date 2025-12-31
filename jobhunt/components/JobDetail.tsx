import React from 'react';
import { useAppStore } from '../store';
import { X, ExternalLink, Bookmark, CheckCircle, ThumbsDown, Share2, Building2, Users, Globe } from 'lucide-react';
import { motion } from 'framer-motion';

interface JobDetailProps {
  jobId: string;
  onClose: () => void;
}

const JobDetail: React.FC<JobDetailProps> = ({ jobId, onClose }) => {
  const { jobs, savedJobIds, saveJob, addApplication } = useAppStore();
  const job = jobs.find(j => j.id === jobId);

  if (!job) return null;

  const isSaved = savedJobIds.has(job.id);
  const salary = `$${(job.salaryMin / 1000).toFixed(0)}k - $${(job.salaryMax / 1000).toFixed(0)}k`;

  return (
    <div className="h-full flex flex-col relative bg-white dark:bg-[#09090B]">
      {/* Header Actions */}
      <div className="h-14 px-4 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between shrink-0">
         <button onClick={onClose} className="p-2 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg md:hidden">
             <X size={20} className="text-zinc-500" />
         </button>
         <div className="flex gap-2 ml-auto">
             <button className="p-2 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg text-zinc-500 transition-colors">
                 <Share2 size={18} />
             </button>
             <button onClick={() => saveJob(job.id)} className={`p-2 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg transition-colors ${isSaved ? 'text-amber-500' : 'text-zinc-500'}`}>
                 <Bookmark size={18} fill={isSaved ? "currentColor" : "none"} />
             </button>
         </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
         {/* Header */}
         <div className="mb-8">
             <div className="w-16 h-16 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white p-2 mb-4 flex items-center justify-center">
                 <img src={job.company.logo} alt={job.company.name} className="w-full h-full object-contain rounded" />
             </div>
             <h1 className="text-2xl font-bold text-zinc-900 dark:text-white mb-2">{job.title}</h1>
             <div className="flex items-center gap-2 text-zinc-500 dark:text-zinc-400 text-sm mb-4">
                 <Building2 size={16} />
                 <span className="font-medium text-zinc-900 dark:text-zinc-200">{job.company.name}</span>
                 <span>•</span>
                 <span>{job.location}</span>
                 <span>•</span>
                 <span>{job.type}</span>
             </div>

             <div className="flex gap-3">
                 <button 
                    onClick={() => {
                        addApplication(job.id);
                        alert('Application Started!');
                    }}
                    className="flex-1 bg-primary-600 hover:bg-primary-700 text-white font-medium py-2.5 px-4 rounded-lg transition-colors flex items-center justify-center gap-2 shadow-lg shadow-primary-500/20"
                 >
                     <ExternalLink size={18} />
                     Apply Now
                 </button>
                 <button className="px-4 py-2.5 border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 rounded-lg font-medium text-zinc-700 dark:text-zinc-300 transition-colors">
                     Not Interested
                 </button>
             </div>
         </div>

         <div className="space-y-8">
             {/* Match Analysis */}
             <section className="bg-zinc-50 dark:bg-zinc-900/50 rounded-xl p-5 border border-zinc-100 dark:border-zinc-800">
                 <div className="flex items-center justify-between mb-4">
                     <h3 className="font-semibold text-zinc-900 dark:text-white flex items-center gap-2">
                         <span className="w-2 h-6 bg-primary-500 rounded-full"></span>
                         Match Analysis
                     </h3>
                     <span className={`text-xl font-bold ${
                         job.matchScore >= 90 ? 'text-emerald-500' : 'text-primary-500'
                     }`}>{job.matchScore}%</span>
                 </div>
                 
                 <div className="space-y-3">
                     <div className="flex items-center justify-between text-sm">
                         <span className="text-zinc-500">Skills Match</span>
                         <span className="text-zinc-900 dark:text-white font-medium">8/10</span>
                     </div>
                     <div className="w-full bg-zinc-200 dark:bg-zinc-800 h-2 rounded-full overflow-hidden">
                         <div className="bg-emerald-500 h-full rounded-full" style={{ width: '80%' }}></div>
                     </div>
                     
                     <div className="grid grid-cols-2 gap-2 mt-4">
                         {job.matchedSkills.slice(0, 6).map(skill => (
                             <div key={skill.name} className="flex items-center gap-2 text-sm">
                                 {skill.match ? (
                                     <CheckCircle size={14} className="text-emerald-500 shrink-0" />
                                 ) : (
                                     <div className="w-3.5 h-3.5 rounded-full border border-zinc-300 dark:border-zinc-600 shrink-0"></div>
                                 )}
                                 <span className={skill.match ? 'text-zinc-700 dark:text-zinc-200' : 'text-zinc-400'}>
                                     {skill.name}
                                 </span>
                             </div>
                         ))}
                     </div>
                 </div>
             </section>

             {/* Job Description */}
             <section>
                 <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-3">About the Role</h3>
                 <p className="text-zinc-600 dark:text-zinc-400 leading-relaxed mb-4">
                     {job.description}
                 </p>
                 
                 <h4 className="font-medium text-zinc-900 dark:text-white mb-2 mt-6">Requirements</h4>
                 <ul className="space-y-2 mb-6">
                     {job.requirements.map((req, i) => (
                         <li key={i} className="flex items-start gap-2 text-zinc-600 dark:text-zinc-400 text-sm">
                             <div className="w-1.5 h-1.5 rounded-full bg-primary-500 mt-1.5 shrink-0"></div>
                             {req}
                         </li>
                     ))}
                 </ul>

                 <h4 className="font-medium text-zinc-900 dark:text-white mb-2 mt-6">Compensation & Benefits</h4>
                 <div className="p-4 rounded-lg bg-emerald-50 dark:bg-emerald-900/10 border border-emerald-100 dark:border-emerald-900/20 mb-4">
                     <p className="font-mono text-emerald-700 dark:text-emerald-400 font-semibold text-lg">{salary}</p>
                     <p className="text-xs text-emerald-600 dark:text-emerald-500/70 mt-1">Base salary range (estimated)</p>
                 </div>
                 <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                     {job.benefits.map((benefit, i) => (
                         <li key={i} className="text-sm text-zinc-600 dark:text-zinc-400 flex items-center gap-2">
                             <CheckCircle size={14} className="text-zinc-400" />
                             {benefit}
                         </li>
                     ))}
                 </ul>
             </section>

             {/* Company Info */}
             <section className="border-t border-zinc-100 dark:border-zinc-800 pt-6">
                 <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-4">About {job.company.name}</h3>
                 <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                     <div className="flex items-center gap-2 text-zinc-500">
                         <Users size={16} />
                         <span>{job.company.size} employees</span>
                     </div>
                     <div className="flex items-center gap-2 text-zinc-500">
                         <Globe size={16} />
                         <a href={`https://${job.company.website}`} target="_blank" rel="noreferrer" className="text-primary-600 hover:underline">
                             {job.company.website}
                         </a>
                     </div>
                 </div>
             </section>
         </div>
      </div>
    </div>
  );
};

export default JobDetail;
