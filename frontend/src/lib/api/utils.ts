/**
 * API utility functions
 */

/**
 * Generate a download URL for a file using its ID
 * @param fileId The ID of the file to download
 * @returns The complete download URL
 */
export const getFileDownloadUrl = (fileId: string): string => {
  if (!fileId) {
    console.error('Invalid file ID provided to getFileDownloadUrl');
    throw new Error('Invalid file ID');
  }
  
  const baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL || '';
  if (!baseUrl) {
    console.warn('NEXT_PUBLIC_BACKEND_URL is not defined, using relative URL for file download');
  }
  
  // Ensure the file ID is properly formatted
  const sanitizedFileId = fileId.trim();
  const downloadUrl = `${baseUrl}/api/v1/files/download/${sanitizedFileId}/`;
  
  console.log(`Generated download URL: ${downloadUrl}`);
  return downloadUrl;
}; 