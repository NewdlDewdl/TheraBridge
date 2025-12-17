import useSWR from 'swr';
import { fetcher } from '@/lib/api';
import type { Session } from '@/lib/types';

export interface UseSessionOptions {
  refreshInterval?: number;
}

export function useSession(sessionId: string | null, options?: UseSessionOptions) {
  const isProcessing = (data?: Session) =>
    data?.status === 'uploading' ||
    data?.status === 'transcribing' ||
    data?.status === 'extracting_notes';

  // Determine refresh interval: 5s while processing, 0 (disabled) otherwise
  // Respects explicit refreshInterval override from options
  const getRefreshInterval = (data?: Session) => {
    if (options?.refreshInterval !== undefined) {
      return options.refreshInterval;
    }
    return isProcessing(data) ? 5000 : 0;
  };

  const { data, error, mutate, isLoading } = useSWR<Session>(
    sessionId ? `/api/sessions/${sessionId}` : null,
    fetcher,
    {
      // Dynamic refresh interval based on processing status
      refreshInterval: (latestData) => getRefreshInterval(latestData),
      // Prevent duplicate requests within 60 seconds
      dedupingInterval: 60000,
      // Don't revalidate on focus - let manual refresh be explicit
      revalidateOnFocus: false,
      // Revalidate on reconnect for network resilience
      revalidateOnReconnect: true,
    }
  );

  return {
    session: data,
    isLoading,
    isError: !!error,
    error,
    isProcessing: isProcessing(data),
    refresh: mutate,
  };
}
