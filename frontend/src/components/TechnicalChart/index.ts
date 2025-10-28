// TechnicalChart/index.ts
// Main container
export { TechnicalChartContainer } from './TechnicalChartContainer';

// Core components
export { ChartCanvas } from './components/ChartCanvas';
export { ChartLegend } from './components/ChartLegend';
export { ChartPanel } from './components/ChartPanel';
export { ChartToolbar } from './components/ChartToolbar';
export { PanelResizer } from './components/PanelResizer';

// Indicator management components
export { IndicatorSelector } from './components/IndicatorSelector';
export { IndicatorParameterEditor } from './components/IndicatorParameterEditor';

// Hooks
export { useChartData } from './hooks/useChartData';

// Export types
export type {
  AssetType,
  ChartType,
  TimeInterval,
  ChartTheme,
  OHLCVData,
  LineData,
  HistogramData,
  ChartDataResponse,
  ProcessedChartData,
  ProcessedIndicator,
  ChartOptions,
  ChartPanel as ChartPanelType,
  CrosshairData,
  TechnicalChartContainerProps,
  IndicatorConfig,
  ParameterDefinition,
  IndicatorPanelAssignment,
  PanelResizeEvent,
  DrawingTool,
  DrawingPoint,
  ScreenPoint,
  ChartDrawing,
} from './types/chart.types';

// Export color utilities
export {
  getColorScheme,
  getIndicatorColor,
  INDICATOR_COLORS,
} from './utils/colorSchemes';

// Export chart helper utilities
export {
  processChartData,
  formatPrice,
  formatVolume,
  formatPercent,
  calculatePriceChange,
} from './utils/chartHelpers';

// Export panel management utilities
export {
  createInitialPanels,
  normalizePanelHeights,
  resizePanel,
  togglePanelVisibility,
  addIndicatorPanel,
  removeIndicatorPanel,
  getPanelPixelHeight,
  calculatePanelPixelHeights,
  getIndicatorsForPanel,
} from './utils/panelHelpers';

// Export indicator configuration utilities
export {
  INDICATOR_CONFIGS,
  getAllIndicators,
  getIndicatorById,
  getIndicatorsByType,
  getOverlayIndicators,
  getSubplotIndicators,
  validateIndicatorParameters,
} from './utils/indicatorConfigs';
