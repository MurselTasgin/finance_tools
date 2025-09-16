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

export interface DownloadProgress {
  isDownloading: boolean;
  progress: number;
  status: string;
  records_downloaded: number;
  total_records: number;
  start_time: string | null;
  estimated_completion: string | null;
  current_phase: string;
}
