// finance_tools/frontend/src/types/index.ts
export interface DatabaseStats {
  totalRecords: number;
  lastDownloadDate: string | null;
  fundCount: number;
  dateRange: {
    start: string | null;
    end: string | null;
  };
}

export interface FundRecord {
  id: number;
  code: string;
  title: string;
  date: string;
  price: number | null;
  market_cap: number | null;
  number_of_investors: number | null;
  number_of_shares: number | null;
  created_at: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface FilterOptions {
  column: string;
  operator: 'equals' | 'contains' | 'greater_than' | 'less_than' | 'between';
  value: string | number;
  value2?: string | number;
}

export interface SortOptions {
  column: string;
  direction: 'asc' | 'desc';
}

export interface DataExplorerState {
  page: number;
  pageSize: number;
  filters: FilterOptions[];
  sort: SortOptions | null;
  searchTerm: string;
}

export interface PlotData {
  x: string | number;
  y: number;
  label?: string;
}

export interface Fund {
  code: string;
  title: string;
}

export interface DownloadProgress {
  is_downloading: boolean;
  progress: number;
  status: string;
  records_downloaded: number;
  total_records: number;
  start_time: string | null;
  estimated_completion: string | null;
  current_phase: string;
  task_id?: string | null;
  error?: string | null;
  last_activity?: string | null;
  progress_history?: Array<{
    timestamp: string;
    progress: number;
    records_downloaded: number;
  }>;
  records_per_minute?: number;
  estimated_remaining_minutes?: number;
  // Stock-specific progress fields
  symbols_completed?: number;
  symbols_total?: number;
  // New detailed progress fields
  detailed_messages?: Array<{
    timestamp: string;
    message: string;
    progress: number;
    chunk: number;
    type: 'info' | 'success' | 'warning' | 'error';
  }>;
  current_chunk_info?: {
    start_date: string;
    end_date: string;
    chunk_number: number;
    total_chunks: number;
  };
  fund_progress?: {
    [fundName: string]: {
      status: 'success' | 'no_data' | 'error';
      rows: number;
      timestamp: string;
      error?: string;
    };
  };
}
