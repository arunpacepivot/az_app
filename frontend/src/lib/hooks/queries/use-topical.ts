import { useMutation, UseMutationResult } from '@tanstack/react-query';
import { topicalService } from '@/lib/api/services/topical.service';
import { TopicalPayload, ApiError, TopicalResponse } from '@/lib/api/types';

export const useProcessTopical = (): UseMutationResult<TopicalResponse, ApiError, TopicalPayload> => {
  return useMutation({
    mutationFn: async (payload: TopicalPayload) => {
      return await topicalService.processTopical(payload);
    },
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 60000),
  });
}; 