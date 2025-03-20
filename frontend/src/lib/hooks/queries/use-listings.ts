import { useQuery, useMutation, UseQueryResult, UseMutationResult } from '@tanstack/react-query';
import { listingService } from '@/lib/api/services/listing.service';
import { Listing, ListingPayload, ApiError } from '@/lib/api/types';

export const useListings = (): UseQueryResult<Listing[], ApiError> => {
  return useQuery({
    queryKey: ['listings'],
    queryFn: async () => {
      const response = await listingService.getSavedListings();
      return response.data;
    },
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};

export const useProcessListings = (): UseMutationResult<Listing[], ApiError, ListingPayload> => {
  return useMutation({
    mutationFn: async (payload: ListingPayload) => {
      const response = await listingService.processAsins(payload);
      return response.data;
    },
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
}; 