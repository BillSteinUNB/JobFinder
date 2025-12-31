import React from 'react';
import { Filter, ChevronDown } from 'lucide-react';

const FilterPanel: React.FC = () => {
  return (
    <div className="space-y-8">
        <div className="flex items-center justify-between">
            <h3 className="font-semibold text-zinc-900 dark:text-white flex items-center gap-2">
                <Filter size={16} /> Filters
            </h3>
            <button className="text-xs text-primary-600 hover:text-primary-700">Clear All</button>
        </div>

        {/* Location */}
        <div className="space-y-3">
            <h4 className="text-sm font-medium text-zinc-700 dark:text-zinc-300">Location</h4>
            <label className="flex items-center gap-2 text-sm text-zinc-600 dark:text-zinc-400 cursor-pointer">
                <input type="checkbox" className="rounded border-zinc-300 text-primary-600 focus:ring-primary-500" defaultChecked />
                Remote
            </label>
            <label className="flex items-center gap-2 text-sm text-zinc-600 dark:text-zinc-400 cursor-pointer">
                <input type="checkbox" className="rounded border-zinc-300 text-primary-600 focus:ring-primary-500" />
                San Francisco, CA
            </label>
            <label className="flex items-center gap-2 text-sm text-zinc-600 dark:text-zinc-400 cursor-pointer">
                <input type="checkbox" className="rounded border-zinc-300 text-primary-600 focus:ring-primary-500" />
                New York, NY
            </label>
        </div>

        {/* Salary */}
        <div className="space-y-3">
            <h4 className="text-sm font-medium text-zinc-700 dark:text-zinc-300">Min Salary</h4>
            <input type="range" min="50" max="300" step="10" defaultValue="120" className="w-full h-1 bg-zinc-200 dark:bg-zinc-700 rounded-lg appearance-none cursor-pointer" />
            <div className="flex justify-between text-xs text-zinc-500 font-mono">
                <span>$50k</span>
                <span>$120k+</span>
                <span>$300k</span>
            </div>
        </div>

        {/* Job Type */}
        <div className="space-y-3">
            <h4 className="text-sm font-medium text-zinc-700 dark:text-zinc-300">Job Type</h4>
             <label className="flex items-center gap-2 text-sm text-zinc-600 dark:text-zinc-400 cursor-pointer">
                <input type="checkbox" className="rounded border-zinc-300 text-primary-600 focus:ring-primary-500" defaultChecked />
                Full-time
            </label>
            <label className="flex items-center gap-2 text-sm text-zinc-600 dark:text-zinc-400 cursor-pointer">
                <input type="checkbox" className="rounded border-zinc-300 text-primary-600 focus:ring-primary-500" />
                Contract
            </label>
        </div>

        {/* Experience */}
        <div className="space-y-3">
            <h4 className="text-sm font-medium text-zinc-700 dark:text-zinc-300">Experience</h4>
            <div className="flex flex-wrap gap-2">
                {['Entry', 'Mid', 'Senior', 'Staff'].map(level => (
                    <button key={level} className={`px-3 py-1 text-xs rounded-full border transition-colors ${level === 'Senior' ? 'bg-primary-50 border-primary-200 text-primary-700 dark:bg-primary-500/20 dark:border-primary-500/30 dark:text-primary-300' : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-600 dark:text-zinc-400 hover:border-zinc-300'}`}>
                        {level}
                    </button>
                ))}
            </div>
        </div>
    </div>
  );
};

export default FilterPanel;
