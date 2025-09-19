// Determine if we're in development or production
const isDevelopment = process.env.NODE_ENV === 'development';

// Set API base URL based on environment
const API_BASE_URL = isDevelopment 
  ? 'http://localhost:8000/api'  // Development: localhost with /api prefix
  : 'https://www.remote-away.com/api';  // Production: your domain

const USE_PROXY = false; // Use direct API calls

console.log('Environment:', process.env.NODE_ENV);
console.log('Is Development:', isDevelopment);
console.log('API Base URL:', API_BASE_URL);
console.log('Using proxy:', USE_PROXY);

export const api = {
  // Get all jobs
  async getJobs(params?: {
    skip?: number;
    limit?: number;
    title?: string;
    company?: string;
    source_platform?: string;
    min_salary?: number;
    remote_type?: string;
    experience_level?: string;
    job_type?: string;
    employment_type?: string;
    skills?: string;
    days_old?: number;
  }) {
    const searchParams = new URLSearchParams();
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          searchParams.append(key, value.toString());
        }
      });
    }

    const url = USE_PROXY ? `/api/jobs?${searchParams}` : `${API_BASE_URL}/v1/jobs/?${searchParams}`;
    console.log('Making API request to:', url);
    console.log('Request headers:', {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    });
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });
    
    console.log('API response status:', response.status);
    console.log('API response headers:', Object.fromEntries(response.headers.entries()));
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('API error response:', errorText);
      throw new Error(`API request failed: ${response.status} ${response.statusText} - ${errorText}`);
    }
    
    const data = await response.json();
    console.log('API response data:', data);
    return data;
  },

  // Search jobs
  async searchJobs(query: string, params?: {
    skip?: number;
    limit?: number;
    source_platform?: string;
    experience_level?: string;
    job_type?: string;
    employment_type?: string;
    min_salary?: number;
  }) {
    const searchParams = new URLSearchParams();
    searchParams.append('q', query);
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && String(value).trim() !== '') {
          searchParams.append(key, value.toString());
        }
      });
    }

    const url = USE_PROXY ? `/api/jobs/search?${searchParams}` : `${API_BASE_URL}/v1/jobs/search/?${searchParams}`;
    console.log('Making search API request to:', url);
    const response = await fetch(url);
    console.log('Search API response status:', response.status);
    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }
    const data = await response.json();
    console.log('Search API response data:', data);
    return data;
  },

  // Get featured jobs
  async getFeaturedJobs(limit: number = 10) {
    const response = await fetch(`${API_BASE_URL}/v1/jobs/featured/?limit=${limit}`);
    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }
    return response.json();
  },

  // Get salary statistics
  async getSalaryStats() {
    const response = await fetch(`${API_BASE_URL}/v1/jobs/stats/salary-ranges`);
    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }
    return response.json();
  }
};

// Analytics API
export const analyticsApi = {
  // Get analytics overview
  async getOverview() {
    const response = await fetch(`${API_BASE_URL}/v1/analytics/overview`);
    if (!response.ok) {
      throw new Error(`Analytics API request failed: ${response.statusText}`);
    }
    return response.json();
  },

  // Get job board analytics
  async getJobBoardAnalytics() {
    const response = await fetch(`${API_BASE_URL}/v1/analytics/job-boards`);
    if (!response.ok) {
      throw new Error(`Analytics API request failed: ${response.statusText}`);
    }
    return response.json();
  },

  // Get job category analytics
  async getJobCategoryAnalytics() {
    const response = await fetch(`${API_BASE_URL}/v1/analytics/job-categories`);
    if (!response.ok) {
      throw new Error(`Analytics API request failed: ${response.statusText}`);
    }
    return response.json();
  },

  // Get salary analytics
  async getSalaryAnalytics() {
    const response = await fetch(`${API_BASE_URL}/v1/analytics/salary-ranges`);
    if (!response.ok) {
      throw new Error(`Analytics API request failed: ${response.statusText}`);
    }
    return response.json();
  },

  // Get trend analytics
  async getTrendAnalytics() {
    const response = await fetch(`${API_BASE_URL}/v1/analytics/trends`);
    if (!response.ok) {
      throw new Error(`Analytics API request failed: ${response.statusText}`);
    }
    return response.json();
  }
};