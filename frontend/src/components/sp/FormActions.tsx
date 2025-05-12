import { Button } from "@/components/ui/button"

interface FormActionsProps {
  isProcessing: boolean
  file: File | null
  targetACOS: number
  hasValidAcos: boolean
  onReset: () => void
}

export function FormActions({ isProcessing, file, hasValidAcos, onReset }: FormActionsProps) {
  return (
    <div className="flex space-x-4 pt-4">
      <Button
        type="submit"
        disabled={isProcessing || !file || !hasValidAcos}
        className="w-3/4 bg-yellow-400 text-black hover:bg-yellow-300 focus:ring-yellow-400 flex items-center justify-center transition-all duration-200 transform hover:translate-y-[-2px] shadow-lg"
      >
        {isProcessing ? (
          <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-black mr-2"></span>
        ) : null}
        {isProcessing ? "Processing..." : "Optimize All Ad Campaigns"}
      </Button>
      <Button
        type="button"
        onClick={onReset}
        disabled={isProcessing}
        className="w-1/4 bg-gray-700 text-white hover:bg-gray-600 transition-all duration-200 border border-gray-600"
      >
        Reset
      </Button>
    </div>
  )
} 