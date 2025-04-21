import { Label } from "@/components/ui/label"

interface TargetAcosInputProps {
  targetACOS: number
  setTargetACOS: (value: number) => void
}

export function TargetAcosInput({ targetACOS, setTargetACOS }: TargetAcosInputProps) {
  return (
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
  )
} 