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

  // Create a stable query key - sort indicators to ensure consistent key
  const sortedIndicators = [...indicators].sort();
  const sortedParameters = Object.keys(indicatorParameters)
    .sort()
    .reduce((acc, key) => {
      acc[key] = indicatorParameters[key];
      return acc;
    }, {} as Record<string, Record<string, any>>);

  const queryKey = [
    'technicalChart',
    assetType,
    identifier,
    startDate,
    endDate,
    interval,
    JSON.stringify(sortedIndicators),
    JSON.stringify(sortedParameters),
  ];
  
  // Debug logging
  if (sortedIndicators.includes('number_of_shares') || sortedIndicators.includes('number_of_investors')) {
    console.log('🔍 useChartData query key:', {
      indicators: sortedIndicators,
      parameters: sortedParameters,
      queryKey
    });
  }

  // Fetch data using React Query
  const {
    data: rawData,
    isLoading,
    error: queryError,
    refetch,
  } = useQuery<ChartDataResponse>(
    queryKey,
    async () => {
      // Log when query function is called
      if (sortedIndicators.includes('number_of_shares') || sortedIndicators.includes('number_of_investors')) {
        console.log('🚀 Fetching chart data with indicators:', sortedIndicators);
      }
      if (!identifier) {
        throw new Error('Symbol/identifier is required');
      }

      // Build indicators payload - use sorted indicators for consistency
      const indicatorPayload: Record<string, any> = {};
      sortedIndicators.forEach((indicatorId) => {
        indicatorPayload[indicatorId] = sortedParameters[indicatorId] || {};
      });

      const response = await analyticsApi.getTechnicalChart({
        asset_type: assetType,
        identifier: identifier.trim(),
        start_date: startDate,
        end_date: endDate,
        interval,
        indicators: indicatorPayload,
      });

      // Debug logging for ETF indicators
      if (sortedIndicators.includes('number_of_shares') || sortedIndicators.includes('number_of_investors')) {
        console.log('📊 API response received:', {
          indicatorDefinitions: response.indicator_definitions?.map((ind: any) => ({
            id: ind.id,
            name: ind.name,
            columns: ind.columns
          })),
          columns: response.columns,
          timeseriesLength: response.timeseries?.length
        });
      }

      return response;
    },
    {
      enabled: enabled && !!identifier && identifier.trim().length > 0,
      staleTime: 0, // Always refetch when query key changes (for indicator changes)
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
      retry: 1,
      onError: (err: any) => {
        const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to load chart data';
        setError(errorMessage);
        // Don't throw - just set error state
      },
    }
  );

  // Process raw data when it changes
  useEffect(() => {
    if (rawData) {
      try {
        const processed = processChartData(rawData);
        
        // Debug logging for ETF indicators
        if (sortedIndicators.includes('number_of_shares') || sortedIndicators.includes('number_of_investors')) {
          console.log('✅ Processed chart data:', {
            ohlcvLength: processed.ohlcv.length,
            indicators: processed.indicators.map(ind => ({
              id: ind.id,
              name: ind.name,
              type: ind.type,
              seriesCount: ind.series.length,
              series: ind.series.map(s => ({ id: s.id, name: s.name, dataLength: s.data.length }))
            }))
          });
        }
        
        setProcessedData(processed);
        setError(null);
      } catch (err: any) {
        console.error('❌ Error processing chart data:', err);
        setError(`Failed to process chart data: ${err.message}`);
        setProcessedData(null);
      }
    } else {
      setProcessedData(null);
    }
  }, [rawData, sortedIndicators]);

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
