"use client"

import { useState } from "react"
import { useAuth } from "@/lib/context/AuthContext"
import { useRouter } from "next/navigation"
import { useEffect } from "react"
import * as XLSX from "xlsx"
import axios, { AxiosError } from "axios"
import { BoltIcon, ChartBarIcon, ShieldCheckIcon } from "@heroicons/react/24/outline"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { json } from "stream/consumers"


export default function ListingGeneratorForm() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [connectivityResult, setConnectivityResult] = useState<string | null>(null)
  const [connectivityError, setConnectivityError] = useState<string | null>(null)
  const [csrfToken, setCsrfToken] = useState<string | null>(null)
  const [error, setError] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [file, setFile] = useState<File | null>(null)
  const [fileData, setFileData] = useState<string | null>(null)
  const [targetACOS, setTargetACOS] = useState<string | null>(null)
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

  const handleFileChange = (event) => {
    const uploadedFile = event.target.files[0]
    setFile(uploadedFile)
  }

  const handleFileParse = async () => {
    if (!file) {
      alert("Please select a file first!")
      return
    }

    const reader = new FileReader()
    reader.onload = async (event) => {
      if (!event.target || !event.target.result) {
        console.error("Error: event.target or event.target.result is null")
        return
      }
      const result = event.target.result
      const workbook = XLSX.read(result, { type: "array" })

      // Parse each sheet into an object
      const sheetsData = {}
      workbook.SheetNames.forEach((sheetName) => {
        const sheet = workbook.Sheets[sheetName]
        const jsonData = XLSX.utils.sheet_to_json(sheet)
        sheetsData[sheetName] = jsonData
      })

      setFileData(JSON.stringify(sheetsData))

      // Send the data to the backend
      try {
        const response = await axios.post("/api/sp", {
          fileData: fileData,
          targetACOS: targetACOS
        })
        console.log("Response from server:", response.data)
      } catch (error) {
        console.error("Error uploading data:", error)
      }
    }

    reader.readAsArrayBuffer(file)
  }

  useEffect(() => {
    async function fetchCsrfToken() {
      console.log("Fetching CSRF token from" + baseUrl + "get_csrf/")
      try {
        const response = await axios.get(`${baseUrl}get_csrf/`, {
          withCredentials: true,
        })
        console.log("CSRF Response:", response)
        const data = response.data
        if (!data.csrfToken) {
          console.error("No CSRF token found in the response.")
          return
        }
        setCsrfToken(data.csrfToken)
      } catch (error) {
        console.error("Error fetching CSRF :", error)
      }
    }
    fetchCsrfToken()
  }, [])

  const processExcelFile = async (file: File) => {
    const reader = new FileReader()
    reader.onload = async (e) => {
      if (e.target?.result) {
        try {
          const response = await axios.post(
            `${baseUrl}api/v1/sp/process_excel/`,
            {
              fileData: fileData,
              targetACOS: targetACOS,
            },
            {
              headers: {
                "X-CSRFToken": csrfToken,
              },
              responseType: "blob",
              withCredentials: true,
            },
          )
          if (response.status === 200) {
            const blob = new Blob([response.data], {
              type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            })
            setOutputFile(blob)
            setProgress(100)
            setError("")
          } else {
            setError("Failed to process the excel file.")
          }
        } catch (error) {
          console.error("Error processing excel file:", error)
          setError("An error occurred while processing the file.")
        } finally {
          setIsProcessing(false)
        }
      }
    }
    reader.readAsArrayBuffer(file)
  }

  const handleReset = () => {
    setError("")
    setIsProcessing(false)
    setProgress(0)
    setFile(null)
    setTargetACOS(null)
    setOutputFile(null)
    setFileData(null)
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
        <Card className="w-full max-w-5xl mt-0">
          <CardHeader>
            <CardTitle className="text-3xl font-bold text-center text-yellow-400">
              Amazon Sponored Product Optimiser
            </CardTitle>
            <CardDescription className="text-center text-black-500">
              Optimise your Amazon Sponsored Products to maximise traffic and conversions at a given ACOS.
            </CardDescription>
          </CardHeader>

          <CardContent>
            <form
              onSubmit={(e) => {
                e.preventDefault()
                if (file && targetACOS) {
                  setIsProcessing(true)
                  processExcelFile(file)
                }
              }}
              className="space-y-6"
            >
              <div className="space-y-2">
                <Label htmlFor="targetACOS" className="text-yellow-400">
                  Target ACOS
                </Label>
                <Input
                  id="targetACOS"
                  type="number"
                  value={targetACOS}
                  onChange={(e) => setTargetACOS(e.target.value)}
                  className="w-full bg-gray-800 text-white border-gray-700 focus:ring-yellow-400"
                  placeholder="Enter Target ACOS"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="excelFile" className="text-yellow-400">
                  Upload Excel File
                </Label>
                <Input
                  id="excelFile"
                  type="file"
                  accept=".xlsx, .xls"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="w-full bg-gray-800 text-white border-gray-700 focus:ring-yellow-400"
                />
              </div>

              <Button
                type="submit"
                disabled={isProcessing || !file || !targetACOS}
                className="w-full bg-yellow-400 text-black hover:bg-yellow-300 focus:ring-yellow-400 flex items-center justify-center"
              >
                {isProcessing ? "Processing..." : "Evaluate Ads"}
              </Button>
            </form>
            {isProcessing && (
              <div className="mt-6 space-y-2">
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
                  a.download = "output.xlsx"
                  document.body.appendChild(a)
                  a.click()
                  document.body.removeChild(a)
                  URL.revokeObjectURL(url)
                }}
                className="mt-6 w-full bg-green-500 text-white hover:bg-green-600 focus:ring-green-400"
              >
                Download Output
              </Button>
            )}
            {error && (
              <div className="mt-6 text-red-500">
                <p>{error}</p>
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
          {/* Feature Section */}
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

