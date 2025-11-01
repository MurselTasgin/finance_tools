// TechnicalChart/components/ChartPanel.tsx
import React, {
  useEffect,
  useRef,
  useImperativeHandle,
  forwardRef,
  useState,
  useCallback,
  useMemo,
} from 'react';
import { createChart, IChartApi, CrosshairMode, Time, Logical } from 'lightweight-charts';
import { Box, Typography, IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import DragHandleIcon from '@mui/icons-material/DragHandle';
import {
  ChartPanel as ChartPanelType,
  ProcessedChartData,
  ChartOptions,
  CrosshairData,
} from '../types/chart.types';
import { getColorScheme } from '../utils/colorSchemes';
import { getIndicatorsForPanel } from '../utils/panelHelpers';

export interface ChartPanelProps {
  panel: ChartPanelType;
  data: ProcessedChartData;
  options: ChartOptions;
  height: number;
  isResizable?: boolean;
  showHeader?: boolean;
  crosshairData?: CrosshairData | null;
  onCrosshairMove?: (data: CrosshairData | null, panelId?: string) => void;
  onClose?: (panelId: string) => void;
  onVisibleRangeChange?: (range: { from: Time; to: Time }) => void;
}

export interface ChartPanelHandle {
  getChartApi: () => IChartApi | null;
  syncCrosshair: (time: Time | null) => void;
  syncVisibleRange: (range: { from: Time; to: Time }) => void;
  getValuesAtTime: (time: Time) => Record<string, number>;
}

const HEADER_HEIGHT = 32;

/**
 * Individual chart panel component
 * Each panel contains its own chart instance and can render price or indicators
 */
export const ChartPanel = forwardRef<ChartPanelHandle, ChartPanelProps>(
  (
    {
      panel,
      data,
      options,
      height,
      isResizable = true,
      showHeader = true,
      crosshairData = null,
      onCrosshairMove,
      onClose,
      onVisibleRangeChange,
    },
    ref
  ) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const seriesRefs = useRef<Map<string, any>>(new Map());
    const resizeObserverRef = useRef<ResizeObserver | null>(null);
    const [overlaySize, setOverlaySize] = useState<{ width: number; height: number }>({
      width: 0,
      height: 0,
    });

    const colorScheme = getColorScheme(options.theme);
    const chartAreaHeight = height - (showHeader ? HEADER_HEIGHT : 0);

    // Expose chart API and sync methods to parent
    useImperativeHandle(ref, () => ({
      getChartApi: () => chartRef.current,
      syncCrosshair: (time: Time | null) => {
        if (!chartRef.current) return;
        
        if (time) {
          // Find the first available series to sync crosshair position
          // This ensures the vertical line aligns correctly across all panels
          const firstSeries = seriesRefs.current.values().next().value;
          if (firstSeries) {
            // Use coordinate-based positioning for better alignment
            const timeScale = chartRef.current.timeScale();
            const coordinate = timeScale.timeToCoordinate(time);
            if (coordinate !== null && coordinate >= 0) {
              // Use coordinate for precise alignment
              chartRef.current.setCrosshairPosition(coordinate, time, firstSeries);
            } else {
              // Fallback to time-based positioning (coordinate might be out of view)
              chartRef.current.setCrosshairPosition(0, time, firstSeries);
            }
          }
        } else {
          chartRef.current.clearCrosshairPosition();
        }
      },
      syncVisibleRange: (range: { from: Time; to: Time }) => {
        if (chartRef.current) {
          chartRef.current.timeScale().setVisibleRange(range);
        }
      },
      // Method to get indicator values at a specific time from the processed data
      getValuesAtTime: (time: Time): Record<string, number> => {
        if (!data || !data.ohlcv || data.ohlcv.length === 0) return {};
        if (!chartRef.current) return {}; // Chart not ready yet
        
        const values: Record<string, number> = {};
        
        try {
        // Convert time to timestamp for comparison
          // Lightweight Charts uses Unix timestamps (seconds since epoch)
          let targetTimestamp: number;
          if (typeof time === 'number') {
            targetTimestamp = time;
          } else if (typeof time === 'string') {
            // Parse ISO string or other date formats
            const date = new Date(time);
            targetTimestamp = Math.floor(date.getTime() / 1000);
          } else {
            return values;
          }
          
          // Find the index in ohlcv that matches this time (or closest)
        let closestIndex = -1;
        let minDiff = Infinity;
        
        data.ohlcv.forEach((point, index) => {
            const pointTime = typeof point.time === 'number' ? point.time : 
                             new Date(point.time as string).getTime() / 1000;
            const diff = Math.abs(pointTime - targetTimestamp);
          if (diff < minDiff) {
            minDiff = diff;
            closestIndex = index;
          }
        });
        
          // Only use if we found a reasonably close match (within 1 day)
          if (closestIndex >= 0 && minDiff < 86400) {
            // Get indicator values for this panel
        const indicatorsForPanel = panel.type === 'main' 
          ? data.indicators.filter(ind => ind.type === 'overlay')
          : data.indicators.filter(ind => panel.indicators.includes(ind.id));
        
            // Extract values from indicator series at this index
        indicatorsForPanel.forEach(indicator => {
          indicator.series.forEach(series => {
            if (series.data && series.data.length > closestIndex) {
              const dataPoint = series.data[closestIndex];
                  
                  // Handle different data formats
                  if (dataPoint !== null && dataPoint !== undefined) {
                    if (typeof dataPoint === 'number') {
                      values[series.id] = dataPoint;
                    } else if (typeof dataPoint === 'object') {
                      if ('value' in dataPoint && typeof dataPoint.value === 'number') {
                values[series.id] = dataPoint.value;
                      } else if ('close' in dataPoint && typeof dataPoint.close === 'number') {
                        values[series.id] = dataPoint.close;
                      }
                    }
              }
            }
          });
        });
          }
        } catch (err) {
          console.debug(`Error in getValuesAtTime for panel ${panel.id}:`, err);
        }
        
        return values;
      },
    }), [data, panel.type, panel.indicators]);

    const updateOverlayDimensions = useCallback(() => {
      if (!containerRef.current) return;
      const { width, height: boundsHeight } = containerRef.current.getBoundingClientRect();
      setOverlaySize({ width, height: boundsHeight });
    }, []);

    // Initialize chart
    useEffect(() => {
      if (!containerRef.current) return;

      const hostElement = containerRef.current;
      const localSeriesRefs = seriesRefs.current;

      const chart = createChart(hostElement, {
        width: containerRef.current.clientWidth,
        height: chartAreaHeight,
        layout: {
          background: { color: colorScheme.background },
          textColor: colorScheme.text,
        },
        grid: {
          vertLines: { visible: options.showGrid, color: colorScheme.grid },
          horzLines: { visible: options.showGrid, color: colorScheme.grid },
        },
        crosshair: {
          mode: CrosshairMode.Normal, // Always enable crosshair for mouse tracking
          vertLine: {
            color: colorScheme.crosshair,
            width: 1,
            style: options.showCrosshair ? 3 : 0, // Visible or hidden based on option
            labelBackgroundColor: colorScheme.crosshair,
          },
          horzLine: {
            color: colorScheme.crosshair,
            width: 1,
            style: options.showCrosshair ? 3 : 0, // Visible or hidden based on option
            labelBackgroundColor: colorScheme.crosshair,
          },
        },
        rightPriceScale: {
          visible: options.showPriceScale,
          borderColor: colorScheme.grid,
          entireTextOnly: false,
          scaleMargins: {
            top: 0.1,
            bottom: 0.1,
          },
        },
        timeScale: {
          visible: panel.type === 'main' ? options.showTimeScale : false,
          borderColor: colorScheme.grid,
          timeVisible: true,
          secondsVisible: false,
        },
        handleScroll: {
          mouseWheel: true,
          pressedMouseMove: true,
          horzTouchDrag: true,
          vertTouchDrag: false,
        },
        handleScale: {
          axisPressedMouseMove: true,
          mouseWheel: true,
          pinch: true,
        },
      });

      chartRef.current = chart;
      updateOverlayDimensions();

      // Setup crosshair move handler
      chart.subscribeCrosshairMove((param) => {
        if (!onCrosshairMove) return;
        
        if (!param || !param.time) {
            onCrosshairMove(null, panel.id);
          return;
        }

        const paramData = param as any;
        const crosshairData: CrosshairData = {
          time: param.time,
          indicators: {},
        };
        
        // Debug: log crosshair events
        if (panel.type === 'main') {
          console.debug('🔍 Crosshair move on main panel:', {
            time: param.time,
            hasSeriesData: !!paramData.seriesData,
            seriesCount: seriesRefs.current.size
          });
        }

        if (paramData.seriesData) {
          const extractedIndicators: string[] = [];
          seriesRefs.current.forEach((series, seriesId) => {
            try {
            const value = paramData.seriesData.get(series);
              if (value !== undefined && value !== null) {
              if (typeof value === 'number') {
                // Direct numeric value - check if it's the price series
                  if (seriesId === 'price' || seriesId.startsWith('price_')) {
                  // This is the main price series (for ETFs and line charts)
                    if (crosshairData.close === undefined) {
                  crosshairData.close = value;
                    }
                  } else if (seriesId === 'volume') {
                    // Volume series
                    crosshairData.volume = value;
                } else {
                    // Indicator series
                  crosshairData.indicators[seriesId] = value;
                }
              } else if (typeof value === 'object') {
                  if ('close' in value && typeof value.close === 'number') {
                  // OHLCV data (candlestick/bar for stocks)
                    if (crosshairData.open === undefined) crosshairData.open = value.open;
                    if (crosshairData.high === undefined) crosshairData.high = value.high;
                    if (crosshairData.low === undefined) crosshairData.low = value.low;
                    if (crosshairData.close === undefined) crosshairData.close = value.close;
                    if ('volume' in value && value.volume !== undefined && crosshairData.volume === undefined) {
                    crosshairData.volume = value.volume;
                  }
                } else if ('value' in value && typeof value.value === 'number') {
                  // Line data point with value property
                    if (seriesId === 'price' || seriesId.startsWith('price_')) {
                    // This is the main price series (for ETFs using line/area charts)
                      if (crosshairData.close === undefined) {
                    crosshairData.close = value.value;
                      }
                    } else if (seriesId === 'volume') {
                      // Volume series
                      crosshairData.volume = value.value;
                  } else {
                    // Indicator series
                    crosshairData.indicators[seriesId] = value.value;
                      extractedIndicators.push(seriesId);
                  }
                }
              }
            }
            } catch (err) {
              // Skip this series if there's an error
              console.debug(`Error getting value for series ${seriesId}:`, err);
            }
          });

          if (panel.type === 'main' && extractedIndicators.length > 0) {
            console.debug('🔍 Main panel extracted indicators:', extractedIndicators);
          }
        } else {
          if (panel.type === 'main') {
            console.debug('⚠️ Main panel: No seriesData in crosshair param');
          }
        }

        // Always call onCrosshairMove with current data (even if empty indicators)
        // This ensures the parent knows about the crosshair position
        console.debug(`📊 Panel ${panel.id} calling onCrosshairMove:`, {
          time: crosshairData.time,
          hasClose: !!crosshairData.close,
          indicatorCount: Object.keys(crosshairData.indicators).length,
          indicatorIds: Object.keys(crosshairData.indicators)
        });
          onCrosshairMove(crosshairData, panel.id);
      });

      // Setup visible range change handler
      if (panel.type === 'main' && onVisibleRangeChange) {
        chart.timeScale().subscribeVisibleLogicalRangeChange(() => {
          const timeRange = chart.timeScale().getVisibleRange();
          if (timeRange) {
            onVisibleRangeChange(timeRange);
          }
        });
      }

      // Setup resize observer
      const resizeObserver = new ResizeObserver((entries) => {
        if (entries.length === 0 || entries[0].target !== containerRef.current) return;
        const { width } = entries[0].contentRect;
        chart.applyOptions({ width, height: chartAreaHeight });
        setOverlaySize({ width, height: chartAreaHeight });
      });

      resizeObserver.observe(hostElement);
      resizeObserverRef.current = resizeObserver;

      return () => {
        resizeObserver.disconnect();
        chart.remove();
        chartRef.current = null;
        localSeriesRefs.clear();
      };
    }, [
      chartAreaHeight,
      colorScheme.background,
      colorScheme.crosshair,
      colorScheme.grid,
      colorScheme.text,
      onCrosshairMove,
      onVisibleRangeChange,
      options.showCrosshair,
      options.showGrid,
      options.showPriceScale,
      options.showTimeScale,
      panel.type,
      panel.id,
      updateOverlayDimensions,
    ]);

    // Update chart options when theme changes
    useEffect(() => {
      if (!chartRef.current) return;

      chartRef.current.applyOptions({
        layout: {
          background: { color: colorScheme.background },
          textColor: colorScheme.text,
        },
        grid: {
          vertLines: { visible: options.showGrid, color: colorScheme.grid },
          horzLines: { visible: options.showGrid, color: colorScheme.grid },
        },
      });
    }, [colorScheme.background, colorScheme.grid, colorScheme.text, options.showGrid]);

    // Update chart height
    useEffect(() => {
      if (!chartRef.current) return;
      chartRef.current.applyOptions({
        height: chartAreaHeight,
      });
      setOverlaySize((prev) => ({
        ...prev,
        height: chartAreaHeight,
      }));
    }, [chartAreaHeight]);

    const getPrimarySeries = useCallback(() => {
      if (seriesRefs.current.has('price')) {
        return seriesRefs.current.get('price');
      }

      const iterator = seriesRefs.current.values();
      const first = iterator.next();
      return first.value ?? null;
    }, []);

    // Render series based on panel type
    useEffect(() => {
      if (!chartRef.current || !data || data.ohlcv.length === 0) return;

      const chart = chartRef.current;

      seriesRefs.current.forEach((series) => chart.removeSeries(series));
      seriesRefs.current.clear();

      if (panel.type === 'main') {
        if (data.hasOHLC && options.chartType === 'candlestick') {
          const candlestickSeries = (chart as any).addCandlestickSeries({
            upColor: colorScheme.upColor,
            downColor: colorScheme.downColor,
            wickUpColor: colorScheme.wickUpColor,
            wickDownColor: colorScheme.wickDownColor,
            borderUpColor: colorScheme.borderUpColor,
            borderDownColor: colorScheme.borderDownColor,
            lastValueVisible: false,
          });
          candlestickSeries.setData(data.ohlcv);
          seriesRefs.current.set('price', candlestickSeries);
        } else {
          const lineData = data.ohlcv.map((d) => ({ time: d.time, value: d.close }));

          if (options.chartType === 'area') {
            const areaSeries = (chart as any).addAreaSeries({
              lineColor: colorScheme.upColor,
              topColor: `${colorScheme.upColor}80`,
              bottomColor: `${colorScheme.upColor}10`,
              lineWidth: 2,
              lastValueVisible: false,
            });
            areaSeries.setData(lineData);
            seriesRefs.current.set('price', areaSeries);
          } else {
            const lineSeries = (chart as any).addLineSeries({
              color: colorScheme.upColor,
              lineWidth: 2,
              lastValueVisible: false,
            });
            lineSeries.setData(lineData);
            seriesRefs.current.set('price', lineSeries);
          }
        }

        if (data.volume && data.volume.length > 0 && options.showVolume) {
          const volumeSeries = (chart as any).addHistogramSeries({
            color: colorScheme.volumeColor,
            priceFormat: {
              type: 'volume',
            },
            priceScaleId: 'volume',
            lastValueVisible: false,
          });

          const volumeData = data.volume.map((v, index) => {
            let color = colorScheme.volumeColor;
            if (index > 0 && data.ohlcv[index] && data.ohlcv[index - 1]) {
              color =
                data.ohlcv[index].close >= data.ohlcv[index - 1].close
                  ? colorScheme.volumeUpColor
                  : colorScheme.volumeDownColor;
            }
            return { ...v, color };
          });

          volumeSeries.setData(volumeData);
          seriesRefs.current.set('volume', volumeSeries);

          chart.priceScale('volume').applyOptions({
            scaleMargins: {
              top: 0.8,
              bottom: 0,
            },
          });
        }

        const overlayIndicators = getIndicatorsForPanel(panel, data.indicators);
        overlayIndicators.forEach((indicator) => {
          indicator.series.forEach((series) => {
            if (!series.visible) return;

            if (series.type === 'line') {
              const lineSeries = (chart as any).addLineSeries({
                color: series.color,
                lineWidth: 2,
                title: series.name,
                lastValueVisible: false,
              });
              lineSeries.setData(series.data as any);
              // Explicitly disable last value visibility after data is set
              lineSeries.applyOptions({ 
                lastValueVisible: false,
                priceLineVisible: false,
              });
              seriesRefs.current.set(series.id, lineSeries);
            } else if (series.type === 'area') {
              const areaSeries = (chart as any).addAreaSeries({
                lineColor: series.color,
                topColor: `${series.color}40`,
                bottomColor: `${series.color}10`,
                lineWidth: 1,
                title: series.name,
                lastValueVisible: false,
              });
              areaSeries.setData(series.data as any);
              // Explicitly disable last value visibility after data is set
              areaSeries.applyOptions({ 
                lastValueVisible: false,
                priceLineVisible: false,
              });
              seriesRefs.current.set(series.id, areaSeries);
            }
          });
        });
      } else {
        const indicators = getIndicatorsForPanel(panel, data.indicators);
        
        // Debug logging for ETF indicators
        if (panel.indicators.some(id => id === 'number_of_shares' || id === 'number_of_investors')) {
          console.log(`📊 Rendering panel ${panel.id} with indicators:`, {
            panelId: panel.id,
            panelIndicators: panel.indicators,
            foundIndicators: indicators.map(ind => ({
              id: ind.id,
              name: ind.name,
              seriesCount: ind.series.length
            })),
            allIndicatorsInData: data.indicators.map(ind => ind.id)
          });
        }

        indicators.forEach((indicator) => {
          indicator.series.forEach((series) => {
            if (!series.visible) return;

            if (series.type === 'line') {
              const lineSeries = (chart as any).addLineSeries({
                color: series.color,
                lineWidth: 2,
                title: series.name,
                lastValueVisible: false,
              });
              lineSeries.setData(series.data as any);
              // Explicitly disable last value visibility after data is set
              lineSeries.applyOptions({ 
                lastValueVisible: false,
                priceLineVisible: false,
              });
              seriesRefs.current.set(series.id, lineSeries);
            } else if (series.type === 'histogram') {
              const histogramSeries = (chart as any).addHistogramSeries({
                color: series.color,
                title: series.name,
                lastValueVisible: false,
              });
              histogramSeries.setData(series.data as any);
              // Explicitly disable last value visibility after data is set
              histogramSeries.applyOptions({ 
                lastValueVisible: false,
                priceLineVisible: false,
              });
              seriesRefs.current.set(series.id, histogramSeries);
            } else if (series.type === 'area') {
              const areaSeries = (chart as any).addAreaSeries({
                lineColor: series.color,
                topColor: `${series.color}40`,
                bottomColor: `${series.color}10`,
                lineWidth: 2,
                title: series.name,
                lastValueVisible: false,
              });
              areaSeries.setData(series.data as any);
              // Explicitly disable last value visibility after data is set
              areaSeries.applyOptions({ 
                lastValueVisible: false,
                priceLineVisible: false,
              });
              seriesRefs.current.set(series.id, areaSeries);
            }
          });
        });
      }

      chart.timeScale().fitContent();
    }, [chartAreaHeight, colorScheme, data, options.chartType, options.showVolume, panel]);


    return (
      <Box
        sx={{
          width: '100%',
          height,
          position: 'relative',
          borderBottom: panel.type !== 'main' ? `1px solid ${colorScheme.grid}` : 'none',
        }}
      >
        {showHeader && (
          <Box
            sx={{
              height: HEADER_HEIGHT,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              px: 1,
              backgroundColor: colorScheme.background,
              borderBottom: `1px solid ${colorScheme.grid}`,
            }}
          >
            <Typography
              variant="caption"
              sx={{
                color: colorScheme.text,
                fontWeight: 500,
                fontSize: '0.75rem',
              }}
            >
              {panel.title}
            </Typography>

            <Box sx={{ display: 'flex', gap: 0.5 }}>
              {isResizable && panel.type !== 'main' && (
                <IconButton
                  size="small"
                  sx={{
                    padding: 0.25,
                    color: colorScheme.text,
                    cursor: 'ns-resize',
                  }}
                >
                  <DragHandleIcon fontSize="small" />
                </IconButton>
              )}

              {panel.type !== 'main' && onClose && (
                <IconButton
                  size="small"
                  onClick={() => onClose(panel.id)}
                  sx={{
                    padding: 0.25,
                    color: colorScheme.text,
                    '&:hover': {
                      color: colorScheme.downColor,
                    },
                  }}
                >
                  <CloseIcon fontSize="small" />
                </IconButton>
              )}
            </Box>
          </Box>
        )}

        <Box
          sx={{
            width: '100%',
            height: chartAreaHeight,
            position: 'relative',
            backgroundColor: colorScheme.background,
          }}
        >
          <Box
            ref={containerRef}
            sx={{
              width: '100%',
              height: '100%',
            }}
          />


        </Box>
      </Box>
    );
  }
);

ChartPanel.displayName = 'ChartPanel';

export default ChartPanel;
