// Common API types
export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

export interface SheetRow {
  [key: string]: string | number | boolean | null;
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

export interface SpAdsResponse {
  data: {
    [sheetName: string]: SheetRow[];
  };
  excel_file: {
    filename: string;
    content: string;
    content_type: string;
  };
} 