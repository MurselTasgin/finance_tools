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

  // Calculate price range for overlay indicators to filter outliers
  const priceColumn = response.price_column || 'close';
  const priceValues: number[] = [];
  records.forEach((record) => {
    const price = parseFloat(record[priceColumn] || record.close || 0);
    if (!isNaN(price) && price > 0) {
      priceValues.push(price);
    }
  });

  const minPrice = priceValues.length > 0 ? Math.min(...priceValues) : 0;
  const maxPrice = priceValues.length > 0 ? Math.max(...priceValues) : 0;
  
  // For overlay indicators, filter out values that are clearly outliers compared to price range
  // This prevents initial low/NaN EMA values (e.g., 0 when price is 100-200) from distorting the y-axis
  // We'll only exclude values that are clearly unreasonable (< 10% of min price or > 300% of max price)
  const validMinValue = minPrice > 0 ? minPrice * 0.1 : 0; // Allow values down to 10% of min price
  const validMaxValue = maxPrice > 0 ? maxPrice * 3.0 : Infinity; // Allow values up to 300% of max price

  response.indicator_definitions.forEach((indicatorDef, index) => {
    // Determine if indicator should be overlay or subplot
    const isOverlay = isOverlayIndicator(indicatorDef.id);

    // Debug logging for ETF-specific indicators
    if (indicatorDef.id === 'number_of_shares' || indicatorDef.id === 'number_of_investors') {
      console.log(`Processing indicator ${indicatorDef.id}:`, {
        columns: indicatorDef.columns,
        recordsLength: records.length,
        firstRecordHasColumns: indicatorDef.columns.map(col => ({
          col,
          exists: records[0] ? records[0][col] !== undefined : false,
          value: records[0] ? records[0][col] : null
        }))
      });
    }

    const series = indicatorDef.columns
      .map((columnName, seriesIndex) => {
        // Check if column exists in data
        if (!records[0] || records[0][columnName] === undefined) {
          // For ETF indicators, log why column is missing
          if (indicatorDef.id === 'number_of_shares' || indicatorDef.id === 'number_of_investors') {
            console.warn(`Column ${columnName} not found in records for indicator ${indicatorDef.id}`, {
              firstRecordKeys: records[0] ? Object.keys(records[0]) : [],
              columnName
            });
          }
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

        // Extract data and filter invalid values
        const data: (LineData | HistogramData)[] = [];
        
        records.forEach((record) => {
          const time = dateToTimestamp(record.date || record.timestamp || record.Date || record.dateTime);
          const rawValue = record[columnName];
          
          // Check if value is null, undefined, or empty string
          if (rawValue === null || rawValue === undefined || rawValue === '') {
            // For overlay indicators, skip invalid values completely to avoid affecting y-axis
            // For ETF-specific metrics (number_of_shares, number_of_investors), skip null values
            // For subplot indicators, use 0 for histograms only
            if (isOverlay) {
              return; // Skip this data point
            } else if (seriesType === 'histogram') {
              // For histogram with null/empty value, use 0 and default to green (positive)
              const histogramValue = 0;
              data.push({
                time,
                value: histogramValue,
                color: '#26A69A', // Default to green for zero/null values
              } as HistogramData);
              return;
            } else {
              // For line/area subplot indicators, skip null values (they'll just have gaps)
              return; // Skip invalid values for subplot line/area too
            }
          }

          const value = parseFloat(rawValue);
          
          // Check if value is NaN or Infinity
          if (isNaN(value) || !isFinite(value)) {
            // Skip invalid numeric values
            return;
          }

          // For overlay indicators, filter out values that are too far from price range
          if (isOverlay && priceValues.length > 0) {
            // Skip values that are significantly outside the price range
            // This prevents initial low/NaN EMA values from distorting the chart
            if (value < validMinValue || value > validMaxValue) {
              return; // Skip this data point
            }
          }

          if (seriesType === 'histogram') {
            data.push({
              time,
              value: value,
              color: value >= 0 ? '#26A69A' : '#EF5350',
            } as HistogramData);
          } else {
            data.push({
              time,
              value: value,
            } as LineData);
          }
        });

        // Only create series if we have valid data points
        // For ETF indicators with EMA, allow some null values (EMA needs warm-up period)
        // but require at least some valid data points
        if (data.length === 0) {
          if (indicatorDef.id === 'number_of_shares' || indicatorDef.id === 'number_of_investors') {
            console.warn(`⚠️ Indicator ${indicatorDef.id} column ${columnName} has no valid data points`, {
              totalRecords: records.length,
              columnName,
              sampleValues: records.slice(0, 5).map(r => r[columnName])
            });
          }
          return null;
        }
        
        // Log successful series creation for debugging
        if (indicatorDef.id === 'number_of_shares' || indicatorDef.id === 'number_of_investors') {
          console.log(`✅ Created series for ${indicatorDef.id} column ${columnName}:`, {
            dataPoints: data.length,
            firstValue: data[0]?.value,
            lastValue: data[data.length - 1]?.value
          });
        }

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
      indicators.push({
        id: indicatorDef.id,
        name: indicatorDef.name,
        type: isOverlay ? 'overlay' : 'subplot',
        series,
      });
    } else {
      // Log when indicator has no valid series
      if (indicatorDef.id === 'number_of_shares' || indicatorDef.id === 'number_of_investors') {
        console.warn(`Indicator ${indicatorDef.id} produced no valid series`, {
          columns: indicatorDef.columns,
          recordsLength: records.length
        });
      }
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
