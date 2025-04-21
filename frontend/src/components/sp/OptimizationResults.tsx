import { ArrowDownTrayIcon } from '@heroicons/react/24/outline'
import { Eye } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { SpAdsResponse } from '@/lib/api/types'
import { Buffer } from 'buffer'
import { EnhancedDataTable } from '@/components/ui/enhanced-data-table'
import { getFileDownloadUrl } from '@/lib/api/utils'
import { spService } from '@/lib/api/services/sp.service'

interface OptimizationResultsProps {
  processedData: SpAdsResponse
  previewOpen: boolean
  setPreviewOpen: (open: boolean) => void
}

export function OptimizationResults({ processedData, previewOpen, setPreviewOpen }: OptimizationResultsProps) {
  // Excel file is embedded in the response as base64
  const handleDownloadExcel = () => {
    try {
      const url = window.URL.createObjectURL(
        new Blob(
          [Buffer.from(processedData.excel_file.content, 'base64')],
          { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }
        )
      );
      const a = document.createElement('a');
      a.href = url;
      a.download = processedData.excel_file.filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading Excel file:', error);
      alert('There was an error downloading the file. Please try again.');
    }
  };

  // For any direct file downloads by ID
  const handleDownloadFile = (fileId: string, filename: string) => {
    try {
      const downloadUrl = spService.downloadFile(fileId);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading file:', error);
      alert('There was an error downloading the file. Please try again.');
    }
  };

  return (
    <div className="mt-8 space-y-6">
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
              onClick={handleDownloadExcel}
              className="bg-green-600 text-white hover:bg-green-500 focus:ring-green-400 flex items-center gap-2"
            >
              <ArrowDownTrayIcon className="h-5 w-5" />
              Download Excel
            </Button>
          </div>
        </div>
      </div>

      {previewOpen && processedData?.data && (
        <EnhancedDataTable
          data={processedData.data}
          onDownload={handleDownloadExcel}
        />
      )}
    </div>
  )
} 