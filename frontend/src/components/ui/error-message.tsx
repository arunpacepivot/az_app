import { ExclamationTriangleIcon, XCircleIcon } from '@heroicons/react/24/outline';

interface ErrorMessageProps {
  message: string;
  details?: string;
  isServerError?: boolean;
  className?: string;
  onRetry?: () => void;
}

export function ErrorMessage({
  message,
  details,
  isServerError,
  className = '',
  onRetry,
}: ErrorMessageProps) {
  return (
    <div className={`rounded-lg border ${isServerError ? 'bg-red-900/20 border-red-700/50' : 'bg-yellow-900/20 border-yellow-700/50'} p-4 ${className}`}>
      <div className="flex items-start">
        {isServerError ? (
          <XCircleIcon className="h-5 w-5 text-red-400 mt-0.5" />
        ) : (
          <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400 mt-0.5" />
        )}
        <div className="ml-3 flex-1">
          <p className={`text-sm font-medium ${isServerError ? 'text-red-400' : 'text-yellow-400'}`}>
            {message}
          </p>
          {details && (
            <p className={`mt-1 text-sm ${isServerError ? 'text-red-400/80' : 'text-yellow-400/80'}`}>
              {details}
            </p>
          )}
          {onRetry && (
            <button
              onClick={onRetry}
              className={`mt-2 text-sm font-medium ${
                isServerError
                  ? 'text-red-400 hover:text-red-300'
                  : 'text-yellow-400 hover:text-yellow-300'
              } transition-colors duration-150`}
            >
              Try again
            </button>
          )}
        </div>
      </div>
    </div>
  );
} 