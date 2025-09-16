import { JobFilters as JobFiltersType } from '../lib/types';
import { useState } from 'react';

interface JobFiltersProps {
  filters: JobFiltersType;
  onFiltersChange: (filters: JobFiltersType) => void;
}

export default function JobFilters({ filters, onFiltersChange }: JobFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleFilterChange = (key: keyof JobFiltersType, value: string) => {
    onFiltersChange({
      ...filters,
      [key]: value
    });
  };

  return (
    <div className="space-y-4">
      {/* Header with collapsible button for mobile */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white flex items-center">
          <span className="w-2 h-2 bg-gradient-to-r from-slate-400 to-slate-600 rounded-full mr-2"></span>
          Advanced Filters
        </h3>
        
        {/* Mobile expand/collapse button */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="md:hidden flex items-center justify-center w-8 h-8 bg-white/10 backdrop-blur-sm border border-white/20 rounded-lg hover:bg-white/20 focus:outline-none focus:ring-2 focus:ring-blue-400/50 transition-all duration-200"
          aria-label={isExpanded ? "Collapse filters" : "Expand filters"}
        >
          <svg
            className={`w-4 h-4 text-white transition-transform duration-200 ${
              isExpanded ? 'rotate-180' : ''
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>
      
      {/* Filters container - hidden on mobile when collapsed */}
      <div className={`${isExpanded ? 'block' : 'hidden md:block'} transition-all duration-300`}>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Salary Range */}
          <div>
            <label className="block text-sm font-medium text-white mb-2">
              Min Salary
            </label>
            <input
              type="number"
              value={filters.minSalary}
              onChange={(e) => handleFilterChange('minSalary', e.target.value)}
              placeholder="50000"
              className="w-full px-3 py-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400/50 focus:bg-white/20 text-white placeholder-gray-300 transition-all duration-200"
            />
          </div>


          {/* Job Category - Software vs Design */}
          <div>
            <label className="block text-sm font-medium text-white mb-2">
              Job Category
            </label>
            <select
              value={filters.jobType || ''}
              onChange={(e) => handleFilterChange('jobType', e.target.value)}
              className="w-full px-3 py-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400/50 focus:bg-white/20 text-white transition-all duration-200"
            >
              <option value="" className="bg-slate-800 text-white">All Categories</option>
              <option value="software_dev" className="bg-slate-800 text-white">Software Development</option>
              <option value="ux_ui_design" className="bg-slate-800 text-white">UX/UI Design</option>
              <option value="product" className="bg-slate-800 text-white">Product Management</option>
            </select>
          </div>

          {/* Employment Type - Full-Time vs Contract */}
          <div>
            <label className="block text-sm font-medium text-white mb-2">
              Employment Type
            </label>
            <select
              value={filters.employmentType || ''}
              onChange={(e) => handleFilterChange('employmentType', e.target.value)}
              className="w-full px-3 py-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400/50 focus:bg-white/20 text-white transition-all duration-200"
            >
              <option value="" className="bg-slate-800 text-white">All Employment Types</option>
              <option value="Full-Time" className="bg-slate-800 text-white">Full-Time</option>
              <option value="Contract" className="bg-slate-800 text-white">Contract</option>
              <option value="Part-Time" className="bg-slate-800 text-white">Part-Time</option>
            </select>
          </div>

          {/* Source Platform */}
          <div>
            <label className="block text-sm font-medium text-white mb-2">
              Source Platform
            </label>
            <select
              value={filters.sourcePlatform || ''}
              onChange={(e) => handleFilterChange('sourcePlatform', e.target.value)}
              className="w-full px-3 py-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400/50 focus:bg-white/20 text-white transition-all duration-200"
            >
              <option value="" className="bg-slate-800 text-white">All Platforms</option>
              <option value="RemoteOK" className="bg-slate-800 text-white">RemoteOK</option>
              <option value="Remotive" className="bg-slate-800 text-white">Remotive</option>
              <option value="WeWorkRemotely" className="bg-slate-800 text-white">WeWorkRemotely</option>
            </select>
          </div>
        </div>

        {/* Clear Filters */}
        <div className="mt-6 flex justify-center">
          <button
            onClick={() => onFiltersChange({
              minSalary: '',
              experienceLevel: '',
              jobType: '',
              employmentType: '',
              sourcePlatform: '',
              daysOld: '30'
            })}
            className="px-8 py-3 bg-gradient-to-r from-gray-600 to-gray-700 text-white rounded-lg hover:from-gray-700 hover:to-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-500/50 focus:ring-offset-2 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 font-medium"
          >
            Clear All Filters
          </button>
        </div>
      </div>
    </div>
  );
}