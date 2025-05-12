import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"

interface ProcessingIndicatorProps {
  progress: number
}

export function ProcessingIndicator({ progress }: ProcessingIndicatorProps) {
  return (
    <div className="mt-8 p-4 bg-gray-800/40 rounded-lg border border-gray-700/50 space-y-4">
      <Label className="text-yellow-400 font-medium">Processing Your Excel File...</Label>
      <Progress value={progress} className="w-full h-2 bg-gray-700" />
      <p className="text-gray-400 text-sm">
        This process may take 5-6 minutes to complete. Please keep this page open.
        We are analyzing your campaigns and optimizing bids for maximum performance.
      </p>
    </div>
  )
} 