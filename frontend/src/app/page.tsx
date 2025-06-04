import { BoltIcon, ChartBarIcon, ShieldCheckIcon } from '@heroicons/react/24/outline'
import Link from 'next/link'
import Image from 'next/image'
import { PricingCard } from '@/components/pricing/PricingCard'

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

          {/* Right side with AI Assistant Preview */}
          <div className="mx-auto mt-16 flex max-w-2xl sm:mt-24 lg:ml-10 lg:mt-0 lg:mr-0 lg:max-w-none lg:flex-none xl:ml-32">
            <div className="max-w-3xl flex-none sm:max-w-5xl lg:max-w-none">
              <div className="relative w-[40rem] h-[35rem] sm:w-[57rem]">
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-tr from-[#ff80b5] to-[#9089fc] opacity-10" />
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 opacity-20 blur-2xl" />
                <div className="relative h-full w-full rounded-2xl bg-white/5 ring-1 ring-white/10 backdrop-blur-3xl">
                  <div className="absolute inset-0 flex flex-col items-center justify-center p-8">
                    <div className="relative h-32 w-80 mb-8">
                      <Image
                        src="/logo.jpg"
                        alt="PacePivot Logo"
                        fill
                        sizes="(max-width: 768px) 240px, 320px"
                        className="object-contain"
                        priority
                      />
                    </div>
                    <div className="text-3xl font-semibold text-gray-600">AI Assistant Preview</div>
                    <p className="mt-4 text-center text-gray-500 max-w-md text-lg">
                      Experience the power of AI-driven insights and automation for your ecommerce business
                    </p>
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

      {/* Pricing Section */}
      <div className="bg-gray-900 py-24 sm:py-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-base font-semibold leading-7 text-yellow-400">Pricing</h2>
            <p className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Choose the right plan for your business
            </p>
            <p className="mt-6 text-lg leading-8 text-gray-300">
              Start with our free trial and scale as you grow. No hidden fees, no commitments.
            </p>
          </div>

          <div className="mx-auto mt-16 grid max-w-lg grid-cols-1 items-center gap-y-6 sm:mt-20 sm:gap-y-0 sm:gap-x-6 lg:max-w-4xl lg:grid-cols-2">
            <PricingCard
              title="Free Trial"
              price="$0"
              period="/7 days"
              features={[
                "Full access to all features",
                "AI-powered insights",
                "Basic analytics",
                "Standard support",
                "Up to 100 queries/day"
              ]}
              ctaText="Start Free Trial"
              ctaLink="/signup"
            />

            <PricingCard
              title="Pro Plan"
              price="$50"
              period="/month"
              highlighted={true}
              features={[
                "Everything in Free Trial",
                "Advanced AI analytics",
                "Unlimited queries",
                "Priority support",
                "Custom integrations",
                "API access"
              ]}
              ctaText="Get Started"
              ctaLink="/signup"
            />
          </div>

          {/* Enterprise Contact */}
          <div className="mt-20 text-center">
            <h3 className="text-xl font-semibold text-white mb-4">Need a custom solution?</h3>
            <div className="space-y-4 mb-6">
              <div className="flex items-center justify-center space-x-2 text-gray-300">
                <svg className="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <a href="mailto:support@pacepivot.com" className="hover:text-yellow-400 transition-colors">
                  support@pacepivot.com
                </a>
              </div>
              <div className="flex items-center justify-center space-x-2 text-gray-300">
                <svg className="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                </svg>
                <a href="tel:+919167612665" className="hover:text-yellow-400 transition-colors">
                  +91 91676 12665
                </a>
              </div>
            </div>
            <Link
              href="/"
              className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-black bg-yellow-400 hover:bg-yellow-500 transition-colors duration-300"
            >
              Contact Us
            </Link>
            <p className="mt-4 text-sm text-gray-400">
              Let's discuss how we can help your enterprise grow
            </p>
          </div>
        </div>
      </div>

      {/* Footer Logo Section */}
      <div className="bg-white py-16">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="flex flex-col items-center justify-center">
            <div className="relative h-24 w-72 mb-6">
              <Image
                src="/logo.jpg"
                alt="PacePivot Logo"
                fill
                sizes="(max-width: 768px) 200px, 288px"
                className="object-contain"
                priority={false}
              />
            </div>
            <p className="mt-4 text-center text-gray-600 text-sm">
              Empowering ecommerce businesses with AI-driven solutions
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}