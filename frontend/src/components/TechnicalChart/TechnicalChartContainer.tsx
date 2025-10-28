// TechnicalChart/TechnicalChartContainer.tsx
import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Box, CircularProgress, Alert, Paper } from '@mui/material';
import { Time } from 'lightweight-charts';
import { ChartPanel, ChartPanelHandle } from './components/ChartPanel';
import { ChartLegend } from './components/ChartLegend';
import { PanelResizer } from './components/PanelResizer';
import { ChartToolbar } from './components/ChartToolbar';
import { IndicatorSelector } from './components/IndicatorSelector';
import { IndicatorParameterEditor } from './components/IndicatorParameterEditor';
import { useChartData } from './hooks/useChartData';
import {
  TechnicalChartContainerProps,
  CrosshairData,
  ChartOptions,
  ChartPanel as ChartPanelType,
  DrawingTool,
  ChartDrawing,
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
  const [activeDrawingTool, setActiveDrawingTool] = useState<DrawingTool | null>(null);
  const [panelDrawings, setPanelDrawings] = useState<Record<string, ChartDrawing[]>>({});

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
      const initialPanels = createInitialPanels(processedData);
      setPanels(initialPanels);

      // Create refs for each panel
      panelRefs.current.clear();
      initialPanels.forEach((panel) => {
        if (!panelRefs.current.has(panel.id)) {
          panelRefs.current.set(panel.id, React.createRef<ChartPanelHandle>());
        }
      });

      // Initialize drawings map for panels
      setPanelDrawings((prev) => {
        const updated: Record<string, ChartDrawing[]> = {};
        initialPanels.forEach((panel) => {
          updated[panel.id] = prev[panel.id] || [];
        });
        return updated;
      });
    }
  }, [processedData]);

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

  // Handle crosshair move - synchronize across all panels
  const handleCrosshairMove = useCallback(
    (data: CrosshairData | null) => {
      setCrosshairData(data);

      // Sync crosshair position to all panels
      if (data && data.time) {
        panelRefs.current.forEach((ref, panelId) => {
          if (ref.current) {
            ref.current.syncCrosshair(data.time);
          }
        });
      } else {
        panelRefs.current.forEach((ref) => {
          if (ref.current) {
            ref.current.syncCrosshair(null);
          }
        });
      }
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
    setPanels((prevPanels) => togglePanelVisibility(prevPanels, panelId));
    panelRefs.current.delete(panelId);

    setPanelDrawings((prev) => {
      if (!prev[panelId]) return prev;
      const updated = { ...prev };
      delete updated[panelId];
      return updated;
    });
  }, []);

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
      if (onIndicatorsChange) {
        const newIndicators = [...indicators, indicatorId];
        const newParameters = {
          ...indicatorParameters,
          [indicatorId]: parameters,
        };
        onIndicatorsChange(newIndicators, newParameters);
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

  const handleDrawingToolChange = useCallback((tool: DrawingTool | null) => {
    setActiveDrawingTool(tool);
  }, []);

  const handleDrawingCreate = useCallback((panelId: string, drawing: ChartDrawing) => {
    setPanelDrawings((prev) => {
      const existing = prev[panelId] || [];
      return {
        ...prev,
        [panelId]: [...existing, drawing],
      };
    });
  }, []);

  const handleDrawingUpdate = useCallback(
    (panelId: string, drawingId: string, nextDrawing: ChartDrawing) => {
      setPanelDrawings((prev) => {
        const existing = prev[panelId] || [];
        const index = existing.findIndex((d) => d.id === drawingId);
        if (index === -1) return prev;
        const updated = [...existing];
        updated[index] = nextDrawing;
        return {
          ...prev,
          [panelId]: updated,
        };
      });
    },
    []
  );

  const handleDrawingDelete = useCallback((panelId: string, drawingId: string) => {
    setPanelDrawings((prev) => {
      const existing = prev[panelId];
      if (!existing) return prev;
      return {
        ...prev,
        [panelId]: existing.filter((drawing) => drawing.id !== drawingId),
      };
    });
  }, []);

  const handleClearDrawings = useCallback(() => {
    setPanelDrawings((prev) => {
      const cleared: Record<string, ChartDrawing[]> = {};
      Object.keys(prev).forEach((panelId) => {
        cleared[panelId] = [];
      });
      return cleared;
    });
  }, []);

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
      {/* Chart Toolbar */}
      {showToolbar && (
        <ChartToolbar
          chartType={chartOptions.chartType}
          onChartTypeChange={handleChartTypeChange}
          onAddIndicator={handleAddIndicator}
          activeDrawingTool={activeDrawingTool}
          onDrawingToolChange={handleDrawingToolChange}
          onClearDrawings={handleClearDrawings}
          theme={theme}
        />
      )}

      {/* Legend overlay */}
      <ChartLegend
        identifier={identifier}
        data={processedData}
        crosshairData={crosshairData}
        showIndicators={true}
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

            return (
              <React.Fragment key={panel.id}>
                <ChartPanel
                  ref={panelRef}
                  panel={panel}
                  data={processedData!}
                  options={chartOptions}
                  height={panelHeight}
                  isResizable={panel.type !== 'main'}
                  showHeader={panel.type !== 'main'}
                  onCrosshairMove={handleCrosshairMove}
                  onClose={handlePanelClose}
                  onVisibleRangeChange={
                    panel.type === 'main' ? handleVisibleRangeChange : undefined
                  }
                  activeDrawingTool={panel.type === 'main' ? activeDrawingTool : null}
                  drawings={panelDrawings[panel.id] || []}
                  onDrawingCreate={handleDrawingCreate}
                  onDrawingUpdate={handleDrawingUpdate}
                  onDrawingDelete={handleDrawingDelete}
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
