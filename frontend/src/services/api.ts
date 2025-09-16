// finance_tools/frontend/src/services/api.ts
import axios from 'axios';
import {
  DatabaseStats,
  FundRecord,
  PaginatedResponse,
  FilterOptions,
  SortOptions,
  DownloadProgress,
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

  getPlotData: async (
    xColumn: string,
    yColumn: string,
    filters: FilterOptions[] = []
  ): Promise<{ x: string | number; y: number; label?: string }[]> => {
    const params = new URLSearchParams({
      xColumn,
      yColumn,
    });

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

export default api;
