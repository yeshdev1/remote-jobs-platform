import { useRef, useEffect, useState, useCallback } from 'react';
import { Job } from '../lib/types';
import JobCard from './JobCard';

interface InfiniteJobListProps {
  jobs: Job[];
  loadMoreJobs: () => void;
  hasMore: boolean;
  loading: boolean;
}

export default function InfiniteJobList({ jobs, loadMoreJobs, hasMore, loading }: InfiniteJobListProps) {
  const observer = useRef<IntersectionObserver | null>(null);
  const [visibleJobs, setVisibleJobs] = useState<Job[]>([]);
  
  // Update visible jobs when the jobs array changes
  useEffect(() => {
    setVisibleJobs(jobs);
  }, [jobs]);

  // Last element ref for intersection observer
  const lastJobElementRef = useCallback((node: HTMLDivElement | null) => {
    if (loading) return;
    
    // Disconnect the previous observer if it exists
    if (observer.current) {
      observer.current.disconnect();
    }
    
    // Create a new observer
    observer.current = new IntersectionObserver(entries => {
      // If the last element is visible and we have more jobs to load
      if (entries[0].isIntersecting && hasMore) {
        loadMoreJobs();
      }
    }, { 
      root: null, // Use the viewport as the root
      rootMargin: '0px',
      threshold: 0.5 // Trigger when 50% of the element is visible
    });
    
    // Observe the last element
    if (node) {
      observer.current.observe(node);
    }
  }, [loading, hasMore, loadMoreJobs]);

  if (jobs.length === 0 && !loading) {
    return (
      <div className="text-center py-16">
        <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-8 border border-white/20 shadow-2xl">
          <div className="text-gray-300 mb-6">
            <svg className="mx-auto h-16 w-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-white mb-3">No jobs found</h3>
          <p className="text-gray-300 max-w-md mx-auto">
            Try adjusting your search criteria or filters to find more remote opportunities.
          </p>
          <div className="mt-6 flex justify-center space-x-2">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-500/20 text-blue-300 border border-blue-500/30">
              <span className="w-2 h-2 bg-blue-400 rounded-full mr-2 animate-pulse"></span>
              AI-Powered Search
            </span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {visibleJobs.map((job, index) => {
        // If this is the last job and we have more to load, attach the ref
        if (index === visibleJobs.length - 1) {
          return (
            <div key={job.id} ref={lastJobElementRef}>
              <JobCard job={job} />
            </div>
          );
        } else {
          return <JobCard key={job.id} job={job} />;
        }
      })}
      
      {/* Loading indicator */}
      {loading && (
        <div className="flex justify-center py-4">
          <div className="flex space-x-2 items-center">
            <div className="w-3 h-3 bg-blue-400 rounded-full animate-bounce"></div>
            <div className="w-3 h-3 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
            <div className="w-3 h-3 bg-pink-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
            <span className="ml-2 text-gray-300">Loading more jobs...</span>
          </div>
        </div>
      )}
    </div>
  );
}
