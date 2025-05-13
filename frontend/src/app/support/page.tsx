import Link from 'next/link'
import { Card, CardContent } from '@/components/ui/card'
import { 
  BookOpenIcon, 
  UserCircleIcon,
  ServerIcon,
  ChartBarIcon,
  TagIcon,
  ShieldCheckIcon,
  BanknotesIcon,
  QuestionMarkCircleIcon,
  PhoneIcon 
} from '@heroicons/react/24/outline'

export default function SupportPage() {
  return (
    <div className="container py-10 max-w-5xl mx-auto">
      {/* Hero section with enhanced styling */}
      <div className="relative mb-16">
        {/* <div className="absolute inset-x-0 -top-40 -z-10 transform-gpu overflow-hidden blur-3xl sm:-top-80">
          <div className="relative left-[calc(50%-11rem)] aspect-[1150/678] w-[36.125rem] -translate-x-1/2 rotate-[50deg] bg-gradient-to-tr from-yellow-400 to-yellow-600 opacity-30 sm:left-[calc(20%-30rem)] sm:w-[72.1875rem]" />
        </div> */}
        
        <div className="bg-gradient-to-r from-yellow-400 via-yellow-500 to-yellow-600 p-0.5 rounded-lg">
          <div className="bg-white dark:bg-gray-950 rounded-md p-10">
            <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-center mb-6 bg-clip-text text-transparent bg-gradient-to-r from-yellow-400 via-yellow-500 to-yellow-600">Pace Pivot Support Center</h1>
            <p className="text-gray-600 dark:text-gray-400 text-center max-w-3xl mx-auto mb-10 text-lg">
              Welcome to the Pace Pivot Support Center. This comprehensive guide will help you navigate and maximize the potential of your all-in-one Amazon Seller management solution. Whether you're just getting started or looking to optimize your experience, you'll find the answers you need here.
            </p>

            {/* Table of Contents with icons */}
            <Card className="mb-12 shadow-lg border-0 overflow-hidden">
              <div className="bg-gradient-to-r from-yellow-400 to-yellow-600 py-3 px-6">
                <h2 className="text-xl font-semibold text-white">Table of Contents</h2>
              </div>
              <CardContent className="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <ul className="space-y-4">
                    <li className="flex items-center gap-2">
                      <BookOpenIcon className="h-5 w-5 text-yellow-600" />
                      <Link href="#getting-started" className="text-yellow-600 hover:text-yellow-500 font-medium">Getting Started</Link>
                    </li>
                    <li className="flex items-center gap-2">
                      <UserCircleIcon className="h-5 w-5 text-yellow-600" />
                      <Link href="#account-setup" className="text-yellow-600 hover:text-yellow-500 font-medium">Account Setup</Link>
                    </li>
                    <li className="flex items-center gap-2">
                      <ServerIcon className="h-5 w-5 text-yellow-600" />
                      <Link href="#amazon-api-integration" className="text-yellow-600 hover:text-yellow-500 font-medium">Amazon API Integration</Link>
                    </li>
                    <li className="flex items-center gap-2">
                      <ChartBarIcon className="h-5 w-5 text-yellow-600" />
                      <Link href="#dashboard-overview" className="text-yellow-600 hover:text-yellow-500 font-medium">Dashboard Overview</Link>
                    </li>
                    <li className="flex items-start gap-2">
                      <TagIcon className="h-5 w-5 text-yellow-600 mt-0.5" />
                      <div>
                        <Link href="#key-features" className="text-yellow-600 hover:text-yellow-500 font-medium">Key Features</Link>
                        <ul className="ml-7 mt-2 space-y-2">
                          <li><Link href="#listing-upgrade" className="text-yellow-600 hover:text-yellow-500 text-sm">Listing Upgrade</Link></li>
                          <li><Link href="#smart-pricing-management" className="text-yellow-600 hover:text-yellow-500 text-sm">Smart Pricing Management</Link></li>
                          <li><Link href="#real-time-order-dashboard" className="text-yellow-600 hover:text-yellow-500 text-sm">Real-Time Order Dashboard</Link></li>
                          <li><Link href="#inventory-status-and-alerts" className="text-yellow-600 hover:text-yellow-500 text-sm">Inventory Status and Alerts</Link></li>
                          <li><Link href="#business-performance-reports" className="text-yellow-600 hover:text-yellow-500 text-sm">Business Performance Reports</Link></li>
                        </ul>
                      </div>
                    </li>
                  </ul>
                </div>
                <div>
                  <ul className="space-y-4">
                    <li className="flex items-center gap-2">
                      <ShieldCheckIcon className="h-5 w-5 text-yellow-600" />
                      <Link href="#troubleshooting" className="text-yellow-600 hover:text-yellow-500 font-medium">Troubleshooting</Link>
                    </li>
                    <li className="flex items-center gap-2">
                      <BanknotesIcon className="h-5 w-5 text-yellow-600" />
                      <Link href="#billing-and-subscription" className="text-yellow-600 hover:text-yellow-500 font-medium">Billing and Subscription</Link>
                    </li>
                    <li className="flex items-center gap-2">
                      <ShieldCheckIcon className="h-5 w-5 text-yellow-600" />
                      <Link href="#security-and-compliance" className="text-yellow-600 hover:text-yellow-500 font-medium">Security and Compliance</Link>
                    </li>
                    <li className="flex items-center gap-2">
                      <QuestionMarkCircleIcon className="h-5 w-5 text-yellow-600" />
                      <Link href="#frequently-asked-questions" className="text-yellow-600 hover:text-yellow-500 font-medium">FAQ</Link>
                    </li>
                    <li className="flex items-center gap-2">
                      <PhoneIcon className="h-5 w-5 text-yellow-600" />
                      <Link href="#contact-support" className="text-yellow-600 hover:text-yellow-500 font-medium">Contact Support</Link>
                    </li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
      
      {/* Content sections with enhanced styling */}
      <div className="space-y-16">
        {/* Getting Started */}
        <section id="getting-started" className="scroll-mt-16">
          <div className="bg-white dark:bg-gray-950 rounded-lg shadow-md overflow-hidden">
            <div className="bg-gradient-to-r from-yellow-400 to-yellow-600 py-3 px-6">
              <h2 className="text-2xl font-bold text-white">Getting Started</h2>
            </div>
            <div className="p-6">
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 mb-6">
                <h3 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">System Requirements</h3>
                <ul className="list-disc pl-6 space-y-2 mb-6">
                  <li>Modern web browser (Chrome, Firefox, Safari, or Edge)</li>
                  <li>Stable internet connection</li>
                  <li>Active Amazon Seller Central account</li>
                  <li>Professional selling plan recommended for full feature access</li>
                </ul>
              </div>

              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6">
                <h3 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">Accessing the App</h3>
                <p className="mb-0">Pace Pivot is available as Web application (access via any browser)</p>
              </div>
            </div>
          </div>
        </section>

        {/* Account Setup */}
        <section id="account-setup" className="scroll-mt-16">
          <div className="bg-white dark:bg-gray-950 rounded-lg shadow-md overflow-hidden">
            <div className="bg-gradient-to-r from-yellow-400 to-yellow-600 py-3 px-6">
              <h2 className="text-2xl font-bold text-white">Account Setup</h2>
            </div>
            <div className="p-6">
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 mb-6">
                <h3 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">Creating Your Account</h3>
                <ol className="list-decimal pl-6 space-y-2 mb-0">
                  <li>Visit <Link href="https://www.pacepivot.com" className="text-yellow-600 hover:underline font-medium">www.pacepivot.com</Link></li>
                  <li>Click "Sign Up" and enter your business email</li>
                  <li>Create a secure password</li>
                  <li>Verify your email address</li>
                  <li>Complete your business profile</li>
                </ol>
              </div>

              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6">
                <h3 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">Connecting Your Amazon Seller Account</h3>
                <ol className="list-decimal pl-6 space-y-2 mb-0">
                  <li>From your Pace Pivot dashboard, navigate to "Settings" &gt; "Marketplace Connections"</li>
                  <li>Select "Connect Amazon Account"</li>
                  <li>You'll be redirected to Amazon to authorize the connection</li>
                  <li>Grant the necessary permissions for Pace Pivot to access your seller data</li>
                  <li>Return to Pace Pivot where your connection will be confirmed</li>
                </ol>
              </div>
            </div>
          </div>
        </section>

        {/* Amazon API Integration */}
        <section id="amazon-api-integration" className="scroll-mt-16">
          <div className="bg-white dark:bg-gray-950 rounded-lg shadow-md overflow-hidden">
            <div className="bg-gradient-to-r from-yellow-400 to-yellow-600 py-3 px-6">
              <h2 className="text-2xl font-bold text-white">Amazon API Integration</h2>
            </div>
            <div className="p-6">
              <p className="mb-4">
                Pace Pivot uses Amazon's Selling Partner API to securely access your seller data. This official integration method ensures:
              </p>
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 mb-6">
                <ul className="list-disc pl-6 space-y-2 mb-0">
                  <li>Full compliance with Amazon's terms of service</li>
                  <li>Enhanced security for your sensitive business information</li>
                  <li>Real-time data synchronization</li>
                  <li>No risk of account suspension due to unauthorized tools</li>
                </ul>
              </div>

              <h3 className="text-xl font-semibold mt-8 mb-4 text-gray-800 dark:text-gray-200">API Permission Scope</h3>
              <p className="mb-4">
                When connecting your account, Pace Pivot will request permissions for:
              </p>
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 mb-4">
                <ul className="list-disc pl-6 space-y-2 mb-0">
                  <li>Inventory management</li>
                  <li>Order processing</li>
                  <li>Product listing data</li>
                  <li>Pricing information</li>
                  <li>Performance metrics</li>
                  <li>Advertisement management</li>
                </ul>
              </div>
              <p>You can review and modify these permissions at any time through your Amazon Seller Central account.</p>
            </div>
          </div>
        </section>

        {/* Dashboard Overview - showing as example, would continue for all sections */}
        <section id="dashboard-overview" className="scroll-mt-16">
          <div className="bg-white dark:bg-gray-950 rounded-lg shadow-md overflow-hidden">
            <div className="bg-gradient-to-r from-yellow-400 to-yellow-600 py-3 px-6">
              <h2 className="text-2xl font-bold text-white">Dashboard Overview</h2>
            </div>
            <div className="p-6">
              <p className="mb-4">
                After logging in, you'll see your personalized dashboard with:
              </p>
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 mb-4">
                <ul className="list-disc pl-6 space-y-2 mb-0">
                  <li>Quick Stats: Today's orders, sales, returns, and Buy Box percentage</li>
                  <li>Performance Snapshot: 7-day trend of key metrics</li>
                  <li>Ads Performance Snapshot: Campaign performance & key metrics</li>
                  <li>Alert Center: Inventory, pricing, and listing alerts requiring attention</li>
                  <li>Recent Orders: Latest customer purchases</li>
                  <li>Navigation Menu: Access to all major features</li>
                </ul>
              </div>
              <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4 border-l-4 border-yellow-500">
                <p className="text-yellow-800 dark:text-yellow-200 text-sm mb-0">
                  <span className="font-semibold">Pro Tip:</span> Customize your dashboard by clicking "Personalize View" to show the metrics most important to your business.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Key Features with improved UI */}
        <section id="key-features" className="scroll-mt-16">
          <div className="bg-white dark:bg-gray-950 rounded-lg shadow-md overflow-hidden">
            <div className="bg-gradient-to-r from-yellow-400 to-yellow-600 py-3 px-6">
              <h2 className="text-2xl font-bold text-white">Key Features</h2>
            </div>
            <div className="p-6">
              <div id="listing-upgrade" className="mb-10 scroll-mt-16">
                <div className="flex items-center gap-2 mb-4">
                  <div className="bg-yellow-100 dark:bg-yellow-800/30 p-2 rounded-full">
                    <TagIcon className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">1. Listing Upgrade</h3>
                </div>
                
                <p className="mb-6 pl-10">
                  Optimize your Amazon product listings to improve search visibility and conversion rates.
                </p>
                
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 mb-6 ml-10">
                  <h4 className="font-medium mb-3 text-gray-800 dark:text-gray-200">How to Use:</h4>
                  <ol className="list-decimal pl-6 space-y-2 mb-0">
                    <li>Navigate to "Products" &gt; "Listing Optimizer"</li>
                    <li>Select the ASINs you want to optimize</li>
                    <li>Click "Run Audit" to evaluate current listing performance</li>
                    <li>Review the suggested improvements across:
                      <ul className="list-disc pl-6 mt-2 space-y-1">
                        <li>Title optimization</li>
                        <li>Bullet point enhancement</li>
                        <li>Description quality</li>
                        <li>Keyword coverage</li>
                        <li>Image quality and quantity</li>
                        <li>Enhanced Brand Content opportunities</li>
                      </ul>
                    </li>
                    <li>Apply recommended changes directly through the interface</li>
                    <li>Track performance improvements over time</li>
                  </ol>
                </div>
                
                <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4 border-l-4 border-yellow-500 ml-10">
                  <h4 className="font-medium mb-2 text-yellow-800 dark:text-yellow-200">Best Practices:</h4>
                  <ul className="list-disc pl-6 space-y-1 text-yellow-800 dark:text-yellow-200 text-sm mb-0">
                    <li>Run audits monthly to ensure ongoing optimization</li>
                    <li>Pay special attention to top-selling products</li>
                    <li>Implement suggested keywords in a natural, readable way</li>
                    <li>Monitor conversion rate changes after optimization</li>
                  </ul>
                </div>
              </div>

              {/* One more feature section to show pattern - would continue for all features */}
              <div id="smart-pricing-management" className="mb-10 scroll-mt-16">
                <div className="flex items-center gap-2 mb-4">
                  <div className="bg-yellow-100 dark:bg-yellow-800/30 p-2 rounded-full">
                    <BanknotesIcon className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">2. Smart Pricing Management</h3>
                </div>
                
                <p className="mb-6 pl-10">
                  Maintain competitive pricing while protecting your margins with intelligent, rule-based price adjustments.
                </p>
                
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 mb-6 ml-10">
                  <h4 className="font-medium mb-3 text-gray-800 dark:text-gray-200">How to Use:</h4>
                  <ol className="list-decimal pl-6 space-y-2 mb-0">
                    <li>Go to "Pricing" &gt; "Price Manager"</li>
                    <li>Select products to include in your pricing strategy</li>
                    <li>Set your pricing rules:
                      <ul className="list-disc pl-6 mt-2 space-y-1">
                        <li>Minimum acceptable price</li>
                        <li>Maximum price</li>
                        <li>Target profit margin</li>
                        <li>Competitor matching parameters</li>
                        <li>Buy Box winning strategy</li>
                      </ul>
                    </li>
                    <li>Choose automation level:
                      <ul className="list-disc pl-6 mt-2 space-y-1">
                        <li>Manual (review recommendations before applying)</li>
                        <li>Semi-automatic (apply changes but notify you)</li>
                        <li>Fully automatic (apply changes without intervention)</li>
                      </ul>
                    </li>
                    <li>Monitor performance in the "Pricing Analysis" section</li>
                  </ol>
                </div>
                
                <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4 border-l-4 border-yellow-500 ml-10">
                  <h4 className="font-medium mb-2 text-yellow-800 dark:text-yellow-200">Strategy Templates:</h4>
                  <ul className="list-disc pl-6 space-y-1 text-yellow-800 dark:text-yellow-200 text-sm mb-0">
                    <li>Buy Box Maximizer: Prioritizes winning the Buy Box</li>
                    <li>Profit Protector: Maintains minimum profit margins</li>
                    <li>Inventory Velocity: Adjusts pricing based on stock levels</li>
                    <li>Custom Strategy: Build your own rule combinations</li>
                  </ul>
                </div>
              </div>
              
              {/* Adding Real-Time Order Dashboard */}
              <div id="real-time-order-dashboard" className="mb-10 scroll-mt-16">
                <div className="flex items-center gap-2 mb-4">
                  <div className="bg-yellow-100 dark:bg-yellow-800/30 p-2 rounded-full">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6 text-yellow-600 dark:text-yellow-400">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5m.75-9 3-3 2.148 2.148A12.061 12.061 0 0 1 16.5 7.605" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">3. Real-Time Order Dashboard</h3>
                </div>
                
                <p className="mb-6 pl-10">
                  Track and manage all your Amazon orders from a centralized interface.
                </p>
                
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 mb-6 ml-10">
                  <h4 className="font-medium mb-3 text-gray-800 dark:text-gray-200">Features:</h4>
                  <ul className="list-disc pl-6 space-y-2 mb-4">
                    <li>Live order notifications</li>
                    <li>Order status tracking</li>
                    <li>Fulfillment method monitoring (FBA vs. FBM)</li>
                    <li>Customer communication management</li>
                    <li>Return and refund processing</li>
                    <li>Order performance analytics</li>
                  </ul>
                  
                  <h4 className="font-medium mb-3 text-gray-800 dark:text-gray-200">Views Available:</h4>
                  <ul className="list-disc pl-6 space-y-2 mb-0">
                    <li>Today's Orders: Real-time stream of incoming sales</li>
                    <li>Order Calendar: Daily, weekly, monthly order volumes</li>
                    <li>Fulfillment Status: Track orders by fulfillment stage</li>
                    <li>Performance Comparison: Compare order metrics across timeframes</li>
                  </ul>
                </div>
              </div>
              
              {/* Adding Inventory Status and Alerts */}
              <div id="inventory-status-and-alerts" className="mb-10 scroll-mt-16">
                <div className="flex items-center gap-2 mb-4">
                  <div className="bg-yellow-100 dark:bg-yellow-800/30 p-2 rounded-full">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6 text-yellow-600 dark:text-yellow-400">
                      <path strokeLinecap="round" strokeLinejoin="round" d="m21 7.5-9-5.25L3 7.5m18 0-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">4. Inventory Status and Alerts</h3>
                </div>
                
                <p className="mb-6 pl-10">
                  Proactively manage your inventory across warehouses and fulfillment centers.
                </p>
                
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 mb-6 ml-10">
                  <h4 className="font-medium mb-3 text-gray-800 dark:text-gray-200">Key Capabilities:</h4>
                  <ol className="list-decimal pl-6 space-y-2 mb-4">
                    <li>Stock Level Monitoring: Real-time visibility of inventory counts</li>
                    <li>Restock Alerts: Customizable notifications when products reach reorder points</li>
                    <li>FBA Inventory Health: Track age of inventory and storage fee projections</li>
                    <li>Slow-Moving Inventory Alerts: Identify products at risk of long-term storage fees</li>
                    <li>Multi-warehouse View: Consolidated view across all storage locations</li>
                    <li>Inventory Forecasting: Predictive analytics for inventory planning</li>
                  </ol>
                  
                  <h4 className="font-medium mb-3 text-gray-800 dark:text-gray-200">Setting Up Alerts:</h4>
                  <ol className="list-decimal pl-6 space-y-2 mb-0">
                    <li>Go to "Inventory" &gt; "Alert Settings"</li>
                    <li>Configure thresholds for:
                      <ul className="list-disc pl-6 mt-2 space-y-1">
                        <li>Low stock warnings (days of inventory remaining)</li>
                        <li>Excess inventory alerts</li>
                        <li>Long-term storage fee warnings</li>
                        <li>Inventory age notifications</li>
                      </ul>
                    </li>
                    <li>Choose notification methods (email, SMS, in-app)</li>
                    <li>Set alert frequency and priority levels</li>
                  </ol>
                </div>
              </div>
              
              {/* Adding Business Performance Reports */}
              <div id="business-performance-reports" className="mb-10 scroll-mt-16">
                <div className="flex items-center gap-2 mb-4">
                  <div className="bg-yellow-100 dark:bg-yellow-800/30 p-2 rounded-full">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6 text-yellow-600 dark:text-yellow-400">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">5. Business Performance Reports</h3>
                </div>
                
                <p className="mb-6 pl-10">
                  Make data-driven decisions with comprehensive analytics and customizable reports.
                </p>
                
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 mb-6 ml-10">
                  <h4 className="font-medium mb-3 text-gray-800 dark:text-gray-200">Available Reports:</h4>
                  <ul className="list-disc pl-6 space-y-2 mb-4">
                    <li>Sales Performance: Revenue, units sold, ASP by product/category</li>
                    <li>Profit Analysis: COGS, fees, shipping, and margin calculations</li>
                    <li>Advertising Performance: ACOS, TACOS, and campaign effectiveness</li>
                    <li>Return Rate Analysis: Return reasons and product quality insights</li>
                    <li>Competitive Positioning: Buy Box win rate and market share</li>
                    <li>Trend Analysis: Year-over-year and period comparisons</li>
                  </ul>
                  
                  <h4 className="font-medium mb-3 text-gray-800 dark:text-gray-200">Custom Report Builder:</h4>
                  <ol className="list-decimal pl-6 space-y-2 mb-0">
                    <li>Navigate to "Analytics" &gt; "Custom Reports"</li>
                    <li>Select metrics and dimensions for your report</li>
                    <li>Choose visualization types (graphs, tables, heat maps)</li>
                    <li>Set date ranges and comparison periods</li>
                    <li>Save report templates for future use</li>
                    <li>Schedule automated report delivery to stakeholders</li>
                  </ol>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Troubleshooting Section */}
        <section id="troubleshooting" className="scroll-mt-16">
          <div className="bg-white dark:bg-gray-950 rounded-lg shadow-md overflow-hidden">
            <div className="bg-gradient-to-r from-yellow-400 to-yellow-600 py-3 px-6">
              <h2 className="text-2xl font-bold text-white">Troubleshooting</h2>
            </div>
            <div className="p-6">
              <h3 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">Common Issues and Solutions</h3>
              
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 mb-6">
                <div className="space-y-6">
                  <div>
                    <h4 className="font-medium mb-2 text-gray-800 dark:text-gray-200">1. Connection Problems</h4>
                    <p className="mb-1"><strong>Issue:</strong> Amazon API connection fails</p>
                    <p><strong>Solution:</strong> Verify your seller credentials and reauthorize Pace Pivot in your Amazon Seller Central account. Check if Amazon's API services are experiencing downtime.</p>
                  </div>
                  
                  <div>
                    <h4 className="font-medium mb-2 text-gray-800 dark:text-gray-200">2. Data Sync Delays</h4>
                    <p className="mb-1"><strong>Issue:</strong> Recent changes not appearing in Pace Pivot</p>
                    <p><strong>Solution:</strong> Click "Sync Now" in the affected section. Amazon's API has a natural delay of up to 30 minutes for some data types.</p>
                  </div>
                  
                  <div>
                    <h4 className="font-medium mb-2 text-gray-800 dark:text-gray-200">3. Pricing Rule Conflicts</h4>
                    <p className="mb-1"><strong>Issue:</strong> Multiple pricing rules creating unexpected results</p>
                    <p><strong>Solution:</strong> Review rule priorities in "Pricing" &gt; "Rule Settings". Higher priority rules will override lower ones when conflicts occur.</p>
                  </div>
                  
                  <div>
                    <h4 className="font-medium mb-2 text-gray-800 dark:text-gray-200">4. Missing Products</h4>
                    <p className="mb-1"><strong>Issue:</strong> Some ASINs not appearing in your inventory</p>
                    <p><strong>Solution:</strong> Check the "Product Filter" settings. Ensure marketplace filters are set correctly. For newly added products, wait 24 hours for them to appear.</p>
                  </div>
                </div>
              </div>
              
              <h3 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">Error Code Reference</h3>
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6">
                <ul className="space-y-2">
                  <li><strong>AM-1001:</strong> Authentication error. Reconnect your Amazon account.</li>
                  <li><strong>AM-1002:</strong> Data access denied. Check your API permissions.</li>
                  <li><strong>AM-1003:</strong> Rate limit exceeded. Reduce the frequency of data requests.</li>
                  <li><strong>AM-2001:</strong> Invalid pricing rule. Review and correct rule parameters.</li>
                  <li><strong>AM-3001:</strong> Report generation failed. Try again with simplified parameters.</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Billing and Subscription */}
        <section id="billing-and-subscription" className="scroll-mt-16">
          <div className="bg-white dark:bg-gray-950 rounded-lg shadow-md overflow-hidden">
            <div className="bg-gradient-to-r from-yellow-400 to-yellow-600 py-3 px-6">
              <h2 className="text-2xl font-bold text-white">Billing and Subscription</h2>
            </div>
            <div className="p-6">
              <div className="mb-8">
                <h3 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">Plans and Pricing</h3>
                <p className="mb-4">Pace Pivot offers flexible subscription plans to meet the needs of sellers at every stage:</p>
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 mb-4">
                  <ul className="list-disc pl-6 space-y-2">
                    <li><strong>Starter:</strong> For sellers with up to 100 ASINs</li>
                    <li><strong>Growth:</strong> For sellers with up to 500 ASINs</li>
                    <li><strong>Professional:</strong> For sellers with up to 2,000 ASINs</li>
                    <li><strong>Enterprise:</strong> Custom solution for sellers with over 2,000 ASINs</li>
                  </ul>
                </div>
                <p>All plans include core features with varying limits on API calls, report exports, and advanced features.</p>
              </div>
              
              <div className="mb-8">
                <h3 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">Managing Your Subscription</h3>
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 mb-4">
                  <ol className="list-decimal pl-6 space-y-2">
                    <li>Access "Account" &gt; "Subscription"</li>
                    <li>View current plan details and usage statistics</li>
                    <li>Upgrade or downgrade your plan</li>
                    <li>Update payment information</li>
                    <li>View billing history and download invoices</li>
                  </ol>
                </div>
              </div>
              
              <div>
                <h3 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">Payment Methods</h3>
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6">
                  <ul className="list-disc pl-6 space-y-2">
                    <li>Credit/debit cards</li>
                    <li>PayPal</li>
                    <li>Razorpay</li>
                    <li>PayU</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Security and Compliance */}
        <section id="security-and-compliance" className="scroll-mt-16">
          <div className="bg-white dark:bg-gray-950 rounded-lg shadow-md overflow-hidden">
            <div className="bg-gradient-to-r from-yellow-400 to-yellow-600 py-3 px-6">
              <h2 className="text-2xl font-bold text-white">Security and Compliance</h2>
            </div>
            <div className="p-6">
              <div className="mb-8">
                <h3 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">Data Protection</h3>
                <p className="mb-4">Pace Pivot implements enterprise-grade security measures:</p>
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6">
                  <ul className="list-disc pl-6 space-y-2">
                    <li>End-to-end encryption for all data</li>
                    <li>SOC 2 Type II compliance</li>
                    <li>Regular security audits and penetration testing</li>
                    <li>No storage of Amazon customer PII</li>
                    <li>Automatic data purging for inactive accounts</li>
                  </ul>
                </div>
              </div>
              
              <div className="mb-8">
                <h3 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">Amazon Terms of Service Compliance</h3>
                <p className="mb-4">Pace Pivot strictly adheres to Amazon's Seller Central terms:</p>
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6">
                  <ul className="list-disc pl-6 space-y-2">
                    <li>Uses only approved API integration methods</li>
                    <li>Maintains compliance with data usage policies</li>
                    <li>Regular updates to align with Amazon policy changes</li>
                    <li>No prohibited data scraping or automation techniques</li>
                  </ul>
                </div>
              </div>
              
              <div>
                <h3 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">Data Retention Policy</h3>
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6">
                  <ul className="list-disc pl-6 space-y-2">
                    <li>Active account data: Stored as long as account remains active</li>
                    <li>Order history: Retained for 7 years for tax compliance</li>
                    <li>User activity logs: 90 days</li>
                    <li>Deleted account data: Purged within 30 days of account closure</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* FAQ */}
        <section id="frequently-asked-questions" className="scroll-mt-16">
          <div className="bg-white dark:bg-gray-950 rounded-lg shadow-md overflow-hidden">
            <div className="bg-gradient-to-r from-yellow-400 to-yellow-600 py-3 px-6">
              <h2 className="text-2xl font-bold text-white">Frequently Asked Questions</h2>
            </div>
            <div className="p-6">
              <h3 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">General Questions</h3>
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 mb-8">
                <div className="space-y-6">
                  <div>
                    <p className="font-medium mb-1 text-gray-800 dark:text-gray-200">Q: Is Pace Pivot compatible with all Amazon marketplaces?</p>
                    <p>A: Yes, Pace Pivot supports all global Amazon marketplaces including US, CA, UK, DE, FR, IT, ES, JP, AU, and more.</p>
                  </div>
                  <div>
                    <p className="font-medium mb-1 text-gray-800 dark:text-gray-200">Q: Can I manage multiple seller accounts with one Pace Pivot account?</p>
                    <p>A: Yes, Growth plans and above support multiple seller account connections. Each connected account will count toward your ASIN limit.</p>
                  </div>
                  <div>
                    <p className="font-medium mb-1 text-gray-800 dark:text-gray-200">Q: Does using Pace Pivot violate Amazon's Terms of Service?</p>
                    <p>A: No, Pace Pivot uses Amazon's official Selling Partner API with proper authorization, ensuring full compliance with Amazon's terms.</p>
                  </div>
                </div>
              </div>
              
              <h3 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">Feature-Specific Questions</h3>
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6">
                <div className="space-y-6">
                  <div>
                    <p className="font-medium mb-1 text-gray-800 dark:text-gray-200">Q: How often is inventory data updated?</p>
                    <p>A: Inventory levels are updated every 30 minutes for FBA inventory and in real-time for merchant-fulfilled inventory.</p>
                  </div>
                  <div>
                    <p className="font-medium mb-1 text-gray-800 dark:text-gray-200">Q: Can I export reports to Excel or Google Sheets?</p>
                    <p>A: Yes, all reports can be exported to CSV, Excel, PDF, and directly to Google Sheets via our integration.</p>
                  </div>
                  <div>
                    <p className="font-medium mb-1 text-gray-800 dark:text-gray-200">Q: Does the pricing tool automatically change my prices on Amazon?</p>
                    <p>A: Only if you choose the fully automatic mode. You can also set it to recommend changes only or require approval before implementation.</p>
                  </div>
                  <div>
                    <p className="font-medium mb-1 text-gray-800 dark:text-gray-200">Q: How far back can I see historical data?</p>
                    <p>A: Standard plans include 12 months of historical data. Enterprise plans can access up to 3 years of history.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Contact Support - final section with call-to-action */}
        <section id="contact-support" className="scroll-mt-16">
          <div className="bg-white dark:bg-gray-950 rounded-lg shadow-md overflow-hidden">
            <div className="bg-gradient-to-r from-yellow-400 to-yellow-600 py-3 px-6">
              <h2 className="text-2xl font-bold text-white">Contact Support</h2>
            </div>
            <div className="p-6">
              <p className="mb-6">
                Our dedicated support team is available to help you get the most out of Pace Pivot:
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 text-center">
                  <div className="mx-auto w-12 h-12 bg-yellow-100 dark:bg-yellow-800/30 rounded-full flex items-center justify-center mb-4">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6 text-yellow-600 dark:text-yellow-400">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold mb-2 text-gray-800 dark:text-gray-200">Support Hours</h3>
                  <ul className="space-y-1 text-sm">
                    <li>Monday-Saturday: 9am-7pm IST</li>
                    <li>Sunday: Email support only</li>
                  </ul>
                </div>
                
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 text-center">
                  <div className="mx-auto w-12 h-12 bg-yellow-100 dark:bg-yellow-800/30 rounded-full flex items-center justify-center mb-4">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6 text-yellow-600 dark:text-yellow-400">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 0 1-.825-.242m9.345-8.334a2.126 2.126 0 0 0-.476-.095 48.64 48.64 0 0 0-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0 0 11.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold mb-2 text-gray-800 dark:text-gray-200">Contact Methods</h3>
                  <ul className="space-y-1 text-sm">
                    <li>Live Chat: Available in-app</li>
                    <li><a href="mailto:support@pacepivot.com" className="text-yellow-600 hover:underline">support@pacepivot.com</a></li>
                    <li><a href="tel:9167612665" className="text-yellow-600 hover:underline">+91 91676 12665</a></li>
                  </ul>
                </div>
                
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 text-center">
                  <div className="mx-auto w-12 h-12 bg-yellow-100 dark:bg-yellow-800/30 rounded-full flex items-center justify-center mb-4">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6 text-yellow-600 dark:text-yellow-400">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 0 1-1.043 3.296 3.745 3.745 0 0 1-3.296 1.043A3.745 3.745 0 0 1 12 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 0 1-3.296-1.043 3.745 3.745 0 0 1-1.043-3.296A3.745 3.745 0 0 1 3 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 0 1 1.043-3.296 3.746 3.746 0 0 1 3.296-1.043A3.746 3.746 0 0 1 12 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 0 1 3.296 1.043 3.746 3.746 0 0 1 1.043 3.296A3.745 3.745 0 0 1 21 12Z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold mb-2 text-gray-800 dark:text-gray-200">Priority Support</h3>
                  <p className="text-sm">
                    Enterprise and Professional plan customers receive priority support with dedicated account managers and faster response times.
                  </p>
                </div>
              </div>
              
              {/* <div className="mt-8 text-center">
                <Link href="" className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-yellow-600 hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500">
                  Contact Us Now
                </Link>
              </div> */}
            </div>
          </div>
        </section>
      </div>

      <div className="text-center text-gray-500 mt-16 pt-6 border-t">
        <p>Thank you for choosing Pace Pivot to power your Amazon selling business. We're continuously improving our platform based on seller feedback, so please don't hesitate to share your suggestions with our team.</p>
      </div>
    </div>
  )
} 