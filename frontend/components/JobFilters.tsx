import { JobFilters as JobFiltersType } from '../lib/types';

interface JobFiltersProps {
  filters: JobFiltersType;
  onFiltersChange: (filters: JobFiltersType) => void;
}

export default function JobFilters({ filters, onFiltersChange }: JobFiltersProps) {
  const handleFilterChange = (key: keyof JobFiltersType, value: string) => {
    onFiltersChange({
      ...filters,
      [key]: value
    });
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
        <span className="w-2 h-2 bg-gradient-to-r from-blue-400 to-purple-400 rounded-full mr-2"></span>
        Advanced Filters
      </h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
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
        
        <div>
          <label className="block text-sm font-medium text-white mb-2">
            Max Salary
          </label>
          <input
            type="number"
            value={filters.maxSalary}
            onChange={(e) => handleFilterChange('maxSalary', e.target.value)}
            placeholder="200000"
            className="w-full px-3 py-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400/50 focus:bg-white/20 text-white placeholder-gray-300 transition-all duration-200"
          />
        </div>

        {/* Experience Level */}
        <div>
          <label className="block text-sm font-medium text-white mb-2">
            Experience Level
          </label>
          <select
            value={filters.experienceLevel}
            onChange={(e) => handleFilterChange('experienceLevel', e.target.value)}
            className="w-full px-3 py-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400/50 focus:bg-white/20 text-white transition-all duration-200"
          >
            <option value="" className="bg-slate-800 text-white">All Levels</option>
            <option value="entry" className="bg-slate-800 text-white">Entry Level</option>
            <option value="mid" className="bg-slate-800 text-white">Mid Level</option>
            <option value="senior" className="bg-slate-800 text-white">Senior Level</option>
            <option value="lead" className="bg-slate-800 text-white">Lead Level</option>
          </select>
        </div>

        {/* Job Type */}
        <div>
          <label className="block text-sm font-medium text-white mb-2">
            Job Type
          </label>
          <select
            value={filters.jobType || ''}
            onChange={(e) => handleFilterChange('jobType', e.target.value)}
            className="w-full px-3 py-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400/50 focus:bg-white/20 text-white transition-all duration-200"
          >
            <option value="" className="bg-slate-800 text-white">All Types</option>
            <option value="full_time" className="bg-slate-800 text-white">Full Time</option>
            <option value="part_time" className="bg-slate-800 text-white">Part Time</option>
            <option value="contract" className="bg-slate-800 text-white">Contract</option>
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

        {/* Days Old */}
        <div>
          <label className="block text-sm font-medium text-white mb-2">
            Posted Within
          </label>
          <select
            value={filters.daysOld}
            onChange={(e) => handleFilterChange('daysOld', e.target.value)}
            className="w-full px-3 py-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400/50 focus:bg-white/20 text-white transition-all duration-200"
          >
            <option value="7" className="bg-slate-800 text-white">7 days</option>
            <option value="14" className="bg-slate-800 text-white">14 days</option>
            <option value="30" className="bg-slate-800 text-white">30 days</option>
            <option value="60" className="bg-slate-800 text-white">60 days</option>
            <option value="90" className="bg-slate-800 text-white">90 days</option>
          </select>
        </div>
      </div>

      {/* Clear Filters */}
      <div className="mt-6 flex justify-end">
        <button
          onClick={() => onFiltersChange({
            minSalary: '',
            maxSalary: '',
            experienceLevel: '',
            jobType: '',
            sourcePlatform: '',
            daysOld: '30'
          })}
          className="px-6 py-2 bg-gradient-to-r from-gray-600 to-gray-700 text-white rounded-lg hover:from-gray-700 hover:to-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-500/50 focus:ring-offset-2 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 font-medium"
        >
          Clear All Filters
        </button>
      </div>
    </div>
  );
}
