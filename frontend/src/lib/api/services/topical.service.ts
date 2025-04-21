import { apiClient, LONG_OPERATION_TIMEOUT } from '../config';
import { TopicalPayload, TopicalResponse } from '../types';
import { getFileDownloadUrl } from '../utils';

export const topicalService = {
  /**
   * Process Topical analysis
   */
  processTopical: async (payload: TopicalPayload): Promise<TopicalResponse> => {
    const formData = new FormData();
    formData.append('file', payload.file);
    formData.append('min_search_volume', payload.min_search_volume.toString());

    try {
      const response = await apiClient.post('api/v1/topical/process_topical/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: LONG_OPERATION_TIMEOUT,
      });
      
      console.log('Topical API response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Topical API error:', error);
      throw error;
    }
  },

  /**
   * Download file using file_id
   */
  downloadTopicalFile: (fileId: string): string => {
    return getFileDownloadUrl(fileId);
  }
}; 