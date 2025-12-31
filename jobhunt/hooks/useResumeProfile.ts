import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getResumeProfile, uploadResume, ResumeUploadSettings } from '../api/endpoints';
import type { ResumeData } from '../types';

export const RESUME_QUERY_KEY = ['resume', 'profile'] as const;

/**
 * Hook to fetch the current resume profile
 */
export function useResumeProfile() {
  return useQuery<ResumeData, Error>({
    queryKey: RESUME_QUERY_KEY,
    queryFn: getResumeProfile,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });
}

/**
 * Hook to upload a new resume
 */
export function useUploadResume() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, settings }: { file: File; settings?: ResumeUploadSettings }) =>
      uploadResume(file, settings),
    onSuccess: (data) => {
      if (data.profile) {
        queryClient.setQueryData(RESUME_QUERY_KEY, data.profile);
      }
      // Invalidate jobs query since match scores may change
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
}

