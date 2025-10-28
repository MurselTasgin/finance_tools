// TechnicalChart/types/chart.types.ts
import { IChartApi, ISeriesApi, Time, UTCTimestamp, Logical } from 'lightweight-charts';

/**
 * Asset type for the chart
 */
export type AssetType = 'stock' | 'etf';

/**
 * Chart type/style
 */
export type ChartType = 'candlestick' | 'line' | 'area' | 'bar' | 'baseline';

/**
 * Time interval for the chart
 */
export type TimeInterval = '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d' | '1wk' | '1mo';

/**
 * Chart theme
 */
export type ChartTheme = 'light' | 'dark';

/**
 * OHLCV data point
 */
export interface OHLCVData {
  time: UTCTimestamp;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

/**
 * Line data point for indicators
 */
export interface LineData {
  time: UTCTimestamp;
  value: number;
}

/**
 * Histogram data point (for MACD, etc.)
 */
export interface HistogramData {
  time: UTCTimestamp;
  value: number;
  color?: string;
}

/**
 * Chart data from API
 */
export interface ChartDataResponse {
  asset_type: AssetType;
  identifier: string;
  columns: string[];
  price_column: string;
  interval: string;
  start_date?: string;
  end_date?: string;
  timeseries: Array<Record<string, any>>;
  indicator_definitions: IndicatorDefinition[];
  indicator_snapshots: Record<string, Record<string, any>>;
  metadata: Record<string, any>;
}

/**
 * Indicator definition from backend
 */
export interface IndicatorDefinition {
  id: string;
  name: string;
  description: string;
  columns: string[];
  parameters: Record<string, any>;
}

/**
 * Processed chart data ready for rendering
 */
export interface ProcessedChartData {
  ohlcv: OHLCVData[];
  volume?: LineData[];
  indicators: ProcessedIndicator[];
  hasOHLC: boolean;
}

/**
 * Processed indicator ready for rendering
 */
export interface ProcessedIndicator {
  id: string;
  name: string;
  type: 'overlay' | 'subplot';
  series: IndicatorSeries[];
}

/**
 * Individual indicator series
 */
export interface IndicatorSeries {
  id: string;
  name: string;
  type: 'line' | 'histogram' | 'area';
  data: LineData[] | HistogramData[];
  color: string;
  visible: boolean;
}

/**
 * Supported drawing tool identifiers
 */
export type DrawingTool =
  | 'trendline'
  | 'horizontal-line'
  | 'vertical-line'
  | 'parallel-channel';

/**
 * Point in time/price space used for drawings
 */
export interface DrawingPoint {
  time: Time;
  price: number;
  logical?: Logical;
}

/**
 * Screen coordinate used for fallback rendering
 */
export interface ScreenPoint {
  x: number;
  y: number;
}

/**
 * Configuration for a drawing element rendered on top of the chart
 */
export interface ChartDrawing {
  id: string;
  type: DrawingTool;
  points: DrawingPoint[];
  screenPoints?: ScreenPoint[];
  color?: string;
  secondaryColor?: string;
  lineWidth?: number;
  opacity?: number;
  panelId?: string;
  locked?: boolean;
}

/**
 * Chart configuration options
 */
export interface ChartOptions {
  theme: ChartTheme;
  chartType: ChartType;
  showVolume: boolean;
  showGrid: boolean;
  showCrosshair: boolean;
  showLegend: boolean;
  showTimeScale: boolean;
  showPriceScale: boolean;
  autoScale: boolean;
  height: number;
  backgroundColor?: string;
  textColor?: string;
  gridColor?: string;
}

/**
 * Panel type
 */
export type PanelType = 'main' | 'indicator';

/**
 * Panel configuration for multi-panel layout
 */
export interface ChartPanel {
  id: string;
  title: string;
  type: PanelType;
  heightPercent: number; // Height as percentage of total (0-100)
  minHeight: number; // Minimum height in pixels
  maxHeight?: number; // Maximum height in pixels (optional)
  indicators: string[]; // indicator IDs rendered in this panel
  visible: boolean;
  chartApi?: IChartApi;
  series: Map<string, ISeriesApi<any>>;
  order: number; // Display order (0 = top)
}

/**
 * Panel resize event
 */
export interface PanelResizeEvent {
  panelId: string;
  oldHeightPercent: number;
  newHeightPercent: number;
  adjacentPanelId?: string; // Panel that should adjust in opposite direction
}

/**
 * Crosshair data for legend display
 */
export interface CrosshairData {
  time: Time;
  open?: number;
  high?: number;
  low?: number;
  close?: number;
  volume?: number;
  change?: number;
  changePercent?: number;
  indicators: Record<string, number>;
}

/**
 * Chart state
 */
export interface ChartState {
  isLoading: boolean;
  error: string | null;
  data: ProcessedChartData | null;
  options: ChartOptions;
  panels: ChartPanel[];
  crosshairData: CrosshairData | null;
  visibleRange: {
    from: Time;
    to: Time;
  } | null;
}

/**
 * Props for TechnicalChartContainer
 */
export interface TechnicalChartContainerProps {
  assetType: AssetType;
  identifier: string;
  startDate?: string;
  endDate?: string;
  interval: TimeInterval;
  indicators: string[];
  indicatorParameters: Record<string, Record<string, any>>;
  onDataLoad?: (data: ChartDataResponse) => void;
  onError?: (error: string) => void;
  onIndicatorsChange?: (indicators: string[], parameters: Record<string, Record<string, any>>) => void;
  height?: number;
  theme?: ChartTheme;
  showToolbar?: boolean;
}

/**
 * Props for ChartCanvas
 */
export interface ChartCanvasProps {
  data: ProcessedChartData;
  options: ChartOptions;
  panels: ChartPanel[];
  onCrosshairMove?: (data: CrosshairData | null) => void;
  onVisibleRangeChange?: (range: { from: Time; to: Time }) => void;
  onPanelResize?: (panelId: string, newHeight: number) => void;
}

/**
 * Indicator configuration for UI
 */
export interface IndicatorConfig {
  id: string;
  name: string;
  description: string;
  type: 'overlay' | 'subplot';
  defaultParameters: Record<string, any>;
  parameterDefinitions: ParameterDefinition[];
}

/**
 * Parameter definition for indicator configuration
 */
export interface ParameterDefinition {
  key: string;
  label: string;
  type: 'number' | 'select' | 'boolean';
  defaultValue: any;
  min?: number;
  max?: number;
  step?: number;
  options?: Array<{ label: string; value: any }>;
  description?: string;
}

/**
 * Indicator panel assignment
 */
export interface IndicatorPanelAssignment {
  indicatorId: string;
  panelId: string;
  visible: boolean;
  order: number; // Order within the panel
}
