export interface Job {
  id: number;
  title: string;
  company: string;
  location?: string;
  salary_min?: number;
  salary_max?: number;
  salary_currency?: string;
  salary_period?: string;
  description?: string;
  requirements?: string;
  benefits?: string;
  job_type?: string;
  experience_level?: string;
  remote_type?: string;
  source_url: string;
  url?: string;
  source_platform: string;
  posted_date?: string;
  application_url?: string;
  company_logo?: string;
  company_description?: string;
  company_size?: string;
  company_industry?: string;
  skills_required?: string[];
  ai_generated_summary?: string;
  ai_processed?: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface JobFilters {
  minSalary: string;
  experienceLevel: string;
  jobType: string;
  employmentType: string;
  sourcePlatform: string;
  daysOld: string;
}

export interface JobListResponse {
  jobs: Job[];
  total: number;
  skip: number;
  limit: number;
}
