"use client"

import { useState } from 'react'
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline'
import { Eye } from 'lucide-react'
import ProtectedRoute from '@/components/auth/protected-route'
import { useProcessSpAds } from '@/lib/hooks/queries/use-sp-ads'
import { getErrorDetails } from '@/lib/utils/error-handler'
import { ErrorMessage } from '@/components/ui/error-message'
import { SpAdsResponse } from '@/lib/api/types'
import { Buffer } from 'buffer'

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { FileInput } from "@/components/ui/file-input"
import { ExcelPreview } from '@/components/ui/excel-preview'

export default function SpPage() {
  return (
    <ProtectedRoute>
      <SpAdsForm />
    </ProtectedRoute>
  )
}

function SpAdsForm() {
  const [file, setFile] = useState<File | null>(null)
  const [targetACOS, setTargetACOS] = useState<number>(0)
  const [progress, setProgress] = useState(0)
  const [processedData, setProcessedData] = useState<SpAdsResponse | null>(null)
  const [previewOpen, setPreviewOpen] = useState(true)

  const { 
    mutate: processSpAds,
    isPending: isProcessing,
    error: mutationError,
    reset: resetMutation
  } = useProcessSpAds();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file || targetACOS <= 0) return

    setProgress(0)
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev < 20) return prev + 0.5
        if (prev < 40) return prev + 0.3
        if (prev < 60) return prev + 0.2
        if (prev < 80) return prev + 0.1
        if (prev < 90) return prev + 0.05
        return prev
      })
    }, 1000)

    try {
      await processSpAds(
        { file, target_acos: targetACOS },
        {
          onSuccess: (response: string | SpAdsResponse) => {
            clearInterval(progressInterval)
            setProgress(100)
            
            // Parse the response if it's a string
            let parsedData: SpAdsResponse
            try {
              if (typeof response === 'string') {
                // Replace NaN and Infinity with null in the string before parsing
                const cleanedResponse = response
                  .replace(/:\s*NaN/g, ': null')
                  .replace(/:\s*Infinity/g, ': null')
                  .replace(/:\s*-Infinity/g, ': null')
                console.log('Cleaned response:', cleanedResponse)
                parsedData = JSON.parse(cleanedResponse)
              } else {
                parsedData = response
              }

              console.log('Parsed API Response:', parsedData)
              console.log('Parsed API Response data:', parsedData.data)
              setProcessedData(parsedData)
            } catch (e) {
              console.error('Error parsing response:', e)
              console.log('Raw response:', response)
            }
          },
          onError: () => {
            clearInterval(progressInterval)
            setProgress(0)
          },
        }
      )
    } catch {
      clearInterval(progressInterval)
      setProgress(0)
    }
  }

  const handleReset = () => {
    setFile(null)
    setTargetACOS(0)
    setProgress(0)
    setProcessedData(null)
    resetMutation()
  }

  return (
    <main className="flex-1">
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 p-6 flex flex-col items-center justify-center">
        <Card className="w-full max-w-4xl mt-0 border border-gray-700 shadow-xl bg-gray-900/60 backdrop-blur-sm">
          <CardHeader className="border-b border-gray-700/50 pb-6">
            <CardTitle className="text-3xl font-bold text-center text-yellow-400">
              Amazon Advertising Optimizer
            </CardTitle>
            <CardDescription className="text-center text-gray-300 mt-2">
              Optimize your Amazon Sponsored Products, Sponsored Brands, and Sponsored Display campaigns at your target ACOS
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
                      placeholder="0.25"
                    />
                    <div className="absolute right-0 top-0 bottom-0 w-7 flex flex-col border-l border-gray-700/50">
                      <button
                        type="button"
                        onClick={() => {
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
                        onClick={() => {
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
                  <p className="text-gray-400 text-sm">Enter a value between 0 and 1 (e.g., 0.25 for 25% ACOS)</p>
                </div>
              </div>

              <div className="space-y-4 p-4 bg-gray-800/40 rounded-lg border border-gray-700/50">
                <Label htmlFor="file" className="text-yellow-400 text-lg font-medium">
                  Upload BULK File (Excel) for Last 30 Days
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
                        onFileSelect={(selectedFile) => setFile(selectedFile)}
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
                  <p className="text-gray-400 text-sm">Upload the Amazon Advertising bulk file that contains your Sponsored Products, Sponsored Brands, and/or Sponsored Display campaigns</p>
                </div>
              </div>

              <div className="flex space-x-4 pt-4">
                <Button
                  type="submit"
                  disabled={isProcessing || !file || !targetACOS}
                  className="w-3/4 bg-yellow-400 text-black hover:bg-yellow-300 focus:ring-yellow-400 flex items-center justify-center transition-all duration-200 transform hover:translate-y-[-2px] shadow-lg"
                >
                  {isProcessing ? (
                    <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-black mr-2"></span>
                  ) : null}
                  {isProcessing ? "Processing..." : "Optimize All Ad Campaigns"}
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
                  We are analyzing your campaigns and optimizing bids for maximum performance.
                </p>
              </div>
            )}

            {processedData && (
              <div className="mt-8 p-6 bg-green-900/20 rounded-lg border border-green-700/50 space-y-6">
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
                      onClick={() => {
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
                      }}
                      className="bg-green-600 text-white hover:bg-green-500 focus:ring-green-400 flex items-center gap-2"
                    >
                      <ArrowDownTrayIcon className="h-5 w-5" />
                      Download Excel
                    </Button>
                  </div>
                </div>

                <div className="rounded-lg border border-gray-700">
                  {(() => {
                    console.log('Before ExcelPreview - processedData:', processedData)
                    console.log('Before ExcelPreview - processedData.data:', processedData?.data)
                    return <ExcelPreview 
                      data={processedData?.data || {}} 
                      isOpen={previewOpen}
                      onOpenChange={setPreviewOpen}
                      onDownload={() => {
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
                      }}
                    />
                  })()}
                </div>
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