import { useQuery, useMutation, UseQueryResult, UseMutationResult } from '@tanstack/react-query';
import { listingService } from '@/lib/api/services/listing.service';
import { Listing, ListingPayload, ApiError } from '@/lib/api/types';

export const useListings = (): UseQueryResult<Listing[], ApiError> => {
  return useQuery({
    queryKey: ['listings'],
    queryFn: async () => {
      const response = await listingService.getSavedListings();
      if (!response.data) {
        throw new Error('No data received from the server');
      }
      return response.data;
    },
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};

export const useProcessListings = (): UseMutationResult<Listing[], ApiError, ListingPayload> => {
  return useMutation({
    mutationFn: async (payload: ListingPayload) => {
      try {
        const response = await listingService.processAsins(payload);
        if (!response.data) {
          throw new Error('No data received from the server');
        }
        // Ensure we have an array of listings
        const listings = Array.isArray(response.data) ? response.data : [response.data];
        if (listings.length === 0) {
          throw new Error('No listings found for the provided ASINs');
        }
        return listings;
      } catch (error) {
        console.error('Error processing listings:', error);
        throw error;
      }
    },
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
}; 