import React, { useEffect, useMemo, useRef, useState } from 'react';
import Plot from 'react-plotly.js';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  SelectChangeEvent,
  Stack,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
  Switch,
  FormControlLabel,
} from '@mui/material';
import { analyticsApi } from '../services/api';
import { TechnicalChartContainer } from './TechnicalChart';

type AssetType = 'stock' | 'etf';

interface IndicatorDefinition {
  id: string;
  name: string;
  description: string;
  required_columns: string[];
  parameter_schema: Record<string, any>;
  capabilities: string[];
}

interface TechnicalChartResponse {
  asset_type: AssetType;
  identifier: string;
  columns: string[];
  price_column: string;
  interval: string;
  start_date?: string;
  end_date?: string;
  timeseries: Array<Record<string, any>>;
  indicator_definitions: Array<{
    id: string;
    name: string;
    description: string;
    columns: string[];
    parameters: Record<string, any>;
  }>;
  indicator_snapshots: Record<string, Record<string, any>>;
  metadata: Record<string, any>;
}

export interface TechnicalAnalysisInitialState {
  assetType: AssetType;
  identifier: string;
  start_date?: string;
  end_date?: string;
  interval?: string;
  indicators?: Record<string, Record<string, any>>;
}

const STOCK_INTERVALS = [
  { value: '1d', label: 'Daily' },
  { value: '1wk', label: 'Weekly' },
  { value: '1mo', label: 'Monthly' },
];

const ETF_INTERVALS = [{ value: '1d', label: 'Daily' }];

const QUICK_RANGES = [
  { label: '1M', days: 30 },
  { label: '3M', days: 90 },
  { label: '6M', days: 180 },
  { label: '1Y', days: 365 },
  { label: '3Y', days: 365 * 3 },
];

const DEFAULT_STOCK_INDICATORS = ['ema_cross', 'macd', 'rsi'];
const DEFAULT_ETF_INDICATORS = ['ema_cross', 'macd', 'rsi'];

const formatDate = (date: Date) => date.toISOString().slice(0, 10);

interface UnifiedTechnicalAnalysisPanelProps {
  initialState?: TechnicalAnalysisInitialState | null;
  onInitialStateConsumed?: () => void;
}

export const UnifiedTechnicalAnalysisPanel: React.FC<UnifiedTechnicalAnalysisPanelProps> = ({
  initialState,
  onInitialStateConsumed,
}) => {
  const today = useMemo(() => new Date(), []);
  const sixMonthsAgo = useMemo(() => {
    const d = new Date(today);
    d.setMonth(d.getMonth() - 6);
    return d;
  }, [today]);

  const initialAssetType = initialState?.assetType ?? 'stock';
  const initialIdentifier = initialState?.identifier ?? (initialAssetType === 'etf' ? 'NNF' : 'AAPL');
  const initialStart = initialState?.start_date ?? formatDate(sixMonthsAgo);
  const initialEnd = initialState?.end_date ?? formatDate(today);
  const initialInterval = initialState?.interval ?? '1d';

  const [assetType, setAssetType] = useState<AssetType>(initialAssetType);
  const [identifier, setIdentifier] = useState<string>(initialIdentifier);
  const [startDate, setStartDate] = useState<string>(initialStart);
  const [endDate, setEndDate] = useState<string>(initialEnd);
  const [timeframe, setTimeframe] = useState<string>(initialInterval);

  const [availableIndicators, setAvailableIndicators] = useState<IndicatorDefinition[]>([]);
  const [indicatorParameters, setIndicatorParameters] = useState<Record<string, Record<string, any>>>({});
  const [selectedIndicators, setSelectedIndicators] = useState<string[]>(DEFAULT_STOCK_INDICATORS);

  const [loadingIndicators, setLoadingIndicators] = useState<boolean>(false);
  const [chartLoading, setChartLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [chartData, setChartData] = useState<TechnicalChartResponse | null>(null);
  const pendingInitialStateRef = useRef<TechnicalAnalysisInitialState | null>(initialState ?? null);
  const [useLightweightCharts, setUseLightweightCharts] = useState<boolean>(true);

  useEffect(() => {
    pendingInitialStateRef.current = initialState ?? null;
  }, [initialState]);

  // Load indicator metadata when asset type changes
  useEffect(() => {
    let isMounted = true;

    const loadIndicators = async () => {
      try {
        setLoadingIndicators(true);
        const response = await analyticsApi.getIndicators(assetType);
        if (!isMounted) return;

        const indicators = response.indicators || [];
        const defaults: Record<string, Record<string, any>> = {};
        indicators.forEach((indicator: IndicatorDefinition) => {
          const params: Record<string, any> = {};
          Object.entries(indicator.parameter_schema || {}).forEach(([key, schema]: [string, any]) => {
            if (schema && schema.default !== undefined) {
              params[key] = schema.default;
            }
          });
          defaults[indicator.id] = params;
        });

        setAvailableIndicators(indicators);
        setIndicatorParameters(defaults);

        const pendingState = pendingInitialStateRef.current;
        const hasPendingForAsset = pendingState && pendingState.assetType === assetType;

        if (!hasPendingForAsset) {
          const fallback = assetType === 'stock' ? DEFAULT_STOCK_INDICATORS : DEFAULT_ETF_INDICATORS;
          const autoSelection = indicators
            .filter((indicator: IndicatorDefinition) => fallback.includes(indicator.id))
            .map((indicator: IndicatorDefinition) => indicator.id);

          setSelectedIndicators(autoSelection.length > 0 ? autoSelection : indicators.slice(0, 3).map(i => i.id));
          setIdentifier(assetType === 'stock' ? 'AAPL' : 'NNF');
          setTimeframe('1d');
        }
      } catch (e: any) {
        if (isMounted) {
          setError(e?.message || 'Failed to load indicators');
        }
      } finally {
        if (isMounted) {
          setLoadingIndicators(false);
        }
      }
    };

    loadIndicators();

    return () => {
      isMounted = false;
    };
  }, [assetType, sixMonthsAgo, today]);

  useEffect(() => {
    const pendingState = pendingInitialStateRef.current;
    if (!pendingState) {
      return;
    }

    if (pendingState.assetType !== assetType) {
      setAssetType(pendingState.assetType);
      return;
    }

    if (loadingIndicators) {
      return;
    }

    if (pendingState.identifier) {
      setIdentifier(pendingState.identifier);
    }
    if (pendingState.start_date) {
      setStartDate(pendingState.start_date);
    }
    if (pendingState.end_date) {
      setEndDate(pendingState.end_date);
    }
    if (pendingState.interval) {
      setTimeframe(pendingState.interval);
    }

    if (pendingState.indicators && Object.keys(pendingState.indicators).length > 0) {
      const indicatorIds = Object.keys(pendingState.indicators);
      setSelectedIndicators(indicatorIds);

      setIndicatorParameters(prev => {
        const updated = { ...prev };
        indicatorIds.forEach((indicatorId) => {
          const params = pendingState.indicators ? pendingState.indicators[indicatorId] : undefined;
          if (!params) {
            return;
          }
          updated[indicatorId] = {
            ...(prev[indicatorId] || {}),
            ...params,
          };
        });
        return updated;
      });
    }

    pendingInitialStateRef.current = null;
    onInitialStateConsumed?.();
  }, [assetType, loadingIndicators, onInitialStateConsumed]);

  const handleQuickRange = (days: number) => {
    const end = new Date(endDate ? new Date(endDate) : today);
    const start = new Date(end);
    start.setDate(start.getDate() - days);
    setStartDate(formatDate(start));
    setEndDate(formatDate(end));
  };

  const handleIntervalChange = (event: SelectChangeEvent<string>) => {
    setTimeframe(event.target.value);
  };

  const handleIndicatorSelection = (event: SelectChangeEvent<string[]>) => {
    const value = event.target.value as string[];
    setSelectedIndicators(value);
    setIndicatorParameters(prev => {
      const updated = { ...prev };
      value.forEach((indicatorId) => {
        if (!updated[indicatorId]) {
          const indicator = availableIndicators.find((item) => item.id === indicatorId);
          if (!indicator) {
            updated[indicatorId] = {};
            return;
          }

          const params: Record<string, any> = {};
          Object.entries(indicator.parameter_schema || {}).forEach(([key, schema]: [string, any]) => {
            if (schema && schema.default !== undefined) {
              params[key] = schema.default;
            }
          });
          updated[indicatorId] = params;
        }
      });
      return updated;
    });
  };

  const handleLoadChart = async () => {
    if (!identifier) {
      setError('Please enter a valid symbol or fund code.');
      return;
    }

    setError(null);
    setChartLoading(true);

    try {
      const indicatorPayload: Record<string, any> = {};
      selectedIndicators.forEach((indicatorId) => {
        indicatorPayload[indicatorId] = indicatorParameters[indicatorId] || {};
      });

      const response = await analyticsApi.getTechnicalChart({
        asset_type: assetType,
        identifier: identifier.trim(),
        start_date: startDate,
        end_date: endDate,
        interval: timeframe,
        indicators: indicatorPayload,
      });

      setChartData(response);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to load technical analysis data');
      setChartData(null);
    } finally {
      setChartLoading(false);
    }
  };

  const processedChart = useMemo(() => {
    if (!chartData || !chartData.timeseries || chartData.timeseries.length === 0) {
      return null;
    }

    const records = chartData.timeseries;
    const priceColumn = chartData.price_column || 'close';
    const hasOHLC =
      records[0] &&
      ['open', 'high', 'low', 'close'].every((key) => key in records[0] && records[0][key] !== undefined);

    const xValues = records.map((row) => row.date || row.timestamp || row.Date || row.dateTime);

    type PanelDescriptor = {
      key: string;
      title: string;
      traces: any[];
    };

    const panelDescriptors: PanelDescriptor[] = [];

    // Price panel (main)
    const priceTraces: any[] = [];
    if (hasOHLC) {
      priceTraces.push({
        type: 'candlestick',
        x: xValues,
        open: records.map((row) => row.open),
        high: records.map((row) => row.high),
        low: records.map((row) => row.low),
        close: records.map((row) => row.close),
        name: `${chartData.identifier} Price`,
      });
    } else {
      priceTraces.push({
        type: 'scatter',
        mode: 'lines',
        x: xValues,
        y: records.map((row) => row[priceColumn]),
        name: `${chartData.identifier} Price`,
        line: { color: '#1976d2', width: 1.8 },
      });
    }
    panelDescriptors.push({
      key: 'price',
      title: `${chartData.identifier} Price`,
      traces: priceTraces,
    });

    // Volume panel
    const volumeColumn =
      (chartData.metadata && chartData.metadata.volume_column) ||
      (records[0] && 'volume' in records[0] ? 'volume' : null);
    if (volumeColumn) {
      panelDescriptors.push({
        key: 'volume',
        title: 'Volume',
        traces: [
          {
            type: 'bar',
            x: xValues,
            y: records.map((row) => row[volumeColumn]),
            name: 'Volume',
            marker: { color: '#9fa8da' },
            opacity: 0.6,
          },
        ],
      });
    }

    // Indicator panels
    chartData.indicator_definitions.forEach((indicator) => {
      const indicatorTraces: any[] = [];
      indicator.columns.forEach((column) => {
        if (!records[0] || records[0][column] === undefined) {
          return;
        }

        const traceType =
          column.toLowerCase().includes('hist') || column.toLowerCase().includes('volume')
            ? 'bar'
            : 'scatter';

        indicatorTraces.push({
          type: traceType,
          mode: traceType === 'scatter' ? 'lines' : undefined,
          x: xValues,
          y: records.map((row) => row[column]),
          name: `${indicator.name} (${column})`,
          line: traceType === 'scatter' ? { width: 1.5 } : undefined,
          marker: traceType === 'bar' ? { opacity: 0.7 } : undefined,
        });
      });

      if (indicatorTraces.length > 0) {
        panelDescriptors.push({
          key: indicator.id,
          title: indicator.name,
          traces: indicatorTraces,
        });
      }
    });

    const totalPanels = panelDescriptors.length;
    const data: any[] = [];

    const baseHeight = 360;
    const extraHeightPerPanel = 200;
    const layoutHeight = baseHeight + Math.max(0, totalPanels - 1) * extraHeightPerPanel;

    const layout: any = {
      margin: { l: 60, r: 60, t: 40, b: 40 },
      hovermode: 'x unified',
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      height: layoutHeight,
      legend: {
        orientation: 'h',
        x: 0,
        y: 1.02,
      },
    };

    const verticalGap = 0.02;
    const availableHeight = 1 - Math.max(0, totalPanels - 1) * verticalGap;
    const panelHeight = availableHeight / totalPanels;

    panelDescriptors.forEach((panel, index) => {
      const axisSuffix = index === 0 ? '' : `${index + 1}`;
      const xAxisKey = `xaxis${axisSuffix}`;
      const yAxisKey = `yaxis${axisSuffix}`;

      const axisDomainTop = 1 - index * (panelHeight + verticalGap);
      const axisDomainBottom = axisDomainTop - panelHeight;

      layout[xAxisKey] = {
        anchor: `y${axisSuffix}`,
        type: 'date',
        matches: index === 0 ? undefined : 'x',
        showticklabels: index === totalPanels - 1,
        title: index === totalPanels - 1 ? 'Date' : undefined,
        showgrid: true,
        gridcolor: '#e0e0e0',
        domain: [0, 1],
      };

      if (index === 0 && hasOHLC) {
        layout[xAxisKey].rangeslider = { visible: true };
      }

      if (index !== totalPanels - 1) {
        layout[xAxisKey].showticklabels = false;
      }

      layout[yAxisKey] = {
        title: panel.title,
        automargin: true,
        gridcolor: '#f0f0f0',
        anchor: `x${axisSuffix}`,
        domain: [axisDomainBottom, axisDomainTop],
      };

      panel.traces.forEach((trace) => {
        const axisRef = axisSuffix;
        trace.xaxis = `x${axisRef}`;
        trace.yaxis = `y${axisRef}`;
        data.push(trace);
      });
    });

    const config: any = {
      responsive: true,
      displaylogo: false,
      modeBarButtonsToRemove: ['lasso2d'],
    };

    return { data, layout, config };
  }, [chartData]);

  const indicatorSnapshots = useMemo(() => {
    if (!chartData || !chartData.indicator_snapshots) {
      return [];
    }

    return chartData.indicator_definitions.map((indicator) => {
      const snapshot = chartData.indicator_snapshots[indicator.id] || {};
      return {
        id: indicator.id,
        name: indicator.name,
        values: snapshot,
      };
    });
  }, [chartData]);

  const lastRecord = useMemo(() => {
    if (!chartData || !chartData.timeseries || chartData.timeseries.length === 0) {
      return null;
    }
    return chartData.timeseries[chartData.timeseries.length - 1];
  }, [chartData]);

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Technical Analysis
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Explore interactive charts with configurable indicators for stocks and ETFs. Select a symbol or fund code,
          choose a timeframe, and overlay popular indicators to analyse price action similar to TradingView.
        </Typography>

        <Stack
          direction={{ xs: 'column', md: 'row' }}
          spacing={3}
          alignItems="flex-start"
          sx={{ mb: 3 }}
        >
          <Stack spacing={2} sx={{ minWidth: 240 }}>
            <Typography variant="subtitle2" color="text.secondary">
              Asset Type
            </Typography>
            <ToggleButtonGroup
              color="primary"
              exclusive
              value={assetType}
              onChange={(_, value: AssetType | null) => {
                if (value) {
                  setAssetType(value);
                }
              }}
              size="small"
            >
              <ToggleButton value="stock">Stock</ToggleButton>
              <ToggleButton value="etf">ETF</ToggleButton>
            </ToggleButtonGroup>

            <TextField
              label={assetType === 'stock' ? 'Stock Symbol' : 'Fund Code'}
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value.toUpperCase())}
              placeholder={assetType === 'stock' ? 'e.g. AAPL' : 'e.g. NNF'}
              helperText="Enter a symbol or fund code"
              size="small"
            />

            <FormControl size="small" fullWidth>
              <InputLabel id="interval-select-label">Interval</InputLabel>
              <Select
                labelId="interval-select-label"
                value={timeframe}
                label="Interval"
                onChange={handleIntervalChange}
              >
                {(assetType === 'stock' ? STOCK_INTERVALS : ETF_INTERVALS).map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField
              label="Start Date"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
              size="small"
            />
            <TextField
              label="End Date"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
              size="small"
            />
            <Stack direction="row" spacing={1}>
              {QUICK_RANGES.map((range) => (
                <Button key={range.label} variant="outlined" size="small" onClick={() => handleQuickRange(range.days)}>
                  {range.label}
                </Button>
              ))}
            </Stack>
          </Stack>

          <Stack spacing={2} sx={{ minWidth: 260 }}>
            <Typography variant="subtitle2" color="text.secondary">
              Indicators
            </Typography>
            {loadingIndicators ? (
              <Box display="flex" justifyContent="center" py={2}>
                <CircularProgress size={24} />
              </Box>
            ) : (
              <FormControl size="small" fullWidth>
                <InputLabel id="indicator-select-label">Select Indicators</InputLabel>
                <Select
                  labelId="indicator-select-label"
                  multiple
                  value={selectedIndicators}
                  onChange={handleIndicatorSelection}
                  renderValue={(selected) =>
                    selected
                      .map((id) => availableIndicators.find((indicator) => indicator.id === id)?.name || id)
                      .join(', ')
                  }
                  label="Select Indicators"
                >
                  {availableIndicators.map((indicator) => (
                    <MenuItem key={indicator.id} value={indicator.id}>
                      {indicator.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
            <Typography variant="caption" color="text.secondary">
              Indicator parameters use sensible defaults and can be adjusted in future iterations.
            </Typography>
          </Stack>
        </Stack>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <FormControlLabel
            control={
              <Switch
                checked={useLightweightCharts}
                onChange={(e) => setUseLightweightCharts(e.target.checked)}
                color="primary"
              />
            }
            label={
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                {useLightweightCharts ? 'Lightweight Charts (New)' : 'Plotly Charts (Legacy)'}
              </Typography>
            }
          />
          <Button
            variant="contained"
            onClick={handleLoadChart}
            disabled={chartLoading || loadingIndicators}
            startIcon={chartLoading ? <CircularProgress size={18} /> : undefined}
          >
            {chartLoading ? 'Loading...' : 'Load Chart'}
          </Button>
        </Box>

        {useLightweightCharts && identifier ? (
          <Box>
            <TechnicalChartContainer
              assetType={assetType}
              identifier={identifier}
              startDate={startDate}
              endDate={endDate}
              interval={timeframe as any}
              indicators={selectedIndicators}
              indicatorParameters={indicatorParameters}
              onDataLoad={(data) => {
                setChartData(data as any);
                setError(null);
              }}
              onError={(err) => {
                setError(err);
                setChartData(null);
              }}
              height={600}
              theme="dark"
            />

            {chartData && lastRecord && (
              <Box sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                <Chip
                  label={`Last Close: ${lastRecord[chartData.price_column]?.toFixed?.(2) ?? lastRecord[chartData.price_column]}`}
                  color="primary"
                  variant="outlined"
                />
                {['open', 'high', 'low'].map((field) =>
                  lastRecord[field] !== undefined ? (
                    <Chip
                      key={field}
                      label={`${field.charAt(0).toUpperCase() + field.slice(1)}: ${lastRecord[field]?.toFixed?.(2) ?? lastRecord[field]}`}
                      variant="outlined"
                    />
                  ) : null
                )}
                {chartData.metadata?.fund_type && (
                  <Chip label={`Fund Type: ${chartData.metadata.fund_type}`} variant="outlined" />
                )}
              </Box>
            )}

            {indicatorSnapshots.some((snapshot) => Object.keys(snapshot.values || {}).length > 0) && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Indicator Snapshots (Latest)
                </Typography>
                <Grid container spacing={2}>
                  {indicatorSnapshots.map((snapshot) => {
                    const entries = Object.entries(snapshot.values || {});
                    if (entries.length === 0) return null;
                    return (
                      <Grid item xs={12} sm={6} md={4} key={snapshot.id}>
                        <Card variant="outlined" sx={{ p: 1.5 }}>
                          <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                            {snapshot.name}
                          </Typography>
                          <Stack spacing={0.5}>
                            {entries.map(([key, value]) => (
                              <Typography key={key} variant="caption">
                                {key}: {typeof value === 'number' ? value.toFixed(4) : String(value)}
                              </Typography>
                            ))}
                          </Stack>
                        </Card>
                      </Grid>
                    );
                  })}
                </Grid>
              </Box>
            )}
          </Box>
        ) : chartData && processedChart ? (
          <Box>
            <Box sx={{ height: processedChart.layout?.height || 480 }}>
              <Plot
                data={processedChart.data}
                layout={processedChart.layout}
                config={processedChart.config}
                style={{ width: '100%', height: '100%' }}
                useResizeHandler
              />
            </Box>

            {lastRecord && (
              <Box sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                <Chip
                  label={`Last Close: ${lastRecord[chartData.price_column]?.toFixed?.(2) ?? lastRecord[chartData.price_column]}`}
                  color="primary"
                  variant="outlined"
                />
                {['open', 'high', 'low'].map((field) =>
                  lastRecord[field] !== undefined ? (
                    <Chip
                      key={field}
                      label={`${field.charAt(0).toUpperCase() + field.slice(1)}: ${lastRecord[field]?.toFixed?.(2) ?? lastRecord[field]}`}
                      variant="outlined"
                    />
                  ) : null
                )}
                {chartData.metadata?.fund_type && (
                  <Chip label={`Fund Type: ${chartData.metadata.fund_type}`} variant="outlined" />
                )}
              </Box>
            )}

            {indicatorSnapshots.some((snapshot) => Object.keys(snapshot.values || {}).length > 0) && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Indicator Snapshots (Latest)
                </Typography>
                <Grid container spacing={2}>
                  {indicatorSnapshots.map((snapshot) => {
                    const entries = Object.entries(snapshot.values || {});
                    if (entries.length === 0) return null;
                    return (
                      <Grid item xs={12} sm={6} md={4} key={snapshot.id}>
                        <Card variant="outlined" sx={{ p: 1.5 }}>
                          <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                            {snapshot.name}
                          </Typography>
                          <Stack spacing={0.5}>
                            {entries.map(([key, value]) => (
                              <Typography key={key} variant="caption">
                                {key}: {typeof value === 'number' ? value.toFixed(4) : String(value)}
                              </Typography>
                            ))}
                          </Stack>
                        </Card>
                      </Grid>
                    );
                  })}
                </Grid>
              </Box>
            )}
          </Box>
        ) : (
          !chartLoading && (
            <Alert severity="info">
              Enter a symbol or fund code and click &quot;Load Chart&quot; to generate an interactive technical chart.
            </Alert>
          )
        )}
      </CardContent>
    </Card>
  );
};

export default UnifiedTechnicalAnalysisPanel;
