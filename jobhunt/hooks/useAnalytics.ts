import { useQuery } from '@tanstack/react-query';
import { getAnalytics } from '../api/endpoints';
import type { AnalyticsData } from '../types';

export const ANALYTICS_QUERY_KEY = ['analytics'] as const;

/**
 * Hook to fetch analytics data
 */
export function useAnalytics() {
  return useQuery<AnalyticsData, Error>({
    queryKey: ANALYTICS_QUERY_KEY,
    queryFn: getAnalytics,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

