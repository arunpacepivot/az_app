import { useState } from 'react'
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline'
import { Eye } from 'lucide-react'
import { useProcessNgram } from '@/lib/hooks/queries/use-ngram'
import { getErrorDetails } from '@/lib/utils/error-handler'
import { NgramResponse, NgramFile } from '@/lib/api/types'
import { ngramService } from '@/lib/api/services/ngram.service'

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { FileInput } from "@/components/ui/file-input"
import { ErrorMessage } from '@/components/ui/error-message'
import { EnhancedDataTable } from '@/components/ui/enhanced-data-table'
import { Spinner } from '@/components/shared/Spinner'

// Reusable component for file download item
interface FileDownloadItemProps {
  file: NgramFile;
  onDownload: (file: NgramFile) => void;
}

function FileDownloadItem({ file, onDownload }: FileDownloadItemProps) {
  return (
    <div className="p-4 bg-gray-700/30 rounded-lg border border-gray-600 flex flex-col sm:flex-row gap-3 sm:justify-between sm:items-center">
      <div className="flex-1 min-w-0">
        <p className="text-gray-200 font-medium truncate">{file.filename || `File`}</p>
        <p className="text-gray-400 text-sm">{file.type || 'Analysis File'}</p>
      </div>
      <Button
        onClick={() => onDownload(file)}
        className="bg-gray-600 text-white hover:bg-gray-500 focus:ring-gray-400 flex-shrink-0 flex items-center gap-2 w-full sm:w-auto"
      >
        <ArrowDownTrayIcon className="h-5 w-5" />
        Download
      </Button>
    </div>
  );
}

// Reusable component for success banner with download options
interface SuccessBannerProps {
  sk_asin_count: number;
  mk_asin_count: number;
  files: NgramFile[];
  tableData: Record<string, Array<Record<string, any>>> | null;
  previewOpen: boolean;
  setPreviewOpen: (open: boolean) => void;
  onDownloadFile: (file: NgramFile) => void;
  onDownloadAll: (files: NgramFile[]) => void;
}

function SuccessBanner({
  sk_asin_count,
  mk_asin_count,
  files,
  tableData,
  previewOpen,
  setPreviewOpen,
  onDownloadFile,
  onDownloadAll
}: SuccessBannerProps) {
  const hasMultipleFiles = files && files.length > 1;
  
  return (
    <div className="p-6 bg-green-900/20 rounded-lg border border-green-700/50">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h3 className="text-green-400 text-lg font-semibold flex items-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          Analysis Complete!
        </h3>
        
        <div className="flex flex-wrap gap-3">
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
          
          {/* Single Download Button for Excel */}
          {files && files.length > 0 && (
            <Button
              onClick={() => hasMultipleFiles ? 
                document.getElementById('download-options')?.classList.toggle('hidden') : 
                onDownloadFile(files[0])
              }
              className="bg-green-600 text-white hover:bg-green-500 focus:ring-green-400 flex items-center gap-2"
            >
              <ArrowDownTrayIcon className="h-5 w-5" />
              {hasMultipleFiles ? "Download Files" : "Download Excel"}
            </Button>
          )}
        </div>
      </div>
      
      {/* Show counts in a more compact format */}
      <div className="mt-2 flex flex-wrap gap-4">
        <span className="text-yellow-400"><strong>B0 ASINs:</strong> {sk_asin_count}</span>
        <span className="text-yellow-400"><strong>Non-B0 ASINs:</strong> {mk_asin_count}</span>
      </div>
    </div>
  );
}

export function NgramForm() {
  const [file, setFile] = useState<File | null>(null)
  const [targetACOS, setTargetACOS] = useState<number>(0.2)
  const [progress, setProgress] = useState(0)
  const [processedData, setProcessedData] = useState<NgramResponse | null>(null)
  const [previewOpen, setPreviewOpen] = useState<boolean>(true)

  const { 
    mutate: processNgram,
    isPending: isProcessing,
    error: mutationError,
    reset: resetMutation
  } = useProcessNgram();

  // FORMAT NGRAM DATA FOR DATA TABLE
  const formatDataForTable = () => {
    if (!processedData?.data?.data) {
      return null;
    }

    const { data } = processedData.data;
    
    // Transform the data structure into the format expected by EnhancedDataTable
    // Each ASIN becomes a sheet
    const formattedData: Record<string, Array<Record<string, any>>> = {};
    
    // Process each ASIN entry
    Object.entries(data).forEach(([asin, rows]) => {
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
        formattedData[asin] = sanitizedRows;
      }
    });
    
    return formattedData;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || targetACOS <= 0) return;

    setProgress(0);
    
    // Setup progress simulation with the same pattern as SP tool
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
      await processNgram(
        { file, target_acos: targetACOS },
        {
          onSuccess: (response) => {
            clearInterval(progressInterval);
            setProgress(100);
            
            // Handle the response
            try {
              let parsedResponse: NgramResponse;
              
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
              
              console.log('Processed N-gram Analysis response:', parsedResponse);
              
              // Additional validation
              if (!parsedResponse || !parsedResponse.data) {
                throw new Error('Invalid response format: Missing data property');
              }
              
              // Make sure data.data exists
              if (!parsedResponse.data.data) {
                console.warn('Response is missing data.data property. Creating empty object.');
                parsedResponse.data.data = {};
              }
              
              // Ensure all required properties exist
              const requiredProps = ['status', 'message', 'sk_asin_count', 'mk_asin_count'];
              for (const prop of requiredProps) {
                if (parsedResponse.data[prop as keyof typeof parsedResponse.data] === undefined) {
                  console.warn(`Response is missing ${prop} property. Setting default value.`);
                  
                  // Set default values based on property type
                  if (prop === 'status') parsedResponse.data.status = 'success';
                  else if (prop === 'message') parsedResponse.data.message = 'Analysis completed';
                  else if (prop === 'sk_asin_count') parsedResponse.data.sk_asin_count = 0;
                  else if (prop === 'mk_asin_count') parsedResponse.data.mk_asin_count = 0;
                }
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
            console.error('Ngram Analysis Error:', error);
          },
        }
      );
    } catch (error) {
      clearInterval(progressInterval);
      setProgress(0);
      console.error('Unexpected error during ngram processing:', error);
    }
  };

  const handleReset = () => {
    setFile(null);
    setTargetACOS(0.2);
    setProgress(0);
    setProcessedData(null);
    setPreviewOpen(true);
    resetMutation();
  };

  // File download handler
  const handleDownloadFile = (file: NgramFile) => {
    try {
      console.log('Downloading file:', file);
      
      // Check if we have a direct URL first
      if (file.url && (file.url.startsWith('http://') || file.url.startsWith('https://'))) {
        console.log('Using direct URL for download:', file.url);
        window.open(file.url, '_blank');
        return;
      }
      
      if (!file.file_id) {
        console.error('Missing file_id in file object:', file);
        alert('Error: File ID is missing. Cannot download the file.');
        return;
      }
      
      // Use the service function with both file_id and url
      const serviceUrl = ngramService.downloadNgramFile(file.file_id, file.url);
      console.log('Generated download URL:', serviceUrl);
      
      // Open in new tab for reliable downloading
      window.open(serviceUrl, '_blank');
    } catch (error) {
      console.error('Error downloading file:', error);
      alert('There was an error downloading the file. Please try again.');
    }
  };
  
  // Function to download all files
  const handleDownloadAll = (files: NgramFile[]) => {
    // Download each file with a small delay to prevent browser blocking
    files.forEach((file, index) => {
      setTimeout(() => {
        handleDownloadFile(file);
      }, index * 500);
    });
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
    const hasMultipleFiles = processedData.data.files && processedData.data.files.length > 1;
    
    return (
      <div className="mt-8 space-y-6">
        {/* Success Banner using reusable component */}
        <SuccessBanner
          sk_asin_count={processedData.data.sk_asin_count}
          mk_asin_count={processedData.data.mk_asin_count}
          files={processedData.data.files || []}
          tableData={tableData}
          previewOpen={previewOpen}
          setPreviewOpen={setPreviewOpen}
          onDownloadFile={handleDownloadFile}
          onDownloadAll={(files) => handleDownloadAll(files)}
        />

        {/* Hidden download options that appear when Download Files is clicked */}
        {hasMultipleFiles && (
          <div id="download-options" className="hidden p-6 bg-gray-800/40 rounded-lg border border-gray-700/50">
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-4">
              <h3 className="text-yellow-400 text-lg font-semibold">Download Analysis Files</h3>
              <Button
                onClick={() => handleDownloadAll(processedData.data.files)}
                className="bg-green-600 text-white hover:bg-green-500 focus:ring-green-400 flex items-center gap-2 w-full sm:w-auto"
              >
                <ArrowDownTrayIcon className="h-5 w-5" />
                Download All
              </Button>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {processedData.data.files.map((file, index) => (
                <FileDownloadItem 
                  key={index} 
                  file={file} 
                  onDownload={handleDownloadFile} 
                />
              ))}
            </div>
          </div>
        )}

        {/* Data Preview Table */}
        {previewOpen && (
          <>
            {tableData && Object.keys(tableData).length > 0 ? (
              <EnhancedDataTable
                data={tableData}
                title="N-gram Analysis Results by ASIN"
                description="Preview the analyzed keywords and performance data by ASIN"
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
                  You can still download the analysis files above.
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

        {/* Debug View - Commented out as requested */}
        {/* 
        <details className="bg-gray-800/40 rounded-lg border border-gray-700/50 p-4">
          <summary className="text-yellow-400 text-sm font-medium cursor-pointer">Show Raw Data (Debug)</summary>
          <div className="mt-2 bg-gray-900 p-4 rounded-md overflow-auto max-h-80">
            <pre className="text-xs text-gray-300 whitespace-pre-wrap">
              {JSON.stringify(processedData.data.data, null, 2)}
            </pre>
          </div>
        </details>
        */}
      </div>
    );
  };

  return (
    <main className="flex-1">
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 p-6 flex flex-col items-center justify-center">
        <Card className="w-full max-w-4xl mt-0 border border-gray-700 shadow-xl bg-gray-900/60 backdrop-blur-sm">
          <CardHeader className="border-b border-gray-700/50 pb-6">
            <CardTitle className="text-3xl font-bold text-center text-yellow-400">
              N-gram Analysis Tool
            </CardTitle>
            <CardDescription className="text-center text-gray-300 mt-2">
              Analyze your Amazon bulk files to discover top-performing keywords and optimize your campaigns
            </CardDescription>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-12">
              {/* Target ACOS Input */}
              <div className="space-y-8 p-4">
                <Label htmlFor="targetACOS" className="text-yellow-400">
                  Target ACOS
                </Label>
                <div className="flex flex-col space-y-2">
                  <div className="relative w-1/4">
                    <input
                      id="targetACOS"
                      type="number"
                      min="0"
                      max="1"
                      step="0.01"
                      value={targetACOS}
                      onChange={(e) => {
                        const value = parseFloat(e.target.value)
                        if (!isNaN(value)) {
                          const clampedValue = Math.min(Math.max(value, 0), 1)
                          setTargetACOS(Number(clampedValue.toFixed(2)))
                        }
                      }}
                      className="w-full bg-gray-900 text-white border border-gray-700 focus:ring-1 focus:ring-yellow-400/50 focus:border-yellow-400/50 rounded-md p-2 outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none pr-8 text-sm font-medium"
                      placeholder="0.2"
                    />
                    <div className="absolute right-0 top-0 bottom-0 w-7 flex flex-col border-l border-gray-700/50">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.preventDefault()
                          const newValue = Math.min(targetACOS + 0.01, 1)
                          setTargetACOS(Number(newValue.toFixed(2)))
                        }}
                        className="flex-1 flex items-center justify-center hover:bg-gray-800 text-gray-500 hover:text-yellow-400 transition-all duration-150 rounded-tr-md"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
                          <path fillRule="evenodd" d="M14.77 12.79a.75.75 0 01-1.06-.02L10 8.832 6.29 12.77a.75.75 0 11-1.08-1.04l4.25-4.5a.75.75 0 011.08 0l4.25 4.5a.75.75 0 01-.02 1.06z" clipRule="evenodd" />
                        </svg>
                      </button>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.preventDefault()
                          const newValue = Math.max(targetACOS - 0.01, 0)
                          setTargetACOS(Number(newValue.toFixed(2)))
                        }}
                        className="flex-1 flex items-center justify-center hover:bg-gray-800 text-gray-500 hover:text-yellow-400 transition-all duration-150 rounded-br-md border-t border-gray-700/50"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
                          <path fillRule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clipRule="evenodd" />
                        </svg>
                      </button>
                    </div>
                  </div>
                  <p className="text-gray-400 text-sm">Enter a value between 0 and 1 (e.g., 0.2 for 20% ACOS)</p>
                </div>
              </div>

              {/* File Upload Section */}
              <div className="space-y-4 p-4 bg-gray-800/40 rounded-lg border border-gray-700/50">
                <Label htmlFor="file" className="text-yellow-400 text-lg font-medium">
                  Upload Bulk File (Excel)
                </Label>
                <div className="flex flex-col space-y-4">
                  <div className="flex items-center space-x-4">
                    <div className="relative w-full">
                      <Button 
                        type="button"
                        className="relative bg-yellow-400 text-black hover:bg-yellow-300 focus:ring-yellow-400 transition-all duration-200 w-full flex items-center justify-center"
                        onClick={() => document.getElementById('file')?.click()}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                        {file ? "Change File" : "Choose File"}
                      </Button>
                      <FileInput
                        id="file"
                        accept=".xlsx"
                        onFileSelect={handleFileChange}
                        className="sr-only"
                      />
                    </div>
                  </div>
                  {file && (
                    <div className="flex items-center p-3 bg-gray-800/80 rounded-lg border border-gray-700 text-sm text-white">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="truncate font-medium">{file.name}</span>
                    </div>
                  )}
                  <p className="text-gray-400 text-sm">Upload the Amazon Advertising bulk file that contains your campaigns for n-gram analysis</p>
                </div>
              </div>

              {/* Form Actions */}
              <div className="flex space-x-4 pt-4">
                <Button
                  type="submit"
                  disabled={isProcessing || !file || !targetACOS}
                  className="w-3/4 bg-yellow-400 text-black hover:bg-yellow-300 focus:ring-yellow-400 flex items-center justify-center transition-all duration-200 transform hover:translate-y-[-2px] shadow-lg"
                >
                  {isProcessing ? (
                    <div className="flex items-center justify-center">
                      <Spinner size="sm" />
                      <span className="ml-2">Processing...</span>
                    </div>
                  ) : "Run N-gram Analysis"}
                </Button>
                <Button
                  type="button"
                  onClick={handleReset}
                  disabled={isProcessing}
                  className="w-1/4 bg-gray-700 text-white hover:bg-gray-600 transition-all duration-200 border border-gray-600"
                >
                  Reset
                </Button>
              </div>
            </form>

            {/* Processing Indicator */}
            {isProcessing && (
              <div className="mt-8 p-4 bg-gray-800/40 rounded-lg border border-gray-700/50 space-y-4">
                <Label className="text-yellow-400 font-medium">Processing Your Excel File...</Label>
                <Progress value={progress} className="w-full h-2 bg-gray-700" />
                <p className="text-gray-400 text-sm">
                  This process may take 5-6 minutes to complete. Please keep this page open.
                  We are analyzing your campaigns using advanced n-gram techniques.
                </p>
              </div>
            )}

            {/* Results Section */}
            {processedData && renderResults()}

            {/* Error Message */}
            {mutationError && (
              <ErrorMessage
                message={getErrorDetails(mutationError).message}
                onRetry={resetMutation}
                className="mt-8"
              />
            )}
          </CardContent>
        </Card>
      </div>
    </main>
  )
} 