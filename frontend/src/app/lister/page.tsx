'use client'

import { useState } from 'react'
import { useAuth } from '@/lib/context/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import axios, { AxiosError } from "axios";

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Progress } from "@/components/ui/progress"
import { json } from "stream/consumers"

type Listing = Record<string, string>;

export default function ListingGeneratorForm() {
    const { user, loading } = useAuth()
    const router = useRouter()
    const [connectivityResult, setConnectivityResult] = useState<string | null>(null)
    const [connectivityError, setConnectivityError] = useState<string | null>(null)
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

   // const baseUrl = process.env.NODE_ENV === "development"
    //    ? //process.env.NEXT_PUBLIC_BASE_URL_LOCAL
  //     : //process.env.NEXT_PUBLIC_BASE_URL_PROD;
  
 const baseUrl = "https://django-backend-epcse2awb3cyh5e8.centralindia-01.azurewebsites.net";
   


  useEffect(() => {
    async function fetchCsrfToken() {
      console.log("Fetching CSRF token from"+baseUrl+"scraper/get_csrf/");
        try {
          const response = await axios.get(baseUrl + "scraper/get_csrf/", {
            withCredentials: true,
          });
          console.log("CSRF Response:", response);
          const data = response.data;
          if (!data.csrfToken) {
            console.error("No CSRF token found in the response.");
            return;
          }
          setCsrfToken(data.csrfToken);
        } catch (error) {
          console.error("Error fetching CSRF :", error);
        }
      }
      fetchCsrfToken();
    }, []);

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
      
        setError("");
        setIsProcessing(true);
        setProgress(0);
      
          const progressInterval = setInterval(() => {
            setProgress((prevProgress) => (prevProgress < 90 ? prevProgress + 10 : prevProgress));
          }, 500);
      
        const payload = { asins, geography: selectedCountry };
    
        try {
        const response = await axios.post(
            baseUrl + "api/v1/lister/",
            payload,
            {
            headers: {
                "X-CSRFToken": csrfToken,
            },
            withCredentials: true,
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
        if (error instanceof AxiosError) {
            console.error("Axios Error generating listings:", error);
            if (error.response) {
            setError(`Server Error: ${error.response.status} - ${error.response.data}`);
            } else if (error.request) {
            setError("Network Error: No response received from the server.");
            }
        } else {
            console.error("Unexpected error:", error);
            setError(`Unexpected Error: ${error instanceof Error ? error.message : String(error)}`);
        }
        }finally {
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
          <table className="listings-table">
            <thead>
              <tr>
                {headers.map((header) => (
                  <th key={header}>{header}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {listings.map((listing, index) => (
                <tr key={index}>
                  {headers.map((header) => (
                    <td key={header}>{listing[header]}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        );
      };
    

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
    </div>
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 p-6 flex items-center justify-center">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle className="text-3xl font-bold text-center text-yellow-400">
            Amazon India AI Listing Generator
          </CardTitle>
          <CardDescription className="text-center text-gray-300">
            Generate optimized listing copy to maximize traffic and conversions for your products.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={(e) => {
            e.preventDefault();
            handleGenerateListings();
          }} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="country" className="text-yellow-400">
                Country
              </Label>
              <Select defaultValue={selectedCountry} onValueChange={setSelectedCountry}>
                <SelectTrigger 
                  id="country" 
                  className="bg-gray-800 text-white border-gray-700"
                  style={{ width: `${Math.max(...countries.map(country => country.length))}ch` }}
                >
                  <SelectValue placeholder="Country" />
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
            <div className="space-y-2">
              <Label htmlFor="asins" className="text-yellow-400">
                Enter the list of ASINs
              </Label>
              <Textarea
                id="asins"
                value={asins}
                onChange={handleInputChange}
                rows={5}
                className="w-full bg-gray-800 text-white border-gray-700 focus:ring-yellow-400"
                placeholder="Enter ASINs separated by comma"
              />
            </div>
            <Button
            type="submit"
            disabled={isProcessing}
            className="w-full bg-yellow-400 text-black hover:bg-yellow-300 focus:ring-yellow-400 flex items-center justify-center"
            >
            {isProcessing ? (
                <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-black mr-2"></span>
            ) : null}
            {isProcessing ? "Processing..." : "Generate Listings"}
            </Button>
          </form>
          {/* {isProcessing && <Progress value={progress} />} */}
          {isProcessing && (
            <div className="mt-6 space-y-2">
              <Label className="text-yellow-400">Generating listings...</Label>
              <Progress value={progress} className="w-full" />
              {renderTable()}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
} 
