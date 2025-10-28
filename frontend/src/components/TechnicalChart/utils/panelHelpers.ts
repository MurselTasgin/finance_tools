// TechnicalChart/utils/panelHelpers.ts
import {
  ChartPanel,
  ProcessedChartData,
  ProcessedIndicator,
} from '../types/chart.types';

/**
 * Default panel heights (as percentages)
 */
export const DEFAULT_MAIN_PANEL_HEIGHT = 70;
export const DEFAULT_INDICATOR_PANEL_HEIGHT = 30;
export const MIN_PANEL_HEIGHT = 100; // pixels
export const MIN_PANEL_HEIGHT_PERCENT = 10;
export const MAX_PANEL_HEIGHT_PERCENT = 80;

/**
 * Creates the initial panel configuration based on chart data
 */
export function createInitialPanels(data: ProcessedChartData): ChartPanel[] {
  const panels: ChartPanel[] = [];

  // Create main panel for price and overlay indicators
  const overlayIndicators = data.indicators
    .filter((ind) => ind.type === 'overlay')
    .map((ind) => ind.id);

  const mainPanel: ChartPanel = {
    id: 'main',
    title: 'Price',
    type: 'main',
    heightPercent: DEFAULT_MAIN_PANEL_HEIGHT,
    minHeight: MIN_PANEL_HEIGHT,
    indicators: overlayIndicators,
    visible: true,
    series: new Map(),
    order: 0,
  };
  panels.push(mainPanel);

  // Create separate panels for subplot indicators
  const subplotIndicators = data.indicators.filter((ind) => ind.type === 'subplot');

  if (subplotIndicators.length > 0) {
    // Distribute remaining height among subplot indicators
    const remainingHeight = 100 - DEFAULT_MAIN_PANEL_HEIGHT;
    const heightPerPanel = remainingHeight / subplotIndicators.length;

    subplotIndicators.forEach((indicator, index) => {
      const panel: ChartPanel = {
        id: `indicator-${indicator.id}`,
        title: indicator.name,
        type: 'indicator',
        heightPercent: heightPerPanel,
        minHeight: MIN_PANEL_HEIGHT,
        indicators: [indicator.id],
        visible: true,
        series: new Map(),
        order: index + 1,
      };
      panels.push(panel);
    });
  }

  return panels;
}

/**
 * Updates panel heights ensuring they sum to 100%
 */
export function normalizePanelHeights(panels: ChartPanel[]): ChartPanel[] {
  const visiblePanels = panels.filter((p) => p.visible);
  if (visiblePanels.length === 0) return panels;

  // Calculate total height
  const totalHeight = visiblePanels.reduce((sum, p) => sum + p.heightPercent, 0);

  if (Math.abs(totalHeight - 100) < 0.01) {
    return panels; // Already normalized
  }

  // Normalize heights proportionally
  const factor = 100 / totalHeight;
  return panels.map((panel) => ({
    ...panel,
    heightPercent: panel.visible ? panel.heightPercent * factor : 0,
  }));
}

/**
 * Resizes a panel and adjusts adjacent panel accordingly
 */
export function resizePanel(
  panels: ChartPanel[],
  panelId: string,
  newHeightPercent: number,
  adjacentPanelId?: string
): ChartPanel[] {
  const panelIndex = panels.findIndex((p) => p.id === panelId);
  if (panelIndex === -1) return panels;

  const panel = panels[panelIndex];
  const heightDelta = newHeightPercent - panel.heightPercent;

  // Clamp to min/max constraints
  const clampedHeight = Math.max(
    MIN_PANEL_HEIGHT_PERCENT,
    Math.min(MAX_PANEL_HEIGHT_PERCENT, newHeightPercent)
  );

  // If no adjacent panel specified, find the next visible panel
  let adjacentIndex = -1;
  if (adjacentPanelId) {
    adjacentIndex = panels.findIndex((p) => p.id === adjacentPanelId);
  } else {
    // Find next visible panel
    adjacentIndex = panels.findIndex(
      (p, idx) => idx > panelIndex && p.visible
    );
  }

  if (adjacentIndex === -1) return panels;

  const adjacentPanel = panels[adjacentIndex];
  const newAdjacentHeight = adjacentPanel.heightPercent - heightDelta;

  // Check if adjacent panel would violate constraints
  if (
    newAdjacentHeight < MIN_PANEL_HEIGHT_PERCENT ||
    newAdjacentHeight > MAX_PANEL_HEIGHT_PERCENT
  ) {
    return panels; // Cannot resize
  }

  // Apply resize
  const updatedPanels = [...panels];
  updatedPanels[panelIndex] = { ...panel, heightPercent: clampedHeight };
  updatedPanels[adjacentIndex] = {
    ...adjacentPanel,
    heightPercent: newAdjacentHeight,
  };

  return normalizePanelHeights(updatedPanels);
}

/**
 * Toggles panel visibility and redistributes heights
 */
export function togglePanelVisibility(
  panels: ChartPanel[],
  panelId: string
): ChartPanel[] {
  const panelIndex = panels.findIndex((p) => p.id === panelId);
  if (panelIndex === -1 || panels[panelIndex].type === 'main') {
    return panels; // Cannot hide main panel
  }

  const updatedPanels = panels.map((panel) =>
    panel.id === panelId ? { ...panel, visible: !panel.visible } : panel
  );

  return normalizePanelHeights(updatedPanels);
}

/**
 * Adds a new indicator panel
 */
export function addIndicatorPanel(
  panels: ChartPanel[],
  indicator: ProcessedIndicator
): ChartPanel[] {
  // Check if panel already exists
  const existingPanel = panels.find((p) => p.id === `indicator-${indicator.id}`);
  if (existingPanel) {
    return panels.map((p) =>
      p.id === existingPanel.id ? { ...p, visible: true } : p
    );
  }

  // Create new panel
  const newPanel: ChartPanel = {
    id: `indicator-${indicator.id}`,
    title: indicator.name,
    type: 'indicator',
    heightPercent: DEFAULT_INDICATOR_PANEL_HEIGHT,
    minHeight: MIN_PANEL_HEIGHT,
    indicators: [indicator.id],
    visible: true,
    series: new Map(),
    order: panels.length,
  };

  const updatedPanels = [...panels, newPanel];
  return normalizePanelHeights(updatedPanels);
}

/**
 * Removes an indicator panel
 */
export function removeIndicatorPanel(
  panels: ChartPanel[],
  panelId: string
): ChartPanel[] {
  const panel = panels.find((p) => p.id === panelId);
  if (!panel || panel.type === 'main') {
    return panels; // Cannot remove main panel
  }

  const updatedPanels = panels.filter((p) => p.id !== panelId);
  return normalizePanelHeights(updatedPanels);
}

/**
 * Gets the pixel height for a panel given the total container height
 */
export function getPanelPixelHeight(
  panel: ChartPanel,
  totalHeight: number
): number {
  if (!panel.visible) return 0;
  const calculatedHeight = (panel.heightPercent / 100) * totalHeight;
  return Math.max(panel.minHeight, calculatedHeight);
}

/**
 * Calculates actual pixel heights for all panels ensuring total equals container
 */
export function calculatePanelPixelHeights(
  panels: ChartPanel[],
  totalHeight: number
): Map<string, number> {
  const visiblePanels = panels.filter((p) => p.visible);
  const heights = new Map<string, number>();

  if (visiblePanels.length === 0) return heights;

  // First pass: calculate heights respecting minimums
  let remainingHeight = totalHeight;
  const panelsNeedingMin: ChartPanel[] = [];

  visiblePanels.forEach((panel) => {
    const idealHeight = (panel.heightPercent / 100) * totalHeight;
    if (idealHeight < panel.minHeight) {
      heights.set(panel.id, panel.minHeight);
      remainingHeight -= panel.minHeight;
      panelsNeedingMin.push(panel);
    }
  });

  // Second pass: distribute remaining height proportionally
  const flexiblePanels = visiblePanels.filter((p) => !panelsNeedingMin.includes(p));
  if (flexiblePanels.length > 0) {
    const totalFlexPercent = flexiblePanels.reduce(
      (sum, p) => sum + p.heightPercent,
      0
    );

    flexiblePanels.forEach((panel) => {
      const proportion = panel.heightPercent / totalFlexPercent;
      const height = Math.max(panel.minHeight, proportion * remainingHeight);
      heights.set(panel.id, height);
    });
  }

  return heights;
}

/**
 * Gets indicator assignments for a specific panel
 */
export function getIndicatorsForPanel(
  panel: ChartPanel,
  indicators: ProcessedIndicator[]
): ProcessedIndicator[] {
  return indicators.filter((ind) => panel.indicators.includes(ind.id));
}

/**
 * Checks if an indicator is assigned to any panel
 */
export function isIndicatorAssigned(
  indicatorId: string,
  panels: ChartPanel[]
): boolean {
  return panels.some((panel) => panel.indicators.includes(indicatorId));
}

/**
 * Gets the panel that contains a specific indicator
 */
export function getPanelForIndicator(
  indicatorId: string,
  panels: ChartPanel[]
): ChartPanel | null {
  return panels.find((panel) => panel.indicators.includes(indicatorId)) || null;
}
