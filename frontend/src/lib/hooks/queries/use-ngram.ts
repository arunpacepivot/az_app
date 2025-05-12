import { useMutation, UseMutationResult } from '@tanstack/react-query';
import { ngramService } from '@/lib/api/services/ngram.service';
import { NgramPayload, ApiError, NgramResponse } from '@/lib/api/types';

export const useProcessNgram = (): UseMutationResult<NgramResponse, ApiError, NgramPayload> => {
  return useMutation({
    mutationFn: async (payload: NgramPayload) => {
      return await ngramService.processNgram(payload);
    },
  });
}; 