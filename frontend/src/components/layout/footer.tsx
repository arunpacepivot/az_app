import Link from 'next/link'

const Footer = () => {
  return (
    <footer className="bg-black border-t">
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center">
          <div className="text-yellow-400 text-sm">
            © {new Date().getFullYear()} Pace Pivot Private Limited. All rights reserved.
          </div>
          <div className="flex space-x-6">
            <Link href="/support" className="text-yellow-400 hover:text-white">
              Support
            </Link>
            {/* <a href="#" className="text-yellow-400 hover:text-white">
              Privacy Policy
            </a>
            <a href="#" className="text-yellow-400 hover:text-white">
              Terms of Service
            </a> */}
          </div>
        </div>
      </div>
    </footer>
  )
}

export default Footer