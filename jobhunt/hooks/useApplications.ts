import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  getApplications, 
  updateApplication, 
  createApplication,
  ApplicationUpdateData 
} from '../api/endpoints';
import type { Application } from '../types';

export const APPLICATIONS_QUERY_KEY = ['applications'] as const;

/**
 * Hook to fetch all applications
 */
export function useApplications() {
  return useQuery({
    queryKey: APPLICATIONS_QUERY_KEY,
    queryFn: getApplications,
    staleTime: 1 * 60 * 1000, // 1 minute
  });
}

/**
 * Hook to update an application status/notes
 */
export function useUpdateApplication() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ applicationId, data }: { applicationId: string; data: ApplicationUpdateData }) =>
      updateApplication(applicationId, data),
    onMutate: async ({ applicationId, data }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: APPLICATIONS_QUERY_KEY });

      // Snapshot the previous value
      const previousApplications = queryClient.getQueryData(APPLICATIONS_QUERY_KEY);

      // Optimistically update
      queryClient.setQueryData(APPLICATIONS_QUERY_KEY, (old: { applications: Application[] } | undefined) => {
        if (!old) return old;
        return {
          ...old,
          applications: old.applications.map((app) =>
            app.id === applicationId ? { ...app, ...data, updatedAt: new Date().toISOString() } : app
          ),
        };
      });

      return { previousApplications };
    },
    onError: (_err, _vars, context) => {
      // Rollback on error
      if (context?.previousApplications) {
        queryClient.setQueryData(APPLICATIONS_QUERY_KEY, context.previousApplications);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: APPLICATIONS_QUERY_KEY });
    },
  });
}

/**
 * Hook to create a new application for a job
 */
export function useCreateApplication() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (jobId: string) => createApplication(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: APPLICATIONS_QUERY_KEY });
    },
  });
}

