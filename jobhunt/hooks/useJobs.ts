import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { searchJobs, getJob, labelJob, JobSearchParams } from '../api/endpoints';
import type { Job } from '../types';

export const JOBS_QUERY_KEY = ['jobs'] as const;

/**
 * Hook to search jobs with filters
 */
export function useJobSearch(params?: JobSearchParams) {
  return useQuery({
    queryKey: [...JOBS_QUERY_KEY, 'search', params],
    queryFn: () => searchJobs(params),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

/**
 * Hook to get a single job by ID
 */
export function useJob(jobId: string | null) {
  return useQuery<Job, Error>({
    queryKey: [...JOBS_QUERY_KEY, jobId],
    queryFn: () => getJob(jobId!),
    enabled: !!jobId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to save or reject a job
 */
export function useLabelJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ jobId, label }: { jobId: string; label: 0 | 1 }) =>
      labelJob(jobId, label),
    onSuccess: () => {
      // Invalidate jobs and applications queries
      queryClient.invalidateQueries({ queryKey: JOBS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ['applications'] });
    },
  });
}

