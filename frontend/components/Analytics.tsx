'use client';

import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import { analyticsApi } from '../lib/api';

interface OverviewData {
  total_jobs: number;
  growth_rate: number;
  avg_salary: number;
  job_boards_count: number;
}

interface JobBoardData {
  platforms: Array<{
    platform: string;
    job_count: number;
    percentage: number;
    avg_salary: number;
    recent_jobs_7_days: number;
  }>;
  total_jobs: number;
}

interface CategoryData {
  categories: Array<{
    category: string;
    job_count: number;
    percentage: number;
    avg_salary: number;
  }>;
  total_jobs: number;
}

interface SalaryData {
  salary_ranges: Array<{
    range: string;
    job_count: number;
    percentage: number;
  }>;
  avg_salary: number;
  min_salary: number;
  max_salary: number;
}

export default function Analytics() {
  const [loading, setLoading] = useState(true);
  const [overviewData, setOverviewData] = useState<OverviewData | null>(null);
  const [jobBoardData, setJobBoardData] = useState<JobBoardData | null>(null);
  const [categoryData, setCategoryData] = useState<CategoryData | null>(null);
  const [salaryData, setSalaryData] = useState<SalaryData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalyticsData = async () => {
      try {
        setLoading(true);
        
        const [overview, jobBoards, categories, salaries] = await Promise.all([
          analyticsApi.getOverview(),
          analyticsApi.getJobBoardAnalytics(),
          analyticsApi.getJobCategoryAnalytics(),
          analyticsApi.getSalaryAnalytics()
        ]);

        setOverviewData(overview);
        setJobBoardData(jobBoards);
        setCategoryData(categories);
        setSalaryData(salaries);
        
      } catch (err) {
        console.error('Error fetching analytics:', err);
        setError('Failed to load analytics data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchAnalyticsData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="relative">
            <div className="w-32 h-32 mx-auto">
              <div className="absolute inset-0 bg-gradient-to-r from-slate-700 via-slate-600 to-slate-700 rounded-full animate-spin
                before:content-[''] before:absolute before:inset-2 before:bg-gradient-to-br before:from-slate-900 before:via-slate-800 before:to-slate-900 before:rounded-full">
              </div>
            </div>
          </div>
          <div className="mt-8 flex justify-center space-x-1">
            <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
            <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
            <div className="w-2 h-2 bg-pink-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
          </div>
          <p className="text-gray-200 mt-4 text-lg">Loading Analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-400 text-xl mb-4">{error}</div>
          <button 
            onClick={() => window.location.reload()} 
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const COLORS = ['#3B82F6', '#10B981', '#8B5CF6', '#F59E0B', '#EF4444'];
  
  const formatSalary = (salary: number) => {
    return `$${(salary / 1000).toFixed(0)}K`;
  };

  return (
    <div className="space-y-8">
      {/* Analytics Header */}
      <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20 shadow-2xl">
        <div className="text-center">
          <h2 className="text-3xl font-bold bg-gradient-to-r from-white via-gray-200 to-gray-300 bg-clip-text text-transparent mb-3">
            Job Market Analytics
          </h2>
          <p className="text-gray-200">
            Comprehensive insights into remote job trends and platform performance
          </p>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20 shadow-2xl">
          <div className="flex items-center">
            <div className="p-3 bg-blue-500/20 rounded-lg">
              <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0H8m8 0v2a2 2 0 002 2h2a2 2 0 002-2V8a2 2 0 00-2-2h-2z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-2xl font-bold text-white">{overviewData?.total_jobs.toLocaleString() || '0'}</p>
              <p className="text-gray-300">Total Jobs</p>
            </div>
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20 shadow-2xl">
          <div className="flex items-center">
            <div className="p-3 bg-green-500/20 rounded-lg">
              <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-2xl font-bold text-white">
                {overviewData?.growth_rate ? `${overviewData.growth_rate > 0 ? '+' : ''}${overviewData.growth_rate}%` : '0%'}
              </p>
              <p className="text-gray-300">Growth Rate</p>
            </div>
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20 shadow-2xl">
          <div className="flex items-center">
            <div className="p-3 bg-purple-500/20 rounded-lg">
              <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-2xl font-bold text-white">{overviewData?.job_boards_count || '0'}</p>
              <p className="text-gray-300">Job Boards</p>
            </div>
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20 shadow-2xl">
          <div className="flex items-center">
            <div className="p-3 bg-yellow-500/20 rounded-lg">
              <svg className="w-6 h-6 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-2xl font-bold text-white">
                {overviewData?.avg_salary ? formatSalary(overviewData.avg_salary) : '$0K'}
              </p>
              <p className="text-gray-300">Avg Salary</p>
            </div>
          </div>
        </div>
      </div>

      {/* Job Board Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20 shadow-2xl">
          <h3 className="text-xl font-semibold text-white mb-6">Job Distribution by Platform</h3>
          {jobBoardData && (
            <div className="space-y-4">
              {jobBoardData.platforms.map((platform, index) => (
                <div key={platform.platform} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div 
                      className="w-4 h-4 rounded-full" 
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    ></div>
                    <span className="text-gray-200">{platform.platform}</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-32 bg-gray-700 rounded-full h-2">
                      <div 
                        className="h-2 rounded-full" 
                        style={{ 
                          backgroundColor: COLORS[index % COLORS.length],
                          width: `${platform.percentage}%` 
                        }}
                      ></div>
                    </div>
                    <span className="text-white font-semibold w-20 text-right">
                      {platform.job_count.toLocaleString()} jobs
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20 shadow-2xl">
          <h3 className="text-xl font-semibold text-white mb-6">Platform Performance</h3>
          {jobBoardData && (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={jobBoardData.platforms}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis 
                  dataKey="platform" 
                  stroke="#9CA3AF"
                  fontSize={12}
                />
                <YAxis stroke="#9CA3AF" fontSize={12} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1F2937', 
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#F3F4F6'
                  }}
                />
                <Bar dataKey="job_count" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Job Categories */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20 shadow-2xl">
          <h3 className="text-xl font-semibold text-white mb-6">Job Categories</h3>
          {categoryData && categoryData.categories.length > 0 ? (
            <>
              <div className="space-y-3 mb-6">
                {categoryData.categories.slice(0, 5).map((category, index) => (
                  <div key={category.category} className="flex justify-between items-center">
                    <span className="text-gray-200">{category.category}</span>
                    <span className="text-white font-semibold">
                      {category.job_count.toLocaleString()} ({category.percentage}%)
                    </span>
                  </div>
                ))}
              </div>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={categoryData.categories.slice(0, 5)}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="job_count"
                    nameKey="category"
                  >
                    {categoryData.categories.slice(0, 5).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1F2937', 
                      border: '1px solid #374151',
                      borderRadius: '8px',
                      color: '#F3F4F6'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </>
          ) : (
            <div className="text-center text-gray-400 py-8">
              <p>No category data available</p>
            </div>
          )}
        </div>

        <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20 shadow-2xl">
          <h3 className="text-xl font-semibold text-white mb-6">Salary Ranges</h3>
          {salaryData && salaryData.salary_ranges.length > 0 ? (
            <>
              <div className="space-y-3 mb-6">
                {salaryData.salary_ranges.map((range, index) => (
                  <div key={range.range} className="flex justify-between items-center">
                    <span className="text-gray-200">{range.range}</span>
                    <span className="text-white font-semibold">
                      {range.job_count.toLocaleString()} ({range.percentage}%)
                    </span>
                  </div>
                ))}
              </div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={salaryData.salary_ranges} layout="horizontal">
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis type="number" stroke="#9CA3AF" fontSize={12} />
                  <YAxis 
                    type="category" 
                    dataKey="range" 
                    stroke="#9CA3AF" 
                    fontSize={10}
                    width={80}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1F2937', 
                      border: '1px solid #374151',
                      borderRadius: '8px',
                      color: '#F3F4F6'
                    }}
                  />
                  <Bar dataKey="job_count" fill="#10B981" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </>
          ) : (
            <div className="text-center text-gray-400 py-8">
              <p>No salary data available</p>
            </div>
          )}
        </div>
      </div>

      {/* Platform Insights */}
      <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20 shadow-2xl">
        <h3 className="text-xl font-semibold text-white mb-6">Platform Insights</h3>
        {jobBoardData && jobBoardData.platforms.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {jobBoardData.platforms.map((platform, index) => (
              <div key={platform.platform} className="text-center">
                <div className="mb-4">
                  <div 
                    className="w-16 h-16 mx-auto rounded-full flex items-center justify-center text-white font-bold text-lg"
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  >
                    {platform.platform.charAt(0)}
                  </div>
                </div>
                <h4 className="text-white font-semibold mb-2">{platform.platform}</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-300">Total Jobs:</span>
                    <span className="text-white">{platform.job_count.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Market Share:</span>
                    <span className="text-white">{platform.percentage}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Avg Salary:</span>
                    <span className="text-white">
                      {platform.avg_salary ? formatSalary(platform.avg_salary) : 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Recent (7d):</span>
                    <span className="text-white">{platform.recent_jobs_7_days || 0}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center text-gray-300 py-8">
            <svg className="w-12 h-12 mx-auto mb-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <p>Loading platform insights...</p>
          </div>
        )}
      </div>
    </div>
  );
}
