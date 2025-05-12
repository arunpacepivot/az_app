/* eslint-disable @typescript-eslint/no-explicit-any */
import { apiClient } from '../config';
import { ApiResponse, Listing, ListingPayload } from '../types';

export const listingService = {
  /**
   * Process ASINs to generate listings
   */
  processAsins: async (payload: ListingPayload): Promise<ApiResponse<Listing[]>> => {
    try {
      if (!payload.asins || !payload.geography) {
        throw new Error('Missing required fields: asins or geography');
      }

      const response = await apiClient.post('api/v1/lister/process_asins/', {
        asins: payload.asins.trim(),
        geography: payload.geography.trim()
      });

      // Validate response
      if (!response.data) {
        throw new Error('No data received from server');
      }

      // Ensure data is properly structured
      const listings = response.data.data || response.data;
      if (!Array.isArray(listings)) {
        throw new Error('Invalid response format: expected an array of listings');
      }

      return {
        data: listings,
        status: response.status,
        message: response.data.message
      };
    } catch (error: any) {
      console.error('Error processing ASINs:', error);
      throw {
        message: error.response?.data?.message || error.message || 'Failed to process ASINs',
        code: error.response?.status,
        details: error.response?.data
      };
    }
  },

  /**
   * Get saved listings
   */
  getSavedListings: async (): Promise<ApiResponse<Listing[]>> => {
    try {
      const response = await apiClient.get('api/v1/lister/products/');
      
      // Validate response
      if (!response.data) {
        throw new Error('No data received from server');
      }

      // Ensure data is properly structured
      const listings = response.data.data || response.data;
      if (!Array.isArray(listings)) {
        throw new Error('Invalid response format: expected an array of listings');
      }

      return {
        data: listings,
        status: response.status,
        message: response.data.message
      };
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (error: any) {
      console.error('Error getting saved listings:', error);
      throw {
        message: error.response?.data?.message || error.message || 'Failed to get saved listings',
        code: error.response?.status,
        details: error.response?.data
      };
    }
  },
}; 