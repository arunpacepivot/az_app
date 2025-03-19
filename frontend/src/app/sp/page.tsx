"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/lib/context/AuthContext"
import axios from "axios"
import { BoltIcon, ChartBarIcon, ShieldCheckIcon, ArrowDownTrayIcon } from "@heroicons/react/24/outline"
import * as XLSX from 'xlsx'

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { FileInput } from "@/components/ui/file-input"

export default function ListingGeneratorForm() {
  const { loading } = useAuth()
  const [csrfToken, setCsrfToken] = useState<string | null>(null)
  const [error, setError] = useState("")
  const [apiError, setApiError] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [file, setFile] = useState<File | null>(null)
  const [fileName, setFileName] = useState<string>("")
  const [targetACOS, setTargetACOS] = useState<number>(0)
  const [outputFile, setOutputFile] = useState<Blob | null>(null)

  // Use environment variables for the backend URL
  const isDevelopment = process.env.NODE_ENV === 'development';
    const baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 
      (isDevelopment ? "http://localhost:8000/" : "https://django-backend-epcse2awb3cyh5e8.centralindia-01.azurewebsites.net/");

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

  useEffect(() => {
    async function fetchCsrfToken() {
      try {
        const response = await axios.get(`${baseUrl}get_csrf/`, {
          withCredentials: true,
          timeout: 10000, // 10 second timeout
        })
        const data = response.data
        if (!data.csrfToken) {
          setError("No security token found. Please try again.")
          return
        }
        setCsrfToken(data.csrfToken)
      } catch (fetchError) {
        console.error("CSRF fetch error:", fetchError)
        if (axios.isAxiosError(fetchError)) {
          if (fetchError.code === 'ECONNABORTED') {
            setError("Connection timeout. Please check your internet connection.")
          } else if (!fetchError.response) {
            setError("Network error. Please check if backend server is running.")
          } else {
            setError("Failed to get security token. Please refresh the page.")
          }
        } else {
          setError("Failed to get security token. Please refresh the page.")
        }
      }
    }
    fetchCsrfToken()
  }, [baseUrl])

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFile = event.target.files?.[0]
    if (uploadedFile) {
      setFile(uploadedFile)
      setFileName(uploadedFile.name)
    } else {
      setFile(null)
      setFileName("")
    }
    setError("")
    setApiError(null)
  }

  const processExcelFile = async (file: File) => {
    if (!csrfToken) {
      setError("Waiting for security token...")
      return
    }

    const formData = new FormData()
    formData.append("file", file)
    formData.append("target_acos", targetACOS.toString())

    try {
      setError("")
      setApiError(null)
      setProgress(20)

      console.log(`Sending request to: ${baseUrl}process_spads/`)
      const response = await axios.post(
        `${baseUrl}process_spads/`,
        formData,
        {
          headers: {
            "X-CSRFToken": csrfToken,
            // "Content-Type": "multipart/form-data",
          },
          withCredentials: true,
          timeout: 60000, // 60 second timeout for file processing
        }
      )
      
      setProgress(60)

      if (response.status === 200) {
        // Convert the JSON response to Excel
        const ws = XLSX.utils.json_to_sheet(response.data)
        const wb = XLSX.utils.book_new()
        XLSX.utils.book_append_sheet(wb, ws, "Results")
        const excelBuffer = XLSX.write(wb, { bookType: 'xlsx', type: 'array' })
        const blob = new Blob([excelBuffer], {
          type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        })
        setOutputFile(blob)
        setProgress(100)
      }
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error("Axios error processing file:", error)
        if (error.code === 'ECONNABORTED') {
          setApiError("Request timed out. The server might be busy or the file is too large.")
        } else if (error.response) {
          if (error.response.data && typeof error.response.data === 'string' && 
              error.response.data.includes("'list' object has no attribute 'items'")) {
            setApiError("Backend error: The product data format is invalid. Please try again with different data.")
          } else {
            const errorMessage = typeof error.response.data === 'object' && error.response.data.error
              ? error.response.data.error
              : typeof error.response.data === 'string'
                ? error.response.data
                : `Server error: ${error.response.status}`
            setApiError(errorMessage)
          }
        } else if (error.request) {
          setApiError("Network Error: No response received from the server. Please check your internet connection.")
        } else {
          setApiError(`Error: ${error.message}`)
        }
      } else {
        console.error("Unexpected error:", error)
        setError("Failed to process file")
      }
    } finally {
      setIsProcessing(false)
    }
  }

  const handleReset = () => {
    setError("")
    setApiError(null)
    setIsProcessing(false)
    setProgress(0)
    setFile(null)
    setFileName("")
    setTargetACOS(0)
    setOutputFile(null)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-gray-900 to-gray-800">
        <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-yellow-400"></div>
      </div>
    )
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
            <form
              onSubmit={(e) => {
                e.preventDefault()
                if (!file || targetACOS <= 0) {
                  setError("Please provide both file and target ACOS")
                  return
                }
                if (!csrfToken) {
                  setError("Please wait for security token...")
                  return
                }
                setIsProcessing(true)
                processExcelFile(file)
              }}
              className="space-y-8"
            >
              <div className="space-y-4 p-4 bg-gray-800/40 rounded-lg border border-gray-700/50">
                <Label htmlFor="targetACOS" className="text-yellow-400 text-lg font-medium">
                  Target ACOS
                </Label>
                <div className="flex flex-col space-y-2">
                  <Input
                    id="targetACOS"
                    type="number"
                    value={targetACOS}
                    onChange={(value) => setTargetACOS(value)}
                    className="w-1/4 bg-gray-800 text-white border-gray-700 focus:ring-yellow-400 focus:border-yellow-400"
                    placeholder="Enter Target ACOS"
                    step="0.01"
                    min="0"
                    max="1"
                  />
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
                <p className="text-gray-400 text-sm">This may take a minute. Please don&apos;t close this page.</p>
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

            {error && (
              <div className="mt-8 p-4 bg-red-900/20 rounded-lg border border-red-700/50">
                <p className="text-red-400 flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  Error: {error}
                </p>
              </div>
            )}

            {apiError && (
              <div className="mt-8 p-4 bg-red-900/20 rounded-lg border border-red-700/50">
                <p className="text-red-400 flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  Server Error: {apiError}
                </p>
              </div>
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

