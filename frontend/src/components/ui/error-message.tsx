import { AlertCircle } from "lucide-react"
import { Button } from "./button"

interface ErrorMessageProps {
  title?: string
  message: string
  className?: string
  onRetry?: () => void
}

export function ErrorMessage({
  title = "Error",
  message,
  className,
  onRetry,
}: ErrorMessageProps) {
  return (
    <div
      className={`rounded-lg border border-red-500/50 bg-red-500/10 p-4 text-red-400 ${className}`}
    >
      <div className="flex items-center gap-2">
        <AlertCircle className="h-5 w-5" />
        <h3 className="font-semibold">{title}</h3>
      </div>
      <p className="mt-2 text-sm">{message}</p>
      {onRetry && (
        <Button
          onClick={onRetry}
          className="mt-4 bg-red-500 text-white hover:bg-red-600"
        >
          Try Again
        </Button>
      )}
    </div>
  )
} 