import React from 'react';
import { useAppStore } from '../store';
import { useJobSearch, useApplications, useResumeProfile, useAnalytics } from '../hooks';
import { ArrowUpRight, TrendingUp, Clock, Calendar, CheckCircle, Briefcase, ChevronRight, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';

const Dashboard: React.FC = () => {
  const { setView } = useAppStore();
  
  // Fetch data from APIs
  const { data: jobsData, isLoading: jobsLoading } = useJobSearch({ limit: 4 });
  const { data: appsData, isLoading: appsLoading } = useApplications();
  const { data: resumeData, isLoading: resumeLoading } = useResumeProfile();
  const { data: analyticsData } = useAnalytics();

  const jobs = jobsData?.jobs || [];
  const applications = appsData?.applications || [];
  
  // Calculate stats
  const savedCount = applications.filter(a => a.status === 'saved').length;
  const appliedCount = applications.filter(a => a.status === 'applied').length;
  const interviewCount = applications.filter(a => ['screening', 'interview'].includes(a.status)).length;
  const avgMatchScore = analyticsData?.avgMatchScore || (jobs.length > 0 
    ? Math.round(jobs.reduce((acc, j) => acc + j.matchScore, 0) / jobs.length)
    : 0);

  // Get upcoming items (applications with nextStep)
  const upcomingApps = applications
    .filter(a => a.nextStep && a.nextStepDate)
    .sort((a, b) => new Date(a.nextStepDate!).getTime() - new Date(b.nextStepDate!).getTime())
    .slice(0, 3);

  const StatCard = ({ label, value, trend, icon: Icon, color, isLoading }: {
    label: string;
    value: string | number;
    trend?: string;
    icon: React.ElementType;
    color: string;
    isLoading?: boolean;
  }) => (
    <div className="bg-white dark:bg-[#18181B] p-6 rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-sm relative overflow-hidden group hover:shadow-md transition-shadow">
      <div className={`absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity ${color}`}>
        <Icon size={64} />
      </div>
      <div className="relative z-10">
        <p className="text-zinc-500 dark:text-zinc-400 text-sm font-medium mb-1">{label}</p>
        {isLoading ? (
          <div className="h-9 w-16 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse" />
        ) : (
          <h3 className="text-3xl font-bold text-zinc-900 dark:text-white font-mono">{value}</h3>
        )}
        {trend && (
          <div className="flex items-center gap-1 mt-2 text-xs font-medium text-emerald-600 dark:text-emerald-400">
            <ArrowUpRight size={14} />
            <span>{trend}</span>
            <span className="text-zinc-400 font-normal ml-1">vs last week</span>
          </div>
        )}
      </div>
    </div>
  );

  const isLoading = jobsLoading || appsLoading || resumeLoading;

  return (
    <div className="h-full overflow-y-auto custom-scrollbar p-6 md:p-10">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Welcome */}
        <div>
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">
            Good {getTimeOfDay()}, {resumeData?.fileName ? 'there' : 'there'} 👋
          </h1>
          <p className="text-zinc-500 dark:text-zinc-400">
            Here's what's happening with your job search today.
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard 
            label="Saved Jobs" 
            value={savedCount} 
            icon={Briefcase} 
            color="text-amber-500" 
            isLoading={appsLoading}
          />
          <StatCard 
            label="Applied" 
            value={appliedCount} 
            icon={CheckCircle} 
            color="text-primary-500" 
            isLoading={appsLoading}
          />
          <StatCard 
            label="Interviews" 
            value={interviewCount} 
            icon={Calendar} 
            color="text-purple-500" 
            isLoading={appsLoading}
          />
          <StatCard 
            label="Match Score" 
            value={`${avgMatchScore}%`} 
            icon={TrendingUp} 
            color="text-emerald-500" 
            isLoading={jobsLoading}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content: Resume & Matches */}
          <div className="lg:col-span-2 space-y-6">
            {/* Resume Status */}
            <div className="bg-white dark:bg-[#18181B] rounded-xl border border-zinc-200 dark:border-zinc-800 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-zinc-900 dark:text-white">Resume Status</h2>
                <button 
                  onClick={() => setView('resume')} 
                  className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                >
                  Manage
                </button>
              </div>
              
              {resumeLoading ? (
                <div className="h-20 bg-zinc-50 dark:bg-zinc-900/50 rounded-lg animate-pulse" />
              ) : resumeData?.fileName ? (
                <div className="flex items-start gap-4 p-4 bg-zinc-50 dark:bg-zinc-900/50 rounded-lg border border-zinc-100 dark:border-zinc-800">
                  <div className="w-10 h-10 bg-emerald-100 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 rounded-lg flex items-center justify-center shrink-0">
                    <CheckCircle size={20} />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-zinc-900 dark:text-white mb-1">
                      Resume uploaded and analyzed
                    </p>
                    <p className="text-xs text-zinc-500 dark:text-zinc-400 mb-2">
                      {resumeData.fileName} • {resumeData.skills?.length || 0} skills detected
                    </p>
                    <div className="flex gap-2 flex-wrap">
                      {resumeData.skills?.slice(0, 4).map(skill => (
                        <span 
                          key={skill}
                          className="inline-flex items-center gap-1 px-2 py-1 rounded bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-xs text-zinc-600 dark:text-zinc-300"
                        >
                          {skill}
                        </span>
                      ))}
                      {(resumeData.skills?.length || 0) > 4 && (
                        <span className="text-xs text-zinc-400">
                          +{resumeData.skills!.length - 4} more
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex items-start gap-4 p-4 bg-amber-50 dark:bg-amber-900/10 rounded-lg border border-amber-100 dark:border-amber-900/20">
                  <div className="w-10 h-10 bg-amber-100 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 rounded-lg flex items-center justify-center shrink-0">
                    <Clock size={20} />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-amber-900 dark:text-amber-200 mb-1">
                      No resume uploaded yet
                    </p>
                    <p className="text-xs text-amber-700 dark:text-amber-300 mb-2">
                      Upload your resume to get personalized job matches
                    </p>
                    <button 
                      onClick={() => setView('resume')}
                      className="text-xs font-medium text-amber-700 dark:text-amber-300 hover:underline"
                    >
                      Upload now →
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Top Matches */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-zinc-900 dark:text-white">Top Matches</h2>
                <button 
                  onClick={() => setView('search')} 
                  className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1"
                >
                  View All <ChevronRight size={14} />
                </button>
              </div>
              
              {jobsLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[1, 2].map(i => (
                    <div key={i} className="h-32 bg-zinc-100 dark:bg-zinc-800 rounded-xl animate-pulse" />
                  ))}
                </div>
              ) : jobs.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {jobs.slice(0, 2).map((job) => (
                    <motion.div 
                      key={job.id} 
                      whileHover={{ scale: 1.02 }}
                      className="p-4 bg-white dark:bg-[#18181B] rounded-xl border border-zinc-200 dark:border-zinc-800 hover:border-primary-300 dark:hover:border-primary-700 transition-colors group cursor-pointer" 
                      onClick={() => setView('search')}
                    >
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex gap-3">
                          {job.company.logo ? (
                            <img src={job.company.logo} className="w-10 h-10 rounded-lg bg-zinc-50" alt="" />
                          ) : (
                            <div className="w-10 h-10 rounded-lg bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center">
                              <span className="font-medium text-zinc-500">{job.company.name.charAt(0)}</span>
                            </div>
                          )}
                          <div>
                            <h3 className="font-semibold text-zinc-900 dark:text-white group-hover:text-primary-600 transition-colors line-clamp-1">
                              {job.title}
                            </h3>
                            <p className="text-xs text-zinc-500">{job.company.name}</p>
                          </div>
                        </div>
                        <span className={`text-xs font-bold px-2 py-1 rounded ${
                          job.matchScore >= 90 
                            ? 'text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20' 
                            : 'text-primary-600 bg-primary-50 dark:bg-primary-900/20'
                        }`}>
                          {Math.round(job.matchScore)}%
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-zinc-500">
                        <span>{job.location}</span>
                        <span>•</span>
                        <span className="font-mono">
                          ${((job.salaryMin || 0) / 1000).toFixed(0)}k+
                        </span>
                      </div>
                    </motion.div>
                  ))}
                </div>
              ) : (
                <div className="p-8 bg-zinc-50 dark:bg-zinc-900/50 rounded-xl border border-zinc-200 dark:border-zinc-800 text-center">
                  <p className="text-zinc-500">
                    {resumeData?.fileName 
                      ? 'No job matches found. Check back later for new listings.'
                      : 'Upload your resume to see personalized job matches.'
                    }
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Sidebar: Upcoming */}
          <div className="space-y-6">
            <div className="bg-white dark:bg-[#18181B] rounded-xl border border-zinc-200 dark:border-zinc-800 p-6 h-full">
              <h2 className="text-lg font-semibold text-zinc-900 dark:text-white mb-4">Upcoming</h2>
              
              {appsLoading ? (
                <div className="space-y-4">
                  {[1, 2].map(i => (
                    <div key={i} className="h-16 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse" />
                  ))}
                </div>
              ) : upcomingApps.length > 0 ? (
                <div className="space-y-6">
                  {upcomingApps.map((app, i) => (
                    <div 
                      key={app.id}
                      className={`relative pl-4 border-l-2 ${i === 0 ? 'border-primary-500' : 'border-zinc-200 dark:border-zinc-700'}`}
                    >
                      <p className={`text-xs font-semibold mb-1 ${i === 0 ? 'text-primary-600' : 'text-zinc-500'}`}>
                        {formatDate(app.nextStepDate!)}
                      </p>
                      <p className="text-sm font-medium text-zinc-900 dark:text-white">{app.nextStep}</p>
                      <p className="text-xs text-zinc-500">
                        {app.job.company.name} • {app.job.title}
                      </p>
                      {i === 0 && (
                        <div className="mt-2 flex gap-2">
                          <button className="text-xs bg-primary-600 text-white px-2 py-1 rounded hover:bg-primary-700">
                            View
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-zinc-500">
                  No upcoming events. Apply to jobs to track your progress.
                </p>
              )}

              <div className="mt-8 pt-6 border-t border-zinc-100 dark:border-zinc-800">
                <h3 className="text-sm font-medium text-zinc-900 dark:text-white mb-3">Quick Actions</h3>
                <div className="space-y-2">
                  <button 
                    onClick={() => setView('search')}
                    className="w-full text-left text-sm text-zinc-600 dark:text-zinc-400 hover:text-primary-600 flex items-center gap-2 py-1"
                  >
                    <Briefcase size={14} />
                    Browse Jobs
                  </button>
                  <button 
                    onClick={() => setView('applications')}
                    className="w-full text-left text-sm text-zinc-600 dark:text-zinc-400 hover:text-primary-600 flex items-center gap-2 py-1"
                  >
                    <Calendar size={14} />
                    View Pipeline
                  </button>
                  <button 
                    onClick={() => setView('analytics')}
                    className="w-full text-left text-sm text-zinc-600 dark:text-zinc-400 hover:text-primary-600 flex items-center gap-2 py-1"
                  >
                    <TrendingUp size={14} />
                    View Analytics
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

// Helper functions
function getTimeOfDay(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'morning';
  if (hour < 17) return 'afternoon';
  return 'evening';
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffDays = Math.floor((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) {
    return `Today, ${date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}`;
  }
  if (diffDays === 1) {
    return `Tomorrow, ${date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}`;
  }
  return date.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
}

export default Dashboard;
