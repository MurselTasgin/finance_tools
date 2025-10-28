// TechnicalChart/utils/chartHelpers.ts
import { UTCTimestamp } from 'lightweight-charts';
import { OHLCVData, LineData, HistogramData, ChartDataResponse, ProcessedChartData, ProcessedIndicator } from '../types/chart.types';
import { getIndicatorColor } from './colorSchemes';

/**
 * Convert date string to UTC timestamp
 */
export function dateToTimestamp(dateString: string): UTCTimestamp {
  return Math.floor(new Date(dateString).getTime() / 1000) as UTCTimestamp;
}

/**
 * Check if data has OHLC columns
 */
export function hasOHLCData(record: Record<string, any>): boolean {
  return (
    'open' in record &&
    'high' in record &&
    'low' in record &&
    'close' in record &&
    record.open !== undefined &&
    record.high !== undefined &&
    record.low !== undefined &&
    record.close !== undefined
  );
}

/**
 * Transform API response to processed chart data
 */
export function processChartData(response: ChartDataResponse): ProcessedChartData {
  const records = response.timeseries;
  const priceColumn = response.price_column || 'close';

  if (!records || records.length === 0) {
    return {
      ohlcv: [],
      volume: undefined,
      indicators: [],
      hasOHLC: false,
    };
  }

  const hasOHLC = hasOHLCData(records[0]);

  // Process OHLCV data
  const ohlcv: OHLCVData[] = records.map((record) => {
    const time = dateToTimestamp(record.date || record.timestamp || record.Date || record.dateTime);

    if (hasOHLC) {
      return {
        time,
        open: parseFloat(record.open),
        high: parseFloat(record.high),
        low: parseFloat(record.low),
        close: parseFloat(record.close),
        volume: record.volume ? parseFloat(record.volume) : undefined,
      };
    } else {
      // Single price series (line chart)
      const value = parseFloat(record[priceColumn]);
      return {
        time,
        open: value,
        high: value,
        low: value,
        close: value,
        volume: record.volume ? parseFloat(record.volume) : undefined,
      };
    }
  });

  // Process volume data
  let volume: LineData[] | undefined;
  if (records[0] && 'volume' in records[0] && records[0].volume !== undefined) {
    volume = records.map((record) => ({
      time: dateToTimestamp(record.date || record.timestamp || record.Date || record.dateTime),
      value: parseFloat(record.volume),
    }));
  }

  // Process indicators
  const indicators = processIndicators(response, records);

  return {
    ohlcv,
    volume,
    indicators,
    hasOHLC,
  };
}

/**
 * Process indicators from API response
 */
function processIndicators(
  response: ChartDataResponse,
  records: Array<Record<string, any>>
): ProcessedIndicator[] {
  const indicators: ProcessedIndicator[] = [];

  response.indicator_definitions.forEach((indicatorDef, index) => {
    const series = indicatorDef.columns
      .map((columnName, seriesIndex) => {
        // Check if column exists in data
        if (!records[0] || records[0][columnName] === undefined) {
          return null;
        }

        // Determine series type
        let seriesType: 'line' | 'histogram' | 'area' = 'line';
        const columnLower = columnName.toLowerCase();
        if (columnLower.includes('hist') || columnLower.includes('histogram')) {
          seriesType = 'histogram';
        } else if (columnLower.includes('area') || columnLower.includes('volume')) {
          seriesType = 'area';
        }

        // Extract data
        const data = records.map((record) => {
          const time = dateToTimestamp(record.date || record.timestamp || record.Date || record.dateTime);
          const value = parseFloat(record[columnName]);

          if (seriesType === 'histogram') {
            return {
              time,
              value: isNaN(value) ? 0 : value,
              color: value >= 0 ? '#26A69A' : '#EF5350',
            } as HistogramData;
          } else {
            return {
              time,
              value: isNaN(value) ? 0 : value,
            } as LineData;
          }
        });

        return {
          id: `${indicatorDef.id}_${columnName}`,
          name: formatColumnName(columnName),
          type: seriesType,
          data,
          color: getIndicatorColor(index * 3 + seriesIndex),
          visible: true,
        };
      })
      .filter((s) => s !== null) as any[];

    if (series.length > 0) {
      // Determine if indicator should be overlay or subplot
      const isOverlay = isOverlayIndicator(indicatorDef.id);

      indicators.push({
        id: indicatorDef.id,
        name: indicatorDef.name,
        type: isOverlay ? 'overlay' : 'subplot',
        series,
      });
    }
  });

  return indicators;
}

/**
 * Determine if indicator should be overlaid on main chart
 */
function isOverlayIndicator(indicatorId: string): boolean {
  const overlayIndicators = [
    'ema_cross',
    'ema_regime',
    'bollinger_bands',
    'sma',
    'ema',
    'vwap',
    'pivot',
  ];
  return overlayIndicators.includes(indicatorId.toLowerCase());
}

/**
 * Format column name for display
 */
function formatColumnName(columnName: string): string {
  // Convert snake_case or camelCase to Title Case
  return columnName
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ')
    .trim();
}

/**
 * Calculate price change and percentage
 */
export function calculatePriceChange(data: OHLCVData[]): { change: number; changePercent: number } | null {
  if (data.length < 2) {
    return null;
  }

  const current = data[data.length - 1].close;
  const previous = data[data.length - 2].close;
  const change = current - previous;
  const changePercent = (change / previous) * 100;

  return { change, changePercent };
}

/**
 * Format number with appropriate precision
 */
export function formatPrice(price: number, decimals: number = 2): string {
  return price.toFixed(decimals);
}

/**
 * Format large numbers (for volume)
 */
export function formatVolume(volume: number): string {
  if (volume >= 1e9) {
    return `${(volume / 1e9).toFixed(2)}B`;
  } else if (volume >= 1e6) {
    return `${(volume / 1e6).toFixed(2)}M`;
  } else if (volume >= 1e3) {
    return `${(volume / 1e3).toFixed(2)}K`;
  } else {
    return volume.toFixed(0);
  }
}

/**
 * Format percentage
 */
export function formatPercent(percent: number): string {
  const sign = percent >= 0 ? '+' : '';
  return `${sign}${percent.toFixed(2)}%`;
}

/**
 * Get default chart options
 */
export function getDefaultChartOptions() {
  return {
    theme: 'dark' as const,
    chartType: 'candlestick' as const,
    showVolume: true,
    showGrid: true,
    showCrosshair: true,
    showLegend: true,
    showTimeScale: true,
    showPriceScale: true,
    autoScale: true,
    height: 600,
  };
}
