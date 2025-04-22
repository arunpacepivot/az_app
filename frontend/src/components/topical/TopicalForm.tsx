"use client";

import { useState, useRef } from 'react';
import { useProcessTopical } from '@/lib/hooks/queries/use-topical';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2, Upload, Download, Eye } from 'lucide-react';
import { TopicalResponse, TopicalFile } from '@/lib/api/types';
import { topicalService } from '@/lib/api/services/topical.service';
import { Label } from '@/components/ui/label';
import { Progress } from "@/components/ui/progress";
import { FileInput } from "@/components/ui/file-input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { EnhancedDataTable } from '@/components/ui/enhanced-data-table';
import { Spinner } from '@/components/shared/Spinner';

// Reusable component for file download item
interface FileDownloadItemProps {
  file: TopicalFile;
  onDownload: (file: TopicalFile) => void;
}

function FileDownloadItem({ file, onDownload }: FileDownloadItemProps) {
  return (
    <div className="p-4 bg-gray-700/30 rounded-lg border border-gray-600 flex justify-between items-center">
      <div className="flex flex-col space-y-1">
        <span className="text-gray-200 font-medium truncate max-w-xs">{file.filename || `File`}</span>
        <span className="text-gray-400 text-sm">Topical Analysis File</span>
      </div>
      <Button
        onClick={() => onDownload(file)}
        className="bg-gray-600 text-white hover:bg-gray-500 focus:ring-gray-400 flex items-center gap-2"
      >
        <Download className="h-5 w-5" />
        Download
      </Button>
    </div>
  );
}

// Reusable component for success banner
interface SuccessBannerProps {
  b0_asin_count: number;
  non_b0_asin_count: number;
  file: TopicalFile | undefined;
  tableData: Record<string, Array<Record<string, any>>> | null;
  previewOpen: boolean;
  setPreviewOpen: (open: boolean) => void;
  onDownload: () => void;
}

function SuccessBanner({
  b0_asin_count,
  non_b0_asin_count,
  file,
  tableData,
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
          Analysis Complete!
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
          
          {file && (
            <Button
              onClick={onDownload}
              className="bg-green-600 text-white hover:bg-green-500 focus:ring-green-400 flex items-center gap-2"
            >
              <Download className="h-5 w-5" />
              Download Excel
            </Button>
          )}
        </div>
      </div>
      
      {/* Show counts in a more compact format */}
      <div className="mt-2 flex flex-wrap gap-4">
        <span className="text-yellow-400"><strong>B0 ASINs:</strong> {b0_asin_count}</span>
        <span className="text-yellow-400"><strong>Non-B0 ASINs:</strong> {non_b0_asin_count}</span>
      </div>
    </div>
  );
}

export function TopicalForm() {
  const [file, setFile] = useState<File | null>(null);
  const [minSearchVolume, setMinSearchVolume] = useState<number>(100);
  const [processedData, setProcessedData] = useState<TopicalResponse | null>(null);
  const [previewOpen, setPreviewOpen] = useState<boolean>(true);
  const [progress, setProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const { mutate, isPending: isLoading, isError, error } = useProcessTopical();

  const handleFileChange = (selectedFile: File) => {
    // Max file size: 20MB
    const MAX_FILE_SIZE = 20 * 1024 * 1024;
    
    if (selectedFile.size > MAX_FILE_SIZE) {
      alert('File size exceeds 20MB limit. Please upload a smaller file or split your data into multiple files.');
      return;
    }
    
    setFile(selectedFile);
  };

  const handleProcessTopical = () => {
    if (!file) {
      alert("Please select a file to upload");
      return;
    }

    if (minSearchVolume < 1) {
      alert("Minimum search volume must be greater than 0");
      return;
    }

    // Reset any previous data
    setProcessedData(null);
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

    mutate(
      { file, min_search_volume: minSearchVolume },
      {
        onSuccess: (data) => {
          try {
            clearInterval(progressInterval);
            setProgress(100);
            
            // Handle any data cleaning if needed
            if (typeof data === 'string') {
              // Clean response by replacing NaN and Infinity values
              const cleanedResponse = (data as string)
                .replace(/:\s*NaN/g, ': null')
                .replace(/:\s*Infinity/g, ': null')
                .replace(/:\s*-Infinity/g, ': null');
                
              setProcessedData(JSON.parse(cleanedResponse));
            } else {
              setProcessedData(data);
            }
            console.log('Topical analysis completed successfully:', data);
          } catch (error) {
            console.error('Error processing response:', error);
            alert('Failed to process the server response. See console for details.');
          }
        },
        onError: (error) => {
          clearInterval(progressInterval);
          setProgress(0);
          console.error('Error processing topical analysis:', error);
          alert(error.message || "Failed to process topical analysis");
        },
      }
    );
  };

  const handleDownload = () => {
    if (processedData?.data?.file) {
      try {
        // Check if we have a direct URL first
        if (processedData.data.file.url && 
           (processedData.data.file.url.startsWith('http://') || 
            processedData.data.file.url.startsWith('https://'))) {
          window.open(processedData.data.file.url, '_blank');
        } else if (processedData.data.file.file_id) {
          // Fallback to using the service with the file_id
          const downloadUrl = topicalService.downloadTopicalFile(processedData.data.file.file_id);
          window.open(downloadUrl, '_blank');
        } else {
          throw new Error('No valid download URL or file ID found');
        }
      } catch (error) {
        console.error('Error downloading file:', error);
        alert('There was an error downloading the file. Please try again.');
      }
    }
  };

  // Format data for EnhancedDataTable if available
  const formatDataForTable = () => {
    if (!processedData?.data?.data) {
      return null;
    }

    // Transform the data structure into the format expected by EnhancedDataTable
    const formattedData: Record<string, Array<Record<string, any>>> = {};
    
    // The data structure should be an object with "B0 ASINs" and "Non-B0 ASINs" keys
    // Each containing an array of objects
    const { data } = processedData.data;
    
    try {
      // Process B0 ASINs if they exist
      if (data["B0 ASINs"] && Array.isArray(data["B0 ASINs"])) {
        const sanitizedRows = data["B0 ASINs"].map(row => {
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
        formattedData['B0 ASINs'] = sanitizedRows;
      }
      
      // Process Non-B0 ASINs if they exist
      if (data["Non-B0 ASINs"] && Array.isArray(data["Non-B0 ASINs"])) {
        const sanitizedRows = data["Non-B0 ASINs"].map(row => {
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
        formattedData['Non-B0 ASINs'] = sanitizedRows;
      }
    } catch (error) {
      console.error('Error formatting table data:', error);
      console.error('Raw data:', data);
      return null;
    }
    
    return formattedData;
  };

  // Check if there's data to preview
  const tableData = processedData ? formatDataForTable() : null;
  const hasPreviewData = tableData !== null && Object.keys(tableData || {}).length > 0;

  const handleReset = () => {
    setFile(null);
    setMinSearchVolume(100);
    setProcessedData(null);
    setPreviewOpen(true);
    setProgress(0);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="flex-1 bg-[#111827] min-h-screen">
      <div className="container mx-auto py-8 px-4">
        <h1 className="text-4xl font-bold text-yellow-400 mb-2">Topical Analysis Tool</h1>
        <p className="text-gray-300 mb-8">Analyze your Amazon bulk files to discover topical trends and optimize your campaigns</p>
        
        <div className="bg-[#131b2c] p-8 rounded-lg border border-gray-700 shadow-xl">
          <div className="space-y-8">
            {/* Minimum Search Volume Section */}
            <div>
              <h2 className="text-yellow-400 text-xl font-medium mb-4">Minimum Search Volume</h2>
              <div className="max-w-xs">
                <div className="relative">
                  <input
                    type="number"
                    min="1"
                    step="1"
                    value={minSearchVolume}
                    onChange={(e) => {
                      const value = parseInt(e.target.value, 10);
                      if (!isNaN(value)) {
                        setMinSearchVolume(Math.max(value, 1));
                      }
                    }}
                    className="w-full bg-gray-900 text-white border border-gray-700 focus:ring-1 focus:ring-yellow-400/50 focus:border-yellow-400/50 rounded-md p-2 outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none pr-8 text-sm font-medium"
                    placeholder="100"
                  />
                  <div className="absolute right-0 top-0 bottom-0 w-7 flex flex-col border-l border-gray-700/50">
                    <button
                      type="button"
                      onClick={() => setMinSearchVolume(prev => Math.max(prev + 10, 1))}
                      className="flex-1 flex items-center justify-center hover:bg-gray-800 text-gray-500 hover:text-yellow-400 transition-all duration-150 rounded-tr-md"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
                        <path fillRule="evenodd" d="M14.77 12.79a.75.75 0 01-1.06-.02L10 8.832 6.29 12.77a.75.75 0 11-1.08-1.04l4.25-4.5a.75.75 0 011.08 0l4.25 4.5a.75.75 0 01-.02 1.06z" clipRule="evenodd" />
                      </svg>
                    </button>
                    <button
                      type="button"
                      onClick={() => setMinSearchVolume(prev => Math.max(prev - 10, 1))}
                      className="flex-1 flex items-center justify-center hover:bg-gray-800 text-gray-500 hover:text-yellow-400 transition-all duration-150 rounded-br-md border-t border-gray-700/50"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
                        <path fillRule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clipRule="evenodd" />
                      </svg>
                    </button>
                  </div>
                </div>
                <p className="text-gray-400 text-sm mt-2">
                  Enter the minimum search volume filter for keywords (e.g., 100)
                </p>
              </div>
            </div>

            {/* File Upload Section */}
            <div>
              <h2 className="text-yellow-400 text-xl font-medium mb-4">Upload Bulk File (Excel)</h2>
              <div className="mb-4">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full bg-yellow-400 text-black hover:bg-yellow-300 focus:ring-yellow-400 transition-all duration-200 flex items-center justify-center py-3 px-4 rounded-md font-medium"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  Choose File
                </button>
                <input
                  id="file"
                  type="file"
                  ref={fileInputRef}
                  className="sr-only"
                  accept=".xlsx,.xls"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      handleFileChange(e.target.files[0]);
                    }
                  }}
                />
              </div>
              {file && (
                <div className="flex items-center p-3 bg-gray-800/80 rounded-lg border border-gray-700 text-sm text-white mb-2">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="truncate font-medium">{file.name}</span>
                </div>
              )}
              <p className="text-gray-400 text-sm">
                Upload the Amazon Advertising bulk file that contains your campaigns for topical analysis
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-4 mt-8">
              <button
                onClick={handleProcessTopical}
                disabled={isLoading || !file || !minSearchVolume}
                className={`flex-1 py-3 px-4 rounded-md font-medium flex items-center justify-center ${
                  isLoading || !file || !minSearchVolume
                    ? "bg-gray-700 text-gray-400 cursor-not-allowed"
                    : "bg-yellow-500 hover:bg-yellow-400 text-gray-900"
                }`}
              >
                {isLoading ? (
                  <div className="flex items-center justify-center">
                    <Spinner size="sm" />
                    <span className="ml-2">Processing...</span>
                  </div>
                ) : "Run Topical Analysis"}
              </button>
              <button
                onClick={handleReset}
                disabled={isLoading}
                className={`px-6 py-3 rounded-md font-medium ${
                  isLoading
                    ? "bg-gray-700 text-gray-400 cursor-not-allowed"
                    : "bg-gray-700 text-white hover:bg-gray-600"
                }`}
              >
                Reset
              </button>
            </div>
          </div>

          {/* Processing Indicator */}
          {isLoading && (
            <div className="mt-8 p-4 bg-gray-800/40 rounded-lg border border-gray-700/50 space-y-4">
              <Label className="text-yellow-400 font-medium">Processing Your Excel File...</Label>
              <Progress value={progress} className="w-full h-2 bg-gray-700" />
              <p className="text-gray-400 text-sm">
                This process may take several minutes to complete. Please keep this page open.
                We are analyzing your campaigns using advanced topical analysis techniques.
              </p>
            </div>
          )}

          {/* Results Section */}
          {processedData && (
            <div className="mt-8 space-y-6">
              {/* Success Banner using reusable component */}
              <SuccessBanner
                b0_asin_count={processedData.data.b0_asin_count}
                non_b0_asin_count={processedData.data.non_b0_asin_count}
                file={processedData.data.file}
                tableData={tableData}
                previewOpen={previewOpen}
                setPreviewOpen={setPreviewOpen}
                onDownload={handleDownload}
              />
              
              {/* Data Preview Table */}
              {previewOpen && (
                <>
                  {hasPreviewData ? (
                    <EnhancedDataTable
                      data={tableData || {}}
                      title="Topical Analysis Results"
                      description="Preview the analyzed topical data"
                    />
                  ) : (
                    <div className="p-6 bg-yellow-900/20 rounded-lg border border-yellow-700/50">
                      <h3 className="text-yellow-400 text-lg font-semibold">No Preview Available</h3>
                      <p className="text-gray-300 mt-2">
                        The analysis is complete but there is no data to preview. 
                        Please download the result file for detailed analysis.
                      </p>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* Error Message */}
          {isError && (
            <div className="mt-8 p-6 bg-red-900/20 rounded-lg border border-red-700/50">
              <h3 className="text-red-400 text-lg font-semibold flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                Error
              </h3>
              <p className="text-gray-300 mt-2">{error?.message || "An error occurred during processing"}</p>
              <Button
                type="button"
                onClick={() => window.location.reload()}
                className="mt-4 bg-red-600 text-white hover:bg-red-500 focus:ring-red-400"
              >
                Reload Page
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 