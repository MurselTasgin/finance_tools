// TechnicalChart/components/ChartLegend.tsx
import React, { useMemo } from 'react';
import { Box, Typography, Chip, Stack } from '@mui/material';
import { CrosshairData, ProcessedChartData } from '../types/chart.types';
import { formatPrice, formatVolume, formatPercent } from '../utils/chartHelpers';

interface ChartLegendProps {
  identifier: string;
  data: ProcessedChartData | null;
  crosshairData: CrosshairData | null;
  showIndicators?: boolean;
  onIdentifierClick?: () => void;
}

/**
 * Formats an indicator series ID into a human-readable name
 * Examples:
 * - "ema_cross_close_ema_12" -> "EMA 12"
 * - "ema_cross_close_ema_26" -> "EMA 26"
 * - "ema_regime_close_ema_8" -> "EMA 8"
 * - "macd_macd_line" -> "MACD"
 * - "rsi_rsi" -> "RSI"
 */
export function formatIndicatorName(seriesId: string, indicators?: ProcessedChartData['indicators']): string {
  const parts = seriesId.split('_');
  
  // Try to find the indicator definition to get better name
  if (indicators) {
    for (const indicator of indicators) {
      const series = indicator.series.find(s => s.id === seriesId);
      if (series) {
        // Use the series name if available, or format it nicely
        if (series.name) {
          // Extract period number if present (e.g., "EMA 12", "SMA 50")
          const periodMatch = series.name.match(/(EMA|SMA|WMA)\s*(\d+)/i);
          if (periodMatch) {
            return `${periodMatch[1].toUpperCase()} ${periodMatch[2]}`;
          }
          // Try to clean up common patterns
          return series.name
            .replace(/_/g, ' ')
            .replace(/\bema\b/gi, 'EMA')
            .replace(/\bsma\b/gi, 'SMA')
            .replace(/\bwma\b/gi, 'WMA')
            .replace(/\bmacd\b/gi, 'MACD')
            .replace(/\brsi\b/gi, 'RSI');
        }
      }
    }
  }
  
  // Fallback: parse the series ID
  // Look for EMA/SMA patterns with numbers
  const emaMatch = seriesId.match(/ema[_\s]*(\d+)/i);
  if (emaMatch) {
    return `EMA ${emaMatch[1]}`;
  }
  
  const smaMatch = seriesId.match(/sma[_\s]*(\d+)/i);
  if (smaMatch) {
    return `SMA ${smaMatch[1]}`;
  }
  
  // Look for common indicator names
  if (seriesId.includes('macd')) {
    if (seriesId.includes('signal')) return 'MACD Signal';
    if (seriesId.includes('histogram')) return 'MACD Histogram';
    return 'MACD';
  }
  
  if (seriesId.includes('rsi')) {
    return 'RSI';
  }
  
  if (seriesId.includes('bb_upper') || seriesId.includes('bollinger_upper')) {
    return 'BB Upper';
  }
  
  if (seriesId.includes('bb_lower') || seriesId.includes('bollinger_lower')) {
    return 'BB Lower';
  }
  
  if (seriesId.includes('bb_middle') || seriesId.includes('bollinger_middle')) {
    return 'BB Middle';
  }
  
  // Default: clean up the ID
  return parts
    .filter(p => p !== 'close' && p !== 'open' && p !== 'high' && p !== 'low')
    .slice(1) // Remove indicator ID prefix
    .map(p => {
      // Capitalize first letter
      if (p.match(/^\d+$/)) return p; // Keep numbers as-is
      return p.charAt(0).toUpperCase() + p.slice(1).toLowerCase();
    })
    .join(' ') || seriesId;
}

export const ChartLegend: React.FC<ChartLegendProps> = ({
  identifier,
  data,
  crosshairData,
  showIndicators = true,
  onIdentifierClick,
}) => {
  // Extract latest indicator values if no crosshair data and we have processed data
  const latestIndicatorValues = useMemo(() => {
    if (crosshairData || !data || !data.indicators) return {};
    
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

  // Merge crosshair indicators with latest indicators
  const indicatorValues = crosshairData?.indicators || latestIndicatorValues;

  // Use crosshair data if available (user is hovering), otherwise use latest data
  const displayData = useMemo(() => {
    if (crosshairData) {
      console.debug('📈 ChartLegend using crosshair data:', {
        time: crosshairData.time,
        close: crosshairData.close,
        indicatorCount: Object.keys(crosshairData.indicators || {}).length
      });
      return crosshairData;
    }
    
    if (data && data.ohlcv.length > 0) {
      return {
    time: data.ohlcv[data.ohlcv.length - 1].time,
    open: data.ohlcv[data.ohlcv.length - 1].open,
    high: data.ohlcv[data.ohlcv.length - 1].high,
    low: data.ohlcv[data.ohlcv.length - 1].low,
    close: data.ohlcv[data.ohlcv.length - 1].close,
    volume: data.ohlcv[data.ohlcv.length - 1].volume,
    indicators: {},
      } as CrosshairData;
    }
    
    return null;
  }, [crosshairData, data]);

  // Calculate price change relative to previous bar (must be before early return)
  const priceChangeInfo = useMemo(() => {
    if (!data || !data.ohlcv || data.ohlcv.length === 0 || !displayData?.close) {
      return null;
    }

    // Find the current bar index
    const currentTime = displayData.time;
    if (!currentTime) return null;

    const currentTimestamp = typeof currentTime === 'number' ? currentTime : new Date(currentTime as string).getTime() / 1000;
    
    // Find the index of current bar
    let currentIndex = -1;
    data.ohlcv.forEach((point, index) => {
      if (Math.abs(point.time - currentTimestamp) < 1) {
        currentIndex = index;
      }
    });

    if (currentIndex === -1) {
      // Use the last bar if we can't find exact match
      currentIndex = data.ohlcv.length - 1;
    }

    // Get previous bar for comparison
    if (currentIndex > 0) {
      const currentBar = data.ohlcv[currentIndex];
      const previousBar = data.ohlcv[currentIndex - 1];
      
      const change = currentBar.close - previousBar.close;
      const changePercent = (change / previousBar.close) * 100;
      
      return {
        change,
        changePercent,
        previousClose: previousBar.close,
      };
    }

    return null;
  }, [data, displayData?.time, displayData?.close]);

  // Calculate High-Low range (only for stocks, ETFs don't have high/low)
  const highLowRange = useMemo(() => {
    // Only show high-low if data has OHLC (stocks), ETFs don't have high/low
    if (data?.hasOHLC && displayData?.high !== undefined && displayData?.low !== undefined) {
      return {
        range: displayData.high - displayData.low,
        high: displayData.high,
        low: displayData.low,
      };
    }
    return null;
  }, [data?.hasOHLC, displayData?.high, displayData?.low]);

  // Group indicators by type for better display (must be before early return)
  const groupedIndicators = useMemo(() => {
    if (!data || !data.indicators || Object.keys(indicatorValues).length === 0) {
      return [];
    }

    const groups: Array<{ indicatorId: string; indicatorName: string; series: Array<{ id: string; name: string; value: number }> }> = [];

    data.indicators.forEach(indicator => {
      const seriesData: Array<{ id: string; name: string; value: number }> = [];
      
      indicator.series.forEach(series => {
        if (indicatorValues[series.id] !== undefined) {
          seriesData.push({
            id: series.id,
            name: formatIndicatorName(series.id, data.indicators),
            value: indicatorValues[series.id],
          });
        }
      });

      if (seriesData.length > 0) {
        groups.push({
          indicatorId: indicator.id,
          indicatorName: indicator.name,
          series: seriesData,
        });
      }
    });

    return groups;
  }, [data, indicatorValues]);

  if (!displayData) {
    return null;
  }

  const changeColor = priceChangeInfo && priceChangeInfo.change >= 0 ? '#26A69A' : '#EF5350';

  return (
    <Box
      sx={{
        position: 'absolute',
        top: 8,
        left: 180, // Move right to avoid AssetHeader (which is at left: 8)
        zIndex: 10,
        backgroundColor: 'rgba(19, 23, 34, 0.85)',
        backdropFilter: 'blur(10px)',
        borderRadius: 1,
        padding: 1.5,
        pointerEvents: 'none',
        minWidth: 250,
        maxWidth: 350,
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
      }}
    >
      {/* Symbol and Price */}
      <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 1, flexWrap: 'wrap' }}>
        <Typography
          variant="h6"
          onClick={onIdentifierClick}
          sx={{
            color: '#D1D4DC',
            fontWeight: 600,
            cursor: onIdentifierClick ? 'pointer' : 'default',
            pointerEvents: onIdentifierClick ? 'auto' : 'none',
            '&:hover': onIdentifierClick
              ? {
                  color: '#2196F3',
                  textDecoration: 'underline',
                }
              : {},
          }}
        >
          {identifier}
        </Typography>
        {displayData.close !== undefined && (
          <Typography
            variant="h6"
            sx={{ color: changeColor, fontWeight: 600 }}
          >
            {formatPrice(displayData.close)}
          </Typography>
        )}
        {priceChangeInfo && (
          <Chip
            label={formatPercent(priceChangeInfo.changePercent)}
            size="small"
            sx={{
              backgroundColor: `${changeColor}20`,
              color: changeColor,
              fontWeight: 600,
              fontSize: '0.75rem',
            }}
          />
        )}
      </Stack>

      {/* Price Change Details */}
      {priceChangeInfo && (
        <Stack direction="row" spacing={1.5} sx={{ mb: 0.5 }}>
          <Typography variant="caption" sx={{ color: '#758696' }}>
            Change: <span style={{ color: changeColor, fontWeight: 500 }}>
              {priceChangeInfo.change >= 0 ? '+' : ''}{formatPrice(priceChangeInfo.change)}
            </span>
          </Typography>
          <Typography variant="caption" sx={{ color: '#758696' }}>
            Prev: <span style={{ color: '#D1D4DC' }}>{formatPrice(priceChangeInfo.previousClose)}</span>
          </Typography>
        </Stack>
      )}

      {/* High-Low Range */}
      {highLowRange && (
        <Stack direction="row" spacing={1.5} sx={{ mb: 0.5 }}>
          <Typography variant="caption" sx={{ color: '#758696' }}>
            H-L: <span style={{ color: '#D1D4DC', fontWeight: 500 }}>
              {formatPrice(highLowRange.range)}
            </span>
          </Typography>
          <Typography variant="caption" sx={{ color: '#758696' }}>
            (<span style={{ color: '#D1D4DC' }}>{formatPrice(highLowRange.low)}</span>
            {' - '}
            <span style={{ color: '#D1D4DC' }}>{formatPrice(highLowRange.high)}</span>)
          </Typography>
        </Stack>
      )}

      {/* OHLC Data - Only show for stocks (hasOHLC), ETFs only show close */}
      {data?.hasOHLC && displayData.open !== undefined && (
        <Stack direction="row" spacing={2} sx={{ mb: 0.5, flexWrap: 'wrap' }}>
          <Typography variant="caption" sx={{ color: '#758696' }}>
            O <span style={{ color: '#D1D4DC', marginLeft: 4 }}>{formatPrice(displayData.open)}</span>
          </Typography>
          {displayData.high !== undefined && (
            <Typography variant="caption" sx={{ color: '#758696' }}>
              H <span style={{ color: '#D1D4DC', marginLeft: 4 }}>{formatPrice(displayData.high)}</span>
            </Typography>
          )}
          {displayData.low !== undefined && (
            <Typography variant="caption" sx={{ color: '#758696' }}>
              L <span style={{ color: '#D1D4DC', marginLeft: 4 }}>{formatPrice(displayData.low)}</span>
            </Typography>
          )}
          <Typography variant="caption" sx={{ color: '#758696' }}>
            C <span style={{ color: '#D1D4DC', marginLeft: 4 }}>{formatPrice(displayData.close!)}</span>
          </Typography>
        </Stack>
      )}

      {/* Volume */}
      {displayData.volume !== undefined && (
        <Typography variant="caption" sx={{ color: '#758696', display: 'block', mb: 0.5 }}>
          Volume: <span style={{ color: '#D1D4DC' }}>{formatVolume(displayData.volume)}</span>
        </Typography>
      )}

      {/* Indicator Values - Dynamic on hover, latest values when not hovering */}
      {showIndicators && groupedIndicators.length > 0 && (
        <Box sx={{ mt: 1, pt: 1, borderTop: '1px solid #2A2E39' }}>
          {groupedIndicators.map((group) => (
            <Box key={group.indicatorId} sx={{ mb: 0.5 }}>
              {group.series.length > 1 && (
                <Typography
                  variant="caption"
                  sx={{
                    color: '#9FA8DA',
                    fontSize: '0.65rem',
                    fontWeight: 500,
                    display: 'block',
                    mb: 0.25,
                  }}
                >
                  {group.indicatorName}
                </Typography>
              )}
              {group.series.map((series) => (
                <Typography
                  key={series.id}
                  variant="caption"
                  sx={{
                    color: '#758696',
                    display: 'block',
                    fontSize: '0.7rem',
                    ml: group.series.length > 1 ? 1 : 0,
                  }}
                >
                  {series.name}: <span style={{ color: '#D1D4DC', fontWeight: 500 }}>
                    {formatPrice(series.value, series.value > 1000 ? 2 : 4)}
                  </span>
                </Typography>
              ))}
            </Box>
          ))}
        </Box>
      )}
    </Box>
  );
};

export default ChartLegend;
