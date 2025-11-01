// TechnicalChart/components/PriceScaleLabels.tsx
import React, { useMemo } from 'react';
import { Box, Typography } from '@mui/material';
import { CrosshairData, ProcessedChartData } from '../types/chart.types';
import { formatPrice } from '../utils/chartHelpers';

interface PriceScaleLabelsProps {
  data: ProcessedChartData | null;
  crosshairData: CrosshairData | null;
  visible: boolean;
  panelType?: 'main' | 'indicator';
  panelIndicators?: string[]; // Indicator IDs for this panel
  theme?: 'dark' | 'light';
}

/**
 * Formats indicator series ID into a human-readable name for price scale labels
 */
function formatIndicatorNameForLabel(seriesId: string, indicators?: ProcessedChartData['indicators']): string {
  const parts = seriesId.split('_');
  
  // Try to find the indicator definition to get better name
  if (indicators) {
    for (const indicator of indicators) {
      const series = indicator.series.find(s => s.id === seriesId);
      if (series && series.name) {
        // Extract period number if present (e.g., "EMA 12", "SMA 50")
        const periodMatch = series.name.match(/(EMA|SMA|WMA)\s*(\d+)/i);
        if (periodMatch) {
          return `${periodMatch[1].toUpperCase()} ${periodMatch[2]}`;
        }
        return series.name
          .replace(/_/g, ' ')
          .replace(/\bema\b/gi, 'EMA')
          .replace(/\bsma\b/gi, 'SMA')
          .replace(/\bmacd\b/gi, 'MACD')
          .replace(/\brsi\b/gi, 'RSI');
      }
    }
  }
  
  // Fallback: parse the series ID
  const emaMatch = seriesId.match(/ema[_\s]*(\d+)/i);
  if (emaMatch) {
    return `EMA ${emaMatch[1]}`;
  }
  
  const smaMatch = seriesId.match(/sma[_\s]*(\d+)/i);
  if (smaMatch) {
    return `SMA ${smaMatch[1]}`;
  }
  
  if (seriesId.includes('macd')) {
    if (seriesId.includes('signal')) return 'MACD Signal';
    if (seriesId.includes('histogram')) return 'MACD Hist';
    return 'MACD';
  }
  
  if (seriesId.includes('rsi')) {
    return 'RSI';
  }
  
  return parts
    .filter(p => p !== 'close' && p !== 'open' && p !== 'high' && p !== 'low')
    .slice(1)
    .map(p => p.charAt(0).toUpperCase() + p.slice(1).toLowerCase())
    .join(' ') || seriesId;
}

export const PriceScaleLabels: React.FC<PriceScaleLabelsProps> = ({
  data,
  crosshairData,
  visible,
  panelType = 'main',
  panelIndicators = [],
  theme = 'dark',
}) => {
  const colorScheme = useMemo(() => {
    return theme === 'dark' 
      ? { background: 'rgba(19, 23, 34, 0.85)', text: '#D1D4DC', label: '#758696' }
      : { background: 'rgba(255, 255, 255, 0.85)', text: '#131722', label: '#787B86' };
  }, [theme]);

  // Get indicator values (use crosshair data if available, otherwise latest)
  const indicatorValues = useMemo(() => {
    if (crosshairData?.indicators) {
      return crosshairData.indicators;
    }
    
    // Fallback to latest values
    if (!data || !data.indicators) return {};
    
    const values: Record<string, number> = {};
    data.indicators.forEach(indicator => {
      indicator.series.forEach(series => {
        if (series.data && series.data.length > 0) {
          const lastValue = series.data[series.data.length - 1];
          if (lastValue && typeof lastValue === 'object' && 'value' in lastValue) {
            values[series.id] = lastValue.value;
          }
        }
      });
    });
    return values;
  }, [crosshairData, data]);

  // Get current price
  const currentPrice = crosshairData?.close || (data && data.ohlcv.length > 0 ? data.ohlcv[data.ohlcv.length - 1].close : undefined);

  // Get indicators to display based on panel type
  // For main panel: show overlay indicators (EMA, SMA, etc.)
  // For indicator panels: show subplot indicators (RSI, MACD, etc.)
  const displayIndicators = useMemo(() => {
    if (!data || !data.indicators) return [];
    
    if (panelType === 'main') {
      // Show overlay indicators (EMA, SMA, Bollinger Bands, etc.)
      // These are price-scale indicators that overlay on the main price chart
      return data.indicators
        .filter(ind => ind.type === 'overlay')
        .flatMap(ind => ind.series)
        .filter(series => indicatorValues[series.id] !== undefined);
    } else {
      // For indicator panels, show only the indicators assigned to this panel
      return data.indicators
        .filter(ind => panelIndicators.length === 0 || panelIndicators.includes(ind.id))
        .filter(ind => ind.type === 'subplot')
        .flatMap(ind => ind.series)
        .filter(series => indicatorValues[series.id] !== undefined);
    }
  }, [data, indicatorValues, panelType, panelIndicators]);

  if (!visible || (!currentPrice && displayIndicators.length === 0)) {
    return null;
  }

  return (
    <Box
      sx={{
        position: 'absolute',
        top: '50%',
        right: 8,
        transform: 'translateY(-50%)',
        zIndex: 5,
        display: 'flex',
        flexDirection: 'column',
        gap: 0.5,
        pointerEvents: 'none',
      }}
    >
      {/* Price label - only show on main panel */}
      {panelType === 'main' && currentPrice !== undefined && (
        <Box
          sx={{
            backgroundColor: colorScheme.background,
            backdropFilter: 'blur(10px)',
            borderRadius: 0.5,
            padding: '2px 6px',
            border: `1px solid ${theme === 'dark' ? '#2A2E39' : '#E0E3EB'}`,
          }}
        >
          <Typography
            variant="caption"
            sx={{
              color: colorScheme.label,
              fontSize: '0.65rem',
              fontWeight: 500,
              lineHeight: 1.2,
            }}
          >
            Price
          </Typography>
          <Typography
            variant="caption"
            sx={{
              color: colorScheme.text,
              fontSize: '0.7rem',
              fontWeight: 600,
              display: 'block',
              lineHeight: 1.2,
            }}
          >
            {formatPrice(currentPrice)}
          </Typography>
        </Box>
      )}

      {/* Overlay indicators (EMA, SMA, etc.) - shown on main panel */}
      {displayIndicators.map((series) => {
        const value = indicatorValues[series.id];
        if (value === undefined) return null;

        const label = formatIndicatorNameForLabel(series.id, data?.indicators);
        
        return (
          <Box
            key={series.id}
            sx={{
              backgroundColor: colorScheme.background,
              backdropFilter: 'blur(10px)',
              borderRadius: 0.5,
              padding: '2px 6px',
              border: `1px solid ${theme === 'dark' ? '#2A2E39' : '#E0E3EB'}`,
            }}
          >
            <Typography
              variant="caption"
              sx={{
                color: colorScheme.label,
                fontSize: '0.65rem',
                fontWeight: 500,
                lineHeight: 1.2,
              }}
            >
              {label}
            </Typography>
            <Typography
              variant="caption"
              sx={{
                color: series.color || colorScheme.text,
                fontSize: '0.7rem',
                fontWeight: 600,
                display: 'block',
                lineHeight: 1.2,
              }}
            >
              {formatPrice(value, value > 1000 ? 2 : 4)}
            </Typography>
          </Box>
        );
      })}
    </Box>
  );
};

export default PriceScaleLabels;

