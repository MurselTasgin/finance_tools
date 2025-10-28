// TechnicalChart/TechnicalChartContainer.tsx
import React, { useState, useCallback } from 'react';
import { Box, CircularProgress, Alert, Paper } from '@mui/material';
import { ChartCanvas } from './components/ChartCanvas';
import { ChartLegend } from './components/ChartLegend';
import { useChartData } from './hooks/useChartData';
import {
  TechnicalChartContainerProps,
  CrosshairData,
  ChartOptions,
} from './types/chart.types';
import { getDefaultChartOptions } from './utils/chartHelpers';

/**
 * Main Technical Chart Container
 *
 * This component integrates the Lightweight Charts library with our backend data
 * and provides a TradingView-like charting experience.
 */
export const TechnicalChartContainer: React.FC<TechnicalChartContainerProps> = ({
  assetType,
  identifier,
  startDate,
  endDate,
  interval,
  indicators,
  indicatorParameters,
  onDataLoad,
  onError,
  height = 600,
  theme = 'dark',
}) => {
  const [crosshairData, setCrosshairData] = useState<CrosshairData | null>(null);
  const [chartOptions, setChartOptions] = useState<ChartOptions>({
    ...getDefaultChartOptions(),
    theme,
    height,
  });

  // Fetch and process chart data
  const {
    data: processedData,
    rawData,
    isLoading,
    error,
  } = useChartData({
    assetType,
    identifier,
    startDate,
    endDate,
    interval,
    indicators,
    indicatorParameters,
    enabled: !!identifier,
  });

  // Handle data load callback
  React.useEffect(() => {
    if (rawData && onDataLoad) {
      onDataLoad(rawData);
    }
  }, [rawData, onDataLoad]);

  // Handle error callback
  React.useEffect(() => {
    if (error && onError) {
      onError(error);
    }
  }, [error, onError]);

  // Handle crosshair move
  const handleCrosshairMove = useCallback((data: CrosshairData | null) => {
    setCrosshairData(data);
  }, []);

  // Handle theme change
  React.useEffect(() => {
    setChartOptions((prev) => ({ ...prev, theme }));
  }, [theme]);

  // Handle height change
  React.useEffect(() => {
    setChartOptions((prev) => ({ ...prev, height }));
  }, [height]);

  // Render loading state
  if (isLoading) {
    return (
      <Paper
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: chartOptions.height,
          backgroundColor: theme === 'dark' ? '#131722' : '#FFFFFF',
        }}
      >
        <CircularProgress />
      </Paper>
    );
  }

  // Render error state
  if (error) {
    return (
      <Paper
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: chartOptions.height,
          backgroundColor: theme === 'dark' ? '#131722' : '#FFFFFF',
          padding: 3,
        }}
      >
        <Alert severity="error" sx={{ maxWidth: 600 }}>
          {error}
        </Alert>
      </Paper>
    );
  }

  // Render empty state
  if (!processedData || processedData.ohlcv.length === 0) {
    return (
      <Paper
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: chartOptions.height,
          backgroundColor: theme === 'dark' ? '#131722' : '#FFFFFF',
          padding: 3,
        }}
      >
        <Alert severity="info">
          No chart data available. Please check your symbol and date range.
        </Alert>
      </Paper>
    );
  }

  // Render chart
  return (
    <Box
      sx={{
        position: 'relative',
        width: '100%',
        height: chartOptions.height,
        backgroundColor: theme === 'dark' ? '#131722' : '#FFFFFF',
      }}
    >
      {/* Legend overlay */}
      <ChartLegend
        identifier={identifier}
        data={processedData}
        crosshairData={crosshairData}
        showIndicators={true}
      />

      {/* Main chart canvas */}
      <ChartCanvas
        data={processedData}
        options={chartOptions}
        onCrosshairMove={handleCrosshairMove}
      />
    </Box>
  );
};

export default TechnicalChartContainer;
