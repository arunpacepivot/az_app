'use client'

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface PricingCardProps {
  title: string
  price: string
  period: string
  features: string[]
  ctaText: string
  ctaLink: string
  highlighted?: boolean
  className?: string
}

export function PricingCard({
  title,
  price,
  period,
  features,
  ctaText,
  ctaLink,
  highlighted = false,
  className
}: PricingCardProps) {
  return (
    <div
      className={cn(
        "relative flex flex-col p-6 bg-white/5 backdrop-blur-xl rounded-2xl border transition-all duration-300",
        highlighted 
          ? "border-yellow-400/50 shadow-lg shadow-yellow-400/10" 
          : "border-gray-800 hover:border-gray-700",
        "hover:shadow-xl hover:shadow-white/5",
        className
      )}
    >
      {highlighted && (
        <div className="absolute -top-5 left-0 right-0 flex justify-center">
          <span className="bg-yellow-400 text-black px-4 py-1 rounded-full text-sm font-medium">
            Most Popular
          </span>
        </div>
      )}
      
      <div className="mb-5">
        <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
        <div className="flex items-baseline text-white">
          <span className="text-4xl font-bold tracking-tight">{price}</span>
          <span className="ml-1 text-gray-400">{period}</span>
        </div>
      </div>

      <ul className="mb-8 space-y-4 flex-1">
        {features.map((feature, index) => (
          <li key={index} className="flex items-center text-gray-300">
            <svg
              className="w-5 h-5 text-yellow-400 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M5 13l4 4L19 7"
              />
            </svg>
            {feature}
          </li>
        ))}
      </ul>

      <Button
        className={cn(
          "w-full text-sm font-semibold",
          highlighted
            ? "bg-yellow-400 text-black hover:bg-yellow-500"
            : "bg-white/10 text-white hover:bg-white/20"
        )}
        asChild
      >
        <a href={ctaLink}>{ctaText}</a>
      </Button>
    </div>
  )
} 