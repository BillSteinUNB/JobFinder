/**
 * Type-safe API endpoint functions
 */

import { get, post, postFormData, patch } from './client';
import type { 
  Job, 
  Application, 
  ResumeData, 
  AnalyticsData,
  ApplicationStatus 
} from '../types';

// ============================================================================
// Response Types (from API)
// ============================================================================

export interface JobSearchResponse {
  jobs: Job[];
  total: number;
  limit: number;
  offset: number;
  hasMore: boolean;
}

export interface ApplicationsResponse {
  applications: Application[];
  total: number;
}

export interface ResumeUploadResponse {
  success: boolean;
  message: string;
  profile: ResumeData | null;
}

export interface HealthResponse {
  status: string;
  version: string;
}

// ============================================================================
// Search Parameters
// ============================================================================

export interface JobSearchParams {
  query?: string;
  location?: string;
  min_salary?: number;
  remote_only?: boolean;
  limit?: number;
  offset?: number;
}

export interface ResumeUploadSettings {
  preferredLocation?: string;
  minSalary?: number;
}

export interface ApplicationUpdateData {
  status?: ApplicationStatus;
  notes?: string;
  nextStep?: string;
  nextStepDate?: string;
}

// ============================================================================
// Health
// ============================================================================

export async function getHealth(): Promise<HealthResponse> {
  return get<HealthResponse>('/api/health');
}

// ============================================================================
// Resume Endpoints
// ============================================================================

export async function getResumeProfile(): Promise<ResumeData> {
  return get<ResumeData>('/api/resume/profile');
}

export async function uploadResume(
  file: File, 
  settings?: ResumeUploadSettings
): Promise<ResumeUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  
  if (settings?.preferredLocation) {
    formData.append('preferred_location', settings.preferredLocation);
  }
  if (settings?.minSalary) {
    formData.append('min_salary', String(settings.minSalary));
  }
  
  return postFormData<ResumeUploadResponse>('/api/resume/upload', formData);
}

// ============================================================================
// Job Endpoints
// ============================================================================

export async function searchJobs(params?: JobSearchParams): Promise<JobSearchResponse> {
  return get<JobSearchResponse>('/api/jobs/search', params as Record<string, unknown>);
}

export async function getJob(jobId: string): Promise<Job> {
  return get<Job>(`/api/jobs/${jobId}`);
}

export async function labelJob(jobId: string, label: 0 | 1): Promise<{ status: string; message: string }> {
  return patch<{ status: string; message: string }>(`/api/jobs/${jobId}/label`, { label });
}

// ============================================================================
// Application Endpoints
// ============================================================================

export async function getApplications(): Promise<ApplicationsResponse> {
  return get<ApplicationsResponse>('/api/applications');
}

export async function updateApplication(
  applicationId: string, 
  data: ApplicationUpdateData
): Promise<Application> {
  return patch<Application>(`/api/applications/${applicationId}`, data);
}

export async function createApplication(jobId: string): Promise<Application> {
  return post<Application>(`/api/applications/${jobId}`);
}

// ============================================================================
// Analytics Endpoints
// ============================================================================

export async function getAnalytics(): Promise<AnalyticsData> {
  return get<AnalyticsData>('/api/analytics');
}

