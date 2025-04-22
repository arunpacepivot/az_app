import { apiClient, LONG_OPERATION_TIMEOUT } from '../config';
import { ApiResponse, SpAdsPayload, SpAdsResponse, ProcessedFile } from '../types';
import { getFileDownloadUrl } from '../utils';

export const spService = {
  /**
   * Process SP ads file
   */
  processSpAds: async (payload: SpAdsPayload): Promise<SpAdsResponse> => {
    const formData = new FormData();
    formData.append('file', payload.file);
    formData.append('target_acos', payload.target_acos.toString());

    try {
      const response = await apiClient.post('api/v1/optimize/all/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: LONG_OPERATION_TIMEOUT,
      });
      
      console.log('SP Ads API response:', response.data);
      
      // Ensure excel_file has file_id if available in the response
      if (response.data && response.data.excel_file && response.data.file_id) {
        response.data.excel_file.file_id = response.data.file_id;
      }
      
      return response.data;
    } catch (error) {
      console.error('SP Ads API error:', error);
      throw error;
    }
  },

  /**
   * Get processed files
   */
  getProcessedFiles: async (): Promise<ApiResponse<ProcessedFile[]>> => {
    try {
      const response = await apiClient.get('api/v1/sp/processed-files/');
      return response.data;
    } catch (error) {
      console.error('Get processed files error:', error);
      throw error;
    }
  },
  
  /**
   * Download file using file_id (if needed)
   */
  downloadFile: (fileId: string): string => {
    if (!fileId) {
      console.error('Invalid file ID for download:', fileId);
      throw new Error('Invalid file ID for download');
    }
    
    const url = getFileDownloadUrl(fileId);
    console.log(`Generating download URL for file ${fileId}: ${url}`);
    return url;
  }
}; 