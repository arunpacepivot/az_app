"use client"

import { useState } from 'react'
import ProtectedRoute from '@/components/auth/protected-route'
import { useProcessSpAds } from '@/lib/hooks/queries/use-sp-ads'
import { SpAdsResponse } from '@/lib/api/types'
import { Buffer } from 'buffer'
import { AdOptimizerCard } from '@/components/sp/AdOptimizerCard'

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
  const [useUnifiedAcos, setUseUnifiedAcos] = useState<boolean>(true)
  const [spTargetACOS, setSpTargetACOS] = useState<number>(0.30)
  const [sbTargetACOS, setSbTargetACOS] = useState<number>(0.30)
  const [sdTargetACOS, setSdTargetACOS] = useState<number>(0.30)
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
    if (!file) return
    if (useUnifiedAcos && targetACOS <= 0) return
    if (!useUnifiedAcos && spTargetACOS <= 0 && sbTargetACOS <= 0 && sdTargetACOS <= 0) return

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
      const payload = {
        file,
        useUnifiedAcos,
        ...(useUnifiedAcos 
          ? { target_acos: targetACOS } 
          : { 
              sp_target_acos: spTargetACOS,
              sb_target_acos: sbTargetACOS,
              sd_target_acos: sdTargetACOS
            }
        )
      };

      await processSpAds(
        payload,
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
    setSpTargetACOS(0.30)
    setSbTargetACOS(0.30)
    setSdTargetACOS(0.30)
    setProgress(0)
    setProcessedData(null)
    resetMutation()
  }

  return (
    <main className="flex-1">
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 p-6 flex flex-col items-center justify-center">
        <AdOptimizerCard 
          file={file}
          setFile={setFile}
          targetACOS={targetACOS}
          setTargetACOS={setTargetACOS}
          useUnifiedAcos={useUnifiedAcos}
          setUseUnifiedAcos={setUseUnifiedAcos}
          spTargetACOS={spTargetACOS}
          setSpTargetACOS={setSpTargetACOS}
          sbTargetACOS={sbTargetACOS}
          setSbTargetACOS={setSbTargetACOS}
          sdTargetACOS={sdTargetACOS}
          setSdTargetACOS={setSdTargetACOS}
          isProcessing={isProcessing}
          progress={progress}
          processedData={processedData}
          previewOpen={previewOpen}
          setPreviewOpen={setPreviewOpen}
          mutationError={mutationError}
          onSubmit={handleSubmit}
          onReset={handleReset}
          resetMutation={resetMutation}
        />
      </div>
    </main>
  )
}