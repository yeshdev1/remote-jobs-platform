'use client';

import { useState, useEffect, useCallback } from 'react';
import JobList from '../components/JobList';
import JobFilters from '../components/JobFilters';
import SearchBar from '../components/SearchBar';
import Pagination from '../components/Pagination';
import Analytics from '../components/Analytics';
import DataConsentModal from '../components/DataConsentModal';
import { Job } from '../lib/types';
import { api } from '../lib/api';
import { intelligentSearch } from '../lib/searchUtils';
import { useConsent } from '../lib/useConsent';

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<'jobs' | 'analytics'>('jobs');
  const [jobs, setJobs] = useState<Job[]>([]);
  const [filteredJobs, setFilteredJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(0);
  const [totalJobs, setTotalJobs] = useState(0);
  const jobsPerPage = 10;
  const [totalPages, setTotalPages] = useState(0);
  const [filters, setFilters] = useState({
    minSalary: '',
    experienceLevel: '',
    jobType: '',
    sourcePlatform: '',
    daysOld: '30',
    employmentType: ''
  });

  // Consent management
  const { 
    needsConsent, 
    hasConsent, 
    giveConsent, 
    canTrackAnalytics, 
    trackEvent, 
    trackPageView 
  } = useConsent();

  const fetchJobs = useCallback(async (page: number = currentPage) => {
    try {
      setLoading(true);
      console.log(`Fetching jobs from API (page ${page})...`);
      console.log('API Base URL:', process.env.NEXT_PUBLIC_API_URL || 'https://remote-away.com');
      
      // Apply any active filters to the API request
      const params: any = {
        skip: page * jobsPerPage,
        limit: jobsPerPage
      };
      
      if (filters.sourcePlatform) {
        params.source_platform = filters.sourcePlatform;
      }
      
      if (filters.jobType) {
        params.job_type = filters.jobType;
      }
      
      if (filters.minSalary) {
        params.min_salary = parseFloat(filters.minSalary);
      }
      
      console.log('Fetch params:', params);
      
      const data = await api.getJobs(params);
      console.log('Jobs fetched:', data);
      console.log('Number of jobs:', data.jobs?.length || 0);
      console.log('Total jobs:', data.total);
      console.log('Current page:', page);
      
      // Update total jobs count and calculate total pages
      setTotalJobs(data.total || 0);
      setTotalPages(Math.ceil((data.total || 0) / jobsPerPage));
      
      // Set jobs for current page
      setJobs(data.jobs || []);
      setFilteredJobs(data.jobs || []); // Make sure filtered jobs are updated too
      
      // Update current page
      setCurrentPage(page);
    } catch (error) {
      console.error('Error fetching jobs:', error);
      console.error('Error details:', error.message);
      console.error('Error stack:', error.stack);
      
      // For now, set empty jobs array if API fails
      setJobs([]);
      setFilteredJobs([]);
      setTotalPages(0);
    } finally {
      setLoading(false);
    }
  }, [filters, jobsPerPage]); // Remove currentPage from dependencies to avoid infinite loop

  useEffect(() => {
    // Reset pagination and fetch jobs when filters change
    setCurrentPage(0);
    setJobs([]);
    fetchJobs(0);
  }, [filters.sourcePlatform, filters.jobType, filters.minSalary, fetchJobs]);

  // We're now handling filtering directly in the API calls
  // This is just a fallback for client-side filtering if needed
  useEffect(() => {
    // Only apply client-side filtering for search results
    // For regular browsing, filtering is handled by the API
    if (searchQuery) {
      applyFilters();
    } else {
      setFilteredJobs(jobs);
    }
  }, [jobs, searchQuery]);

  const applyFilters = () => {
    // Only used for client-side filtering of search results
    if (jobs.length === 0) return;
    
    let filtered = [...jobs];

    // For search results, we may want to do additional client-side filtering
    if (searchQuery && !loading) {
      // Apply any additional client-side filters here if needed
    }

    setFilteredJobs(filtered);
  };

  const handleSearch = async (query: string) => {
    console.log('Search triggered with query:', query);
    setSearchQuery(query);
    
    // Reset pagination state for new search
    setCurrentPage(0);
    
    if (query.trim()) {
      try {
        setSearching(true);
        console.log('Calling API search with query:', query);
        
        // Include any active filters in the search
        const params: any = {
          skip: 0,
          limit: jobsPerPage
        };
        
        if (filters.sourcePlatform) {
          params.source_platform = filters.sourcePlatform;
        }
        
        if (filters.jobType) {
          params.job_type = filters.jobType;
        }
        
        const data = await api.searchJobs(query, params);
        console.log('Search API response:', data);
        
        // Update total jobs count and calculate total pages
        setTotalJobs(data.total || 0);
        setTotalPages(Math.ceil((data.total || 0) / jobsPerPage));
        
        // Set both jobs and filtered jobs to show search results immediately
        setJobs(data.jobs || []);
        setFilteredJobs(data.jobs || []);
      } catch (error) {
        console.error('Error searching jobs:', error);
        // Fall back to intelligent local search
        const localResults = intelligentSearch(jobs, query);
        setFilteredJobs(localResults);
        setTotalPages(1); // Only one page for local search results
      } finally {
        setSearching(false);
      }
    } else {
      // If search is empty, fetch all jobs
      console.log('Empty search, fetching all jobs');
      setJobs([]);
      fetchJobs(0);
    }
  };

  const handleFiltersChange = (newFilters: typeof filters) => {
    setFilters(newFilters);
    
    // Track filter usage if analytics consent is given
    if (canTrackAnalytics()) {
      trackEvent('filters_changed', {
        filters: newFilters,
        hasSearch: !!searchQuery
      });
    }
  };

  const handleTabChange = (tab: 'jobs' | 'analytics') => {
    setActiveTab(tab);
    
    // Track tab navigation if analytics consent is given
    if (canTrackAnalytics()) {
      trackEvent('tab_switch', {
        from: activeTab,
        to: tab
      });
      
      // Track page view for analytics tab
      if (tab === 'analytics') {
        trackPageView('/analytics', 'Remote Jobs Platform - Analytics');
      } else {
        trackPageView('/', 'Remote Jobs Platform - Jobs');
      }
    }
  };

  if (loading && jobs.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="relative">
            <div className="w-32 h-32 mx-auto">
              <div className="absolute inset-0 bg-gradient-to-r from-slate-700 via-slate-600 to-slate-700 rounded-full animate-spin"></div>
              <div className="absolute inset-2 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-full"></div>
              <div className="absolute inset-0 bg-gradient-to-r from-slate-700 via-slate-600 to-slate-700 rounded-full animate-pulse opacity-20"></div>
            </div>
          </div>
          <p className="mt-6 text-xl text-white font-medium">Loading remote jobs...</p>
          <p className="mt-2 text-gray-300">AI-powered job validation in progress</p>
          <div className="mt-4 flex justify-center space-x-1">
            <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
            <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
            <div className="w-2 h-2 bg-pink-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="bg-white/10 backdrop-blur-xl border-b border-white/20 shadow-2xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 sm:py-6 lg:py-8">
          <div className="text-center">
            <h1 className="text-2xl sm:text-4xl lg:text-5xl font-bold bg-gradient-to-r from-white via-gray-200 to-gray-300 bg-clip-text text-transparent mb-2 sm:mb-3">
              Remote Away
            </h1>
            <p className="text-sm sm:text-lg lg:text-xl text-gray-200 font-medium">
              100% Remote • Location Agnostic • US-Level Salaries • AI-Verified
            </p>
            <div className="mt-2 sm:mt-4 flex flex-wrap justify-center gap-1 sm:gap-2">
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs sm:text-sm font-medium bg-green-500/20 text-green-300 border border-green-500/30">
                <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-green-400 rounded-full mr-1 sm:mr-2 animate-pulse"></span>
                100% Remote
              </span>
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs sm:text-sm font-medium bg-blue-500/20 text-blue-300 border border-blue-500/30">
                <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-blue-400 rounded-full mr-1 sm:mr-2 animate-pulse"></span>
                Global
              </span>
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs sm:text-sm font-medium bg-purple-500/20 text-purple-300 border border-purple-500/30">
                <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-purple-400 rounded-full mr-1 sm:mr-2 animate-pulse"></span>
                AI-Verified
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-2 border border-white/20 shadow-2xl">
          <nav className="flex space-x-1">
            <button
              onClick={() => handleTabChange('jobs')}
              className={`flex-1 px-6 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${
                activeTab === 'jobs'
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
                  : 'text-gray-300 hover:text-white hover:bg-white/10'
              }`}
            >
              <div className="flex items-center justify-center space-x-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0H8m8 0v2a2 2 0 002 2h2a2 2 0 002-2V8a2 2 0 00-2-2h-2z" />
                </svg>
                <span>Jobs</span>
                {totalJobs > 0 && (
                  <span className="bg-white/20 text-xs px-2 py-1 rounded-full">
                    {totalJobs.toLocaleString()}
                  </span>
                )}
              </div>
            </button>
            
            <button
              onClick={() => handleTabChange('analytics')}
              className={`flex-1 px-6 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${
                activeTab === 'analytics'
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
                  : 'text-gray-300 hover:text-white hover:bg-white/10'
              }`}
            >
              <div className="flex items-center justify-center space-x-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <span>Analytics</span>
              </div>
            </button>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'jobs' && (
          <>
            {/* Search and Filters */}
            <div className="mb-8 space-y-6">
          <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20 shadow-2xl">
            <SearchBar 
              onSearch={handleSearch} 
              searchQuery={searchQuery}
              isSearching={searching}
            />
          </div>
          <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20 shadow-2xl">
            <JobFilters 
              filters={filters} 
              onFiltersChange={handleFiltersChange} 
            />
          </div>
        </div>

        {/* Results Summary */}
        <div className="mb-6">
          <div className="bg-gradient-to-r from-slate-700/20 via-slate-600/20 to-slate-700/20 backdrop-blur-xl rounded-2xl p-6 border border-white/20 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-gray-200 text-lg">
                  {searching ? (
                    <span className="flex items-center">
                      <span className="w-4 h-4 border-2 border-blue-400/30 border-t-blue-400 rounded-full animate-spin mr-2 inline-block"></span>
                      Searching for remote jobs...
                    </span>
                  ) : (
                    <>
                      Found <span className="font-bold text-white text-2xl">{totalJobs}</span> remote jobs
                      {searchQuery && (
                        <span className="text-blue-300"> matching "{searchQuery}"</span>
                      )}
                    </>
                  )}
                </p>
                <p className="text-gray-300 text-sm mt-1">
                  {searching ? 'AI-powered semantic search in progress...' : 'International remote positions with intelligent search matching'}
                </p>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold bg-gradient-to-r from-green-400 to-blue-400 bg-clip-text text-transparent">
                  {totalJobs}
                </div>
                <div className="text-gray-300 text-sm">Jobs Available</div>
              </div>
            </div>
          </div>
        </div>

        {/* Job List */}
        <JobList jobs={filteredJobs} />
        
        {/* Pagination */}
        {totalPages > 0 && (
          <div className="relative">
            {loading && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/20 backdrop-blur-sm rounded-lg">
                <div className="w-8 h-8 border-4 border-blue-400/30 border-t-blue-400 rounded-full animate-spin"></div>
              </div>
            )}
            <Pagination 
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={(page) => {
                setLoading(true);
                console.log(`Changing to page ${page + 1}`);
                
                if (searchQuery) {
                  // For search results, we need to re-run the search with new page
                  const params = {
                    skip: page * jobsPerPage,
                    limit: jobsPerPage,
                    source_platform: filters.sourcePlatform || undefined,
                    job_type: filters.jobType || undefined,
                  };
                  
                  console.log('Search params for pagination:', params);
                  
                  api.searchJobs(searchQuery, params)
                    .then(data => {
                      console.log('Search pagination response:', data);
                      setJobs(data.jobs || []);
                      setFilteredJobs(data.jobs || []);
                      setCurrentPage(page);
                    })
                    .catch(err => {
                      console.error('Error during search pagination:', err);
                    })
                    .finally(() => {
                      setLoading(false);
                    });
                } else {
                  // For normal browsing
                  fetchJobs(page);
                }
              }}
            />
          </div>
        )}
          </>
        )}

        {activeTab === 'analytics' && (
          <Analytics />
        )}
      </main>

      {/* Data Consent Modal */}
      {needsConsent && (
        <DataConsentModal 
          onConsent={(accepted) => {
            giveConsent(accepted);
            
            // Track initial page view if consent given
            if (accepted) {
              trackPageView('/', 'Remote Jobs Platform - Home');
            }
          }} 
        />
      )}
    </div>
  );
}