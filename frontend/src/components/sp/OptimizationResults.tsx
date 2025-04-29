import { ArrowDownTrayIcon } from '@heroicons/react/24/outline'
import { Eye } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { SpAdsResponse } from '@/lib/api/types'
import { Buffer } from 'buffer'
import { DataTable } from "@/components/ui/data-table"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { spService } from '@/lib/api/services/sp.service'
import { useMemo, useState, useCallback, useEffect } from 'react'
import { ColumnDef } from '@tanstack/react-table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { cn } from "@/lib/utils"

// Custom CSS for hiding scrollbars while keeping scroll functionality
const scrollbarHideStyles = `
  .scrollbar-hide {
    -ms-overflow-style: none;  /* IE and Edge */
    scrollbar-width: none;  /* Firefox */
  }
  
  .scrollbar-hide::-webkit-scrollbar {
    display: none;  /* Chrome, Safari and Opera */
  }
`;

interface OptimizationResultsProps {
  processedData: SpAdsResponse
  previewOpen: boolean
  setPreviewOpen: (open: boolean) => void
}

export function OptimizationResults({ processedData, previewOpen, setPreviewOpen }: OptimizationResultsProps) {
  // Handle direct file downloads - using useCallback to ensure it doesn't recreate between renders
  const handleDownloadFile = useCallback(() => {
    try {
      // Add defensive checks
      if (!processedData) {
        console.error('No processed data available');
        alert('Error: No data available for download. Please try again.');
        return;
      }
      
      console.log('Download requested, data structure:', processedData);
      
      // Check for the file property (new structure)
      if (processedData.file) {
        console.log('Using file property:', processedData.file);
        if (processedData.file.url && (processedData.file.url.startsWith('http://') || processedData.file.url.startsWith('https://'))) {
          console.log('Downloading via direct URL:', processedData.file.url);
          window.open(processedData.file.url, '_blank');
          return;
        } else if (processedData.file.file_id) {
          const downloadUrl = spService.downloadFile(processedData.file.file_id, processedData.file.url);
          console.log('Downloading via file_id:', processedData.file.file_id);
          window.open(downloadUrl, '_blank');
          return;

        }
      }
  
      // Check for excel_file property (old structure)
      if (processedData.excel_file) {
        // Use file_id if available (preferred approach)
        if (processedData.excel_file.file_id) {
          const downloadUrl = spService.downloadFile(processedData.excel_file.file_id);
          console.log('Downloading via excel_file.file_id:', processedData.excel_file.file_id);
          window.open(downloadUrl, '_blank');
          return;
        }
        // Fallback to base64 content if necessary
        else if (processedData.excel_file.content) {
          console.log('Downloading via base64 content');
          const url = window.URL.createObjectURL(
            new Blob(
              [Buffer.from(processedData.excel_file.content, 'base64')],
              { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }
            )
          );
          const a = document.createElement('a');
          a.href = url;
          a.download = processedData.excel_file.filename || 'optimized_sp_data.xlsx';
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
          return;
        } else {
          console.error('Excel file object exists but has no content or file_id');
        }
      }

      // Last resort - check if there's a file_id at the root level
      if (processedData.file_id) {
        console.log('Using root level file_id:', processedData.file_id);
        const downloadUrl = spService.downloadFile(processedData.file_id);
        window.open(downloadUrl, '_blank');
        return;
      }
      
      // If we got here, we couldn't find any valid file information
      console.error('No valid file information found in the response data');
      alert('Error: No file data available for download. Please try again.');
      
    } catch (error) {
      console.error('Error downloading file:', error);
      alert('There was an error downloading the file. Please try again.');
    }
  }, [processedData]);

  // Get all available sheets
  const availableSheets = useMemo(() => {
    return Object.keys(processedData?.data || {});
  }, [processedData]);

  // Set default active tab to the first sheet
  const [activeTab, setActiveTab] = useState<string>(() => {
    return availableSheets.length > 0 ? availableSheets[0] : '';
  });

  // Update activeTab when sheets change
  useEffect(() => {
    if (availableSheets.length > 0 && !availableSheets.includes(activeTab)) {
      setActiveTab(availableSheets[0]);
    }
  }, [availableSheets, activeTab]);

  // Get the human-readable name for each sheet
  const getSheetDisplayName = (sheetKey: string) => {
    // Handle common sheet names and make them more readable
    if (sheetKey.includes('SP_')) return 'Sponsored Products';
    if (sheetKey.includes('SB_')) return 'Sponsored Brands';
    if (sheetKey.includes('SD_')) return 'Sponsored Display';
    
    // Remove underscores and capitalize
    return sheetKey
      .replace(/_/g, ' ')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  };

  // Get the count of rows in each sheet
  const getSheetRowCount = (sheetKey: string) => {
    if (processedData?.data && processedData.data[sheetKey]) {
      return processedData.data[sheetKey].length;
    }
    return 0;
  };

  // Generate columns for the active tab
  const columns = useMemo(() => {
    if (!processedData?.data || !processedData.data[activeTab] || !processedData.data[activeTab].length) {
      return [];
    }

    const firstRow = processedData.data[activeTab][0];
    return Object.keys(firstRow).map((key) => ({
      accessorKey: key,
      header: key,
      cell: ({ row }) => {
        const value = row.getValue(key);
        // Format cell based on value type
        if (typeof value === 'number') {
          // Format numbers with 2 decimal places
          return Number.isInteger(value) ? value : value.toFixed(2);
        }
        return value;
      },
    })) as ColumnDef<any>[];
  }, [activeTab, processedData]);

  // Get current tab data
  const tableData = useMemo(() => {
    if (!processedData?.data || !processedData.data[activeTab]) {
      return [];
    }
    return processedData.data[activeTab];
  }, [activeTab, processedData]);

  return (
    <div className="mt-8 space-y-6">
      <style dangerouslySetInnerHTML={{ __html: scrollbarHideStyles }} />
      
      <div className="p-6 bg-green-900/20 rounded-lg border border-green-700/50">
        <div className="flex items-center justify-between">
          <h3 className="text-green-400 text-lg font-semibold flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Optimization Complete!
          </h3>
          <div className="flex space-x-3">
            {!previewOpen && (
              <Button
                onClick={() => setPreviewOpen(true)}
                className="bg-gray-600 text-white hover:bg-gray-500 focus:ring-gray-400 flex items-center gap-2"
              >
                <Eye className="h-5 w-5" />
                Preview Data
              </Button>
            )}
            <Button
              onClick={handleDownloadFile}
              className="bg-green-600 text-white hover:bg-green-500 focus:ring-green-400 flex items-center gap-2"
            >
              <ArrowDownTrayIcon className="h-5 w-5" />
              Download Excel
            </Button>
          </div>
        </div>
      </div>

      {previewOpen && processedData?.data && Object.keys(processedData.data).length > 0 && (
        <Card className="w-full mt-6 border border-gray-700 shadow-xl bg-gray-900/60 backdrop-blur-sm">
          <CardHeader className="border-b border-gray-700/50 pb-3">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div>
                <CardTitle className="text-xl font-bold text-yellow-400">
                  Amazon Ads Optimization Results
                </CardTitle>
                <CardDescription className="text-gray-300 mt-1">
                  Preview and analyze the optimized data before download
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-4">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="mb-4 w-full overflow-x-auto flex flex-nowrap pb-1 bg-gray-800/60 border border-gray-700/50 rounded-md scrollbar-hide">
                {availableSheets.map(sheet => (
                  <TabsTrigger 
                    key={sheet} 
                    value={sheet}
                    className="min-w-max px-4 py-2 whitespace-nowrap text-sm font-medium data-[state=active]:bg-yellow-400 data-[state=active]:text-black flex items-center gap-1.5"
                  >
                    {getSheetDisplayName(sheet)}
                    <span className="inline-flex items-center justify-center bg-gray-700 text-gray-300 text-xs rounded-full px-1.5 py-0.5 min-w-[20px] data-[state=active]:bg-yellow-500 data-[state=active]:text-black">
                      {getSheetRowCount(sheet)}
                    </span>
                  </TabsTrigger>
                ))}
              </TabsList>
              
              {availableSheets.map(sheet => (
                <TabsContent key={sheet} value={sheet} className="mt-2">
                  {(
                    <DataTable
                      columns={sheet === activeTab ? columns : []}
                      data={sheet === activeTab ? tableData : []}
                      enableSorting={true}
                      enableFiltering={true}
                      enableColumnVisibility={true}
                      enablePagination={true}
                      onDownload={handleDownloadFile}
                    />
                  )}
                </TabsContent>
              ))}
            </Tabs>
          </CardContent>
        </Card>
      )}
    </div>
  )
} 