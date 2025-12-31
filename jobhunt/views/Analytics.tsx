import React from 'react';
import { useAnalytics } from '../hooks';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area, CartesianGrid, Cell } from 'recharts';
import { Loader2, AlertCircle, BarChart3 } from 'lucide-react';

const Analytics: React.FC = () => {
  const { data: analytics, isLoading, error } = useAnalytics();

  // Loading state
  if (isLoading) {
    return (
      <div className="h-full overflow-y-auto p-6 md:p-10 custom-scrollbar">
        <div className="h-8 w-56 bg-zinc-200 dark:bg-zinc-800 rounded animate-pulse mb-8" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <div className="bg-white dark:bg-[#18181B] p-6 rounded-xl border border-zinc-200 dark:border-zinc-800 h-80 animate-pulse" />
          <div className="bg-white dark:bg-[#18181B] p-6 rounded-xl border border-zinc-200 dark:border-zinc-800 h-80 animate-pulse" />
        </div>
        <div className="bg-white dark:bg-[#18181B] p-6 rounded-xl border border-zinc-200 dark:border-zinc-800 h-64 animate-pulse" />
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
          <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-2">Failed to Load Analytics</h3>
          <p className="text-zinc-500 max-w-sm">
            {error.message || 'An error occurred while fetching analytics data.'}
          </p>
        </div>
      </div>
    );
  }

  // No data state
  if (!analytics) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center p-8">
          <div className="w-16 h-16 bg-zinc-100 dark:bg-zinc-800 rounded-full flex items-center justify-center mx-auto mb-4">
            <BarChart3 size={32} className="text-zinc-400" />
          </div>
          <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-2">No Analytics Yet</h3>
          <p className="text-zinc-500 max-w-sm">
            Start applying to jobs to see your analytics and insights.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-6 md:p-10 custom-scrollbar">
      <h1 className="text-2xl font-bold text-zinc-900 dark:text-white mb-8">Analytics & Insights</h1>
      
      {/* Summary Stats */}
      {(analytics.totalJobs !== undefined || analytics.totalApplications !== undefined) && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-white dark:bg-[#18181B] p-4 rounded-xl border border-zinc-200 dark:border-zinc-800">
            <p className="text-sm text-zinc-500 mb-1">Total Jobs</p>
            <p className="text-2xl font-bold text-zinc-900 dark:text-white">{analytics.totalJobs || 0}</p>
          </div>
          <div className="bg-white dark:bg-[#18181B] p-4 rounded-xl border border-zinc-200 dark:border-zinc-800">
            <p className="text-sm text-zinc-500 mb-1">Applications</p>
            <p className="text-2xl font-bold text-zinc-900 dark:text-white">{analytics.totalApplications || 0}</p>
          </div>
          <div className="bg-white dark:bg-[#18181B] p-4 rounded-xl border border-zinc-200 dark:border-zinc-800">
            <p className="text-sm text-zinc-500 mb-1">Avg Match Score</p>
            <p className="text-2xl font-bold text-zinc-900 dark:text-white">
              {analytics.avgMatchScore ? `${Math.round(analytics.avgMatchScore)}%` : 'N/A'}
            </p>
          </div>
        </div>
      )}
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Application Funnel */}
        {analytics.funnel && analytics.funnel.length > 0 && (
          <div className="bg-white dark:bg-[#18181B] p-6 rounded-xl border border-zinc-200 dark:border-zinc-800">
            <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-6">Application Funnel</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart layout="vertical" data={analytics.funnel} margin={{ left: 20 }}>
                  <XAxis type="number" hide />
                  <YAxis 
                    dataKey="stage" 
                    type="category" 
                    width={80} 
                    tick={{ fill: '#71717A', fontSize: 12 }} 
                    axisLine={false} 
                    tickLine={false} 
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#18181B', 
                      border: 'none', 
                      borderRadius: '8px', 
                      color: '#fff' 
                    }}
                    cursor={{ fill: 'transparent' }}
                  />
                  <Bar dataKey="count" radius={[0, 4, 4, 0]} barSize={32}>
                    {analytics.funnel.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill || '#6366F1'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Activity Over Time */}
        {analytics.applicationsOverTime && analytics.applicationsOverTime.length > 0 && (
          <div className="bg-white dark:bg-[#18181B] p-6 rounded-xl border border-zinc-200 dark:border-zinc-800">
            <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-6">Applications Last 7 Days</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={analytics.applicationsOverTime}>
                  <defs>
                    <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366F1" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#6366F1" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#27272A" />
                  <XAxis 
                    dataKey="date" 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fill: '#71717A', fontSize: 12 }} 
                    dy={10} 
                  />
                  <YAxis 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fill: '#71717A', fontSize: 12 }} 
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#18181B', 
                      border: 'none', 
                      borderRadius: '8px', 
                      color: '#fff' 
                    }} 
                  />
                  <Area 
                    type="monotone" 
                    dataKey="count" 
                    stroke="#6366F1" 
                    strokeWidth={3} 
                    fillOpacity={1} 
                    fill="url(#colorCount)" 
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>

      {/* Skills Analysis */}
      {analytics.skillsMatch && analytics.skillsMatch.length > 0 && (
        <div className="bg-white dark:bg-[#18181B] p-6 rounded-xl border border-zinc-200 dark:border-zinc-800">
          <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-6">Skill Match Analysis</h3>
          <div className="space-y-4">
            {analytics.skillsMatch.map(skill => (
              <div key={skill.name}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium text-zinc-700 dark:text-zinc-200">{skill.name}</span>
                  <span className="text-zinc-500">{Math.round(skill.score)}% Market Demand</span>
                </div>
                <div className="w-full bg-zinc-100 dark:bg-zinc-800 h-2 rounded-full overflow-hidden">
                  <div 
                    className="h-full rounded-full transition-all duration-1000" 
                    style={{ 
                      width: `${skill.score}%`,
                      backgroundColor: skill.score > 80 ? '#10B981' : skill.score > 50 ? '#6366F1' : '#F59E0B'
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state when no chart data */}
      {(!analytics.funnel || analytics.funnel.length === 0) && 
       (!analytics.applicationsOverTime || analytics.applicationsOverTime.length === 0) &&
       (!analytics.skillsMatch || analytics.skillsMatch.length === 0) && (
        <div className="bg-white dark:bg-[#18181B] p-12 rounded-xl border border-zinc-200 dark:border-zinc-800 text-center">
          <BarChart3 size={48} className="text-zinc-300 mx-auto mb-4" />
          <h3 className="font-semibold text-zinc-900 dark:text-white mb-2">No Data Available</h3>
          <p className="text-zinc-500 text-sm max-w-md mx-auto">
            Analytics will appear here as you search for jobs, upload your resume, and track applications.
          </p>
        </div>
      )}
    </div>
  );
};

export default Analytics;
