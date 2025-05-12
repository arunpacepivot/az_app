import { useMutation, UseMutationResult } from '@tanstack/react-query';
import { spService } from '@/lib/api/services/sp.service';
import { SpAdsPayload, ApiError, SpAdsResponse } from '@/lib/api/types';

export const useProcessSpAds = (): UseMutationResult<SpAdsResponse, ApiError, SpAdsPayload> => {
  return useMutation({
    mutationFn: async (payload: SpAdsPayload) => {
      return await spService.processSpAds(payload);
    },
    // Retry logic commented out - will implement later
    // retry: 2,
    // retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 60000),
  });
}; 