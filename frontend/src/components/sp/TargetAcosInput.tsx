import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"

interface TargetAcosInputProps {
  targetACOS: number;
  setTargetACOS: (value: number) => void;
  useUnifiedAcos: boolean;
  setUseUnifiedAcos: (value: boolean) => void;
  spTargetACOS: number;
  setSpTargetACOS: (value: number) => void;
  sbTargetACOS: number;
  setSbTargetACOS: (value: number) => void;
  sdTargetACOS: number;
  setSdTargetACOS: (value: number) => void;
}

// Helper component for ACOS input fields
function AcosInput({ 
  id, 
  value, 
  onChange, 
  label 
}: { 
  id: string; 
  value: number; 
  onChange: (value: number) => void; 
  label: string 
}) {
  return (
    <div className="flex flex-col space-y-2">
      <Label htmlFor={id} className="text-white font-medium">
        {label}
      </Label>
      <div className="relative w-full">
        <input
          id={id}
          type="number"
          min="0"
          max="1"
          step="0.01"
          value={value}
          onChange={(e) => {
            const value = parseFloat(e.target.value);
            if (!isNaN(value)) {
              const clampedValue = Math.min(Math.max(value, 0), 1);
              onChange(Number(clampedValue.toFixed(2)));
            }
          }}
          className="w-full bg-gray-900 text-white border border-gray-700 focus:ring-1 focus:ring-yellow-400/50 focus:border-yellow-400/50 rounded-md p-2 outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none pr-8 text-sm font-medium"
          placeholder="0.25"
        />
        <div className="absolute right-0 top-0 bottom-0 w-7 flex flex-col border-l border-gray-700/50">
          <button
            type="button"
            onClick={() => {
              const newValue = Math.min(value + 0.01, 1);
              onChange(Number(newValue.toFixed(2)));
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
              const newValue = Math.max(value - 0.01, 0);
              onChange(Number(newValue.toFixed(2)));
            }}
            className="flex-1 flex items-center justify-center hover:bg-gray-800 text-gray-500 hover:text-yellow-400 transition-all duration-150 rounded-br-md border-t border-gray-700/50"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
              <path fillRule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

export function TargetAcosInput({ 
  targetACOS, 
  setTargetACOS,
  useUnifiedAcos,
  setUseUnifiedAcos,
  spTargetACOS,
  setSpTargetACOS,
  sbTargetACOS,
  setSbTargetACOS,
  sdTargetACOS,
  setSdTargetACOS
}: TargetAcosInputProps) {
  return (
    <div className="space-y-8 p-4">
      <div className="flex justify-between items-center">
        <Label htmlFor="targetACOSType" className="text-yellow-400 text-lg font-medium">
          Target ACOS Settings
        </Label>
        <div className="flex items-center space-x-3">
          <Label htmlFor="targetACOSType" className="text-gray-300 text-sm">
            {useUnifiedAcos ? "Single ACOS" : "Separate ACOS"}
          </Label>
          <Switch
            id="targetACOSType"
            checked={useUnifiedAcos}
            onCheckedChange={setUseUnifiedAcos}
            className="data-[state=checked]:bg-yellow-400"
          />
        </div>
      </div>

      {useUnifiedAcos ? (
        <div className="flex flex-col space-y-2">
          <div className="relative w-1/4">
            <AcosInput 
              id="targetACOS"
              value={targetACOS}
              onChange={setTargetACOS}
              label="Unified Target ACOS"
            />
          </div>
          <p className="text-gray-400 text-sm">Enter a value between 0 and 1 (e.g., 0.25 for 25% ACOS)</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <AcosInput 
            id="spTargetACOS"
            value={spTargetACOS}
            onChange={setSpTargetACOS}
            label="Sponsored Products ACOS"
          />
          <AcosInput 
            id="sbTargetACOS"
            value={sbTargetACOS}
            onChange={setSbTargetACOS}
            label="Sponsored Brands ACOS"
          />
          <AcosInput 
            id="sdTargetACOS"
            value={sdTargetACOS}
            onChange={setSdTargetACOS}
            label="Sponsored Display ACOS"
          />
          <p className="text-gray-400 text-sm col-span-full">Enter values between 0 and 1 (e.g., 0.25 for 25% ACOS)</p>
        </div>
      )}
    </div>
  )
} 