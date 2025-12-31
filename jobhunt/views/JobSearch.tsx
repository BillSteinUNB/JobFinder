import React from 'react';
import { useAppStore } from '../store';
import { useJobSearch } from '../hooks';
import FilterPanel from '../components/FilterPanel';
import JobCard from '../components/JobCard';
import JobDetail from '../components/JobDetail';
import { AnimatePresence, motion } from 'framer-motion';
import { Loader2, AlertCircle, SearchX } from 'lucide-react';

const JobSearch: React.FC = () => {
  const { searchQuery, selectedJobId, selectJob } = useAppStore();
  
  // Fetch jobs from API
  const { data, isLoading, error, isFetching } = useJobSearch({
    query: searchQuery || undefined,
    limit: 50,
  });

  const jobs = data?.jobs || [];

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="flex h-full w-full">
        <div className="hidden xl:block w-72 h-full border-r border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#09090B] p-5">
          <div className="space-y-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-10 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse" />
            ))}
          </div>
        </div>
        <div className="flex-1 p-6">
          <div className="max-w-4xl mx-auto space-y-4">
            <div className="h-8 w-40 bg-zinc-200 dark:bg-zinc-800 rounded animate-pulse" />
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-32 bg-zinc-100 dark:bg-zinc-800 rounded-xl animate-pulse" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <div className="text-center p-8">
          <div className="w-16 h-16 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle size={32} className="text-red-500" />
          </div>
          <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-2">Failed to Load Jobs</h3>
          <p className="text-zinc-500 max-w-sm">
            {error.message || 'An error occurred while fetching jobs. Please try again.'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full w-full">
      {/* Left: Filters */}
      <div className="hidden xl:block w-72 h-full border-r border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#09090B] overflow-y-auto custom-scrollbar p-5">
        <FilterPanel />
      </div>

      {/* Middle: Job List */}
      <div className={`flex-1 h-full overflow-y-auto bg-zinc-50 dark:bg-zinc-900/50 custom-scrollbar ${selectedJobId ? 'hidden md:block' : 'block'}`}>
        <div className="p-4 md:p-6 space-y-4 max-w-4xl mx-auto">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold text-zinc-900 dark:text-white flex items-center gap-2">
              {data?.total || 0} Jobs Found
              {isFetching && <Loader2 size={16} className="animate-spin text-primary-500" />}
            </h2>
            <div className="text-sm text-zinc-500">
              Sorted by <span className="font-medium text-zinc-900 dark:text-zinc-300 cursor-pointer">Best Match</span>
            </div>
          </div>
          
          <div className="space-y-3">
            <AnimatePresence mode="popLayout">
              {jobs.map((job, index) => (
                <motion.div
                  key={job.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ delay: index * 0.03 }}
                >
                  <JobCard 
                    job={job} 
                    isSelected={selectedJobId === job.id} 
                    onClick={() => selectJob(job.id)} 
                  />
                </motion.div>
              ))}
            </AnimatePresence>
            
            {jobs.length === 0 && (
              <div className="text-center py-20">
                <div className="w-16 h-16 bg-zinc-100 dark:bg-zinc-800 rounded-full flex items-center justify-center mx-auto mb-4">
                  <SearchX size={28} className="text-zinc-400" />
                </div>
                <h3 className="font-medium text-zinc-900 dark:text-white mb-2">No Jobs Found</h3>
                <p className="text-zinc-500 max-w-sm mx-auto">
                  {searchQuery 
                    ? `No jobs matching "${searchQuery}". Try a different search term.`
                    : 'Upload your resume to see personalized job matches, or check back later for new listings.'
                  }
                </p>
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
