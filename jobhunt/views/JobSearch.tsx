import React from 'react';
import { useAppStore } from '../store';
import FilterPanel from '../components/FilterPanel';
import JobCard from '../components/JobCard';
import JobDetail from '../components/JobDetail';
import { AnimatePresence, motion } from 'framer-motion';

const JobSearch: React.FC = () => {
  const { jobs, searchQuery, selectedJobId, selectJob } = useAppStore();

  const filteredJobs = jobs.filter(job => 
    job.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    job.company.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex h-full w-full">
      {/* Left: Filters (Hidden on mobile usually, but keeping simple here) */}
      <div className="hidden xl:block w-72 h-full border-r border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#09090B] overflow-y-auto custom-scrollbar p-5">
        <FilterPanel />
      </div>

      {/* Middle: Job List */}
      <div className={`flex-1 h-full overflow-y-auto bg-zinc-50 dark:bg-zinc-900/50 custom-scrollbar ${selectedJobId ? 'hidden md:block' : 'block'}`}>
        <div className="p-4 md:p-6 space-y-4 max-w-4xl mx-auto">
           <div className="flex items-center justify-between mb-2">
             <h2 className="text-lg font-semibold text-zinc-900 dark:text-white">
                {filteredJobs.length} Jobs Found
             </h2>
             <div className="text-sm text-zinc-500">
                Sorted by <span className="font-medium text-zinc-900 dark:text-zinc-300 cursor-pointer">Best Match</span>
             </div>
           </div>
           
           <div className="space-y-3">
             {filteredJobs.map((job, index) => (
               <motion.div
                 key={job.id}
                 initial={{ opacity: 0, y: 10 }}
                 animate={{ opacity: 1, y: 0 }}
                 transition={{ delay: index * 0.05 }}
               >
                 <JobCard job={job} isSelected={selectedJobId === job.id} onClick={() => selectJob(job.id)} />
               </motion.div>
             ))}
             {filteredJobs.length === 0 && (
                <div className="text-center py-20">
                    <p className="text-zinc-500">No jobs found matching your criteria.</p>
                </div>
             )}
           </div>
        </div>
      </div>

      {/* Right: Job Detail */}
      <div className={`w-full md:w-[600px] lg:w-[700px] h-full bg-white dark:bg-[#09090B] border-l border-zinc-200 dark:border-zinc-800 absolute md:relative z-20 md:z-auto transition-transform duration-300 ${selectedJobId ? 'translate-x-0' : 'translate-x-full md:translate-x-0 md:hidden'}`}>
        {selectedJobId ? (
            <JobDetail jobId={selectedJobId} onClose={() => selectJob(null)} />
        ) : (
            <div className="h-full flex flex-col items-center justify-center text-zinc-400">
                <div className="w-16 h-16 rounded-2xl bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center mb-4">
                    <svg className="w-8 h-8 text-zinc-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                </div>
                <p>Select a job to view details</p>
            </div>
        )}
      </div>
    </div>
  );
};

export default JobSearch;
