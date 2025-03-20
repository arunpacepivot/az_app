// Common API types
export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

// Listing types
export interface Listing {
  [key: string]: string;
}

export interface ListingPayload {
  asins: string;
  geography: string;
}

// SP Ads types
export interface SpAdsPayload {
  file: File;
  target_acos: number;
}

export interface ProcessedFile {
  id: string;
  originalName: string;
  processedUrl: string;
  createdAt: string;
}

// Error types
export interface ApiError {
  message: string;
  code?: string;
  details?: unknown;
} 