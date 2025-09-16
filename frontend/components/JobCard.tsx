import { Job } from '../lib/types';
import { formatDistanceToNow } from 'date-fns';

interface JobCardProps {
  job: Job;
}

export default function JobCard({ job }: JobCardProps) {
  const formatSalary = () => {
    if (job.salary_min && job.salary_max) {
      return `$${job.salary_min.toLocaleString()} - $${job.salary_max.toLocaleString()}`;
    } else if (job.salary_min) {
      return `$${job.salary_min.toLocaleString()}+`;
    } else if (job.salary_max) {
      return `Up to $${job.salary_max.toLocaleString()}`;
    }
    return 'Salary not specified';
  };

  const getExperienceColor = (level?: string) => {
    switch (level) {
      case 'entry': return 'bg-green-500/20 text-green-300 border-green-500/30';
      case 'mid': return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
      case 'senior': return 'bg-purple-500/20 text-purple-300 border-purple-500/30';
      case 'lead': return 'bg-red-500/20 text-red-300 border-red-500/30';
      default: return 'bg-gray-500/20 text-gray-300 border-gray-500/30';
    }
  };

  const getRemoteTypeColor = (type?: string) => {
    // Since we only show remote jobs, always use remote styling
    return 'bg-green-500/20 text-green-300 border-green-500/30';
  };

  return (
    <div className="bg-white/10 backdrop-blur-xl rounded-2xl shadow-2xl border border-white/20 hover:bg-white/15 hover:shadow-3xl transition-all duration-300 transform hover:-translate-y-1">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="text-xl font-semibold text-white mb-2 hover:text-blue-300 transition-colors">
              <a href={job.application_url || job.url || job.source_url} target="_blank" rel="noopener noreferrer">
                {job.title}
              </a>
            </h3>
            <div className="flex items-center space-x-4 text-sm text-gray-300">
              <span className="font-medium">{job.company}</span>
              {job.location && (
                <>
                  <span>•</span>
                  <span>{job.location}</span>
                </>
              )}
            </div>
          </div>
          
          {/* Company Logo */}
          {job.company_logo && (
            <div className="ml-4">
              <img 
                src={job.company_logo} 
                alt={`${job.company} logo`}
                className="w-16 h-16 object-contain rounded"
              />
            </div>
          )}
        </div>

        {/* Salary and Tags */}
        <div className="mb-4">
          <div className="text-lg font-semibold bg-gradient-to-r from-green-400 to-blue-400 bg-clip-text text-transparent mb-3">
            {formatSalary()}
          </div>
          
          <div className="flex flex-wrap gap-2">
            {job.experience_level && (
              <span className={`px-3 py-1 text-xs font-medium rounded-full border ${getExperienceColor(job.experience_level)}`}>
                {job.experience_level.charAt(0).toUpperCase() + job.experience_level.slice(1)} Level
              </span>
            )}
            
            <span className={`px-3 py-1 text-xs font-medium rounded-full border ${getRemoteTypeColor()} flex items-center`}>
              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM4.332 8.027a6.012 6.012 0 011.912-2.706C6.512 5.73 6.974 6 7.5 6A1.5 1.5 0 019 7.5V8a2 2 0 004 0 2 2 0 011.523-1.943A5.977 5.977 0 0116 10c0 .34-.028.675-.083 1H15a2 2 0 00-2 2v2.197A5.973 5.973 0 0110 16v-2a2 2 0 00-2-2 2 2 0 01-2-2 2 2 0 00-1.668-1.973z" clipRule="evenodd" />
              </svg>
              Remote
            </span>
            
            {job.job_type && (
              <span className="px-3 py-1 text-xs font-medium rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30">
                {job.job_type.charAt(0).toUpperCase() + job.job_type.slice(1)}
              </span>
            )}
            
            {job.ai_processed && (
              <span className="px-3 py-1 text-xs font-medium rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30 flex items-center">
                <span className="w-2 h-2 bg-purple-400 rounded-full mr-1 animate-pulse"></span>
                AI Verified
              </span>
            )}
          </div>
        </div>

        {/* Description */}
        {job.ai_generated_summary && (
          <div className="mb-4">
            <p className="text-gray-200 leading-relaxed">
              {job.ai_generated_summary}
            </p>
          </div>
        )}

        {/* Skills */}
        {job.skills_required && job.skills_required.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-white mb-2">Required Skills:</h4>
            <div className="flex flex-wrap gap-2">
              {job.skills_required.slice(0, 6).map((skill, index) => (
                <span 
                  key={index}
                  className="px-3 py-1 text-xs bg-white/10 text-gray-200 rounded-lg border border-white/20"
                >
                  {skill}
                </span>
              ))}
              {job.skills_required.length > 6 && (
                <span className="px-3 py-1 text-xs text-gray-400">
                  +{job.skills_required.length - 6} more
                </span>
              )}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-4 border-t border-white/20">
          <div className="flex items-center space-x-4 text-sm text-gray-300">
            <span>Posted {formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}</span>
            <span>via {job.source_platform}</span>
          </div>
          
          <div className="flex space-x-2">
            {job.application_url && (
              <a
                href={job.application_url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white text-sm font-medium rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
              >
                Apply Now
              </a>
            )}
            <a
              href={job.url || job.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 border border-white/20 text-gray-200 text-sm font-medium rounded-lg hover:bg-white/10 hover:border-white/30 transition-all duration-200"
            >
              Apply!
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
