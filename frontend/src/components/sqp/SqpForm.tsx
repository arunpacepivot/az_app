'use client'
import { useState } from 'react'
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline'
import { Eye } from 'lucide-react'
import { useProcessSqp } from '@/lib/hooks/queries/use-sqp'
import { getErrorDetails } from '@/lib/utils/error-handler'
import { SqpResponse, SqpFile } from '@/lib/api/types'
import { sqpService } from '@/lib/api/services/sqp.service'

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { FileInput } from "@/components/ui/file-input"
import { ErrorMessage } from '@/components/ui/error-message'
import { EnhancedDataTable } from '@/components/ui/enhanced-data-table'
import { Spinner } from '@/components/shared/Spinner'

// Reusable component for success banner with download options
interface SuccessBannerProps {
  file: SqpFile | undefined;
  tableData: Record<string, Array<Record<string, any>>> | null;
  keywordCount: number;
  previewOpen: boolean;
  setPreviewOpen: (open: boolean) => void;
  onDownload: () => void;
}

function SuccessBanner({
  file,
  tableData,
  keywordCount,
  previewOpen,
  setPreviewOpen,
  onDownload
}: SuccessBannerProps) {
  return (
    <div className="p-6 bg-green-900/20 rounded-lg border border-green-700/50">
      <div className="flex items-center justify-between">
        <h3 className="text-green-400 text-lg font-semibold flex items-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          SQP Analysis Complete!
        </h3>
        
        <div className="flex space-x-3">
          {/* Preview Data Button - Only shown when preview is closed */}
          {!previewOpen && tableData && Object.keys(tableData).length > 0 && (
            <Button
              onClick={() => setPreviewOpen(true)}
              className="bg-gray-600 text-white hover:bg-gray-500 focus:ring-gray-400 flex items-center gap-2"
            >
              <Eye className="h-5 w-5" />
              Preview Data
            </Button>
          )}
          
          {/* Download Button for Excel */}
          {file && (
            <Button
              onClick={onDownload}
              className="bg-green-600 text-white hover:bg-green-500 focus:ring-green-400 flex items-center gap-2"
            >
              <ArrowDownTrayIcon className="h-5 w-5" />
              Download Excel
            </Button>
          )}
        </div>
      </div>
      
      {/* Show keyword count in a more compact format */}
      <div className="mt-2 flex flex-wrap gap-4">
        <span className="text-yellow-400"><strong>Keywords Analyzed:</strong> {keywordCount}</span>
      </div>
    </div>
  );
}

export function SqpForm() {
  const [file, setFile] = useState<File | null>(null)
  const [progress, setProgress] = useState(0)
  const [processedData, setProcessedData] = useState<SqpResponse | null>(null)
  const [previewOpen, setPreviewOpen] = useState<boolean>(true)

  const { 
    mutate: processSqp,
    isPending: isProcessing,
    error: mutationError,
    reset: resetMutation
  } = useProcessSqp();

  // FORMAT SQP DATA FOR DATA TABLE
  const formatDataForTable = () => {
    if (!processedData?.data?.data) {
      return null;
    }

    const { data } = processedData.data;
    
    // The data is already in the format expected by EnhancedDataTable
    // Just need to ensure values are sanitized for table display
    const formattedData: Record<string, Array<Record<string, any>>> = {};
    
    // Process each category of data
    Object.entries(data).forEach(([category, rows]) => {
      if (Array.isArray(rows)) {
        // Replace any NaN or Infinity values with null
        // Also sanitize field names by replacing dots with underscores
        const sanitizedRows = rows.map(row => {
          const sanitizedRow: Record<string, any> = {};
          Object.entries(row).forEach(([key, value]) => {
            // Replace dots in keys with underscores to avoid column ID issues
            const sanitizedKey = key.replace(/\./g, '_');
            
            // Handle NaN and Infinity values
            if (typeof value === 'number' && (isNaN(value) || !isFinite(value))) {
              sanitizedRow[sanitizedKey] = null;
            } else {
              sanitizedRow[sanitizedKey] = value;
            }
          });
          return sanitizedRow;
        });
        formattedData[category] = sanitizedRows;
      }
    });
    
    // Add keywords as a separate sheet if they exist
    if (processedData.data.keywords && processedData.data.keywords.length > 0) {
      // Format keywords as rows with a single column
      const keywordRows = processedData.data.keywords.map(keyword => ({
        keyword: keyword
      }));
      
      formattedData['Keywords'] = keywordRows;
    }
    
    return formattedData;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setProgress(0);
    
    // Setup progress simulation
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev < 20) return prev + 0.5;
        if (prev < 40) return prev + 0.3;
        if (prev < 60) return prev + 0.2;
        if (prev < 80) return prev + 0.1;
        if (prev < 90) return prev + 0.05;
          return prev;
        });
    }, 1000);
      
    try {
      await processSqp(
        { file },
        {
          onSuccess: (response) => {
            clearInterval(progressInterval);
            setProgress(100);
            
            // Handle the response
            try {
              let parsedResponse: SqpResponse;
              
              // Handle string response
              if (typeof response === 'string') {
                // Clean response by replacing NaN values
                const cleanedResponse = (response as string)
                  .replace(/:\s*NaN/g, ': null')
                  .replace(/:\s*Infinity/g, ': null')
                  .replace(/:\s*-Infinity/g, ': null');
                  
                console.log('Cleaned response string:', cleanedResponse);
                parsedResponse = JSON.parse(cleanedResponse);
              } 
              // Handle object response
              else {
                // Create a clean copy by serializing and deserializing
                const responseString = JSON.stringify(response, (_, value) => {
                  if (typeof value === 'number' && (isNaN(value) || !isFinite(value))) {
                    return null;
                  }
                  return value;
                });
                parsedResponse = JSON.parse(responseString);
              }
              
              console.log('Processed SQP Analysis response:', parsedResponse);
              
              // Additional validation
              if (!parsedResponse || !parsedResponse.data) {
                throw new Error('Invalid response format: Missing data property');
              }
              
              // Store the processed data
              setProcessedData(parsedResponse);
            } catch (error) {
              console.error('Error processing response:', error);
              console.error('Raw response:', response);
              alert('Failed to process the server response. See console for details.');
            }
          },
          onError: (error) => {
            clearInterval(progressInterval);
            setProgress(0);
            console.error('SQP Analysis Error:', error);
          },
        }
      );
    } catch (error) {
      clearInterval(progressInterval);
      setProgress(0);
      console.error('Unexpected error during SQP processing:', error);
    }
  };

  const handleReset = () => {
    setFile(null);
    setProgress(0);
    setProcessedData(null);
    setPreviewOpen(true);
    resetMutation();
  };

  // File download handler
  const handleDownloadFile = () => {
    try {
      if (!processedData?.data?.file) {
        console.error('Missing file information in response:', processedData);
        alert('Error: File information is missing. Cannot download the file.');
        return;
      }
      
      const fileData = processedData.data.file;
      
      // Check if we have a direct URL first
      if (fileData.url && (fileData.url.startsWith('http://') || fileData.url.startsWith('https://'))) {
        console.log('Using direct URL for download:', fileData.url);
        window.open(fileData.url, '_blank');
        return;
      }
      
      if (!fileData.file_id) {
        console.error('Missing file_id in file object:', fileData);
        alert('Error: File ID is missing. Cannot download the file.');
        return;
      }
      
      // Use the service function with both file_id and url
      const downloadUrl = sqpService.downloadSqpFile(fileData.file_id, fileData.url);
      console.log('Generated download URL:', downloadUrl);
      
      // Open in new tab for reliable downloading
      window.open(downloadUrl, '_blank');
    } catch (error) {
      console.error('Error downloading file:', error);
      alert('There was an error downloading the file. Please try again.');
    }
  };
  
  const handleFileChange = (selectedFile: File) => {
    // Max file size: 20MB
    const MAX_FILE_SIZE = 20 * 1024 * 1024;
    
    if (selectedFile.size > MAX_FILE_SIZE) {
      alert('File size exceeds 20MB limit. Please upload a smaller file or split your data into multiple files.');
      return;
    }
    
    setFile(selectedFile);
  };

  // RENDER THE RESULTS SECTION
  const renderResults = () => {
    if (!processedData || !processedData.data) return null;
    
    const tableData = formatDataForTable();
    const keywordCount = processedData.data.keywords?.length ?? 0;
    
    return (
      <div className="mt-8 space-y-6">
        {/* Success Banner using reusable component */}
        <SuccessBanner
          file={processedData.data.file}
          tableData={tableData}
          keywordCount={keywordCount}
          previewOpen={previewOpen}
          setPreviewOpen={setPreviewOpen}
          onDownload={handleDownloadFile}
        />

        {/* Data Preview Table */}
        {previewOpen && (
          <>
            {tableData && Object.keys(tableData).length > 0 ? (
              <EnhancedDataTable
                data={tableData}
                title="SQP Analysis Results"
                description="Preview the analyzed keywords and performance data by category"
              />
            ) : (
              <div className="p-6 bg-red-900/20 rounded-lg border border-red-700/50">
                <h3 className="text-red-400 text-lg font-semibold flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  Data Format Error
                </h3>
                <p className="text-gray-300 mt-2">
                  The analysis data could not be displayed in a table. This may be due to a structure incompatible with the table component.
                  You can still download the analysis file above.
                </p>
                <Button
                  onClick={handleReset}
                  className="mt-4 bg-red-600 text-white hover:bg-red-500 focus:ring-red-400"
                >
                  Reset and Try Again
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    );
  };

  return (
    <main className="flex-1">
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 py-12 px-6 flex flex-col items-center">
        <div className="w-full max-w-4xl">
          <Card className="w-full border border-gray-700 shadow-xl bg-gray-900/60 backdrop-blur-sm">
            <CardHeader className="border-b border-gray-700/50 pb-6">
              <CardTitle className="text-3xl font-bold text-center text-yellow-400">
                SQP Analysis Tool
              </CardTitle>
              <CardDescription className="text-center text-gray-300 mt-2">
                Analyze your search query performance to identify high-performing keywords and opportunities for improvement
              </CardDescription>
            </CardHeader>

            <CardContent className="pt-8">
              <form onSubmit={handleSubmit} className="space-y-16">
                {/* File Upload Section */}
                <div className="space-y-6 p-6 bg-gray-800/40 rounded-lg border border-gray-700/50">
                  <Label htmlFor="file" className="text-yellow-400 text-lg font-medium">
                    Upload CSV File
                  </Label>
                  <div className="flex flex-col space-y-6">
                    <div className="flex items-center space-x-4">
                      <div className="relative w-full">
                        <Button 
                          type="button"
                          className="relative bg-yellow-400 text-black hover:bg-yellow-300 focus:ring-yellow-400 transition-all duration-200 w-full flex items-center justify-center py-6"
                          onClick={() => document.getElementById('file')?.click()}
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                          </svg>
                          {file ? "Change File" : "Choose File"}
                        </Button>
                        <FileInput
                          id="file"
                          accept=".csv"
                          onFileSelect={handleFileChange}
                          className="sr-only"
                        />
                      </div>
                    </div>
                    {file && (
                      <div className="flex items-center p-4 bg-gray-800/80 rounded-lg border border-gray-700 text-sm text-white">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span className="truncate font-medium">{file.name}</span>
                      </div>
                    )}
                    <p className="text-gray-400 text-sm mt-2">Upload a CSV file containing your search query performance data</p>
                  </div>
                </div>

                {/* Form Actions */}
                <div className="flex space-x-4 pt-4 mb-6">
                  <Button
                    type="submit"
                    disabled={isProcessing || !file}
                    className="w-3/4 bg-yellow-400 text-black hover:bg-yellow-300 focus:ring-yellow-400 flex items-center justify-center transition-all duration-200 transform hover:translate-y-[-2px] shadow-lg py-6"
                  >
                    {isProcessing ? (
                      <div className="flex items-center justify-center">
                        <Spinner size="sm" />
                        <span className="ml-2">Processing...</span>
                      </div>
                    ) : "Run SQP Analysis"}
                  </Button>
                  <Button
                    type="button"
                    onClick={handleReset}
                    disabled={isProcessing}
                    className="w-1/4 bg-gray-700 text-white hover:bg-gray-600 transition-all duration-200 border border-gray-600 py-6"
                  >
                    Reset
                  </Button>
                </div>
              </form>

              {/* Processing Indicator */}
              {isProcessing && (
                <div className="mt-12 p-6 bg-gray-800/40 rounded-lg border border-gray-700/50 space-y-4">
                  <Label className="text-yellow-400 font-medium">Processing Your CSV File...</Label>
                  <Progress value={progress} className="w-full h-2 bg-gray-700" />
                  <p className="text-gray-400 text-sm">
                    This process may take a few minutes to complete. Please keep this page open.
                    We are analyzing your search query performance data.
                  </p>
                </div>
              )}

              {/* Results Section */}
              {processedData && renderResults()}

              {/* Empty Data Handling */}
              {processedData && !processedData.data?.data && (
                <div className="mt-12 p-6 bg-red-900/20 rounded-lg border border-red-700/50">
                  <h3 className="text-red-400 text-lg font-semibold flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    No Analysis Data
                  </h3>
                  <p className="text-gray-300 mt-2">
                    No analysis data was returned. This might be because there were no matching patterns in your data.
                    Please try with a different CSV file.
                  </p>
                  <Button
                    onClick={handleReset}
                    className="mt-4 bg-red-600 text-white hover:bg-red-500 focus:ring-red-400"
                  >
                    Reset and Try Again
                  </Button>
                </div>
              )}

              {/* Error Message */}
              {mutationError && (
                <ErrorMessage
                  message={getErrorDetails(mutationError).message}
                  onRetry={resetMutation}
                  className="mt-12"
                />
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  )
} 