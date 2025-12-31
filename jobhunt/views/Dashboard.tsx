import React from 'react';
import { useAppStore } from '../store';
import { ArrowUpRight, TrendingUp, Clock, Calendar, CheckCircle, Briefcase, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';

const Dashboard: React.FC = () => {
  const { jobs, applications, setView, resume } = useAppStore();
  
  const savedCount = useAppStore(state => state.savedJobIds.size);
  const appliedCount = applications.filter(a => a.status === 'applied').length;
  const interviewCount = applications.filter(a => ['phone_screen', 'interview', 'final_round'].includes(a.status)).length;

  const StatCard = ({ label, value, trend, icon: Icon, color }: any) => (
    <div className="bg-white dark:bg-[#18181B] p-6 rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-sm relative overflow-hidden group hover:shadow-md transition-shadow">
      <div className={`absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity ${color}`}>
          <Icon size={64} />
      </div>
      <div className="relative z-10">
          <p className="text-zinc-500 dark:text-zinc-400 text-sm font-medium mb-1">{label}</p>
          <h3 className="text-3xl font-bold text-zinc-900 dark:text-white font-mono">{value}</h3>
          <div className="flex items-center gap-1 mt-2 text-xs font-medium text-emerald-600 dark:text-emerald-400">
            <ArrowUpRight size={14} />
            <span>{trend}</span>
            <span className="text-zinc-400 font-normal ml-1">vs last week</span>
          </div>
      </div>
    </div>
  );

  return (
    <div className="h-full overflow-y-auto custom-scrollbar p-6 md:p-10">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Welcome */}
        <div>
            <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">Good morning, Alex 👋</h1>
            <p className="text-zinc-500 dark:text-zinc-400">Here's what's happening with your job search today.</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard label="Saved Jobs" value={savedCount} trend="+8" icon={Briefcase} color="text-amber-500" />
            <StatCard label="Applied" value={appliedCount} trend="+4" icon={CheckCircle} color="text-primary-500" />
            <StatCard label="Interviews" value={interviewCount} trend="+1" icon={Calendar} color="text-purple-500" />
            <StatCard label="Match Score" value="89%" trend="+2%" icon={TrendingUp} color="text-emerald-500" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Content: Resume & Matches */}
            <div className="lg:col-span-2 space-y-6">
                {/* Resume Status */}
                <div className="bg-white dark:bg-[#18181B] rounded-xl border border-zinc-200 dark:border-zinc-800 p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-lg font-semibold text-zinc-900 dark:text-white">Resume Status</h2>
                        <button onClick={() => setView('resume')} className="text-sm text-primary-600 hover:text-primary-700 font-medium">Manage</button>
                    </div>
                    <div className="flex items-start gap-4 p-4 bg-zinc-50 dark:bg-zinc-900/50 rounded-lg border border-zinc-100 dark:border-zinc-800">
                        <div className="w-10 h-10 bg-emerald-100 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 rounded-lg flex items-center justify-center shrink-0">
                            <CheckCircle size={20} />
                        </div>
                        <div className="flex-1">
                            <p className="text-sm font-medium text-zinc-900 dark:text-white mb-1">Optimized for Senior Frontend roles</p>
                            <p className="text-xs text-zinc-500 dark:text-zinc-400 mb-2">Last parsed: Today, 9:42 AM</p>
                            <div className="flex gap-2">
                                <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-xs text-zinc-600 dark:text-zinc-300">
                                    24 Skills Extracted
                                </span>
                                <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-xs text-zinc-600 dark:text-zinc-300">
                                    6 Years Exp
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Top Matches */}
                <div>
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-lg font-semibold text-zinc-900 dark:text-white">Top Matches</h2>
                        <button onClick={() => setView('search')} className="text-sm text-primary-600 hover:text-primary-700 font-medium">View All</button>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {jobs.slice(0, 2).map((job) => (
                            <div key={job.id} className="p-4 bg-white dark:bg-[#18181B] rounded-xl border border-zinc-200 dark:border-zinc-800 hover:border-primary-300 dark:hover:border-primary-700 transition-colors group cursor-pointer" onClick={() => setView('search')}>
                                <div className="flex justify-between items-start mb-3">
                                    <div className="flex gap-3">
                                        <img src={job.company.logo} className="w-10 h-10 rounded-lg bg-zinc-50" />
                                        <div>
                                            <h3 className="font-semibold text-zinc-900 dark:text-white group-hover:text-primary-600 transition-colors">{job.title}</h3>
                                            <p className="text-xs text-zinc-500">{job.company.name}</p>
                                        </div>
                                    </div>
                                    <span className="text-xs font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 px-2 py-1 rounded">{job.matchScore}%</span>
                                </div>
                                <div className="flex items-center gap-2 text-xs text-zinc-500">
                                    <span>{job.location}</span>
                                    <span>•</span>
                                    <span className="font-mono">${(job.salaryMin/1000).toFixed(0)}k+</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Sidebar: Upcoming */}
            <div className="space-y-6">
                <div className="bg-white dark:bg-[#18181B] rounded-xl border border-zinc-200 dark:border-zinc-800 p-6 h-full">
                    <h2 className="text-lg font-semibold text-zinc-900 dark:text-white mb-4">Upcoming</h2>
                    
                    <div className="space-y-6">
                        <div className="relative pl-4 border-l-2 border-primary-500">
                            <p className="text-xs font-semibold text-primary-600 mb-1">Today, 2:00 PM</p>
                            <p className="text-sm font-medium text-zinc-900 dark:text-white">Phone Screen</p>
                            <p className="text-xs text-zinc-500">Stripe • Senior Frontend</p>
                            <div className="mt-2 flex gap-2">
                                <button className="text-xs bg-primary-600 text-white px-2 py-1 rounded hover:bg-primary-700">Join</button>
                                <button className="text-xs bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 px-2 py-1 rounded">Prep</button>
                            </div>
                        </div>

                        <div className="relative pl-4 border-l-2 border-zinc-200 dark:border-zinc-700">
                            <p className="text-xs font-semibold text-zinc-500 mb-1">Tomorrow, 10:00 AM</p>
                            <p className="text-sm font-medium text-zinc-900 dark:text-white">Tech Interview</p>
                            <p className="text-xs text-zinc-500">Vercel • Staff Eng</p>
                        </div>
                    </div>

                    <div className="mt-8 pt-6 border-t border-zinc-100 dark:border-zinc-800">
                         <h3 className="text-sm font-medium text-zinc-900 dark:text-white mb-3">Recent Activity</h3>
                         <ul className="space-y-3">
                             <li className="text-xs text-zinc-600 dark:text-zinc-400 flex gap-2">
                                 <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0"></div>
                                 Application viewed by Stripe
                             </li>
                             <li className="text-xs text-zinc-600 dark:text-zinc-400 flex gap-2">
                                 <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0"></div>
                                 New match: Linear (92%)
                             </li>
                         </ul>
                    </div>
                </div>
            </div>
        </div>

      </div>
    </div>
  );
};

export default Dashboard;
