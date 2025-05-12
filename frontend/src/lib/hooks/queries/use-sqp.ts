import { useMutation, UseMutationResult } from '@tanstack/react-query';
import { sqpService } from '@/lib/api/services/sqp.service';
import { SqpPayload, ApiError, SqpResponse } from '@/lib/api/types';

export const useProcessSqp = (): UseMutationResult<SqpResponse, ApiError, SqpPayload> => {
  return useMutation({
    mutationFn: async (payload: SqpPayload) => {
      return await sqpService.processSqp(payload);
    },
  });
}; 