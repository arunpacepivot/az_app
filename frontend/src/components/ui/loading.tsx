export default function LoadingScreen() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      <div className="relative">
        <div className="h-24 w-24 rounded-full border-t-4 border-b-4 border-indigo-600 animate-spin"></div>
        <div className="h-16 w-16 rounded-full border-t-4 border-b-4 border-purple-600 animate-spin absolute top-4 left-4"></div>
      </div>
      <h2 className="text-xl font-semibold text-gray-700 mt-8 animate-pulse">
        Loading...
      </h2>
    </div>
  )
} 