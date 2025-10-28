// TechnicalChart/hooks/useChartData.ts
import { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import { analyticsApi } from '../../../services/api';
import { ChartDataResponse, ProcessedChartData, AssetType, TimeInterval } from '../types/chart.types';
import { processChartData } from '../utils/chartHelpers';

interface UseChartDataParams {
  assetType: AssetType;
  identifier: string;
  startDate?: string;
  endDate?: string;
  interval: TimeInterval;
  indicators: string[];
  indicatorParameters: Record<string, Record<string, any>>;
  enabled?: boolean;
}

interface UseChartDataReturn {
  data: ProcessedChartData | null;
  rawData: ChartDataResponse | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

/**
 * Hook for managing chart data fetching and processing
 */
export function useChartData({
  assetType,
  identifier,
  startDate,
  endDate,
  interval,
  indicators,
  indicatorParameters,
  enabled = true,
}: UseChartDataParams): UseChartDataReturn {
  const [processedData, setProcessedData] = useState<ProcessedChartData | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Create a stable query key
  const queryKey = [
    'technicalChart',
    assetType,
    identifier,
    startDate,
    endDate,
    interval,
    JSON.stringify(indicators),
    JSON.stringify(indicatorParameters),
  ];

  // Fetch data using React Query
  const {
    data: rawData,
    isLoading,
    error: queryError,
    refetch,
  } = useQuery<ChartDataResponse>(
    queryKey,
    async () => {
      if (!identifier) {
        throw new Error('Symbol/identifier is required');
      }

      // Build indicators payload
      const indicatorPayload: Record<string, any> = {};
      indicators.forEach((indicatorId) => {
        indicatorPayload[indicatorId] = indicatorParameters[indicatorId] || {};
      });

      const response = await analyticsApi.getTechnicalChart({
        asset_type: assetType,
        identifier: identifier.trim(),
        start_date: startDate,
        end_date: endDate,
        interval,
        indicators: indicatorPayload,
      });

      return response;
    },
    {
      enabled: enabled && !!identifier,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
      retry: 1,
      onError: (err: any) => {
        const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to load chart data';
        setError(errorMessage);
      },
    }
  );

  // Process raw data when it changes
  useEffect(() => {
    if (rawData) {
      try {
        const processed = processChartData(rawData);
        setProcessedData(processed);
        setError(null);
      } catch (err: any) {
        setError(`Failed to process chart data: ${err.message}`);
        setProcessedData(null);
      }
    } else {
      setProcessedData(null);
    }
  }, [rawData]);

  // Handle query error
  useEffect(() => {
    if (queryError) {
      const errorMessage = (queryError as any)?.response?.data?.detail || (queryError as Error).message || 'Unknown error';
      setError(errorMessage);
    }
  }, [queryError]);

  return {
    data: processedData,
    rawData: rawData || null,
    isLoading,
    error,
    refetch,
  };
}
