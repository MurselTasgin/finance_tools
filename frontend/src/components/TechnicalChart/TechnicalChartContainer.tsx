// TechnicalChart/TechnicalChartContainer.tsx
import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Box, CircularProgress, Alert, Paper } from '@mui/material';
import { Time } from 'lightweight-charts';
import { ChartPanel, ChartPanelHandle } from './components/ChartPanel';
import { PriceInfoOverlay } from './components/PriceInfoOverlay';
import { AssetHeader } from './components/AssetHeader';
import { PanelResizer } from './components/PanelResizer';
import { ChartToolbar } from './components/ChartToolbar';
import { IndicatorSelector } from './components/IndicatorSelector';
import { IndicatorParameterEditor } from './components/IndicatorParameterEditor';
import { AssetSelector } from './components/AssetSelector';
import { useChartData } from './hooks/useChartData';
import {
  TechnicalChartContainerProps,
  CrosshairData,
  ChartOptions,
  ChartPanel as ChartPanelType,
} from './types/chart.types';
import { getDefaultChartOptions } from './utils/chartHelpers';
import {
  createInitialPanels,
  calculatePanelPixelHeights,
  togglePanelVisibility,
  resizePanel,
} from './utils/panelHelpers';

const MIN_CHART_HEIGHT = 320;

/**
 * Main Technical Chart Container with Multi-Panel Support
 *
 * This component integrates the Lightweight Charts library with our backend data
 * and provides a TradingView-like charting experience with multiple synchronized panels.
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
  onIndicatorsChange,
  onAssetChange,
  height = 600,
  theme = 'dark',
  showToolbar = true,
}) => {
  const [crosshairData, setCrosshairData] = useState<CrosshairData | null>(null);
  const [chartOptions, setChartOptions] = useState<ChartOptions>({
    ...getDefaultChartOptions(),
    theme,
    height,
  });
  const [containerHeight, setContainerHeight] = useState<number>(height);
  const [panels, setPanels] = useState<ChartPanelType[]>([]);
  const [indicatorSelectorOpen, setIndicatorSelectorOpen] = useState(false);
  const [paramEditorOpen, setParamEditorOpen] = useState(false);
  const [editingIndicatorId, setEditingIndicatorId] = useState<string | null>(null);
  const [assetSelectorOpen, setAssetSelectorOpen] = useState(false);

  // Refs for each panel to enable synchronization
  const panelRefs = useRef<Map<string, React.RefObject<ChartPanelHandle>>>(new Map());

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

  // Initialize panels when data changes
  useEffect(() => {
    if (processedData && processedData.ohlcv.length > 0) {
      const newPanels = createInitialPanels(processedData);
      
      // Preserve visibility state of existing panels (so closed panels stay closed)
      setPanels((prevPanels) => {
        // Only update if the structure actually changed (new indicators added/removed)
        const prevIndicatorIds = new Set(
          prevPanels
            .filter(p => p.type === 'indicator')
            .flatMap(p => p.indicators || [])
        );
        const newIndicatorIds = new Set(
          newPanels
            .filter(p => p.type === 'indicator')
            .flatMap(p => p.indicators || [])
        );
        
        // Check if indicator sets are different
        const indicatorsChanged = 
          prevIndicatorIds.size !== newIndicatorIds.size ||
          Array.from(prevIndicatorIds).some(id => !newIndicatorIds.has(id)) ||
          Array.from(newIndicatorIds).some(id => !prevIndicatorIds.has(id));
        
        // If panels haven't structurally changed and we have existing panels, just return them
        if (!indicatorsChanged && prevPanels.length > 0) {
          // Still update refs for new panels that might have been added
          newPanels.forEach((panel) => {
            if (!panelRefs.current.has(panel.id)) {
              panelRefs.current.set(panel.id, React.createRef<ChartPanelHandle>());
            }
          });
          return prevPanels;
        }
        
        const visibilityMap = new Map<string, boolean>();
        prevPanels.forEach((panel) => {
          visibilityMap.set(panel.id, panel.visible);
        });

        // Merge visibility state from previous panels
        const mergedPanels = newPanels.map((newPanel) => {
          const previousVisibility = visibilityMap.get(newPanel.id);
          // Only preserve visibility if panel already existed
          // New panels should be visible by default
          if (previousVisibility !== undefined) {
            return { ...newPanel, visible: previousVisibility };
          }
          return newPanel;
        });

        // Create refs for each panel (only for new panels, don't clear existing ones)
        mergedPanels.forEach((panel) => {
          if (!panelRefs.current.has(panel.id)) {
            panelRefs.current.set(panel.id, React.createRef<ChartPanelHandle>());
          }
        });

        return mergedPanels;
      });
    }
  }, [processedData, indicators]);

  // Handle data load callback
  useEffect(() => {
    if (rawData && onDataLoad) {
      onDataLoad(rawData);
    }
  }, [rawData, onDataLoad]);

  // Handle error callback
  useEffect(() => {
    if (error && onError) {
      onError(error);
    }
  }, [error, onError]);

  // Store crosshair data per panel to merge values from all panels
  const panelCrosshairDataRef = useRef<Map<string, CrosshairData>>(new Map());

  // Handle crosshair move - synchronize across all panels and merge indicator values
  const handleCrosshairMove = useCallback(
    (data: CrosshairData | null, panelId?: string) => {
      if (!data) {
        setCrosshairData(null);
        panelCrosshairDataRef.current.clear();
        // Sync crosshair position to all panels
        panelRefs.current.forEach((ref) => {
          if (ref.current) {
            ref.current.syncCrosshair(null);
          }
        });
        return;
      }

      console.debug('📊 handleCrosshairMove called:', { 
        panelId, 
        time: data.time, 
        hasClose: !!data.close,
        indicatorCount: Object.keys(data.indicators || {}).length 
      });

      // Store crosshair data for this panel first
      if (panelId) {
        panelCrosshairDataRef.current.set(panelId, data);
      }

      // Sync crosshair position to all panels immediately
      if (data.time) {
        panelRefs.current.forEach((ref) => {
          if (ref.current) {
            ref.current.syncCrosshair(data.time!);
          }
        });
      }

      // Query indicator values from ALL panels at this time
      // This ensures we get values from all panels, not just the one being hovered
      const allIndicatorValues: Record<string, number> = {};
      
      // First, merge values from the current panel's data
      if (data.indicators) {
        Object.assign(allIndicatorValues, data.indicators);
      }
      
      // Then query from all panels
      panelRefs.current.forEach((ref, id) => {
        if (ref.current && data.time) {
          try {
            const panelValues = ref.current.getValuesAtTime(data.time);
            Object.assign(allIndicatorValues, panelValues);
          } catch (err) {
            // Panel might not be ready yet, skip it
          }
        }
      });

      // Also merge stored indicator values from panel crosshair events
      panelCrosshairDataRef.current.forEach((panelData) => {
        if (panelData.indicators) {
          Object.assign(allIndicatorValues, panelData.indicators);
        }
      });

      // Merge crosshair data from all panels
      // Start with current panel's data (OHLCV from main panel)
      const mergedData: CrosshairData = {
        time: data.time,
        // Preserve OHLCV from current data (typically from main panel)
        open: data.open,
        high: data.high,
        low: data.low,
        close: data.close,
        volume: data.volume,
        // Use merged indicator values from all panels
        indicators: allIndicatorValues,
      };

      // Fallback: if OHLCV is missing, try to get from stored panel data (main panel)
      if (!mergedData.open && panelCrosshairDataRef.current.has('main')) {
        const mainPanelData = panelCrosshairDataRef.current.get('main');
        if (mainPanelData) {
          mergedData.open = mainPanelData.open ?? mergedData.open;
          mergedData.high = mainPanelData.high ?? mergedData.high;
          mergedData.low = mainPanelData.low ?? mergedData.low;
          mergedData.close = mainPanelData.close ?? mergedData.close;
          mergedData.volume = mainPanelData.volume ?? mergedData.volume;
        }
      }

      // Update state immediately with merged data
      // Force a new object reference to ensure React detects the change
      const newCrosshairData: CrosshairData = {
        time: mergedData.time,
        open: mergedData.open,
        high: mergedData.high,
        low: mergedData.low,
        close: mergedData.close,
        volume: mergedData.volume,
        indicators: { ...mergedData.indicators }, // Create new object to ensure reference change
      };
      
      console.debug('✅ Setting crosshair data:', {
        time: newCrosshairData.time,
        close: newCrosshairData.close,
        indicatorCount: Object.keys(newCrosshairData.indicators).length
      });
      
      setCrosshairData(newCrosshairData);
    },
    []
  );

  // Handle visible range change - synchronize time axis across panels
  const handleVisibleRangeChange = useCallback(
    (range: { from: Time; to: Time }) => {
      // Sync visible range to all panels
      panelRefs.current.forEach((ref) => {
        if (ref.current) {
          ref.current.syncVisibleRange(range);
        }
      });
    },
    []
  );

  // Handle panel close
  const handlePanelClose = useCallback((panelId: string) => {
    // Find the panel being closed to check if it's an indicator panel
    setPanels((prevPanels) => {
      const panel = prevPanels.find((p) => p.id === panelId);
      
      // If it's an indicator panel (not main), remove the indicator from selection
      if (panel && panel.type === 'indicator' && panel.indicators && panel.indicators.length > 0) {
        const indicatorsToRemove = panel.indicators;
        
        // Remove indicators from selection
        if (onIndicatorsChange) {
          // Use a ref-based approach to get current indicators without dependency
          const currentIndicators = indicators;
          const newIndicators = currentIndicators.filter((indId) => !indicatorsToRemove.includes(indId));
          
          // Only update if there's actually a change
          if (newIndicators.length !== currentIndicators.length) {
            // Remove parameters for removed indicators
            const currentParameters = indicatorParameters;
            const newParameters = { ...currentParameters };
            indicatorsToRemove.forEach((indId) => {
              delete newParameters[indId];
            });
            
            console.log('🗑️ Removing indicators after panel close:', {
              panelId,
              removedIndicators: indicatorsToRemove,
              newIndicators,
              currentIndicators,
            });
            
            // Call immediately but use requestAnimationFrame to defer to next render cycle
            requestAnimationFrame(() => {
              onIndicatorsChange(newIndicators, newParameters);
            });
          }
        }
      }
      
      // Toggle panel visibility (or remove it completely)
      return togglePanelVisibility(prevPanels, panelId);
    });
    
    panelRefs.current.delete(panelId);
  }, [indicators, indicatorParameters, onIndicatorsChange]);

  // Handle panel resize
  const handlePanelResize = useCallback(
    (panelId: string, adjacentPanelId: string, deltaPercent: number) => {
      setPanels((prevPanels) => {
        const panel = prevPanels.find((p) => p.id === panelId);
        if (!panel) return prevPanels;

        const newHeightPercent = panel.heightPercent + deltaPercent;
        return resizePanel(prevPanels, panelId, newHeightPercent, adjacentPanelId);
      });
    },
    []
  );

  // Handle theme change
  useEffect(() => {
    setChartOptions((prev) => ({ ...prev, theme }));
  }, [theme]);

  // Handle height change
  useEffect(() => {
    setContainerHeight(height);
  }, [height]);

  useEffect(() => {
    setChartOptions((prev) => ({ ...prev, height: containerHeight }));
  }, [containerHeight]);

  // Handle chart type change
  const handleChartTypeChange = useCallback((newChartType: ChartOptions['chartType']) => {
    setChartOptions((prev) => ({ ...prev, chartType: newChartType }));
  }, []);

  // Handle add indicator
  const handleAddIndicator = useCallback(() => {
    setIndicatorSelectorOpen(true);
  }, []);

  // Handle indicator selected from selector
  const handleIndicatorSelected = useCallback(
    (indicatorId: string, parameters: Record<string, any>) => {
      console.log('➕ Indicator selected:', { indicatorId, parameters, currentIndicators: indicators });
      
      if (onIndicatorsChange) {
        const newIndicators = [...indicators, indicatorId];
        const newParameters = {
          ...indicatorParameters,
          [indicatorId]: parameters,
        };
        
        console.log('📤 Calling onIndicatorsChange:', { newIndicators, newParameters });
        onIndicatorsChange(newIndicators, newParameters);
      } else {
        console.warn('⚠️ onIndicatorsChange is not defined!');
      }
    },
    [indicators, indicatorParameters, onIndicatorsChange]
  );

  // Handle indicator parameter edit
  // Handle parameter save
  const handleParametersSaved = useCallback(
    (indicatorId: string, parameters: Record<string, any>) => {
      if (onIndicatorsChange) {
        const newParameters = {
          ...indicatorParameters,
          [indicatorId]: parameters,
        };
        onIndicatorsChange(indicators, newParameters);
      }
    },
    [indicators, indicatorParameters, onIndicatorsChange]
  );


  const handleResizeDrag = useCallback(
    (event: React.MouseEvent<HTMLDivElement>) => {
      event.preventDefault();
      const startY = event.clientY;
      const initialHeight = containerHeight;

      const handleMouseMove = (moveEvent: MouseEvent) => {
        const delta = moveEvent.clientY - startY;
        const nextHeight = Math.max(MIN_CHART_HEIGHT, initialHeight + delta);
        setContainerHeight(nextHeight);
      };

      const handleMouseUp = () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };

      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    },
    [containerHeight]
  );

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

  // Calculate panel heights
  const panelHeights = processedData
    ? calculatePanelPixelHeights(panels, containerHeight)
    : new Map<string, number>();

  // Render chart with multi-panel layout
  return (
    <Box
      sx={{
        position: 'relative',
        width: '100%',
        height: chartOptions.height,
        backgroundColor: theme === 'dark' ? '#131722' : '#FFFFFF',
        overflow: 'hidden',
      }}
    >
      {/* Asset Header - Top Left */}
      <AssetHeader
        assetType={assetType}
        identifier={identifier}
        onAssetChange={onAssetChange ? () => setAssetSelectorOpen(true) : undefined}
        theme={theme}
      />

      {/* Chart Toolbar */}
      {showToolbar && (
        <ChartToolbar
          chartType={chartOptions.chartType}
          onChartTypeChange={handleChartTypeChange}
          onAddIndicator={handleAddIndicator}
          theme={theme}
        />
      )}


      {/* Price Info Overlay - follows mouse cursor */}
      <PriceInfoOverlay
        crosshairData={crosshairData}
        data={processedData}
        visible={true}
        assetType={assetType}
        theme={theme}
      />

      {/* Multi-panel chart layout */}
      <Box
        sx={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {panels
          .filter((panel) => panel.visible)
          .sort((a, b) => a.order - b.order)
          .map((panel, index, visiblePanels) => {
            const panelHeight = panelHeights.get(panel.id) || 0;
            const panelRef = panelRefs.current.get(panel.id);
            const isLastPanel = index === visiblePanels.length - 1;
            const nextPanel = !isLastPanel ? visiblePanels[index + 1] : null;

            // Skip rendering if no processed data
            if (!processedData) {
              return null;
            }

            return (
              <React.Fragment key={panel.id}>
                <ChartPanel
                  ref={panelRef}
                  panel={panel}
                  data={processedData}
                  options={chartOptions}
                  height={panelHeight}
                  isResizable={panel.type !== 'main'}
                  showHeader={panel.type !== 'main'}
                  crosshairData={crosshairData}
                  onCrosshairMove={handleCrosshairMove}
                  onClose={handlePanelClose}
                  onVisibleRangeChange={
                    panel.type === 'main' ? handleVisibleRangeChange : undefined
                  }
                />

                {/* Add resizer between panels (except after last panel) */}
                {!isLastPanel && nextPanel && (
                  <PanelResizer
                    panelId={panel.id}
                    adjacentPanelId={nextPanel.id}
                    onResize={handlePanelResize}
                    theme={theme}
                    containerHeight={containerHeight}
                  />
                )}
              </React.Fragment>
            );
          })}
      </Box>

      {/* Indicator Selector Dialog */}
      <IndicatorSelector
        open={indicatorSelectorOpen}
        onClose={() => setIndicatorSelectorOpen(false)}
        onSelectIndicator={handleIndicatorSelected}
        selectedIndicators={indicators}
      />

      {/* Indicator Parameter Editor Dialog */}
      <IndicatorParameterEditor
        open={paramEditorOpen}
        indicatorId={editingIndicatorId}
        currentParameters={
          editingIndicatorId ? indicatorParameters[editingIndicatorId] || {} : {}
        }
        onClose={() => {
          setParamEditorOpen(false);
          setEditingIndicatorId(null);
        }}
        onSave={handleParametersSaved}
      />

      {/* Asset Selector Dialog */}
      {onAssetChange && (
        <AssetSelector
          open={assetSelectorOpen}
          onClose={() => setAssetSelectorOpen(false)}
          onSelectAsset={(newAssetType, newIdentifier) => {
            onAssetChange(newAssetType, newIdentifier);
            setAssetSelectorOpen(false);
          }}
          currentAssetType={assetType}
          currentIdentifier={identifier}
        />
      )}

      {/* Chart resize handle */}
      <Box
        sx={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          width: '100%',
          height: 12,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'ns-resize',
          zIndex: 120,
        }}
        onMouseDown={handleResizeDrag}
      >
        <Box
          sx={{
            width: 80,
            height: 4,
            borderRadius: 999,
            backgroundColor: theme === 'dark' ? '#2a2e39' : '#d0d4da',
          }}
        />
      </Box>
    </Box>
  );
};

export default TechnicalChartContainer;
