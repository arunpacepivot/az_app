import { apiClient, LONG_OPERATION_TIMEOUT } from '../config';
import { SqpPayload, SqpResponse } from '../types';
import { getFileDownloadUrl } from '../utils';

export const sqpService = {
  /**
   * Process SQP analysis
   */
  processSqp: async (payload: SqpPayload): Promise<SqpResponse> => {
    try {
      console.log(`Starting SQP processing for file: ${payload.file.name}, size: ${(payload.file.size / 1024 / 1024).toFixed(2)}MB`);
      
      const formData = new FormData();
      formData.append('file', payload.file);
      
      // Log when request starts
      const startTime = Date.now();
      console.log(`SQP API request started at: ${new Date(startTime).toISOString()}`);
      
      const response = await apiClient.post('api/v1/sqp/process_sqp/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: LONG_OPERATION_TIMEOUT,
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total || progressEvent.loaded));
          console.log(`Upload progress: ${percentCompleted}%`);
        },
      });
      
      // Log when response received
      const endTime = Date.now();
      const duration = (endTime - startTime) / 1000;
      console.log(`SQP API response received after ${duration.toFixed(2)} seconds`);
      console.log('SQP API response status:', response.status);
      
      // Check for empty response
      if (!response.data) {
        throw new Error('Empty response received from server');
      }
      
      return response.data;
    } catch (error) {
      console.error('SQP API error:', error);
      throw error;
    }
  },

  /**
   * Download file using file_id
   */
  downloadSqpFile: (fileId: string, url?: string): string => {
    // If direct URL is provided, use it instead of file_id
    if (url && (url.startsWith('http://') || url.startsWith('https://'))) {
      console.log(`Using direct download URL: ${url}`);
      return url;
    }
    
    if (!fileId) {
      console.error('Invalid file ID for download:', fileId);
      throw new Error('Invalid file ID for download');
    }
    
    const downloadUrl = getFileDownloadUrl(fileId);
    console.log(`Generating download URL for file ${fileId}: ${downloadUrl}`);
    return downloadUrl;
  }
}; 