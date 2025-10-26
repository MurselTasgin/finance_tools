// finance_tools/frontend/src/services/api.ts
import axios from 'axios';
import {
  DatabaseStats,
  FundRecord,
  PaginatedResponse,
  FilterOptions,
  SortOptions,
  DownloadProgress,
  Fund,
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8070';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

export const databaseApi = {
  getStats: async (): Promise<DatabaseStats> => {
    const response = await api.get('/api/database/stats');
    return response.data;
  },

  downloadData: async (startDate: string, endDate: string, kind: string = 'BYF', funds: string[] = []): Promise<{ message: string }> => {
    const response = await api.post('/api/database/download', {
      startDate,
      endDate,
      kind,
      funds,
    });
    return response.data;
  },

  getDownloadProgress: async (): Promise<DownloadProgress> => {
    const response = await api.get('/api/database/download-progress');
    return response.data;
  },

  getActiveTasks: async (): Promise<{ active_tasks: number; tasks: any[] }> => {
    const response = await api.get('/api/database/tasks');
    return response.data;
  },

  getDownloadHistory: async (params: {
    page?: number;
    pageSize?: number;
    search?: string;
    status?: string;
  } = {}): Promise<{
    downloads: any[];
    total: number;
    page: number;
    pageSize: number;
  }> => {
    const response = await api.get('/api/database/download-history', { params });
    return response.data;
  },

  getDownloadStatistics: async (): Promise<{
    total_downloads: number;
    successful_downloads: number;
    failed_downloads: number;
    total_records_downloaded: number;
    date_range: {
      start: string | null;
      end: string | null;
    };
  }> => {
    const response = await api.get('/api/database/download-statistics');
    return response.data;
  },

  getDataDistribution: async (groupBy: string = 'monthly'): Promise<{
    distribution: Array<{ period: string; count: number }>;
  }> => {
    const response = await api.get('/api/database/data-distribution', {
      params: { groupBy }
    });
    return response.data;
  },

  getFundTypeDistribution: async (): Promise<{
    distribution: Array<{ name: string; value: number }>;
  }> => {
    const response = await api.get('/api/database/fund-type-distribution');
    return response.data;
  },

  cancelTask: async (taskId: string): Promise<{ message: string; task_id: string }> => {
    const response = await api.post(`/api/database/cancel-task/${taskId}`);
    return response.data;
  },

  getDownloadTaskDetails: async (taskId: string): Promise<{
    task_info: {
      id: number;
      task_id: string;
      start_date: string;
      end_date: string;
      kind: string;
      funds: string[];
      status: string;
      start_time: string;
      end_time: string | null;
      records_downloaded: number;
      total_records: number;
      error_message: string | null;
      created_at: string;
    };
    progress_logs: Array<{
      id: number;
      task_id: string;
      timestamp: string;
      message: string;
      message_type: string;
      progress_percent: number;
      chunk_number: number;
      records_count: number | null;
      fund_name: string | null;
      created_at: string;
    }>;
    statistics: {
      total_messages: number;
      success_messages: number;
      error_messages: number;
      warning_messages: number;
      total_records_from_logs: number;
      duration_seconds: number;
    };
  }> => {
    const response = await api.get(`/api/database/download-task-details/${taskId}`);
    return response.data;
  },
};

export const dataApi = {
  getRecords: async (
    page: number = 1,
    pageSize: number = 50,
    filters: FilterOptions[] = [],
    sort: SortOptions | null = null,
    searchTerm: string = ''
  ): Promise<PaginatedResponse<FundRecord>> => {
    const params = new URLSearchParams({
      page: page.toString(),
      pageSize: pageSize.toString(),
      search: searchTerm,
    });

    if (sort) {
      params.append('sortBy', sort.column);
      params.append('sortDir', sort.direction);
    }

    filters.forEach((filter, index) => {
      params.append(`filters[${index}][column]`, filter.column);
      params.append(`filters[${index}][operator]`, filter.operator);
      params.append(`filters[${index}][value]`, filter.value.toString());
      if (filter.value2 !== undefined) {
        params.append(`filters[${index}][value2]`, filter.value2.toString());
      }
    });

    const response = await api.get(`/api/data/records?${params.toString()}`);
    return response.data;
  },

  getColumns: async (): Promise<string[]> => {
    const response = await api.get('/api/data/columns');
    return response.data;
  },

  getFunds: async (): Promise<Fund[]> => {
    const response = await api.get('/api/data/funds');
    return response.data;
  },

  getPlotData: async (
    xColumn: string,
    yColumn: string,
    fundCode?: string,
    startDate?: string,
    endDate?: string,
    filters: FilterOptions[] = []
  ): Promise<{ x: string | number; y: number; label?: string }[]> => {
    const params = new URLSearchParams({
      xColumn,
      yColumn,
    });

    if (fundCode) {
      params.append('fundCode', fundCode);
    }

    if (startDate) {
      params.append('startDate', startDate);
    }

    if (endDate) {
      params.append('endDate', endDate);
    }

    filters.forEach((filter, index) => {
      params.append(`filters[${index}][column]`, filter.column);
      params.append(`filters[${index}][operator]`, filter.operator);
      params.append(`filters[${index}][value]`, filter.value.toString());
      if (filter.value2 !== undefined) {
        params.append(`filters[${index}][value2]`, filter.value2.toString());
      }
    });

    const response = await api.get(`/api/data/plot?${params.toString()}`);
    return response.data;
  },
};

// Stock API
export const stockApi = {
  downloadData: async (symbols: string[], startDate: string, endDate: string, interval: string = '1d'): Promise<{ message: string; task_id: string }> => {
    const response = await api.post('/api/stocks/download', {
      symbols,
      startDate,
      endDate,
      interval,
    });
    return response.data;
  },

  getDownloadProgress: async (): Promise<DownloadProgress> => {
    const response = await api.get('/api/stocks/download-progress');
    return response.data;
  },

  getStats: async (): Promise<any> => {
    const response = await api.get('/api/stocks/stats');
    return response.data;
  },

  // Stock Groups
  getGroups: async (): Promise<any> => {
    const response = await api.get('/api/stocks/groups');
    return response.data;
  },

  createGroup: async (name: string, description: string, symbols: string[]): Promise<any> => {
    const response = await api.post('/api/stocks/groups', {
      name,
      description,
      symbols,
    });
    return response.data;
  },

  updateGroup: async (groupId: number, name?: string, description?: string, symbols?: string[]): Promise<any> => {
    const response = await api.put(`/api/stocks/groups/${groupId}`, {
      name,
      description,
      symbols,
    });
    return response.data;
  },

  deleteGroup: async (groupId: number): Promise<any> => {
    const response = await api.delete(`/api/stocks/groups/${groupId}`);
    return response.data;
  },

  getHistory: async (params: {
    page?: number;
    pageSize?: number;
    search?: string;
    status?: string;
  }): Promise<{ downloads: any[]; total: number; page: number; pageSize: number }> => {
    const response = await api.get('/api/stocks/history', { params });
    return response.data;
  },

  getData: async (symbol: string, startDate?: string, endDate?: string, interval: string = '1d'): Promise<any> => {
    const response = await api.get('/api/stocks/data', {
      params: { symbol, start_date: startDate, end_date: endDate, interval },
    });
    return response.data;
  },

  getInfo: async (symbol: string): Promise<any> => {
    const response = await api.get(`/api/stocks/info/${symbol}`);
    return response.data;
  },

  // Data explorer endpoints
  getRecords: async (
    page: number = 1,
    pageSize: number = 50,
    filters: FilterOptions[] = [],
    sort: SortOptions | null = null,
    searchTerm: string = ''
  ): Promise<PaginatedResponse<any>> => {
    const params = new URLSearchParams({
      page: page.toString(),
      pageSize: pageSize.toString(),
      search: searchTerm,
    });

    if (sort) {
      params.append('sortBy', sort.column);
      params.append('sortDir', sort.direction);
    }

    filters.forEach((filter, index) => {
      params.append(`filters[${index}][column]`, filter.column);
      params.append(`filters[${index}][operator]`, filter.operator);
      params.append(`filters[${index}][value]`, filter.value.toString());
      if (filter.value2 !== undefined) {
        params.append(`filters[${index}][value2]`, filter.value2.toString());
      }
    });

    const response = await api.get(`/api/stocks/records?${params.toString()}`);
    return response.data;
  },

  getColumns: async (): Promise<string[]> => {
    const response = await api.get('/api/stocks/columns');
    return response.data;
  },

  getSymbols: async (): Promise<{ symbols: Array<{ symbol: string }> }> => {
    const response = await api.get('/api/stocks/symbols');
    return response.data;
  },
};

// Analytics API
export const analyticsApi = {
  // Task Management - Start Analysis in Background
  startAnalysis: async (analysis_type: string, analysis_name: string, parameters: any): Promise<{ task_id: string; message: string }> => {
    const response = await api.post('/api/analytics/run', {
      analysis_type,
      analysis_name,
      parameters,
    });
    return response.data;
  },

  // Task Management - Get Current Progress
  getAnalysisProgress: async (): Promise<any> => {
    const response = await api.get('/api/analytics/progress');
    return response.data;
  },

  // Task Management - Get Active Tasks
  getActiveTasks: async (): Promise<{ active_tasks: number; tasks: any[] }> => {
    const response = await api.get('/api/analytics/tasks');
    return response.data;
  },

  // Task Management - Get Task History
  getAnalysisHistory: async (params: {
    analysis_type?: string;
    status?: string;
    limit?: number;
    page?: number;
  } = {}): Promise<{ tasks: any[]; total: number; page: number; limit: number; pages: number }> => {
    const response = await api.get('/api/analytics/history', { params });
    return response.data;
  },

  // Task Management - Cancel Running Task
  cancelAnalysis: async (task_id: string): Promise<{ message: string; task_id: string }> => {
    const response = await api.post(`/api/analytics/cancel/${ task_id}`);
    return response.data;
  },

  // Task Management - Get Task Details with Logs
  getAnalysisTaskDetails: async (task_id: string): Promise<any> => {
    const response = await api.get(`/api/analytics/task-details/${ task_id}`);
    return response.data;
  },

  // ETF Analytics
  runETFTechnicalAnalysis: async (parameters: any): Promise<any> => {
    const response = await api.post('/api/analytics/etf/technical', parameters);
    return response.data;
  },

  runETFScanAnalysis: async (parameters: any): Promise<any> => {
    const response = await api.post('/api/analytics/etf/scan', parameters);
    return response.data;
  },

  // Stock Analytics
  runStockTechnicalAnalysis: async (parameters: any): Promise<any> => {
    const response = await api.post('/api/analytics/stock/technical', parameters);
    return response.data;
  },

  // Analytics capabilities and metadata
  getCapabilities: async (): Promise<any> => {
    const response = await api.get('/api/analytics/capabilities');
    return response.data;
  },

  getHistory: async (params: {
    user_id?: string;
    analysis_type?: string;
    limit?: number;
  } = {}): Promise<{ history: any[] }> => {
    const response = await api.get('/api/analytics/history', { params });
    return response.data;
  },

  getCachedResults: async (params: {
    analysis_type?: string;
    status?: string;
    search?: string;
    page?: number;
    limit?: number;
  } = {}): Promise<{
    results: any[];
    total: number;
    page: number;
    limit: number;
    pages: number;
  }> => {
    const response = await api.get('/api/analytics/cache', { params });
    return response.data;
  },

  // Export functionality
  exportResults: async (resultId: string, format: string = 'csv'): Promise<Blob> => {
    const response = await api.get(`/api/analytics/results/${resultId}/export`, {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  },
};

export default api;
