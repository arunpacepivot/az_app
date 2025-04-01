import React, { useRef, useState } from 'react'
import { cn } from '@/lib/utils'

interface FileInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  onFileSelect?: (file: File) => void
}

export const FileInput = React.forwardRef<HTMLInputElement, FileInputProps>(
  ({ className, onFileSelect, id, ...props }, ref) => {
    const inputRef = useRef<HTMLInputElement | null>(null)
    const [dragActive, setDragActive] = useState(false)

    const handleFiles = (files: FileList | null) => {
      if (files && files.length > 0) {
        const file = files[0]
        onFileSelect?.(file)
      }
    }

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      handleFiles(event.target.files)
    }

    const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault()
      e.stopPropagation()
      if (e.type === 'dragenter' || e.type === 'dragover') {
        setDragActive(true)
      } else if (e.type === 'dragleave') {
        setDragActive(false)
      }
    }

    const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault()
      e.stopPropagation()
      setDragActive(false)
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        handleFiles(e.dataTransfer.files)
      }
    }

    return (
      <input
        ref={(node) => {
          if (typeof ref === 'function') {
            ref(node)
          } else if (ref) {
            ref.current = node
          }
          inputRef.current = node
        }}
        type="file"
        onChange={handleChange}
        className={cn(className)}
        id={id}
        {...props}
      />
    )
  }
)

FileInput.displayName = 'FileInput' 