import { apiClient } from '../config';
import { ApiResponse, SpAdsPayload, ProcessedFile } from '../types';

export const spService = {
  /**
   * Process SP ads file
   */
  processSpAds: async (payload: SpAdsPayload): Promise<ApiResponse<ProcessedFile>> => {
    const formData = new FormData();
    formData.append('file', payload.file);
    formData.append('target_acos', payload.target_acos.toString());

    const response = await apiClient.post('api/v1/sp/process_spads/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
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