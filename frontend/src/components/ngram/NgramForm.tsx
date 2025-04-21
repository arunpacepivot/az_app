import { useState, useEffect } from 'react'
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline'
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

export function NgramForm() {
  const [file, setFile] = useState<File | null>(null)
  const [targetACOS, setTargetACOS] = useState<number>(0.2)
  const [progress, setProgress] = useState(0)
  const [processedData, setProcessedData] = useState<NgramResponse | null>(null)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [uploadProgress, setUploadProgress] = useState<number>(0)

  const { 
    mutate: processNgram,
    isPending: isProcessing,
    error: mutationError,
    reset: resetMutation
  } = useProcessNgram();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file || targetACOS <= 0) return

    setIsSubmitting(true)
    setProgress(0)
    setUploadProgress(0)

    // Declare interval outside try block so it's accessible in catch block
    let progressInterval: NodeJS.Timeout | undefined;
    
    try {
      // Show initial upload status
      setUploadProgress(10);
      
      // Simulate upload progress
      progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev < 90) return prev + 5;
          return prev;
        });
      }, 500);
      
      await processNgram(
        { file, target_acos: targetACOS },
        {
          onSuccess: (response: NgramResponse) => {
            if (progressInterval) clearInterval(progressInterval);
            setUploadProgress(100);
            setIsSubmitting(false);
            setProgress(100);
            setProcessedData(response);
            console.log('Ngram Analysis Complete:', response);
          },
          onError: (error) => {
            if (progressInterval) clearInterval(progressInterval);
            setUploadProgress(0);
            setIsSubmitting(false);
            setProgress(0);
            console.error('Ngram Analysis Error:', error);
            
            // Check if the backend process actually completed successfully despite the error
            // This can happen with large files when the frontend times out but the backend finishes
            if (error?.message?.includes('timeout') || error?.message?.includes('network error')) {
              // Tell the user to refresh or check downloads
              alert('The file is taking longer than expected to process. The analysis may still be running on the server. Please wait a few minutes and check your notifications or refresh the page to see if results are available.')
            }
          },
        }
      )
    } catch (error) {
      if (progressInterval) clearInterval(progressInterval);
      setUploadProgress(0);
      setIsSubmitting(false);
      setProgress(0);
      console.error('Unexpected error during ngram processing:', error);
    }
  }

  const handleReset = () => {
    setFile(null)
    setTargetACOS(0.2)
    setProgress(0)
    setProcessedData(null)
    resetMutation()
  }

  const handleDownloadFile = (file: NgramFile) => {
    try {
      console.log('Downloading file:', file);
      
      let downloadUrl;
      
      // If direct URL is provided in the response, use it as primary option
      if (file.url && file.url.startsWith('http')) {
        console.log('Using direct URL from response:', file.url);
        downloadUrl = file.url;
      } else {
        // Otherwise use the file_id to generate a download URL
        console.log('Using file_id to generate URL:', file.file_id);
        downloadUrl = ngramService.downloadNgramFile(file.file_id);
      }
      
      console.log('Final download URL:', downloadUrl);
      
      // Create and trigger download
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = file.filename || `ngram_${file.file_id}.xlsx`;
      a.target = '_blank'; // Open in new tab as fallback
      document.body.appendChild(a);
      a.click();
      
      // Clean up
      setTimeout(() => {
        document.body.removeChild(a);
      }, 100);
    } catch (error) {
      console.error('Error downloading file:', error, file);
      alert('There was an error downloading the file. Please check the console for details.');
    }
  }

  const handleFileChange = (selectedFile: File) => {
    // Max file size: 20MB
    const MAX_FILE_SIZE = 20 * 1024 * 1024;
    
    if (selectedFile.size > MAX_FILE_SIZE) {
      alert('File size exceeds 20MB limit. Please upload a smaller file or split your data into multiple files.');
      console.log(`File rejected: ${selectedFile.name}, size: ${(selectedFile.size / 1024 / 1024).toFixed(2)}MB (exceeds limit)`);
      return;
    }
    
    console.log(`File selected: ${selectedFile.name}, size: ${(selectedFile.size / 1024 / 1024).toFixed(2)}MB, type: ${selectedFile.type}`);
    setFile(selectedFile);
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
                        onClick={(e) => {
                          e.preventDefault()
                          document.getElementById('file')?.click()
                        }}
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

              <div className="flex space-x-4 pt-4">
                <Button
                  type="submit"
                  disabled={isProcessing || !file || !targetACOS}
                  className="w-3/4 bg-yellow-400 text-black hover:bg-yellow-300 focus:ring-yellow-400 flex items-center justify-center transition-all duration-200 transform hover:translate-y-[-2px] shadow-lg"
                >
                  {isProcessing ? (
                    <div className="flex items-center justify-center">
                      <Spinner size="sm" />
                      <span className="ml-2">
                        {uploadProgress < 100 ? `Uploading (${uploadProgress}%)` : 'Processing...'}
                      </span>
                    </div>
                  ) : null}
                  {isProcessing ? "Processing..." : "Run N-gram Analysis"}
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

            {processedData && (
              <div className="mt-8 space-y-6">
                <div className="p-6 bg-green-900/20 rounded-lg border border-green-700/50">
                  <div className="flex items-center justify-between">
                    <h3 className="text-green-400 text-lg font-semibold flex items-center">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      Analysis Complete!
                    </h3>
                  </div>
                  <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
                    <div className="flex flex-col space-y-2">
                      <p className="text-gray-300"><span className="font-medium">Status:</span> {processedData?.status === 200 ? 'Success' : processedData?.data?.status || 'Processing'}</p>
                      <p className="text-gray-300"><span className="font-medium">Message:</span> {processedData?.data?.message || 'Analyzing data...'}</p>
                    </div>
                    <div className="flex flex-col space-y-2">
                      <p className="text-yellow-400"><span className="font-medium">B0 ASINs:</span> {processedData?.data?.sk_asin_count || 0}</p>
                      <p className="text-yellow-400"><span className="font-medium">Non-B0 ASINs:</span> {processedData?.data?.mk_asin_count || 0}</p>
                    </div>
                  </div>
                </div>

                {processedData?.data?.files && processedData.data.files.length > 0 && (
                  <div className="p-6 bg-gray-800/40 rounded-lg border border-gray-700/50">
                    <h3 className="text-yellow-400 text-lg font-semibold mb-4">Download Analysis Files</h3>
                    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                      {processedData.data.files.map((file, index) => (
                        <div key={index} className="p-4 bg-gray-700/30 rounded-lg border border-gray-600 flex justify-between items-center">
                          <div className="flex flex-col space-y-1">
                            <span className="text-gray-200 font-medium truncate max-w-xs">{file.filename}</span>
                            <span className="text-gray-400 text-sm">{file.type}</span>
                          </div>
                          <Button
                            onClick={() => handleDownloadFile(file)}
                            className="bg-gray-600 text-white hover:bg-gray-500 focus:ring-gray-400 flex items-center gap-2"
                          >
                            <ArrowDownTrayIcon className="h-5 w-5" />
                            Download
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {processedData?.data?.data && Object.keys(processedData.data.data).length > 0 && (
                  <EnhancedDataTable
                    data={processedData.data.data}
                    title="N-gram Analysis Results"
                    description="Preview the analyzed data organized by ASIN"
                  />
                )}
              </div>
            )}

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