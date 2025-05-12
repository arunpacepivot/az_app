import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { ErrorMessage } from '@/components/ui/error-message'
import { SpAdsResponse } from '@/lib/api/types'
import { getErrorDetails } from '@/lib/utils/error-handler'
import { TargetAcosInput } from './TargetAcosInput'
import { BulkFileUploader } from './BulkFileUploader'
import { FormActions } from './FormActions'
import { ProcessingIndicator } from './ProcessingIndicator'
import { OptimizationResults } from './OptimizationResults'

interface AdOptimizerCardProps {
  file: File | null
  setFile: (file: File | null) => void
  targetACOS: number
  setTargetACOS: (acos: number) => void
  useUnifiedAcos: boolean
  setUseUnifiedAcos: (value: boolean) => void
  spTargetACOS: number
  setSpTargetACOS: (value: number) => void
  sbTargetACOS: number
  setSbTargetACOS: (value: number) => void
  sdTargetACOS: number
  setSdTargetACOS: (value: number) => void
  isProcessing: boolean
  progress: number
  processedData: SpAdsResponse | null
  previewOpen: boolean
  setPreviewOpen: (open: boolean) => void
  mutationError: any
  onSubmit: (e: React.FormEvent) => Promise<void>
  onReset: () => void
  resetMutation: () => void
}

export function AdOptimizerCard({
  file,
  setFile,
  targetACOS,
  setTargetACOS,
  useUnifiedAcos,
  setUseUnifiedAcos,
  spTargetACOS,
  setSpTargetACOS,
  sbTargetACOS,
  setSbTargetACOS,
  sdTargetACOS,
  setSdTargetACOS,
  isProcessing,
  progress,
  processedData,
  previewOpen,
  setPreviewOpen,
  mutationError,
  onSubmit,
  onReset,
  resetMutation
}: AdOptimizerCardProps) {
  return (
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
        <form onSubmit={onSubmit} className="space-y-12">
          <TargetAcosInput 
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
          />

          <BulkFileUploader 
            file={file} 
            setFile={setFile} 
          />

          <FormActions 
            isProcessing={isProcessing} 
            file={file} 
            targetACOS={targetACOS}
            hasValidAcos={useUnifiedAcos ? targetACOS > 0 : (spTargetACOS > 0 || sbTargetACOS > 0 || sdTargetACOS > 0)}
            onReset={onReset} 
          />
        </form>

        {isProcessing && (
          <ProcessingIndicator progress={progress} />
        )}

        {processedData && (
          <OptimizationResults 
            processedData={processedData} 
            previewOpen={previewOpen} 
            setPreviewOpen={setPreviewOpen} 
          />
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
  )
} 