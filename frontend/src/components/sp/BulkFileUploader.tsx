import { Button } from "@/components/ui/button"
import { FileInput } from "@/components/ui/file-input"
import { Label } from "@/components/ui/label"

interface BulkFileUploaderProps {
  file: File | null
  setFile: (file: File | null) => void
}

export function BulkFileUploader({ file, setFile }: BulkFileUploaderProps) {
  return (
    <div className="space-y-4 p-4 bg-gray-800/40 rounded-lg border border-gray-700/50">
      <Label htmlFor="file" className="text-yellow-400 text-lg font-medium">
        Upload BULK File (Excel) for Last 30 Days
      </Label>
      <div className="flex flex-col space-y-4">
        <div className="flex items-center space-x-4">
          <div className="relative w-full">
            <Button 
              type="button"
              className="relative bg-yellow-400 text-black hover:bg-yellow-300 focus:ring-yellow-400 transition-all duration-200 w-full flex items-center justify-center"
              onClick={() => document.getElementById('file')?.click()}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              {file ? "Change File" : "Choose File"}
            </Button>
            <FileInput
              id="file"
              accept=".xlsx"
              onFileSelect={(selectedFile) => setFile(selectedFile)}
              className="sr-only"
            />
          </div>
        </div>
        {file && (
          <div className="flex items-center p-3 bg-gray-800/80 rounded-lg border border-gray-700 text-sm text-white">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="truncate font-medium">{file.name}</span>
          </div>
        )}
        <p className="text-gray-400 text-sm">Upload the Amazon Advertising bulk file that contains your Sponsored Products, Sponsored Brands, and/or Sponsored Display campaigns</p>
      </div>
    </div>
  )
} 