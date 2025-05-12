import { BoltIcon, ChartBarIcon, ShieldCheckIcon } from '@heroicons/react/24/outline'
import Link from 'next/link'

const features = [
  {
    name: 'Easy Integration',
    description: 'Connect and deploy your AI models with just a few clicks. No complex setup required.',
    icon: BoltIcon
  },
  {
    name: 'Powerful Analytics',
    description: 'Get detailed insights and performance metrics to optimize your AI solutions.',
    icon: ChartBarIcon
  },
  {
    name: 'Secure & Scalable',
    description: 'Enterprise-grade security with scalable infrastructure to grow with your needs.',
    icon: ShieldCheckIcon
  },
]

export default function Home() {
  return (
    <main className="flex-1">
      {/* Hero Section */}
      <div className="relative isolate overflow-hidden bg-white">
        {/* Add decorative background elements */}
        <div className="absolute inset-x-0 -top-40 -z-10 transform-gpu overflow-hidden blur-3xl sm:-top-80">
          <div className="relative left-[calc(50%-11rem)] aspect-[1155/678] w-[36.125rem] -translate-x-1/2 rotate-[30deg] bg-gradient-to-tr from-[#ff80b5] to-[#9089fc] opacity-30 sm:left-[calc(50%-30rem)] sm:w-[72.1875rem]" />
        </div>

        <div className="mx-auto max-w-7xl px-6 pb-24 pt-10 sm:pb-32 lg:flex lg:px-8 lg:py-40">
          {/* Left side content */}
          <div className="mx-auto max-w-2xl lg:mx-0 lg:max-w-xl lg:flex-shrink-0 lg:pt-8">
            <h1 className="mt-10 text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
              AI-Powered Solutions for Your Ecommerce Business
            </h1>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              Transform your ecommerce workflow with cutting-edge AI technology. Streamline processes, 
              gain insights, and unlock new possibilities for your business.
            </p>
            <div className="mt-10 flex items-center gap-x-6">
              <Link
                href="/signup"
                className="rounded-md bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
              >
                Get started
              </Link>
              <Link href="/login" className="text-sm font-semibold leading-6 text-gray-900">
                Learn more <span aria-hidden="true">→</span>
              </Link>
            </div>
          </div>

          {/* Right side with placeholder or actual image */}
          <div className="mx-auto mt-16 flex max-w-2xl sm:mt-24 lg:ml-10 lg:mt-0 lg:mr-0 lg:max-w-none lg:flex-none xl:ml-32">
            <div className="max-w-3xl flex-none sm:max-w-5xl lg:max-w-none">
              <div className="relative w-[40rem] h-[35rem] sm:w-[57rem]">
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-tr from-[#ff80b5] to-[#9089fc] opacity-10" />
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 opacity-20 blur-2xl" />
                {/* You can replace this div with an actual image when ready */}
                <div className="relative h-full w-full rounded-2xl bg-white/5 ring-1 ring-white/10 backdrop-blur-3xl">
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-2xl font-semibold text-gray-400">AI Assistant Preview</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Section */}
      <div className="bg-gray-50 py-24 sm:py-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl lg:text-center">
            <h2 className="text-base font-semibold leading-7 text-indigo-600">Scale faster</h2>
            <p className="mt-2 text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Everything you need to scale your ecommerce business
            </p>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              Get started with our intuitive platform and powerful features designed to help you succeed.
            </p>
          </div>
          <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
            <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
              {features.map((feature) => (
                <div key={feature.name} className="flex flex-col">
                  <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-gray-900">
                    <feature.icon className="h-5 w-5 flex-none text-indigo-600" aria-hidden="true" />
                    {feature.name}
                  </dt>
                  <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-gray-600">
                    <p className="flex-auto">{feature.description}</p>
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </div>
    </main>
  )
}