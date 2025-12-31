import React from 'react';
import { useAppStore } from '../store';
import { ANALYTICS_DATA } from '../constants';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area, CartesianGrid } from 'recharts';

const Analytics: React.FC = () => {
  return (
    <div className="h-full overflow-y-auto p-6 md:p-10 custom-scrollbar">
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-white mb-8">Analytics & Insights</h1>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            {/* Application Funnel */}
            <div className="bg-white dark:bg-[#18181B] p-6 rounded-xl border border-zinc-200 dark:border-zinc-800">
                <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-6">Application Funnel</h3>
                <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart layout="vertical" data={ANALYTICS_DATA.funnel} margin={{ left: 20 }}>
                            <XAxis type="number" hide />
                            <YAxis dataKey="stage" type="category" width={80} tick={{ fill: '#71717A', fontSize: 12 }} axisLine={false} tickLine={false} />
                            <Tooltip 
                                contentStyle={{ backgroundColor: '#18181B', border: 'none', borderRadius: '8px', color: '#fff' }}
                                cursor={{ fill: 'transparent' }}
                            />
                            <Bar dataKey="count" radius={[0, 4, 4, 0]} barSize={32}>
                                {ANALYTICS_DATA.funnel.map((entry, index) => (
                                    <cell key={`cell-${index}`} fill={entry.fill} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Activity Over Time */}
            <div className="bg-white dark:bg-[#18181B] p-6 rounded-xl border border-zinc-200 dark:border-zinc-800">
                <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-6">Applications Last 7 Days</h3>
                <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={ANALYTICS_DATA.applicationsOverTime}>
                            <defs>
                                <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#6366F1" stopOpacity={0.3}/>
                                    <stop offset="95%" stopColor="#6366F1" stopOpacity={0}/>
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#27272A" />
                            <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: '#71717A', fontSize: 12 }} dy={10} />
                            <YAxis axisLine={false} tickLine={false} tick={{ fill: '#71717A', fontSize: 12 }} />
                            <Tooltip contentStyle={{ backgroundColor: '#18181B', border: 'none', borderRadius: '8px', color: '#fff' }} />
                            <Area type="monotone" dataKey="count" stroke="#6366F1" strokeWidth={3} fillOpacity={1} fill="url(#colorCount)" />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>

        {/* Skills Analysis */}
        <div className="bg-white dark:bg-[#18181B] p-6 rounded-xl border border-zinc-200 dark:border-zinc-800">
            <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-6">Skill Match Analysis</h3>
            <div className="space-y-4">
                {ANALYTICS_DATA.skillsMatch.map(skill => (
                    <div key={skill.name}>
                        <div className="flex justify-between text-sm mb-1">
                            <span className="font-medium text-zinc-700 dark:text-zinc-200">{skill.name}</span>
                            <span className="text-zinc-500">{skill.score}% Market Demand</span>
                        </div>
                        <div className="w-full bg-zinc-100 dark:bg-zinc-800 h-2 rounded-full overflow-hidden">
                            <div 
                                className="h-full rounded-full transition-all duration-1000" 
                                style={{ 
                                    width: `${skill.score}%`,
                                    backgroundColor: skill.score > 80 ? '#10B981' : skill.score > 50 ? '#6366F1' : '#F59E0B'
                                }}
                            ></div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    </div>
  );
};

export default Analytics;
