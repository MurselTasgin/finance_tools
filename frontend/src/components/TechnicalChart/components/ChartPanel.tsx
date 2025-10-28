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
  DrawingTool,
  ChartDrawing,
  DrawingPoint,
  ScreenPoint,
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
  onCrosshairMove?: (data: CrosshairData | null) => void;
  onClose?: (panelId: string) => void;
  onVisibleRangeChange?: (range: { from: Time; to: Time }) => void;
  activeDrawingTool?: DrawingTool | null;
  drawings?: ChartDrawing[];
  onDrawingCreate?: (panelId: string, drawing: ChartDrawing) => void;
  onDrawingUpdate?: (panelId: string, drawingId: string, drawing: ChartDrawing) => void;
  onDrawingDelete?: (panelId: string, drawingId: string) => void;
}

export interface ChartPanelHandle {
  getChartApi: () => IChartApi | null;
  syncCrosshair: (time: Time | null) => void;
  syncVisibleRange: (range: { from: Time; to: Time }) => void;
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
      onCrosshairMove,
      onClose,
      onVisibleRangeChange,
      activeDrawingTool = null,
      drawings = [],
      onDrawingCreate,
      onDrawingUpdate: _onDrawingUpdate,
      onDrawingDelete: _onDrawingDelete,
    },
    ref
  ) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const seriesRefs = useRef<Map<string, any>>(new Map());
    const resizeObserverRef = useRef<ResizeObserver | null>(null);
    const overlayRef = useRef<SVGSVGElement | null>(null);
    const activePointerIdRef = useRef<number | null>(null);
    const pointerHasMovedRef = useRef<boolean>(false);
    const lastPointerPointRef = useRef<DrawingPoint | null>(null);
    const lastPointerScreenPointRef = useRef<ScreenPoint | null>(null);

    const [draftDrawing, setDraftDrawing] = useState<ChartDrawing | null>(null);
    const [overlaySize, setOverlaySize] = useState<{ width: number; height: number }>({
      width: 0,
      height: 0,
    });

    const colorScheme = getColorScheme(options.theme);
    const chartAreaHeight = height - (showHeader ? HEADER_HEIGHT : 0);
    const isMainPanel = panel.type === 'main';

    const primaryDrawingColor = colorScheme.crosshair;

    // Expose chart API and sync methods to parent
    useImperativeHandle(ref, () => ({
      getChartApi: () => chartRef.current,
      syncCrosshair: (time: Time | null) => {
        if (chartRef.current && time) {
          const firstSeries = seriesRefs.current.values().next().value;
          chartRef.current.setCrosshairPosition(0, time, firstSeries);
        } else if (chartRef.current) {
          chartRef.current.clearCrosshairPosition();
        }
      },
      syncVisibleRange: (range: { from: Time; to: Time }) => {
        if (chartRef.current) {
          chartRef.current.timeScale().setVisibleRange(range);
        }
      },
    }));

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
          mode: options.showCrosshair ? CrosshairMode.Normal : CrosshairMode.Hidden,
          vertLine: {
            color: colorScheme.crosshair,
            width: 1,
            style: 3,
            labelBackgroundColor: colorScheme.crosshair,
          },
          horzLine: {
            color: colorScheme.crosshair,
            width: 1,
            style: 3,
            labelBackgroundColor: colorScheme.crosshair,
          },
        },
        rightPriceScale: {
          visible: options.showPriceScale,
          borderColor: colorScheme.grid,
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
        if (!param || !param.time || !onCrosshairMove) {
          if (onCrosshairMove) {
            onCrosshairMove(null);
          }
          return;
        }

        const paramData = param as any;
        const crosshairData: CrosshairData = {
          time: param.time,
          indicators: {},
        };

        if (paramData.seriesData) {
          seriesRefs.current.forEach((series, seriesId) => {
            const value = paramData.seriesData.get(series);
            if (value !== undefined) {
              if (typeof value === 'number') {
                crosshairData.indicators[seriesId] = value;
              } else if (typeof value === 'object' && 'close' in value) {
                crosshairData.open = value.open;
                crosshairData.high = value.high;
                crosshairData.low = value.low;
                crosshairData.close = value.close;
              }
            }
          });
        }

        onCrosshairMove(crosshairData);
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
            });
            areaSeries.setData(lineData);
            seriesRefs.current.set('price', areaSeries);
          } else {
            const lineSeries = (chart as any).addLineSeries({
              color: colorScheme.upColor,
              lineWidth: 2,
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
              });
              lineSeries.setData(series.data as any);
              seriesRefs.current.set(series.id, lineSeries);
            } else if (series.type === 'area') {
              const areaSeries = (chart as any).addAreaSeries({
                lineColor: series.color,
                topColor: `${series.color}40`,
                bottomColor: `${series.color}10`,
                lineWidth: 1,
                title: series.name,
              });
              areaSeries.setData(series.data as any);
              seriesRefs.current.set(series.id, areaSeries);
            }
          });
        });
      } else {
        const indicators = getIndicatorsForPanel(panel, data.indicators);

        indicators.forEach((indicator) => {
          indicator.series.forEach((series) => {
            if (!series.visible) return;

            if (series.type === 'line') {
              const lineSeries = (chart as any).addLineSeries({
                color: series.color,
                lineWidth: 2,
                title: series.name,
              });
              lineSeries.setData(series.data as any);
              seriesRefs.current.set(series.id, lineSeries);
            } else if (series.type === 'histogram') {
              const histogramSeries = (chart as any).addHistogramSeries({
                color: series.color,
                title: series.name,
              });
              histogramSeries.setData(series.data as any);
              seriesRefs.current.set(series.id, histogramSeries);
            } else if (series.type === 'area') {
              const areaSeries = (chart as any).addAreaSeries({
                lineColor: series.color,
                topColor: `${series.color}40`,
                bottomColor: `${series.color}10`,
                lineWidth: 2,
                title: series.name,
              });
              areaSeries.setData(series.data as any);
              seriesRefs.current.set(series.id, areaSeries);
            }
          });
        });
      }

      chart.timeScale().fitContent();
    }, [chartAreaHeight, colorScheme, data, options.chartType, options.showVolume, panel]);

    // Drawing helpers
    const getRequiredPoints = useCallback((tool: DrawingTool | null) => {
      switch (tool) {
        case 'horizontal-line':
        case 'vertical-line':
          return 1;
        case 'parallel-channel':
          return 3;
        case 'trendline':
        default:
          return 2;
      }
    }, []);

    const coordinateToPoint = useCallback(
      (x: number, y: number) => {
        if (!chartRef.current) return null;
        const timeScale = chartRef.current.timeScale();
        const time = timeScale.coordinateToTime(x);
        const logical = timeScale.coordinateToLogical(x) as Logical | null;
        const series = getPrimarySeries();
        if (!series || time === null || logical === null) return null;
        const price = series.priceScale().coordinateToPrice(y);
        if (price === null || price === undefined) return null;
        return { time, price: price as number, logical };
      },
      [getPrimarySeries]
    );

    const finalizeDrawing = useCallback(
      (draft: ChartDrawing): ChartDrawing => {
        const id = `${panel.id}-${draft.type}-${Date.now()}-${Math.random()
          .toString(36)
          .slice(2, 7)}`;
        return {
          ...draft,
          id,
          panelId: panel.id,
          color: draft.color ?? primaryDrawingColor,
          secondaryColor: draft.secondaryColor ?? `${primaryDrawingColor}66`,
          lineWidth: draft.lineWidth ?? 2,
          opacity: draft.opacity ?? 0.9,
        };
      },
      [panel.id, primaryDrawingColor]
    );

    const resetDraft = useCallback(() => {
      setDraftDrawing(null);
    }, []);

    useEffect(() => {
      resetDraft();
    }, [activeDrawingTool, resetDraft]);

    const handlePointerDown = useCallback(
      (event: React.PointerEvent<SVGSVGElement>) => {
        if (!isMainPanel || !activeDrawingTool) return;
        event.preventDefault();
        event.stopPropagation();
        const svg = overlayRef.current;
        if (!svg) return;
        const rect = svg.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        const point = coordinateToPoint(x, y);
        if (!point) return;

        const pointerId = event.pointerId;
        const requiredPoints = getRequiredPoints(activeDrawingTool);
        const screenPoint: ScreenPoint = { x, y };

        setDraftDrawing((current) => {
          if (!current || current.type !== activeDrawingTool) {
            const nextDraft: ChartDrawing = {
              id: `draft-${activeDrawingTool}-${Date.now()}`,
              type: activeDrawingTool,
              points: [point],
              screenPoints: [screenPoint],
              color: primaryDrawingColor,
              secondaryColor: `${primaryDrawingColor}66`,
              lineWidth: 2,
              opacity: 0.85,
            };

            if (requiredPoints === 1) {
              const finalDrawing = finalizeDrawing(nextDraft);
              onDrawingCreate?.(panel.id, finalDrawing);
              return null;
            }

            svg.setPointerCapture(pointerId);
            activePointerIdRef.current = pointerId;
            pointerHasMovedRef.current = false;
            lastPointerPointRef.current = point;
            lastPointerScreenPointRef.current = screenPoint;
            return nextDraft;
          }

          const nextPoints = [...current.points, point];
          const nextScreenPoints = [...(current.screenPoints ?? []), screenPoint];
          if (nextPoints.length >= requiredPoints) {
            const readyDraft: ChartDrawing = {
              ...current,
              points: nextPoints,
              screenPoints: nextScreenPoints,
            };
            const finalDrawing = finalizeDrawing(readyDraft);
            onDrawingCreate?.(panel.id, finalDrawing);
            activePointerIdRef.current = null;
            pointerHasMovedRef.current = false;
            lastPointerPointRef.current = null;
            lastPointerScreenPointRef.current = null;
            return null;
          }

          svg.setPointerCapture(pointerId);
          activePointerIdRef.current = pointerId;
          pointerHasMovedRef.current = false;
          lastPointerPointRef.current = point;
          lastPointerScreenPointRef.current = screenPoint;
          return {
            ...current,
            points: nextPoints,
            screenPoints: nextScreenPoints,
          };
        });
      },
      [
        activeDrawingTool,
        coordinateToPoint,
        finalizeDrawing,
        getRequiredPoints,
        isMainPanel,
        onDrawingCreate,
        panel.id,
        primaryDrawingColor,
      ]
    );

    const handlePointerMove = useCallback(
      (event: React.PointerEvent<SVGSVGElement>) => {
        if (!activeDrawingTool || !isMainPanel) return;
        if (
          activePointerIdRef.current !== null &&
          activePointerIdRef.current !== event.pointerId
        ) {
          return;
        }

        setDraftDrawing((current) => {
          if (!current || current.type !== activeDrawingTool) return current;
          const svg = overlayRef.current;
          event.preventDefault();
          event.stopPropagation();
          if (!svg) return current;
          const rect = svg.getBoundingClientRect();
          const x = event.clientX - rect.left;
          const y = event.clientY - rect.top;
          const point = coordinateToPoint(x, y);
          if (!point) return current;

          pointerHasMovedRef.current = true;
          lastPointerPointRef.current = point;
          lastPointerScreenPointRef.current = { x, y };

          const requiredPoints = getRequiredPoints(activeDrawingTool);
          const points = [...current.points];
          const screenPoints = [...(current.screenPoints ?? [])];

          if (points.length === 1 && requiredPoints >= 2) {
            points[1] = point;
            screenPoints[1] = { x, y };
          } else if (points.length >= 2) {
            points[points.length - 1] = point;
            screenPoints[screenPoints.length - 1] = { x, y };
          }

          return {
            ...current,
            points,
            screenPoints,
          };
        });
      },
      [activeDrawingTool, coordinateToPoint, getRequiredPoints, isMainPanel]
    );

    const finalizeTwoPointDraft = useCallback(
      (point: DrawingPoint | null, screenPoint: ScreenPoint | null) => {
        setDraftDrawing((current) => {
          if (!current || !activeDrawingTool) return current;
          const requiredPoints = getRequiredPoints(activeDrawingTool);
          if (requiredPoints !== 2 || current.points.length === 0) {
            return current;
          }

          const lastPoint = point ?? lastPointerPointRef.current;
          const fallbackScreen = screenPoint ?? lastPointerScreenPointRef.current;
          if (!lastPoint || !fallbackScreen) {
            return current;
          }

          const nextPoints =
            current.points.length === 1
              ? [current.points[0], lastPoint]
              : [...current.points.slice(0, 1), lastPoint];
          const existingScreens = current.screenPoints ?? [];
          const nextScreenPoints =
            existingScreens.length === 1
              ? [existingScreens[0], fallbackScreen]
              : [...existingScreens.slice(0, 1), fallbackScreen];

          const readyDraft: ChartDrawing = {
            ...current,
            points: nextPoints,
            screenPoints: nextScreenPoints,
          };
          const finalDrawing = finalizeDrawing(readyDraft);
          onDrawingCreate?.(panel.id, finalDrawing);
          return null;
        });
      },
      [activeDrawingTool, finalizeDrawing, getRequiredPoints, onDrawingCreate, panel.id]
    );

    const handlePointerUp = useCallback(
      (event: React.PointerEvent<SVGSVGElement>) => {
        const pointerId = event.pointerId;
        if (
          activePointerIdRef.current !== null &&
          activePointerIdRef.current !== pointerId
        ) {
          return;
        }

        const svg = overlayRef.current;
        event.preventDefault();
        event.stopPropagation();
        if (svg && svg.hasPointerCapture(pointerId)) {
          svg.releasePointerCapture(pointerId);
        }

        const rect = svg?.getBoundingClientRect();
        let point: DrawingPoint | null = null;
        let screenPoint: ScreenPoint | null = null;
        if (rect) {
          point = coordinateToPoint(event.clientX - rect.left, event.clientY - rect.top);
          screenPoint = {
            x: event.clientX - rect.left,
            y: event.clientY - rect.top,
          };
        }

        if (pointerHasMovedRef.current) {
          finalizeTwoPointDraft(point, screenPoint);
        }

        activePointerIdRef.current = null;
        pointerHasMovedRef.current = false;
        lastPointerPointRef.current = null;
        lastPointerScreenPointRef.current = null;
      },
      [coordinateToPoint, finalizeTwoPointDraft]
    );

    const handlePointerLeave = useCallback((event: React.PointerEvent<SVGSVGElement>) => {
      event.preventDefault();
      event.stopPropagation();
    }, []);

    useEffect(() => {
      const chart = chartRef.current;
      if (!chart) return;

      const disabled = Boolean(activeDrawingTool);
      chart.applyOptions({
        handleScroll: {
          mouseWheel: !disabled,
          pressedMouseMove: !disabled,
          horzTouchDrag: !disabled,
          vertTouchDrag: !disabled,
        },
        handleScale: {
          axisPressedMouseMove: !disabled,
          mouseWheel: !disabled,
          pinch: !disabled,
        },
      });
    }, [activeDrawingTool]);

    const renderTrendline = useCallback(
      (drawing: ChartDrawing, key: string, dashed: boolean) => {
        if (!chartRef.current || drawing.points.length < 2) return null;
        const [p1, p2] = drawing.points;
        const timeScale = chartRef.current.timeScale();
        const x1 =
          p1.logical !== undefined
            ? timeScale.logicalToCoordinate(p1.logical)
            : timeScale.timeToCoordinate(p1.time);
        const x2 =
          p2.logical !== undefined
            ? timeScale.logicalToCoordinate(p2.logical)
            : timeScale.timeToCoordinate(p2.time);
        const series = getPrimarySeries();
        const screenPoints = drawing.screenPoints ?? [];
        const x1Fallback = screenPoints[0]?.x ?? null;
        const x2Fallback = screenPoints[1]?.x ?? null;
        const y1Fallback = screenPoints[0]?.y ?? null;
        const y2Fallback = screenPoints[1]?.y ?? null;
        if (!series) return null;
        const y1 = series.priceScale().priceToCoordinate(p1.price);
        const y2 = series.priceScale().priceToCoordinate(p2.price);

        const x1Coord = x1 ?? x1Fallback;
        const x2Coord = x2 ?? x2Fallback;
        const y1Coord = y1 ?? y1Fallback;
        const y2Coord = y2 ?? y2Fallback;
        if (
          x1Coord === null ||
          x2Coord === null ||
          y1Coord === null ||
          y2Coord === null
        ) {
          return null;
        }

        return (
          <line
            key={key}
            x1={x1Coord}
            y1={y1Coord}
            x2={x2Coord}
            y2={y2Coord}
            stroke={drawing.color ?? primaryDrawingColor}
            strokeWidth={drawing.lineWidth ?? 2}
            strokeDasharray={dashed ? '4 2' : undefined}
            opacity={drawing.opacity ?? 0.9}
          />
        );
      },
      [getPrimarySeries, primaryDrawingColor]
    );

    const renderHorizontalLine = useCallback(
      (drawing: ChartDrawing, key: string, dashed: boolean) => {
        if (!chartRef.current || drawing.points.length === 0) return null;
        const series = getPrimarySeries();
        if (!series) return null;
        const y = series.priceScale().priceToCoordinate(drawing.points[0].price);
        const screenY = drawing.screenPoints?.[0]?.y ?? null;
        const yCoord = y ?? screenY;
        if (yCoord === null) return null;

        return (
          <line
            key={key}
            x1={0}
            y1={yCoord}
            x2={overlaySize.width}
            y2={yCoord}
            stroke={drawing.color ?? primaryDrawingColor}
            strokeWidth={drawing.lineWidth ?? 1.5}
            strokeDasharray={dashed ? '4 2' : '6 4'}
            opacity={drawing.opacity ?? 0.85}
          />
        );
      },
      [chartRef, getPrimarySeries, overlaySize.width, primaryDrawingColor]
    );

    const renderVerticalLine = useCallback(
      (drawing: ChartDrawing, key: string, dashed: boolean) => {
        if (!chartRef.current || drawing.points.length === 0) return null;
        const point = drawing.points[0];
        const timeScale = chartRef.current.timeScale();
        const x =
          point.logical !== undefined
            ? timeScale.logicalToCoordinate(point.logical)
            : timeScale.timeToCoordinate(point.time);
        const screenX = drawing.screenPoints?.[0]?.x ?? null;
        const xCoord = x ?? screenX;
        if (xCoord === null) return null;

        return (
          <line
            key={key}
            x1={xCoord}
            y1={0}
            x2={xCoord}
            y2={overlaySize.height}
            stroke={drawing.color ?? primaryDrawingColor}
            strokeWidth={drawing.lineWidth ?? 1.5}
            strokeDasharray={dashed ? '4 2' : '6 4'}
            opacity={drawing.opacity ?? 0.85}
          />
        );
      },
      [chartRef, overlaySize.height, primaryDrawingColor]
    );

    const renderParallelChannel = useCallback(
      (drawing: ChartDrawing, key: string, dashed: boolean) => {
        if (!chartRef.current || drawing.points.length < 2) return null;
        const series = getPrimarySeries();
        if (!series) return null;

        const p1 = drawing.points[0];
        const p2 = drawing.points[Math.min(1, drawing.points.length - 1)];
        const p3 = drawing.points[Math.min(2, drawing.points.length - 1)];

        const timeScale = chartRef.current.timeScale();
        const screenPoints = drawing.screenPoints ?? [];
        const x1Fallback = screenPoints[0]?.x ?? null;
        const x2Fallback = screenPoints[1]?.x ?? null;
        const x3Fallback = screenPoints[2]?.x ?? x2Fallback;
        const y1Fallback = screenPoints[0]?.y ?? null;
        const y2Fallback = screenPoints[1]?.y ?? null;
        const y3Fallback = screenPoints[2]?.y ?? y2Fallback;

        const x1 =
          (p1.logical !== undefined
            ? timeScale.logicalToCoordinate(p1.logical)
            : timeScale.timeToCoordinate(p1.time)) ?? x1Fallback;
        const x2 =
          (p2.logical !== undefined
            ? timeScale.logicalToCoordinate(p2.logical)
            : timeScale.timeToCoordinate(p2.time)) ?? x2Fallback;
        const x3 =
          (p3.logical !== undefined
            ? timeScale.logicalToCoordinate(p3.logical)
            : timeScale.timeToCoordinate(p3.time)) ?? x3Fallback;
        const y1 = series.priceScale().priceToCoordinate(p1.price) ?? y1Fallback;
        const y2 = series.priceScale().priceToCoordinate(p2.price) ?? y2Fallback;
        const y3 = series.priceScale().priceToCoordinate(p3.price) ?? y3Fallback;

        if (
          x1 === null ||
          x2 === null ||
          x3 === null ||
          y1 === null ||
          y2 === null ||
          y3 === null
        ) {
          return null;
        }

        const dx = x2 - x1;
        const dy = y2 - y1;
        const length = Math.sqrt(dx * dx + dy * dy) || 1;
        const normalX = -dy / length;
        const normalY = dx / length;
        const distance = (x3 - x1) * normalX + (y3 - y1) * normalY;

        const x1b = x1 + normalX * distance;
        const y1b = y1 + normalY * distance;
        const x2b = x2 + normalX * distance;
        const y2b = y2 + normalY * distance;

        const fill = drawing.secondaryColor ?? `${primaryDrawingColor}33`;
        const stroke = drawing.color ?? primaryDrawingColor;

        return (
          <g key={key} opacity={drawing.opacity ?? 0.65}>
            <polygon points={`${x1},${y1} ${x2},${y2} ${x2b},${y2b} ${x1b},${y1b}`} fill={fill} />
            <line
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke={stroke}
              strokeWidth={drawing.lineWidth ?? 1.5}
              strokeDasharray={dashed ? '4 2' : undefined}
            />
            <line
              x1={x1b}
              y1={y1b}
              x2={x2b}
              y2={y2b}
              stroke={stroke}
              strokeWidth={drawing.lineWidth ?? 1.5}
              strokeDasharray={dashed ? '4 2' : undefined}
            />
          </g>
        );
      },
      [chartRef, getPrimarySeries, primaryDrawingColor]
    );

    const renderDrawing = useCallback(
      (drawing: ChartDrawing, index: number, dashed: boolean) => {
        switch (drawing.type) {
          case 'horizontal-line':
            return renderHorizontalLine(drawing, `${drawing.id ?? index}`, dashed);
          case 'vertical-line':
            return renderVerticalLine(drawing, `${drawing.id ?? index}`, dashed);
          case 'parallel-channel':
            return renderParallelChannel(drawing, `${drawing.id ?? index}`, dashed);
          case 'trendline':
          default:
            return renderTrendline(drawing, `${drawing.id ?? index}`, dashed);
        }
      },
      [renderHorizontalLine, renderParallelChannel, renderTrendline, renderVerticalLine]
    );

    const overlayElements = useMemo(() => {
      if (!isMainPanel) return null;
      const nodes: React.ReactNode[] = [];
      drawings.forEach((drawing, index) => {
        const element = renderDrawing(drawing, index, false);
        if (element) nodes.push(element);
      });

      if (draftDrawing) {
        const draftElement = renderDrawing(draftDrawing, drawings.length + 1, true);
        if (draftElement) nodes.push(draftElement);
      }

      return nodes;
    }, [drawings, draftDrawing, isMainPanel, renderDrawing]);

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

          {isMainPanel && (
            <svg
              ref={overlayRef}
              width={overlaySize.width}
              height={overlaySize.height}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                pointerEvents: activeDrawingTool ? 'auto' : 'none',
                cursor: activeDrawingTool ? 'crosshair' : 'default',
              }}
              onPointerDown={handlePointerDown}
              onPointerMove={handlePointerMove}
              onPointerUp={handlePointerUp}
              onPointerLeave={handlePointerLeave}
            >
              {overlayElements}
            </svg>
          )}
        </Box>
      </Box>
    );
  }
);

ChartPanel.displayName = 'ChartPanel';

export default ChartPanel;
