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
  useUnifiedAcos: boolean;
  target_acos?: number; // Used when useUnifiedAcos is true
  sp_target_acos?: number;
  sb_target_acos?: number;
  sd_target_acos?: number;
}

export interface ProcessedFile {
  id: string;
  originalName: string;
  processedUrl: string;
  createdAt: string;
}

// N-gram Analysis types
export interface NgramPayload {
  file: File;
  target_acos: number;
}

export interface NgramFile {
  filename: string;
  url: string;
  file_id: string;
  type: string;
}

export interface NgramResponse {
  data: {
    status: string;
    message: string;
    sk_asin_count: number;
    mk_asin_count: number;
    data: Record<string, any[]>;
    files: NgramFile[];
  };
  status: number;
}

// SQP Analysis types
export interface SqpPayload {
  file: File;
}

export interface SqpFile {
  filename: string;
  url?: string;
  file_id: string;
}

export interface SqpResponse {
  data: {
    data: {
      'Good CTR & CVR': any[];
      'CTR Improve': any[];
      'CVR Improve': any[];
      'Declining Trend': any[];
    };
    keywords?: string[];
    file: SqpFile;
  };
  status: number;
}

// Topical Analysis types
export interface TopicalPayload {
  file: File;
  min_search_volume: number;
}

export interface TopicalFile {
  filename: string;
  url: string;
  file_id: string;
}

export interface TopicalResponse {
  data: {
    status: string;
    message: string;
    b0_asin_count: number;
    non_b0_asin_count: number;
    data: Record<string, any[]>;
    file: TopicalFile;
  };
  status: number;
}

// Cerebro Analysis types
export interface CerebroPayload {
  file: File;
  min_search_volume: number;
}

export interface CerebroFile {
  filename: string;
  url: string;
  file_id: string;
}

export interface CerebroResponse {
  data: {
    status: string;
    message: string;
    keyword_count: number;
    search_volume_avg: number;
    data: Record<string, any[]>;
    file: CerebroFile;
    keywords?: any[];
  };
  status: number;
}

// Error types
export interface ApiError {
  message: string;
  code?: string;
  details?: unknown;
}

// Common file interface used across multiple response types
export interface FileInfo {
  filename: string;
  url?: string;
  file_id: string;
  content_type?: string;
}

export interface SpAdsResponse {
  data: {
    [sheetName: string]: SheetRow[];
  };
  excel_file?: {
    filename: string;
    content: string;
    content_type: string;
    file_id?: string;
  };
  file?: FileInfo;
  file_id?: string;
} 