import { apiClient, LONG_OPERATION_TIMEOUT } from '../config';
import { CerebroPayload, CerebroResponse } from '../types';
import { getFileDownloadUrl } from '../utils';

export const cerebroService = {
  /**
   * Process Cerebro analysis
   */
  processCerebro: async (payload: CerebroPayload): Promise<CerebroResponse> => {
    const formData = new FormData();
    formData.append('file', payload.file);
    formData.append('min_search_volume', payload.min_search_volume.toString());

    try {
      const response = await apiClient.post('api/v1/cerebro/process_cerebro/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: LONG_OPERATION_TIMEOUT,
      });
      
      console.log('Cerebro API response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Cerebro API error:', error);
      throw error;
    }
  },

  /**
   * Download file using file_id
   */
  downloadCerebroFile: (fileId: string, url?: string): string => {
    // If direct URL is provided, use it instead of file_id
    if (url && (url.startsWith('http://') || url.startsWith('https://'))) {
      console.log(`Using direct download URL: ${url}`);
      return url;
    }
    
    if (!fileId) {
      console.error('Invalid file ID for download:', fileId);
      throw new Error('Invalid file ID for download');
    }
    
    return getFileDownloadUrl(fileId);
  }
}; 