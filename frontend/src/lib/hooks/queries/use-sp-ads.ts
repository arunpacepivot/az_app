import { useMutation, UseMutationResult } from '@tanstack/react-query';
import { spService } from '@/lib/api/services/sp.service';
import { SpAdsPayload, ProcessedFile, ApiError } from '@/lib/api/types';

export const useProcessSpAds = (): UseMutationResult<ProcessedFile, ApiError, SpAdsPayload> => {
  return useMutation({
    mutationFn: async (payload: SpAdsPayload) => {
      const response = await spService.processSpAds(payload);
      return response.data;
    },
    // Retry logic commented out - will implement later
    // retry: 2,
    // retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 60000),
  });
}; 