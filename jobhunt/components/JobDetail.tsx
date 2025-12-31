import React from 'react';
import { useJob, useLabelJob, useCreateApplication } from '../hooks';
import { X, ExternalLink, Bookmark, CheckCircle, Share2, Building2, Users, Globe, Loader2, AlertCircle, ThumbsDown } from 'lucide-react';

interface JobDetailProps {
  jobId: string;
  onClose: () => void;
}

const JobDetail: React.FC<JobDetailProps> = ({ jobId, onClose }) => {
  const { data: job, isLoading, error } = useJob(jobId);
  const labelMutation = useLabelJob();
  const applyMutation = useCreateApplication();

  // Loading state
  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center bg-white dark:bg-[#09090B]">
        <div className="text-center">
          <Loader2 size={32} className="animate-spin text-primary-500 mx-auto mb-3" />
          <p className="text-zinc-500">Loading job details...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !job) {
    return (
      <div className="h-full flex items-center justify-center bg-white dark:bg-[#09090B]">
        <div className="text-center p-6">
          <AlertCircle size={32} className="text-red-500 mx-auto mb-3" />
          <h3 className="font-semibold text-zinc-900 dark:text-white mb-2">Failed to load job</h3>
          <p className="text-zinc-500 text-sm">{error?.message || 'Job not found'}</p>
        </div>
      </div>
    );
  }

  const handleSave = () => {
    labelMutation.mutate({ jobId: job.id, label: 1 });
  };

  const handleReject = () => {
    labelMutation.mutate({ jobId: job.id, label: 0 });
  };

  const handleApply = () => {
    applyMutation.mutate(job.id, {
      onSuccess: () => {
        // Open job URL if available
        if (job.url) {
          window.open(job.url, '_blank');
        }
      },
    });
  };

  const salary = job.salaryMin || job.salaryMax 
    ? `$${((job.salaryMin || 0) / 1000).toFixed(0)}k - $${((job.salaryMax || 0) / 1000).toFixed(0)}k`
    : 'Not specified';

  const matchedCount = job.matchedSkills?.filter(s => s.match).length || 0;
  const totalSkillsCount = job.matchedSkills?.length || 0;

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
          <button 
            onClick={handleSave}
            disabled={labelMutation.isPending}
            className="p-2 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg text-zinc-500 hover:text-amber-500 transition-colors disabled:opacity-50"
          >
            <Bookmark size={18} />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
        {/* Header */}
        <div className="mb-8">
          <div className="w-16 h-16 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white p-2 mb-4 flex items-center justify-center">
            {job.company.logo ? (
              <img src={job.company.logo} alt={job.company.name} className="w-full h-full object-contain rounded" />
            ) : (
              <Building2 size={24} className="text-zinc-400" />
            )}
          </div>
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-white mb-2">{job.title}</h1>
          <div className="flex items-center gap-2 text-zinc-500 dark:text-zinc-400 text-sm mb-4 flex-wrap">
            <Building2 size={16} />
            <span className="font-medium text-zinc-900 dark:text-zinc-200">{job.company.name}</span>
            <span>•</span>
            <span>{job.location}</span>
            <span>•</span>
            <span>{job.type}</span>
            {job.isRemote && (
              <>
                <span>•</span>
                <span className="text-emerald-600 dark:text-emerald-400">Remote</span>
              </>
            )}
          </div>

          <div className="flex gap-3">
            <button 
              onClick={handleApply}
              disabled={applyMutation.isPending}
              className="flex-1 bg-primary-600 hover:bg-primary-700 text-white font-medium py-2.5 px-4 rounded-lg transition-colors flex items-center justify-center gap-2 shadow-lg shadow-primary-500/20 disabled:opacity-50"
            >
              {applyMutation.isPending ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <ExternalLink size={18} />
              )}
              Apply Now
            </button>
            <button 
              onClick={handleReject}
              disabled={labelMutation.isPending}
              className="px-4 py-2.5 border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 rounded-lg font-medium text-zinc-700 dark:text-zinc-300 transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              <ThumbsDown size={16} />
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
                job.matchScore >= 90 ? 'text-emerald-500' : 
                job.matchScore >= 70 ? 'text-primary-500' : 
                'text-amber-500'
              }`}>
                {Math.round(job.matchScore)}%
              </span>
            </div>
            
            {totalSkillsCount > 0 && (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-zinc-500">Skills Match</span>
                  <span className="text-zinc-900 dark:text-white font-medium">
                    {matchedCount}/{totalSkillsCount}
                  </span>
                </div>
                <div className="w-full bg-zinc-200 dark:bg-zinc-800 h-2 rounded-full overflow-hidden">
                  <div 
                    className="bg-emerald-500 h-full rounded-full transition-all" 
                    style={{ width: `${(matchedCount / totalSkillsCount) * 100}%` }}
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-2 mt-4">
                  {job.matchedSkills.slice(0, 8).map(skill => (
                    <div key={skill.name} className="flex items-center gap-2 text-sm">
                      {skill.match ? (
                        <CheckCircle size={14} className="text-emerald-500 shrink-0" />
                      ) : (
                        <div className="w-3.5 h-3.5 rounded-full border border-zinc-300 dark:border-zinc-600 shrink-0" />
                      )}
                      <span className={skill.match ? 'text-zinc-700 dark:text-zinc-200' : 'text-zinc-400'}>
                        {skill.name}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Score Breakdown */}
            {job.breakdown && (
              <div className="mt-4 pt-4 border-t border-zinc-200 dark:border-zinc-700">
                <h4 className="text-sm font-medium text-zinc-600 dark:text-zinc-400 mb-3">Score Breakdown</h4>
                <div className="space-y-2">
                  {Object.entries(job.breakdown).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between text-sm">
                      <span className="text-zinc-500 capitalize">{key.replace(/_/g, ' ')}</span>
                      <span className="font-mono text-zinc-900 dark:text-white">{(value * 100).toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Explanation */}
            {job.explanation && (
              <div className="mt-4 pt-4 border-t border-zinc-200 dark:border-zinc-700">
                <p className="text-sm text-zinc-600 dark:text-zinc-400">{job.explanation}</p>
              </div>
            )}
          </section>

          {/* Job Description */}
          <section>
            <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-3">About the Role</h3>
            <div 
              className="text-zinc-600 dark:text-zinc-400 leading-relaxed mb-4 prose prose-sm dark:prose-invert max-w-none"
              dangerouslySetInnerHTML={{ __html: job.description.replace(/\n/g, '<br/>') }}
            />
            
            {job.requirements && job.requirements.length > 0 && (
              <>
                <h4 className="font-medium text-zinc-900 dark:text-white mb-2 mt-6">Requirements</h4>
                <ul className="space-y-2 mb-6">
                  {job.requirements.map((req, i) => (
                    <li key={i} className="flex items-start gap-2 text-zinc-600 dark:text-zinc-400 text-sm">
                      <div className="w-1.5 h-1.5 rounded-full bg-primary-500 mt-1.5 shrink-0" />
                      {req}
                    </li>
                  ))}
                </ul>
              </>
            )}

            <h4 className="font-medium text-zinc-900 dark:text-white mb-2 mt-6">Compensation & Benefits</h4>
            <div className="p-4 rounded-lg bg-emerald-50 dark:bg-emerald-900/10 border border-emerald-100 dark:border-emerald-900/20 mb-4">
              <p className="font-mono text-emerald-700 dark:text-emerald-400 font-semibold text-lg">{salary}</p>
              <p className="text-xs text-emerald-600 dark:text-emerald-500/70 mt-1">Base salary range (estimated)</p>
            </div>
            
            {job.benefits && job.benefits.length > 0 && (
              <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {job.benefits.map((benefit, i) => (
                  <li key={i} className="text-sm text-zinc-600 dark:text-zinc-400 flex items-center gap-2">
                    <CheckCircle size={14} className="text-zinc-400" />
                    {benefit}
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* Company Info */}
          <section className="border-t border-zinc-100 dark:border-zinc-800 pt-6">
            <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-4">About {job.company.name}</h3>
            <div className="grid grid-cols-2 gap-4 text-sm mb-4">
              {job.company.size && (
                <div className="flex items-center gap-2 text-zinc-500">
                  <Users size={16} />
                  <span>{job.company.size} employees</span>
                </div>
              )}
              {job.company.website && (
                <div className="flex items-center gap-2 text-zinc-500">
                  <Globe size={16} />
                  <a 
                    href={job.company.website.startsWith('http') ? job.company.website : `https://${job.company.website}`} 
                    target="_blank" 
                    rel="noreferrer" 
                    className="text-primary-600 hover:underline"
                  >
                    {job.company.website}
                  </a>
                </div>
              )}
            </div>
            
            {/* External Link */}
            {job.url && (
              <a 
                href={job.url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 text-sm text-primary-600 hover:text-primary-700"
              >
                <ExternalLink size={14} />
                View Original Posting
              </a>
            )}
          </section>
        </div>
      </div>
    </div>
  );
};

export default JobDetail;
