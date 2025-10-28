// TechnicalChart/components/ChartCanvas.tsx
import React, { useEffect, useRef } from 'react';
import { createChart, CrosshairMode, Time } from 'lightweight-charts';
import { Box } from '@mui/material';
import {
  ProcessedChartData,
  ChartOptions,
  CrosshairData,
} from '../types/chart.types';
import { getColorScheme } from '../utils/colorSchemes';

interface ChartCanvasProps {
  data: ProcessedChartData;
  options: ChartOptions;
  onCrosshairMove?: (data: CrosshairData | null) => void;
  onVisibleRangeChange?: (range: { from: Time; to: Time }) => void;
}

export const ChartCanvas: React.FC<ChartCanvasProps> = ({
  data,
  options,
  onCrosshairMove,
  onVisibleRangeChange,
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);
  const mainSeriesRef = useRef<any>(null);
  const volumeSeriesRef = useRef<any>(null);
  const indicatorSeriesRefs = useRef<Map<string, any>>(new Map());
  const resizeObserverRef = useRef<ResizeObserver | null>(null);

  const colorScheme = getColorScheme(options.theme);

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: options.height,
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
        visible: options.showTimeScale,
        borderColor: colorScheme.grid,
        timeVisible: true,
        secondsVisible: false,
      },
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
        horzTouchDrag: true,
        vertTouchDrag: true,
      },
      handleScale: {
        axisPressedMouseMove: true,
        mouseWheel: true,
        pinch: true,
      },
    });

    chartRef.current = chart;

    // Setup crosshair move handler
    chart.subscribeCrosshairMove((param) => {
      if (!param || !param.time || !onCrosshairMove) {
        if (onCrosshairMove) {
          onCrosshairMove(null);
        }
        return;
      }

      // Use type assertion for v4 API compatibility
      const paramData = param as any;
      const mainSeriesData = paramData.seriesData && mainSeriesRef.current
        ? paramData.seriesData.get(mainSeriesRef.current)
        : null;

      if (mainSeriesData) {
        const crosshairData: CrosshairData = {
          time: param.time,
          indicators: {},
        };

        // Extract OHLCV if available
        if (typeof mainSeriesData === 'object' && 'open' in mainSeriesData) {
          crosshairData.open = (mainSeriesData as any).open;
          crosshairData.high = (mainSeriesData as any).high;
          crosshairData.low = (mainSeriesData as any).low;
          crosshairData.close = (mainSeriesData as any).close;
        } else if (typeof mainSeriesData === 'number') {
          crosshairData.close = mainSeriesData;
        }

        // Extract volume if available
        const volumeData = paramData.seriesData && volumeSeriesRef.current
          ? paramData.seriesData.get(volumeSeriesRef.current)
          : null;
        if (volumeData && typeof volumeData === 'number') {
          crosshairData.volume = volumeData;
        }

        // Extract indicator values
        if (paramData.seriesData) {
          indicatorSeriesRefs.current.forEach((series, seriesId) => {
            const value = paramData.seriesData.get(series);
            if (value !== undefined && typeof value === 'number') {
              crosshairData.indicators[seriesId] = value;
            }
          });
        }

        onCrosshairMove(crosshairData);
      }
    });

    // Setup visible range change handler
    chart.timeScale().subscribeVisibleLogicalRangeChange((logicalRange) => {
      if (logicalRange && onVisibleRangeChange) {
        const barsInfo = mainSeriesRef.current?.barsInLogicalRange(logicalRange);
        if (barsInfo && barsInfo.barsBefore <= 0) {
          // User scrolled to the beginning
        }
        if (barsInfo && barsInfo.barsAfter <= 0) {
          // User scrolled to the end
        }
      }
    });

    // Setup resize observer
    const resizeObserver = new ResizeObserver((entries) => {
      if (entries.length === 0 || entries[0].target !== chartContainerRef.current) return;
      const { width } = entries[0].contentRect;
      chart.applyOptions({ width, height: options.height });
    });

    resizeObserver.observe(chartContainerRef.current);
    resizeObserverRef.current = resizeObserver;

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      mainSeriesRef.current = null;
      volumeSeriesRef.current = null;
      indicatorSeriesRefs.current.clear();
    };
  }, []); // Only run once on mount

  // Update chart options when theme or settings change
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
      crosshair: {
        mode: options.showCrosshair ? CrosshairMode.Normal : CrosshairMode.Hidden,
      },
      rightPriceScale: {
        visible: options.showPriceScale,
      },
      timeScale: {
        visible: options.showTimeScale,
      },
    });
  }, [options, colorScheme]);

  // Render main price series and indicators
  useEffect(() => {
    if (!chartRef.current || !data || data.ohlcv.length === 0) return;

    const chart = chartRef.current;

    // Clear existing series
    if (mainSeriesRef.current) {
      chart.removeSeries(mainSeriesRef.current);
      mainSeriesRef.current = null;
    }
    if (volumeSeriesRef.current) {
      chart.removeSeries(volumeSeriesRef.current);
      volumeSeriesRef.current = null;
    }
    indicatorSeriesRefs.current.forEach((series) => chart.removeSeries(series));
    indicatorSeriesRefs.current.clear();

    // Create main price series
    if (data.hasOHLC && options.chartType === 'candlestick') {
      const candlestickSeries = chart.addCandlestickSeries({
        upColor: colorScheme.upColor,
        downColor: colorScheme.downColor,
        wickUpColor: colorScheme.wickUpColor,
        wickDownColor: colorScheme.wickDownColor,
        borderUpColor: colorScheme.borderUpColor,
        borderDownColor: colorScheme.borderDownColor,
      });
      candlestickSeries.setData(data.ohlcv);
      mainSeriesRef.current = candlestickSeries;
    } else {
      // Line or area chart
      const lineData = data.ohlcv.map((d) => ({ time: d.time, value: d.close }));

      if (options.chartType === 'area') {
        const areaSeries = chart.addAreaSeries({
          lineColor: colorScheme.upColor,
          topColor: `${colorScheme.upColor}80`,
          bottomColor: `${colorScheme.upColor}10`,
          lineWidth: 2,
        });
        areaSeries.setData(lineData);
        mainSeriesRef.current = areaSeries;
      } else {
        const lineSeries = chart.addLineSeries({
          color: colorScheme.upColor,
          lineWidth: 2,
        });
        lineSeries.setData(lineData);
        mainSeriesRef.current = lineSeries;
      }
    }

    // Add volume series if available and enabled
    if (data.volume && data.volume.length > 0 && options.showVolume) {
      const volumeSeries = chart.addHistogramSeries({
        color: colorScheme.volumeColor,
        priceFormat: {
          type: 'volume',
        },
        priceScaleId: 'volume',
      });

      // Color volume bars based on price direction
      const volumeData = data.volume.map((v, index) => {
        let color = colorScheme.volumeColor;
        if (index > 0 && data.ohlcv[index] && data.ohlcv[index - 1]) {
          color = data.ohlcv[index].close >= data.ohlcv[index - 1].close
            ? colorScheme.volumeUpColor
            : colorScheme.volumeDownColor;
        }
        return { ...v, color };
      });

      volumeSeries.setData(volumeData);
      volumeSeriesRef.current = volumeSeries;

      // Configure volume scale
      chart.priceScale('volume').applyOptions({
        scaleMargins: {
          top: 0.8,
          bottom: 0,
        },
      });
    }

    // Add overlay indicators (on main chart)
    data.indicators
      .filter((ind) => ind.type === 'overlay')
      .forEach((indicator) => {
        indicator.series.forEach((series) => {
          if (!series.visible) return;

          if (series.type === 'line') {
            const lineSeries = chart.addLineSeries({
              color: series.color,
              lineWidth: 1.5,
              title: series.name,
            });
            lineSeries.setData(series.data as any);
            indicatorSeriesRefs.current.set(series.id, lineSeries);
          } else if (series.type === 'area') {
            const areaSeries = chart.addAreaSeries({
              lineColor: series.color,
              topColor: `${series.color}40`,
              bottomColor: `${series.color}10`,
              lineWidth: 1,
              title: series.name,
            });
            areaSeries.setData(series.data as any);
            indicatorSeriesRefs.current.set(series.id, areaSeries);
          }
        });
      });

    // Fit content
    chart.timeScale().fitContent();
  }, [data, options.chartType, options.showVolume, colorScheme]);

  return (
    <Box
      ref={chartContainerRef}
      sx={{
        width: '100%',
        height: options.height,
        position: 'relative',
        backgroundColor: colorScheme.background,
      }}
    />
  );
};

export default ChartCanvas;
