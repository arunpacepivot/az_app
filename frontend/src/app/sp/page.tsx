"use client"

import { useState } from "react"
import { useAuth } from "@/lib/context/AuthContext"
import { useRouter } from "next/navigation"
import { useEffect } from "react"
import axios from "axios"
import { BoltIcon, ChartBarIcon, ShieldCheckIcon } from "@heroicons/react/24/outline"
import * as XLSX from 'xlsx'

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { FileInput } from "@/components/ui/file-input"

export default function ListingGeneratorForm() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [csrfToken, setCsrfToken] = useState<string | null>(null)
  const [error, setError] = useState("")
  const [apiError, setApiError] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [file, setFile] = useState<File | null>(null)
  const [targetACOS, setTargetACOS] = useState<number>(0)
  const [outputFile, setOutputFile] = useState<Blob | null>(null)

  const baseUrl = "https://django-backend-epcse2awb3cyh5e8.centralindia-01.azurewebsites.net/"

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
        })
        const data = response.data
        if (!data.csrfToken) {
          setError("No security token found. Please try again.")
          return
        }
        setCsrfToken(data.csrfToken)
      } catch (error) {
        setError("Failed to get security token. Please refresh the page.")
      }
    }
    fetchCsrfToken()
  }, [])

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFile = event.target.files?.[0]
    setFile(uploadedFile || null)
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

      const response = await axios.post(
        `${baseUrl}process_spads/`,
        formData,
        {
          headers: {
            "X-CSRFToken": csrfToken,
            "Content-Type": "multipart/form-data",
          },
          withCredentials: true,
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
        setApiError(error.response?.data?.error || "Server error occurred")
      } else {
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
    setTargetACOS(0)
    setOutputFile(null)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  return (
    <main className="flex-1">
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 p-6 flex flex-col items-center justify-center">
        <Card className="w-1/2 max-h-[180vh] overflow-y-auto mt-0">
          <CardHeader>
            <CardTitle className="text-3xl font-bold text-center text-yellow-400">
              Amazon Sponsored Product Optimiser
            </CardTitle>
            <CardDescription className="text-center text-black-500">
              Optimise your Amazon Sponsored Products to maximise traffic and conversions at a given ACOS.
            </CardDescription>
          </CardHeader>

          <CardContent>
            <form
              onSubmit={(e) => {
                e.preventDefault()
                if (!file || !targetACOS) {
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
              className="space-y-12"
            >
              <div className="space-y-8 p-4">
                <Label htmlFor="targetACOS" className="text-yellow-400">
                  Target ACOS
                </Label>
                <Input
                  id="targetACOS"
                  type="number"
                  value={targetACOS}
                  onChange={(e) => setTargetACOS(parseFloat(e.target.value))}
                  className="w-1/6 bg-gray-800 text-white border-gray-700 focus:ring-yellow-400"
                  placeholder="Enter Target ACOS"
                  step="0.01"
                  min="0"
                  max="1"
                />
              </div>

              <div className="space-y-8 p-4">
                <Label htmlFor="excelFile" className="text-yellow-400">
                  Upload BULK File (Excel) for Last 30 Days
                </Label>
                <FileInput
                  id="excelFile"
                  accept=".xlsx"
                  onChange={handleFileChange}
                  className="w-1/4 bg-gray-800 text-white border-gray-700 focus:ring-yellow-400"
                />
              </div>

              <Button
                type="submit"
                disabled={isProcessing || !file || !targetACOS}
                className="w-full mt-8 bg-yellow-400 text-black hover:bg-yellow-300 focus:ring-yellow-400 flex items-center justify-center"
              >
                {isProcessing ? "Processing..." : "Evaluate Ads"}
              </Button>
            </form>

            {isProcessing && (
              <div className="mt-8 space-y-8">
                <Label className="text-yellow-400">Processing Excel File...</Label>
                <Progress value={progress} className="w-full" />
              </div>
            )}

            {outputFile && (
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
                className="mt-8 w-full bg-green-500 text-white hover:bg-green-600 focus:ring-green-400"
              >
                Download Optimized Campaigns
              </Button>
            )}

            {error && (
              <div className="mt-8 text-red-500">
                <p>Error: {error}</p>
              </div>
            )}

            {apiError && (
              <div className="mt-8 text-red-500">
                <p>Server Error: {apiError}</p>
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
              Tired of lackluster results? Pace Pivot's free listing generator equips you to skyrocket sales and
              conversions. Get started instantly - no credit card needed.
            </p>
            <div className="mt-10">
              <a
                href="https://pacepivot.com/contact-us/"
                className="inline-block rounded-md bg-yellow-400 px-6 py-3 text-base font-semibold text-gray-900 shadow-sm hover:bg-yellow-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-yellow-400"
              >
                Contact Us
              </a>
            </div>
          </div>

          {/* Features Grid */}
          <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
            <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
              {features.map((feature) => (
                <div key={feature.name} className="flex flex-col items-start">
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

