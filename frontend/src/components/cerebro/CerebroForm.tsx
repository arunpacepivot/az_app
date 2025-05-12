"use client";

import { useState, useEffect } from 'react';
import { useProcessCerebro } from '@/lib/hooks/queries/use-cerebro';
import { Upload, ArrowDown, Eye } from 'lucide-react';
import { CerebroResponse, CerebroFile } from '@/lib/api/types';
import { cerebroService } from '@/lib/api/services/cerebro.service';
import { getErrorDetails } from '@/lib/utils/error-handler';

import { EnhancedDataTable } from '@/components/ui/enhanced-data-table';
import { Spinner } from '@/components/shared/Spinner';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

// Custom parser for handling NaN, Infinity values in JSON
const customJSONParse = (jsonString: string): any => {
  if (typeof jsonString !== 'string') {
    return jsonString; // Not a string, return as is
  }
  
  try {
    // First attempt: Regular JSON parse
    return JSON.parse(jsonString);
  } catch (err) {
    try {
      // Handle NaN, Infinity, undefined by replacing them before parsing
      const preparedJson = jsonString
        .replace(/"([^"]+)":\s*NaN/g, '"$1": null')
        .replace(/"([^"]+)":\s*Infinity/g, '"$1": null')
        .replace(/"([^"]+)":\s*undefined/g, '"$1": null')
        .replace(/:\s*NaN/g, ': null')
        .replace(/:\s*Infinity/g, ': null')
        .replace(/:\s*undefined/g, ': null')
        .replace(/NaN/g, 'null')
        .replace(/Infinity/g, 'null')
        .replace(/undefined/g, 'null');
        
      return JSON.parse(preparedJson);
    } catch (deepErr) {
      const typedDeepErr = deepErr as Error;
      const typedErr = err as Error;
      console.error('JSON parsing failed', typedDeepErr);
      throw new Error(`JSON Parse Error: ${typedDeepErr.message} - Original error: ${typedErr.message}`);
    }
  }
};

// Success banner component for displaying analysis results
interface SuccessBannerProps {
  file: CerebroFile | undefined;
  onDownload: () => void;
}

function SuccessBanner({
  file,
  onDownload
}: SuccessBannerProps) {
  return (
    <div className="bg-gray-800/50 rounded-lg border border-gray-700/50 overflow-hidden">
      <div className="flex items-center justify-between p-6">
        <div className="flex items-center gap-4">
        {/* Success Icon */}
        <div className="rounded-full bg-green-500 bg-opacity-10 p-2 flex-shrink-0">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        
        {/* Content */}
          <div>
          <h3 className="text-xl font-medium text-green-500">Analysis Complete!</h3>
            <p className="text-gray-300 text-sm mt-1">Your keyword analysis has been processed successfully.</p>
          </div>
        </div>
        
        {/* Download Button */}
        <Button 
          onClick={onDownload}
          className="bg-green-600 hover:bg-green-500 text-white flex items-center gap-2"
        >
          <ArrowDown className="h-5 w-5" />
          Download Excel
        </Button>
      </div>
    </div>
  );
}

export function CerebroForm() {
  const [file, setFile] = useState<File | null>(null);
  const [minSearchVolume, setMinSearchVolume] = useState<number>(100);
  const [processedData, setProcessedData] = useState<CerebroResponse | null>(null);
  const [progress, setProgress] = useState(0);
  const [tableData, setTableData] = useState<Record<string, Array<Record<string, any>>> | null>(null);
  
  const { 
    mutate: processCerebro, 
    isPending: isProcessing,
    error: mutationError,
    reset: resetMutation 
  } = useProcessCerebro();

  const handleFileChange = (selectedFile: File) => {
    // Max file size: 20MB
    const MAX_FILE_SIZE = 20 * 1024 * 1024;
    
    if (selectedFile.size > MAX_FILE_SIZE) {
      alert('File size exceeds 20MB limit. Please upload a smaller file.');
      return;
    }
    
    setFile(selectedFile);
  };

  const handleSubmit = () => {
    if (!file || minSearchVolume < 1) return;

    // Reset any previous data
    setProcessedData(null);
    setTableData(null);
    setProgress(0);
    
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev < 30) return prev + 5; // Much faster initial progress
        if (prev < 50) return prev + 3;
        if (prev < 70) return prev + 2;
        if (prev < 85) return prev + 1;
        if (prev < 95) return prev + 0.5;
        return prev; // Stay at 95% until we get response
      });
    }, 200);

    processCerebro(
      { file, min_search_volume: minSearchVolume },
      {
        onSuccess: (data) => {
          clearInterval(progressInterval);
          setProgress(100);
          
          try {
            // Format the data for the table component
            const formattedData = formatDataForTable(data);
            
            setProcessedData(data);
            setTableData(formattedData);
          } catch (error) {
            console.error('Error processing response:', error);
          }
        },
        onError: (error) => {
          clearInterval(progressInterval);
          setProgress(0);
          console.error('Cerebro Analysis Error:', error);
        },
      }
    );
  };

  const formatDataForTable = (data: CerebroResponse) => {
    // Default result structure - always have a Keywords tab with at least one row
    const formattedData: Record<string, Array<Record<string, any>>> = {
      "Keywords": [{ ID: 1, Keyword: "Loading data...", "Search Volume": 0 }]
    };
    
    try {
      // Handle null/undefined data
      if (!data) {
        formattedData["Keywords"] = [{ ID: 1, Keyword: "No response received", "Search Volume": 0 }];
        return formattedData;
      }
      
      // HANDLE STRING RESPONSE - The API sometimes returns a JSON string instead of a parsed object
      let processedData: any = data;
      if (typeof data === 'string') {
        try {
          processedData = customJSONParse(data);
        } catch (e) {
          console.error('Failed to parse string response as JSON:', e);
          formattedData["Keywords"] = [{ ID: 1, Keyword: "Invalid JSON string response", "Search Volume": 0 }];
          return formattedData;
        }
      }
      
      // DIRECT ARRAY HANDLING - check if data is directly an array of objects with Keyword Phrase
      if (Array.isArray(processedData) && processedData.length > 0 && typeof processedData[0] === 'object') {
        if (processedData[0] && 'Keyword Phrase' in processedData[0]) {
          formattedData["Keywords"] = processedData.map((item: any, index: number) => {
            const result: Record<string, any> = { ID: index + 1 };
            
            // Use Keyword Phrase as Keyword
            result.Keyword = item['Keyword Phrase'];
            
            // Copy all other properties
            Object.entries(item).forEach(([key, value]) => {
              if (key !== 'Keyword Phrase' && key !== 'ID') {
                result[key] = value;
              }
            });
            
            return result;
          });
          
          return formattedData;
        }
      }
      
      // Make sure we're dealing with an object before using 'in' operator
      const isDataObject = processedData && typeof processedData === 'object' && !Array.isArray(processedData);
      
      // Special handling for the "data" property if it's a direct array
      if (isDataObject && 'data' in processedData && Array.isArray(processedData.data) && processedData.data.length > 0) {
        if (processedData.data[0] && typeof processedData.data[0] === 'object' && 'Keyword Phrase' in processedData.data[0]) {
          formattedData["Keywords"] = processedData.data.map((item: any, index: number) => {
            const result: Record<string, any> = { ID: index + 1 };
            
            // Use Keyword Phrase as Keyword
            result.Keyword = item['Keyword Phrase'];
            
            // Copy all other properties
            Object.entries(item).forEach(([key, value]) => {
              if (key !== 'Keyword Phrase' && key !== 'ID') {
                result[key] = value;
              }
            });
            
            return result;
          });
          
          return formattedData;
        }
      }
      
      // Check for the Analysis array in data.data.data.Analysis - PRIORITIZE KEYWORD PHRASE
      const analysisArray = isDataObject && processedData.data && 
                           typeof processedData.data === 'object' && 
                           processedData.data.data && 
                           typeof processedData.data.data === 'object' && 
                           'Analysis' in processedData.data.data ? 
                           processedData.data.data.Analysis : null;
                           
      if (analysisArray && Array.isArray(analysisArray) && analysisArray.length > 0) {
        formattedData["Keywords"] = analysisArray.map((item: any, index: number) => {
          const result: Record<string, any> = { ID: index + 1 };
          
          // Copy all properties, prioritizing Keyword Phrase over Keyword
          if (item && typeof item === 'object') {
            // Make sure we have a Keyword field (prioritize Keyword Phrase)
            if ('Keyword Phrase' in item) {
              result.Keyword = item['Keyword Phrase'];
            } else if ('Keyword' in item) {
              result.Keyword = item.Keyword;
            } else {
              result.Keyword = 'Unknown';
            }
            
            // Copy all other properties
            Object.entries(item).forEach(([key, value]) => {
              if (key !== 'Keyword' && key !== 'Keyword Phrase' && key !== 'ID') {
                result[key] = value;
              }
            });
          }
          
          return result;
        });
        return formattedData;
      }
      
      // Check for the Keywords array in data.data.data.Keywords
      const keywordsArray = isDataObject && processedData.data && 
                          typeof processedData.data === 'object' && 
                          processedData.data.data && 
                          typeof processedData.data.data === 'object' && 
                          'Keywords' in processedData.data.data ? 
                          processedData.data.data.Keywords : null;
                          
      if (keywordsArray && Array.isArray(keywordsArray) && keywordsArray.length > 0) {
        formattedData["Keywords"] = keywordsArray.map((item: any, index: number) => {
          const result: Record<string, any> = { ID: index + 1 };
          
          if (typeof item === 'string') {
            result.Keyword = item;
            result["Search Volume"] = 0;
          } else if (item && typeof item === 'object') {
            // Check for the Keywords field (capital K)
            if ('Keywords' in item) {
              result.Keyword = item.Keywords;
            } else if ('Keyword' in item) {
              result.Keyword = item.Keyword;
            } else if ('Keyword Phrase' in item) {
              result.Keyword = item['Keyword Phrase'];
                  } else {
              result.Keyword = 'Unknown';
            }
            
            // Copy other properties
            Object.entries(item).forEach(([key, value]) => {
              if (!['Keywords', 'Keyword', 'Keyword Phrase', 'ID'].includes(key)) {
                result[key] = value;
              }
            });
          }
          
          return result;
        });
        return formattedData;
      }
      
      // Second check: Is there a direct array in data.data that contains objects?
      const directDataArray = isDataObject && processedData.data && 
                             typeof processedData.data === 'object' && 
                             'data' in processedData.data ? 
                             processedData.data.data : null;
                             
      if (directDataArray && Array.isArray(directDataArray) && directDataArray.length > 0 && typeof directDataArray[0] === 'object') {
        formattedData["Keywords"] = directDataArray.map((item: any, index: number) => {
          return { ID: index + 1, ...item };
        });
        return formattedData;
      }
      
      // Third check: Is there a keywords array in data.data?
      const dataKeywordsArray = isDataObject && processedData.data && 
                               typeof processedData.data === 'object' && 
                               'keywords' in processedData.data ? 
                               processedData.data.keywords : null;
                               
      if (dataKeywordsArray && Array.isArray(dataKeywordsArray) && dataKeywordsArray.length > 0) {
        formattedData["Keywords"] = dataKeywordsArray.map((keyword: any, index: number) => {
          if (typeof keyword === 'string') {
            return { ID: index + 1, Keyword: keyword, "Search Volume": 0 };
          } else if (typeof keyword === 'object' && keyword) {
            return { ID: index + 1, ...keyword };
          }
          return { ID: index + 1, Keyword: String(keyword), "Search Volume": 0 };
        });
        return formattedData;
      }
      
      // Handle the case where the response might be a raw array - sometimes APIs return just the array
      if (Array.isArray(processedData) && processedData.length > 0) {
        formattedData["Keywords"] = processedData.map((item: any, index: number) => {
          if (typeof item === 'string') {
            return { ID: index + 1, Keyword: item, "Search Volume": 0 };
          } else if (typeof item === 'object' && item) {
            const result: Record<string, any> = { ID: index + 1 };
            
            // Map keyword field
            if ('Keyword Phrase' in item) result.Keyword = item['Keyword Phrase'];
            else if ('Keyword' in item) result.Keyword = item.Keyword;
            else if ('Keywords' in item) result.Keyword = item.Keywords;
            else result.Keyword = 'Unknown';
            
            // Add other properties
            Object.entries(item).forEach(([key, value]) => {
              if (!['Keyword Phrase', 'ID'].includes(key) && key !== 'Keyword' && key !== 'Keywords') {
                result[key] = value;
              }
            });
            
            return result;
          }
          return { ID: index + 1, Keyword: String(item), "Search Volume": 0 };
        });
        return formattedData;
      }
      
      // Fourth check: Look for ANY array in the response that might contain keyword data
      const findKeywordArrays = (obj: any): any[] | null => {
        // If obj is null or not an object, return null
        if (!obj || typeof obj !== 'object') return null;
        
        // If obj is an array with elements, check if it might contain keyword data
        if (Array.isArray(obj) && obj.length > 0) {
          const firstItem = obj[0];
          // If array contains strings or objects, it might be keyword data
          if (typeof firstItem === 'string' || 
             (typeof firstItem === 'object' && firstItem && 
              (typeof firstItem === 'object' && ('Keyword' in firstItem || 'Keywords' in firstItem || 'Keyword Phrase' in firstItem)))) {
            return obj;
          }
        }
        
        // Recursively check all properties
        for (const key in obj) {
          const result = findKeywordArrays(obj[key]);
          if (result) return result;
        }
        
        return null;
      };
      
      const anyKeywordArray = findKeywordArrays(processedData);
      if (anyKeywordArray) {
        formattedData["Keywords"] = anyKeywordArray.map((item: any, index: number) => {
          if (typeof item === 'string') {
            return { ID: index + 1, Keyword: item, "Search Volume": 0 };
          } else if (typeof item === 'object' && item) {
            const result: Record<string, any> = { ID: index + 1 };
            
            // Map keyword field
            if (typeof item === 'object' && 'Keyword Phrase' in item) result.Keyword = item['Keyword Phrase'];
            else if (typeof item === 'object' && 'Keyword' in item) result.Keyword = item.Keyword;
            else if (typeof item === 'object' && 'Keywords' in item) result.Keyword = item.Keywords;
            else result.Keyword = 'Unknown';
            
            // Add other properties
            if (typeof item === 'object') {
              Object.entries(item).forEach(([key, value]) => {
                if (!['Keyword Phrase', 'ID'].includes(key) && key !== 'Keyword' && key !== 'Keywords') {
                  result[key] = value;
                }
              });
            }
            
            return result;
          }
          return { ID: index + 1, Keyword: String(item), "Search Volume": 0 };
        });
        return formattedData;
      }
      
      // If we've tried everything and still haven't found keyword data,
      // return a message explaining that we couldn't find any data
      formattedData["Keywords"] = [{ 
        ID: 1, 
        Keyword: "Could not extract keyword data from response", 
        "Search Volume": 0 
      }];
      return formattedData;
      
    } catch (error) {
      console.error('Error processing response:', error);
      
      // Always return a valid data structure even if an error occurs
      return { 
        "Keywords": [{ 
          ID: 1, 
          Keyword: "Error processing data: " + (error instanceof Error ? error.message : String(error)), 
          "Search Volume": 0 
        }] 
      };
    }
  };

  const handleReset = () => {
    setFile(null);
    setMinSearchVolume(100);
    setProgress(0);
    setProcessedData(null);
    setTableData(null);
    resetMutation();
  };
  
  const handleDownloadFile = () => {
    try {
      // Try multiple paths to find the file data
      let fileData: CerebroFile | undefined;
      
      // Handle string response case for file data
      let processedDataObj: any = processedData;
      if (processedData && typeof processedData === 'string') {
        try {
          processedDataObj = customJSONParse(processedData);
        } catch (e) {
          console.error('Failed to parse processedData string:', e);
        }
      }
      
      if (processedDataObj?.data?.file) {
        fileData = processedDataObj.data.file as unknown as CerebroFile;
      } else if (processedDataObj?.data?.data?.file) {
        fileData = processedDataObj.data.data.file as unknown as CerebroFile;
      }
      
      if (!fileData) {
        console.error('Missing file data in response:', fileData);
        alert('Error: File data is missing. Cannot download the file.');
        return;
      }
      
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
      const downloadUrl = cerebroService.downloadCerebroFile(fileData.file_id, fileData.url);
      console.log('Generated download URL:', downloadUrl);
      
      window.open(downloadUrl, '_blank');
    } catch (error) {
      console.error('Error downloading file:', error);
      alert('There was an error downloading the file. Please try again.');
    }
  };

  // Render results if data is available
  const renderResults = () => {
    if (!processedData || !tableData || Object.keys(tableData).length === 0) {
      return null;
    }
    
    // Safely extract the file data based on new structure
    let fileData: CerebroFile | undefined;
    try {
      // Handle string response case for file data in render
      let dataToProcess: any = processedData;
      if (typeof processedData === 'string') {
        try {
          dataToProcess = customJSONParse(processedData);
        } catch (e) {
          console.error('Failed to parse processedData string:', e);
        }
      }
      
      // First check the direct file path (new structure)
      if (dataToProcess?.data?.file) {
        fileData = dataToProcess.data.file as unknown as CerebroFile;
      } 
      // Fallback to the old path
      else if (dataToProcess?.data?.data?.file) {
        fileData = dataToProcess.data.data.file as unknown as CerebroFile;
      }
    } catch (e) {
      console.error('Error extracting file data:', e);
    }
    
    return (
      <div className="mt-8 space-y-6">
        {/* Success Banner */}
        <SuccessBanner
          file={fileData}
          onDownload={handleDownloadFile}
        />
        
        {/* Data Table */}
        <EnhancedDataTable
          data={tableData}
          title="Cerebro Analysis Results"
          description="The analyzed keywords sorted by relevance"
          onDownload={handleDownloadFile}
        />
      </div>
    );
  };

  // Ensure we attempt to format data correctly when we receive API response
  useEffect(() => {
    if (processedData) {
      try {
        const formattedData = formatDataForTable(processedData);
        
        // Only update if we have actual data
        if (Object.keys(formattedData).length > 0) {
          setTableData(formattedData);
        }
      } catch (error) {
        console.error('Error in useEffect formatting data:', error);
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [processedData]);

  return (
    <div className="flex flex-col">
      <div className="w-full max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-yellow-400">Cerebro Analysis Tool</h1>
          <p className="text-gray-300 mt-2">
            Analyze your keyword data to discover search volumes and optimize your campaigns
          </p>
        </div>

        {/* Main form container */}
        <div className="bg-gray-900 rounded-lg overflow-hidden border border-gray-800 shadow-xl">
          {/* Form fields */}
          <div className="p-8 space-y-6">
            {/* Minimum Search Volume */}
            <div className="space-y-4 p-4 bg-gray-800/40 rounded-lg border border-gray-700/50">
              <h3 className="text-yellow-400 text-lg font-medium">
                Minimum Search Volume
              </h3>
              <div className="relative">
                <input
                  type="number"
                  min="1"
                  value={minSearchVolume}
                  onChange={(e) => setMinSearchVolume(Number(e.target.value))}
                  className="w-full bg-gray-900 text-white border border-gray-700 focus:ring-1 focus:ring-yellow-400/50 focus:border-yellow-400/50 rounded-md p-2 outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none text-sm font-medium"
                />
              </div>
              <p className="text-gray-400 text-sm">
                Enter the minimum search volume for keywords to include in the analysis
              </p>
            </div>

            {/* File Upload */}
            <div className="space-y-4 p-4 bg-gray-800/40 rounded-lg border border-gray-700/50">
              <h3 className="text-yellow-400 text-lg font-medium">
                Upload Bulk File (Excel)
              </h3>
              
              <div className="flex items-center space-x-4">
                <div className="relative w-full">
                  <button 
                    type="button"
                    className="relative bg-yellow-400 text-black hover:bg-yellow-300 focus:ring-yellow-400 transition-all duration-200 w-full flex items-center justify-center p-2.5 rounded-md font-medium"
                    onClick={() => document.getElementById('fileInput')?.click()}
                  >
                    <Upload className="h-5 w-5 mr-2" />
                    {file ? "Change File" : "Choose File"}
                  </button>
                  <input
                    id="fileInput"
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={(e) => e.target.files?.[0] && handleFileChange(e.target.files[0])}
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
              
              <p className="text-gray-400 text-sm">
                Upload the Excel file containing the keywords you want to analyze
              </p>
            </div>

            {/* Progress indicator */}
            {isProcessing && (
              <div className="mt-8 p-4 bg-gray-800/40 rounded-lg border border-gray-700/50 space-y-4">
                <h3 className="text-yellow-400 font-medium">Processing Your Excel File...</h3>
                <div className="w-full bg-gray-700 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-yellow-400 h-full transition-all duration-300 ease-in-out"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
                <p className="text-gray-400 text-sm">
                  This process may take up to a minute to complete. Please keep this page open.
                </p>
              </div>
            )}

            {/* Error message */}
            {mutationError && !isProcessing && (
              <div className="p-4 bg-red-900/20 rounded-md border border-red-700/50 text-red-400">
                <p className="font-medium">Error</p>
                <p className="text-sm mt-1">{getErrorDetails(mutationError).message}</p>
                <button
                  onClick={resetMutation}
                  className="mt-2 px-3 py-1 bg-red-500 text-white text-sm rounded-md hover:bg-red-600"
                >
                  Try Again
                </button>
              </div>
            )}

            {/* Action buttons */}
            <div className="flex space-x-4 pt-4">
              <button
                onClick={handleSubmit}
                disabled={isProcessing || !file || minSearchVolume < 1}
                className={cn(
                  "w-3/4 bg-yellow-400 text-black hover:bg-yellow-300 focus:ring-yellow-400 flex items-center justify-center transition-all duration-200 p-2.5 rounded-md font-medium transform hover:translate-y-[-2px] shadow-lg",
                  (isProcessing || !file || minSearchVolume < 1) && "opacity-50 cursor-not-allowed hover:translate-y-0"
                )}
              >
                {isProcessing ? (
                  <div className="flex items-center justify-center">
                    <Spinner size="sm" />
                    <span className="ml-2">Processing...</span>
                  </div>
                ) : "Run Cerebro Analysis"}
              </button>
              <button
                onClick={handleReset}
                disabled={isProcessing}
                className={cn(
                  "w-1/4 bg-gray-700 text-white hover:bg-gray-600 transition-all duration-200 p-2.5 rounded-md font-medium border border-gray-600",
                  isProcessing && "opacity-50 cursor-not-allowed"
                )}
              >
                Reset
              </button>
            </div>
            
            {/* Display results */}
            {processedData && renderResults()}
          </div>
        </div>
      </div>
    </div>
  );
} 