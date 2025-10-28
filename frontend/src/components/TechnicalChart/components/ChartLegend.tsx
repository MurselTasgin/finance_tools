// TechnicalChart/components/ChartLegend.tsx
import React from 'react';
import { Box, Typography, Chip, Stack } from '@mui/material';
import { CrosshairData, ProcessedChartData } from '../types/chart.types';
import { formatPrice, formatVolume, formatPercent, calculatePriceChange } from '../utils/chartHelpers';

interface ChartLegendProps {
  identifier: string;
  data: ProcessedChartData | null;
  crosshairData: CrosshairData | null;
  showIndicators?: boolean;
}

export const ChartLegend: React.FC<ChartLegendProps> = ({
  identifier,
  data,
  crosshairData,
  showIndicators = true,
}) => {
  // Use latest data if no crosshair data
  const displayData = crosshairData || (data && data.ohlcv.length > 0 ? {
    time: data.ohlcv[data.ohlcv.length - 1].time,
    open: data.ohlcv[data.ohlcv.length - 1].open,
    high: data.ohlcv[data.ohlcv.length - 1].high,
    low: data.ohlcv[data.ohlcv.length - 1].low,
    close: data.ohlcv[data.ohlcv.length - 1].close,
    volume: data.ohlcv[data.ohlcv.length - 1].volume,
    indicators: {},
  } as CrosshairData : null);

  if (!displayData) {
    return null;
  }

  // Calculate price change
  const priceChange = data ? calculatePriceChange(data.ohlcv) : null;
  const changeColor = priceChange && priceChange.change >= 0 ? '#26A69A' : '#EF5350';

  return (
    <Box
      sx={{
        position: 'absolute',
        top: 8,
        left: 12,
        zIndex: 10,
        backgroundColor: 'rgba(19, 23, 34, 0.85)',
        backdropFilter: 'blur(10px)',
        borderRadius: 1,
        padding: 1.5,
        pointerEvents: 'none',
        minWidth: 250,
      }}
    >
      {/* Symbol and Price */}
      <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 1 }}>
        <Typography variant="h6" sx={{ color: '#D1D4DC', fontWeight: 600 }}>
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
        {priceChange && !crosshairData && (
          <Chip
            label={`${formatPercent(priceChange.changePercent)} (${priceChange.change >= 0 ? '+' : ''}${formatPrice(priceChange.change)})`}
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

      {/* OHLC Data */}
      {displayData.open !== undefined && (
        <Stack direction="row" spacing={2} sx={{ mb: 0.5 }}>
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

      {/* Indicator Values */}
      {showIndicators && displayData.indicators && Object.keys(displayData.indicators).length > 0 && (
        <Box sx={{ mt: 1, pt: 1, borderTop: '1px solid #2A2E39' }}>
          {Object.entries(displayData.indicators).map(([key, value]) => {
            // Format indicator name (remove indicator prefix)
            const displayName = key.split('_').slice(1).join(' ').toUpperCase() || key;

            return (
              <Typography
                key={key}
                variant="caption"
                sx={{
                  color: '#758696',
                  display: 'block',
                  fontSize: '0.7rem',
                }}
              >
                {displayName}: <span style={{ color: '#D1D4DC' }}>{formatPrice(value, 4)}</span>
              </Typography>
            );
          })}
        </Box>
      )}
    </Box>
  );
};

export default ChartLegend;
