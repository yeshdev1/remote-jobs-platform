'use client';

import { useState, useEffect, useCallback } from 'react';
import JobList from '../components/JobList';
import JobFilters from '../components/JobFilters';
import SearchBar from '../components/SearchBar';
import Pagination from '../components/Pagination';
import { Job } from '../lib/types';
import { api } from '../lib/api';
import { intelligentSearch } from '../lib/searchUtils';

export default function HomePage() {
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
    maxSalary: '',
    experienceLevel: '',
    jobType: '',
    sourcePlatform: '',
    daysOld: '30'
  });

  const fetchJobs = useCallback(async (page: number = currentPage) => {
    try {
      setLoading(true);
      console.log(`Fetching jobs from API (page ${page})...`);
      console.log('API Base URL:', process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000');
      
      // Apply any active filters to the API request
      const params: any = {
        skip: page * jobsPerPage,
        limit: jobsPerPage
      };
      
      if (filters.experienceLevel) {
        params.experience_level = filters.experienceLevel;
      }
      
      if (filters.sourcePlatform) {
        params.source_platform = filters.sourcePlatform;
      }
      
      if (filters.jobType) {
        params.job_type = filters.jobType;
      }
      
      if (filters.minSalary) {
        params.min_salary = parseFloat(filters.minSalary);
      }
      
      if (filters.maxSalary) {
        params.max_salary = parseFloat(filters.maxSalary);
      }
      
      if (filters.daysOld) {
        params.days_old = parseInt(filters.daysOld);
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
  }, [filters.sourcePlatform, filters.experienceLevel, filters.jobType, filters.minSalary, filters.maxSalary, filters.daysOld, fetchJobs]);

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
        
        if (filters.experienceLevel) {
          params.experience_level = filters.experienceLevel;
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
  };

  if (loading && jobs.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="relative">
            <div className="w-32 h-32 mx-auto">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-full animate-spin"></div>
              <div className="absolute inset-2 bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 rounded-full"></div>
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-full animate-pulse opacity-20"></div>
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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <header className="bg-white/10 backdrop-blur-xl border-b border-white/20 shadow-2xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <h1 className="text-5xl font-bold bg-gradient-to-r from-white via-blue-100 to-purple-100 bg-clip-text text-transparent mb-3">
              Remote Away
            </h1>
            <p className="text-xl text-gray-200 font-medium">
              100% Remote • Location Agnostic • US-Level Salaries • AI-Verified
            </p>
            <div className="mt-4 flex justify-center space-x-2">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-500/20 text-green-300 border border-green-500/30">
                <span className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></span>
                100% Remote
              </span>
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-500/20 text-blue-300 border border-blue-500/30">
                <span className="w-2 h-2 bg-blue-400 rounded-full mr-2 animate-pulse"></span>
                Global
              </span>
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-500/20 text-purple-300 border border-purple-500/30">
                <span className="w-2 h-2 bg-purple-400 rounded-full mr-2 animate-pulse"></span>
                AI-Verified
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
          <div className="bg-gradient-to-r from-blue-600/20 via-purple-600/20 to-pink-600/20 backdrop-blur-xl rounded-2xl p-6 border border-white/20 shadow-2xl">
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
                    experience_level: filters.experienceLevel || undefined
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
      </main>
    </div>
  );
}