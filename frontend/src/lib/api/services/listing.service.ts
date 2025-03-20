import { apiClient } from '../config';
import { ApiResponse, Listing, ListingPayload } from '../types';

export const listingService = {
  /**
   * Process ASINs to generate listings
   */
  processAsins: async (payload: ListingPayload): Promise<ApiResponse<Listing[]>> => {
    try {
      const response = await apiClient.post('api/v1/lister/process_asins/', payload);
      return response.data;
    } catch (error) {
      console.error('Error processing ASINs:', error);
      throw error;
    }
  },

  /**
   * Get saved listings
   */
  getSavedListings: async (): Promise<ApiResponse<Listing[]>> => {
    try {
      const response = await apiClient.get('api/v1/lister/products/');
      return response.data;
    } catch (error) {
      console.error('Error getting saved listings:', error);
      throw error;
    }
  },
}; 