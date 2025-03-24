"use client"

import { useState } from 'react'
import { ArrowDownTrayIcon, BoltIcon, ChartBarIcon, ShieldCheckIcon } from '@heroicons/react/24/outline'
import * as XLSX from 'xlsx'
import ProtectedRoute from '@/components/auth/protected-route'
import { useProcessSpAds } from '@/lib/hooks/queries/use-sp-ads'
import { getErrorDetails } from '@/lib/utils/error-handler'
import { ErrorMessage } from '@/components/ui/error-message'

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { FileInput } from "@/components/ui/file-input"

export default function SpPage() {
  return (
    <ProtectedRoute>
      <SpAdsForm />
    </ProtectedRoute>
  )
}

function SpAdsForm() {
  const [file, setFile] = useState<File | null>(null)
  const [fileName, setFileName] = useState<string>("")
  const [targetACOS, setTargetACOS] = useState<number>(0)
  const [progress, setProgress] = useState(0)
  const [outputFile, setOutputFile] = useState<Blob | null>(null)

  const { 
    mutate: processSpAds,
    isPending: isProcessing,
    error: mutationError,
    reset: resetMutation
  } = useProcessSpAds();

  const features = [
    {
      name: "Boost Sales & Profitability (Guaranteed)",
      description: "Achieve rapid growth with combination of strategic AI-powered solutions tailored for you.",
      icon: ChartBarIcon,
    },
    {
      name: "Effortless Listing Generation",
      description: "Generate optimized, high-quality listings effortlessly with powerful AI-driven tools.",
      icon: ShieldCheckIcon,
    },
    {
      name: "Self-learning Ads Management",
      description: "Optimize ad campaigns intelligently with self-learning AI for enhanced performance.",
      icon: BoltIcon,
    },
  ]

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (files && files.length > 0) {
      const uploadedFile = files[0]
      setFile(uploadedFile)
      setFileName(uploadedFile.name)
    } else {
      setFile(null)
      setFileName("")
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file || targetACOS <= 0) return

    setProgress(0)
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev < 20) return prev + 0.5  // Slower progress at the beginning
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
          onSuccess: (data) => {
            clearInterval(progressInterval)
            setProgress(100)
            
            // Convert the response data to Excel
            const ws = XLSX.utils.json_to_sheet(Array.isArray(data) ? data : [data])
            const wb = XLSX.utils.book_new()
            XLSX.utils.book_append_sheet(wb, ws, "Results")
            const excelBuffer = XLSX.write(wb, { bookType: 'xlsx', type: 'array' })
            const blob = new Blob([excelBuffer], {
              type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            })
            setOutputFile(blob)
          },
          onError: () => {
            clearInterval(progressInterval)
            setProgress(0)
            // console.error('Error processing file:', error)
          },
        }
      )
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    } catch (error) {
      clearInterval(progressInterval)
      setProgress(0)
      // console.error('Unexpected error:', error)
    }
  }

  const handleReset = () => {
    setFile(null)
    setFileName("")
    setTargetACOS(0)
    setProgress(0)
    setOutputFile(null)
  }

  return (
    <main className="flex-1">
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 p-6 flex flex-col items-center justify-center">
        <Card className="w-full max-w-4xl mt-0 border border-gray-700 shadow-xl bg-gray-900/60 backdrop-blur-sm">
          <CardHeader className="border-b border-gray-700/50 pb-6">
            <CardTitle className="text-3xl font-bold text-center text-yellow-400">
              Amazon Sponsored Products Optimizer
            </CardTitle>
            <CardDescription className="text-center text-gray-300 mt-2">
              Optimize your Amazon Sponsored Products to maximize traffic and conversions at a given ACOS
            </CardDescription>
          </CardHeader>

          <CardContent className="pt-8">
            <form onSubmit={handleSubmit} className="space-y-8">
              <div className="space-y-4 p-4 bg-gray-800/40 rounded-lg border border-gray-700/50">
                <Label htmlFor="targetACOS" className="text-yellow-400 text-lg font-medium">
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
                <Label htmlFor="excelFile" className="text-yellow-400 text-lg font-medium">
                  Upload BULK File (Excel) for Last 30 Days
                </Label>
                <div className="flex flex-col space-y-4">
                  <div className="flex items-center space-x-4">
                    <div className="relative w-full">
                      <Button 
                        type="button"
                        className="relative bg-yellow-400 text-black hover:bg-yellow-300 focus:ring-yellow-400 transition-all duration-200 w-full flex items-center justify-center"
                        onClick={() => document.getElementById('excelFile')?.click()}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                        {fileName ? "Change File" : "Choose File"}
                      </Button>
                      <FileInput
                        id="excelFile"
                        accept=".xlsx"
                        onChange={handleFileChange}
                        className="sr-only"
                      />
                    </div>
                  </div>
                  {fileName && (
                    <div className="flex items-center p-3 bg-gray-800/80 rounded-lg border border-gray-700 text-sm text-white">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="truncate font-medium">{fileName}</span>
                    </div>
                  )}
                  <p className="text-gray-400 text-sm">Upload the Sponsored Products bulk file from your Amazon Advertising account</p>
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
                  {isProcessing ? "Processing..." : "Evaluate & Optimize Ads"}
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

            {outputFile && (
              <div className="mt-8 p-6 bg-green-900/20 rounded-lg border border-green-700/50 space-y-4">
                <h3 className="text-green-400 text-lg font-semibold flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Optimization Complete!
                </h3>
                <p className="text-gray-300">Your optimized ad campaigns are ready for download.</p>
                <Button
                  onClick={() => {
                    const url = URL.createObjectURL(outputFile)
                    const a = document.createElement("a")
                    a.href = url
                    a.download = "optimized_campaigns.xlsx"
                    document.body.appendChild(a)
                    a.click()
                    document.body.removeChild(a)
                    URL.revokeObjectURL(url)
                  }}
                  className="w-full bg-green-600 text-white hover:bg-green-500 focus:ring-green-400 flex items-center justify-center gap-2 transition-all duration-200"
                >
                  <ArrowDownTrayIcon className="h-5 w-5" />
                  Download Optimized Campaigns
                </Button>
              </div>
            )}

            {mutationError && (
              <ErrorMessage
                {...getErrorDetails(mutationError)}
                className="mt-8"
                onRetry={() => {
                  resetMutation()
                  if (file && targetACOS > 0) {
                    processSpAds({ file, target_acos: targetACOS })
                  }
                }}
              />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Feature Section */}
      <div className="bg-gradient-to-b from-gray-900 to-gray-800 py-24 sm:py-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl lg:text-center">
            <h2 className="text-base font-semibold leading-7 text-yellow-400">Scale faster</h2>
            <p className="mt-2 text-4xl font-extrabold tracking-tight text-white sm:text-5xl">
              Unleash Your Sales Potential: Free Version & Advanced Tools Available
            </p>
            <p className="mt-6 text-lg leading-8 text-gray-300">
              Tired of lackluster results? Pace Pivot&apos;s free listing generator equips you to skyrocket sales and
              conversions. Get started instantly - no credit card needed.
            </p>
            <div className="mt-10">
              <a
                href="https://pacepivot.com/contact-us/"
                className="inline-block rounded-md bg-yellow-400 px-6 py-3 text-base font-semibold text-gray-900 shadow-sm hover:bg-yellow-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-yellow-400 transition-all duration-200 transform hover:translate-y-[-2px]"
              >
                Contact Us
              </a>
            </div>
          </div>

          {/* Features Grid */}
          <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
            <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
              {features.map((feature) => (
                <div key={feature.name} className="flex flex-col items-start p-6 rounded-lg bg-gray-800/40 border border-gray-700/50 hover:border-yellow-400/30 transition-all duration-300 hover:bg-gray-800/60 transform hover:translate-y-[-5px]">
                  <div className="flex items-center justify-center h-12 w-12 rounded-md bg-yellow-400 text-gray-900">
                    <feature.icon className="h-6 w-6" aria-hidden="true" />
                  </div>
                  <dt className="mt-4 text-lg font-bold leading-7 text-white">{feature.name}</dt>
                  <dd className="mt-2 text-base leading-7 text-gray-300">{feature.description}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </div>
    </main>
  )
}

