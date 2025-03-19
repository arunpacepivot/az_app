'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/context/AuthContext'
import axios from "axios";
import { BoltIcon, ChartBarIcon, ShieldCheckIcon, DocumentTextIcon } from '@heroicons/react/24/outline'

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Progress } from "@/components/ui/progress"

type Listing = Record<string, string>;

const formatText = (text: string) => {
  if (!text) return '-';
  
  // Split the text by ** markers
  const parts = text.split(/(\*\*.*?\*\*)/g);
  
  return (
    <span>
      {parts.map((part, index) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          // Remove ** and apply bold styling
          return (
            <span key={index} className="font-semibold text-yellow-400">
              {part.slice(2, -2)}
            </span>
          );
        }
        return <span key={index}>{part}</span>;
      })}
    </span>
  );
};

export default function ListingGeneratorForm() {
    const { loading } = useAuth()
    const [selectedCountry, setSelectedCountry] = useState("");
    const [asins, setAsins] = useState("");
    const [csrfToken, setCsrfToken] = useState<string | null>(null);
    const [error, setError] = useState("");
    const [listings, setListings] = useState<Listing[] | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [progress, setProgress] = useState(0);

    const countries = [
        "India",
        "United States",
        "United Kingdom",
        "Canada",
        "Germany",
        "France",
        "Italy",
        "Spain",
        "Japan",
        "Australia",
    ];

    // More robust URL determination
    const isDevelopment = process.env.NODE_ENV === 'development';
    const baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 
      (isDevelopment ? "http://localhost:8000/" : "https://django-backend-epcse2awb3cyh5e8.centralindia-01.azurewebsites.net/");
   
    const features = [
      {
        name: 'Boost Sales & Profitability (Guaranteed)',
        description: 'Achieve rapid growth with combination of strategic AI-powered solutions tailored for you.',
        icon: ChartBarIcon
      },
      {
        name: 'Effortless Listing Generation',
        description: 'Generate optimized, high-quality listings effortlessly with powerful AI-driven tools.',
        icon: ShieldCheckIcon
      },
      {
        name: 'Self-learning Ads Management',
        description: 'Optimize ad campaigns intelligently with self-learning AI for enhanced performance.',
        icon: BoltIcon
      },
    ]   

    useEffect(() => {
      async function fetchCsrfToken() {
        console.log("Fetching CSRF token from "+baseUrl+"get_csrf/");
        try {
          const response = await axios.get(`${baseUrl}get_csrf/`, {
            withCredentials: true,
            timeout: 10000, // 10 second timeout
          });
          console.log("CSRF Response:", response);
          const data = response.data;
          if (!data.csrfToken) {
            console.error("No CSRF token found in the response.");
            setError("No security token found in response. Please try again.");
            return;
          }
          setCsrfToken(data.csrfToken);
        } catch (error) {
          console.error("Error fetching CSRF:", error);
          // Don't show error to user during initial load
          if (axios.isAxiosError(error) && error.code === 'ECONNABORTED') {
            setError("Connection timeout. Please check your internet connection.");
          } else if (axios.isAxiosError(error) && !error.response) {
            setError("Network error. Please check if backend server is running.");
          }
        }
      }
      fetchCsrfToken();
    }, [baseUrl]);

    const handleInputChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
        setAsins(event.target.value);
    };
    
    const handleGenerateListings = async () => {
        const sanitizedAsins = asins
        .split(',')
        .map(asin => asin.trim())
        .filter(asin => asin);

        if (!sanitizedAsins.length) {
            setError("Please enter one or more ASINs.");
            return;
        }
        
        if (!csrfToken) {
            setError("No security token available. Please refresh the page.");
            return;
        }
      
        setError("");
        setIsProcessing(true);
        setProgress(0);
      
        const progressInterval = setInterval(() => {
          setProgress((prevProgress) => (prevProgress < 90 ? prevProgress + 10 : prevProgress));
        }, 500);
      
        const payload = { asins, geography: selectedCountry };
    
        try {
          console.log(`Sending request to: ${baseUrl}api/v1/lister/process_asins/`);
          const response = await axios.post(
            `${baseUrl}api/v1/lister/process_asins/`,
            payload,
            {
              headers: {
                "X-CSRFToken": csrfToken,
                "Content-Type": "application/json",
              },
              withCredentials: true,
              timeout: 30000, // 30 second timeout
            }
          );
    
          clearInterval(progressInterval);
          setProgress(100);

          console.log("Listings Data:", response.data);
    
          if (response.status === 200 && response.data) {
            console.log("Response Data:", response.data);
            if (Array.isArray(response.data) && response.data.length > 0) {
              setListings(response.data); 
            } else {
              setError("No listings found in the response.");
            }
          } else {
            setError("Failed to get listings. Please try again.");
          }
        } catch (error) {
          clearInterval(progressInterval);
          if (axios.isAxiosError(error)) {
            console.error("Axios Error generating listings:", error);
            
            // Check for specific backend errors
            if (error.response?.data && typeof error.response.data === 'string' && 
                error.response.data.includes("'list' object has no attribute 'items'")) {
              setError("Backend error: The product data format is invalid. This often happens with certain ASINs. Please try a different ASIN.");
            } else if (error.code === 'ECONNABORTED') {
              setError("Request timed out. The server might be busy or unavailable.");
            } else if (error.response) {
              const errorMessage = typeof error.response.data === 'string' 
                ? error.response.data 
                : JSON.stringify(error.response.data);
              setError(`Server Error (${error.response.status}): ${errorMessage}`);
            } else if (error.request) {
              setError("Network Error: No response received from the server. Please check your internet connection and if the backend is running.");
            } else {
              setError(`Error: ${error.message}`);
            }
          } else {
            console.error("Unexpected error:", error);
            setError(`Unexpected Error: ${error instanceof Error ? error.message : String(error)}`);
          }
        } finally {
          clearInterval(progressInterval);
          setTimeout(() => {
            setIsProcessing(false);
          }, 500);
        }
    };

    const handleReset = () => {
      setAsins('');
      setListings(null);
      setError('');
      setIsProcessing(false);
      setProgress(0);
    };

    const renderTable = () => {
      if (!listings || !Array.isArray(listings) || listings.length === 0) return null;        
  
      const headers = Object.keys(listings[0]);
      
      return (
        <div className="overflow-x-auto mt-4">
          <table className="w-full border-collapse text-sm text-gray-300 table-fixed">
            <thead>
              <tr className="bg-gray-800/60 border-b border-gray-700">
                {headers.map((header) => (
                  <th key={header} 
                    className={`px-4 py-3 text-left font-medium text-yellow-400 ${
                      header.toLowerCase().includes('description') ? 'w-[600px]' : 'w-[250px]'
                    }`}
                    scope="col">{header.replace(/_/g, ' ')}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {listings.map((listing, index) => (
                <tr key={index} className={index % 2 === 0 ? 'bg-gray-800/30' : 'bg-gray-800/10'}>
                  {headers.map((header) => (
                    <td key={header}
                      className={`px-4 py-3 border-t border-gray-700 align-top ${
                        header.toLowerCase().includes('description') 
                          ? 'w-[600px] whitespace-normal' 
                          : 'w-[250px]'
                      }`}
                    >
                      <div 
                        className={`
                          ${header.toLowerCase().includes('description') ? 'max-h-[300px]' : 'max-h-[150px]'}
                          overflow-y-auto pr-4 custom-scrollbar
                        `}
                      >
                        {formatText(listing[header])}
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    };
    

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-gray-900 to-gray-800">
        <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-yellow-400"></div>
      </div>
    )
  }

  return (
    <main className="flex-1">
    <style jsx global>{`
      .custom-scrollbar::-webkit-scrollbar {
        width: 8px;
        height: 8px;
      }
      
      .custom-scrollbar::-webkit-scrollbar-track {
        background: rgba(31, 41, 55, 0.5);
        border-radius: 4px;
      }
      
      .custom-scrollbar::-webkit-scrollbar-thumb {
        background: rgba(250, 204, 21, 0.4);
        border-radius: 4px;
        transition: all 0.2s ease-in-out;
      }
      
      .custom-scrollbar::-webkit-scrollbar-thumb:hover {
        background: rgba(250, 204, 21, 0.6);
      }
      
      .custom-scrollbar {
        scrollbar-width: thin;
        scrollbar-color: rgba(250, 204, 21, 0.4) rgba(31, 41, 55, 0.5);
      }
    `}</style>

    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 p-6 flex flex-col items-center justify-center">
      <Card className="w-full max-w-4xl mt-0 border border-gray-700 shadow-xl bg-gray-900/60 backdrop-blur-sm">
        <CardHeader className="border-b border-gray-700/50 pb-6">
          <CardTitle className="text-3xl font-bold text-center text-yellow-400">
            Amazon AI Listing Generator
          </CardTitle>
          <CardDescription className="text-center text-gray-300 mt-2">
            Generate optimized listing copy to maximize traffic and conversions for your products.
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-8">
          <form onSubmit={(e) => {
            e.preventDefault();
            handleGenerateListings();
          }} className="space-y-8">
            <div className="space-y-4 p-4 bg-gray-800/40 rounded-lg border border-gray-700/50">
              <Label htmlFor="country" className="text-yellow-400 text-lg font-medium">
                Country
              </Label>
              <Select defaultValue={selectedCountry} onValueChange={setSelectedCountry}>
                <SelectTrigger 
                  id="country" 
                  className="w-full md:w-1/3 bg-gray-800 text-white border-gray-700 focus:ring-yellow-400 focus:border-yellow-400"
                >
                  <SelectValue placeholder="Select Country" />
                </SelectTrigger>
                <SelectContent className="bg-gray-800 text-white border-gray-700">
                  {countries.map((country) => (
                    <SelectItem key={country} value={country}>
                      {country}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-4 p-4 bg-gray-800/40 rounded-lg border border-gray-700/50">
              <Label htmlFor="asins" className="text-yellow-400 text-lg font-medium">
                Enter the list of ASINs
              </Label>
              <Textarea
                id="asins"
                value={asins}
                onChange={handleInputChange}
                rows={7}
                className="w-full bg-gray-800 text-white border-gray-700 focus:ring-yellow-400 focus:border-yellow-400"
                placeholder="Enter ASINs separated by comma"
              />
              <p className="text-gray-400 text-sm">Enter one or more Amazon Standard Identification Numbers (ASINs) separated by commas</p>
            </div>
            <div className="flex space-x-4 pt-4">
              <Button
                type="submit"
                disabled={isProcessing || !selectedCountry}
                className="w-3/4 bg-yellow-400 text-black hover:bg-yellow-300 focus:ring-yellow-400 flex items-center justify-center transition-all duration-200 transform hover:translate-y-[-2px] shadow-lg"
              >
                {isProcessing ? (
                  <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-black mr-2"></span>
                ) : (
                  <DocumentTextIcon className="h-5 w-5 mr-2" />
                )}
                {isProcessing ? "Processing..." : "Generate Listings"}
              </Button>
              <Button
                type="button"
                onClick={handleReset}
                disabled={isProcessing}
                className="w-1/4 bg-gray-700 text-white hover:bg-gray-600 transition-all duration-200 border border-gray-600"
              >
                Reset
              </Button>
            </div>
          </form>
          
          {isProcessing && (
            <div className="mt-8 p-4 bg-gray-800/40 rounded-lg border border-gray-700/50 space-y-4">
              <Label className="text-yellow-400 font-medium">Generating your listings...</Label>
              <Progress value={progress} className="w-full h-2 bg-gray-700" />
              <p className="text-gray-400 text-sm">This may take a minute. Please don&apos;t close this page.</p>
            </div>
          )}
          
          {!isProcessing && listings && listings.length > 0 && (
            <div className="mt-8 p-6 bg-green-900/20 rounded-lg border border-green-700/50 space-y-4">
              <h3 className="text-green-400 text-lg font-semibold flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Listing Generation Complete!
              </h3>
              <p className="text-gray-300">Your optimized listings are ready.</p>
              <div className="bg-gray-800/60 rounded-lg border border-gray-700 shadow-inner overflow-hidden">
                <div className="overflow-x-auto custom-scrollbar" style={{ maxWidth: '100%' }}>
                  {renderTable()}
                </div>
              </div>
              <div className="text-gray-400 text-sm flex items-center mt-2">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Tip: Scroll horizontally to view all columns and vertically within cells to see all content
              </div>
            </div>
          )}
          
          {error && (
            <div className="mt-8 p-4 bg-red-900/20 rounded-lg border border-red-700/50">
              <p className="text-red-400 flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                Error: {error}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
      </div>

      {/* Feature Section */}
      <div className="bg-gradient-to-b from-gray-900 to-gray-800 py-24 sm:py-32"> 
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl lg:text-center">
            <h2 className="text-base font-semibold leading-7 text-yellow-400">
              Scale faster
            </h2>
            <p className="mt-2 text-4xl font-extrabold tracking-tight text-white sm:text-5xl"> 
              Unleash Your Sales Potential: Free Version & Advanced Tools Available
            </p>
            <p className="mt-6 text-lg leading-8 text-gray-300"> 
              Tired of lackluster results? Pace Pivot&apos;s free listing generator equips you to skyrocket sales and conversions. Get started instantly - no credit card needed.
            </p>
            <div className="mt-10">
              <a
                href="https://pacepivot.com/contact-us/"
                className="inline-block rounded-md bg-yellow-400 px-6 py-3 text-base font-semibold text-gray-900 shadow-sm hover:bg-yellow-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-yellow-400 transition-all duration-200 transform hover:translate-y-[-2px]"
              >
                Contact Us
              </a>
            </div>
          </div>
          
          {/* Features Grid */}
          <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
            <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
              {features.map((feature) => (
                <div key={feature.name} className="flex flex-col items-start p-6 rounded-lg bg-gray-800/40 border border-gray-700/50 hover:border-yellow-400/30 transition-all duration-300 hover:bg-gray-800/60 transform hover:translate-y-[-5px]"> 
                  <div className="flex items-center justify-center h-12 w-12 rounded-md bg-yellow-400 text-gray-900"> 
                    <feature.icon className="h-6 w-6" aria-hidden="true" />
                  </div>
                  <dt className="mt-4 text-lg font-bold leading-7 text-white"> 
                    {feature.name}
                  </dt>
                  <dd className="mt-2 text-base leading-7 text-gray-300"> 
                    {feature.description}
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
