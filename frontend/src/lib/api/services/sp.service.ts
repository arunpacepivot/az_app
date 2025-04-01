import { apiClient } from '../config';
import { ApiResponse, SpAdsPayload, SpAdsResponse, ProcessedFile } from '../types';

export const spService = {
  /**
   * Process SP ads file
   */
  processSpAds: async (payload: SpAdsPayload): Promise<SpAdsResponse> => {
    const formData = new FormData();
    formData.append('file', payload.file);
    formData.append('target_acos', payload.target_acos.toString());

    const response = await apiClient.post('api/v1/optimize/all/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 3000000, // 5 minutes timeout
    });
    return response.data;
  },

  /**
   * Get processed files
   */
  getProcessedFiles: async (): Promise<ApiResponse<ProcessedFile[]>> => {
    const response = await apiClient.get('api/v1/sp/processed-files/');
    return response.data;
  },
}; 