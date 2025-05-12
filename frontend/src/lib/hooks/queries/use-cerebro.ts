import { useMutation, UseMutationResult } from '@tanstack/react-query';
import { cerebroService } from '@/lib/api/services/cerebro.service';
import { CerebroPayload, ApiError, CerebroResponse } from '@/lib/api/types';

export const useProcessCerebro = (): UseMutationResult<CerebroResponse, ApiError, CerebroPayload> => {
  return useMutation({
    mutationFn: async (payload: CerebroPayload) => {
      return await cerebroService.processCerebro(payload);
    },
  });
}; 