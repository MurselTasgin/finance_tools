// TechnicalChart/utils/colorSchemes.ts
import { ChartTheme } from '../types/chart.types';

/**
 * Color scheme for charts
 */
export interface ColorScheme {
  background: string;
  text: string;
  grid: string;
  crosshair: string;
  upColor: string;
  downColor: string;
  wickUpColor: string;
  wickDownColor: string;
  borderUpColor: string;
  borderDownColor: string;
  volumeColor: string;
  volumeUpColor: string;
  volumeDownColor: string;
}

/**
 * Indicator color palette
 */
export const INDICATOR_COLORS = [
  '#2962FF', // Blue
  '#FF6D00', // Orange
  '#00897B', // Teal
  '#E91E63', // Pink
  '#9C27B0', // Purple
  '#FF9800', // Amber
  '#00BCD4', // Cyan
  '#F44336', // Red
  '#4CAF50', // Green
  '#FFC107', // Yellow
  '#3F51B5', // Indigo
  '#009688', // Teal
];

/**
 * Get color for indicator by index
 */
export function getIndicatorColor(index: number): string {
  return INDICATOR_COLORS[index % INDICATOR_COLORS.length];
}

/**
 * Dark theme color scheme
 */
export const DARK_THEME: ColorScheme = {
  background: '#131722',
  text: '#D1D4DC',
  grid: '#2A2E39',
  crosshair: '#758696',
  upColor: '#26A69A',
  downColor: '#EF5350',
  wickUpColor: '#26A69A',
  wickDownColor: '#EF5350',
  borderUpColor: '#26A69A',
  borderDownColor: '#EF5350',
  volumeColor: '#26A69A50',
  volumeUpColor: '#26A69A',
  volumeDownColor: '#EF5350',
};

/**
 * Light theme color scheme
 */
export const LIGHT_THEME: ColorScheme = {
  background: '#FFFFFF',
  text: '#191919',
  grid: '#E0E3EB',
  crosshair: '#9598A1',
  upColor: '#089981',
  downColor: '#F23645',
  wickUpColor: '#089981',
  wickDownColor: '#F23645',
  borderUpColor: '#089981',
  borderDownColor: '#F23645',
  volumeColor: '#08998150',
  volumeUpColor: '#089981',
  volumeDownColor: '#F23645',
};

/**
 * Get color scheme for theme
 */
export function getColorScheme(theme: ChartTheme): ColorScheme {
  return theme === 'dark' ? DARK_THEME : LIGHT_THEME;
}

/**
 * Convert hex color to rgba
 */
export function hexToRgba(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
