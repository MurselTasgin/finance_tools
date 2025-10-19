// finance_tools/frontend/src/components/PlotViewer.tsx
import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Alert,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  BarChart,
  Bar,
} from 'recharts';

interface PlotViewerProps {
  data: { x: string | number; y: number; label?: string }[];
  xColumn: string;
  yColumn: string;
  fundCode?: string;
  fundTitle?: string;
  startDate?: string;
  endDate?: string;
}

export const PlotViewer: React.FC<PlotViewerProps> = ({ data, xColumn, yColumn, fundCode, fundTitle, startDate, endDate }) => {
  if (!data || data.length === 0) {
    return (
      <Alert severity="info">
        No data available for plotting. Please check your filters and try again.
      </Alert>
    );
  }

  const isNumericX = data.every(d => typeof d.x === 'number');
  const isNumericY = data.every(d => typeof d.y === 'number');
  
  // Determine chart type based on data characteristics
  const getChartType = () => {
    if (xColumn === 'date' || xColumn.includes('date')) {
      return 'line';
    }
    if (isNumericX && isNumericY) {
      return 'scatter';
    }
    return 'bar';
  };

  const chartType = getChartType();

  const formatXAxis = (value: any) => {
    if (xColumn === 'date' || xColumn.includes('date')) {
      try {
        return new Date(value).toLocaleDateString();
      } catch {
        return value;
      }
    }
    if (typeof value === 'number') {
      return new Intl.NumberFormat().format(value);
    }
    return value.toString();
  };

  const formatYAxis = (value: any) => {
    if (typeof value === 'number') {
      return new Intl.NumberFormat().format(value);
    }
    return value.toString();
  };

  const formatTooltip = (value: any, name: string) => {
    if (name === 'y') {
      return [formatYAxis(value), yColumn.replace(/_/g, ' ').toUpperCase()];
    }
    return [value, name];
  };

  const renderChart = () => {
    const commonProps = {
      data: data,
      margin: { top: 20, right: 30, left: 20, bottom: 20 },
    };

    switch (chartType) {
      case 'line':
        return (
          <LineChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="x" 
              tickFormatter={formatXAxis}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis tickFormatter={formatYAxis} />
            <Tooltip 
              formatter={formatTooltip}
              labelFormatter={(label) => `${xColumn.replace(/_/g, ' ').toUpperCase()}: ${formatXAxis(label)}`}
            />
            <Line 
              type="monotone" 
              dataKey="y" 
              stroke="#1976d2" 
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        );

      case 'scatter':
        return (
          <ScatterChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="x" 
              tickFormatter={formatXAxis}
              name={xColumn.replace(/_/g, ' ').toUpperCase()}
            />
            <YAxis 
              dataKey="y" 
              tickFormatter={formatYAxis}
              name={yColumn.replace(/_/g, ' ').toUpperCase()}
            />
            <Tooltip 
              formatter={formatTooltip}
              labelFormatter={(label) => `${xColumn.replace(/_/g, ' ').toUpperCase()}: ${formatXAxis(label)}`}
            />
            <Scatter 
              dataKey="y" 
              fill="#1976d2" 
              r={4}
            />
          </ScatterChart>
        );

      case 'bar':
      default:
        return (
          <BarChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="x" 
              tickFormatter={formatXAxis}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis tickFormatter={formatYAxis} />
            <Tooltip 
              formatter={formatTooltip}
              labelFormatter={(label) => `${xColumn.replace(/_/g, ' ').toUpperCase()}: ${formatXAxis(label)}`}
            />
            <Bar 
              dataKey="y" 
              fill="#1976d2"
            />
          </BarChart>
        );
    }
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        {xColumn.replace(/_/g, ' ').toUpperCase()} vs {yColumn.replace(/_/g, ' ').toUpperCase()}
        {fundCode && (
          <Typography component="span" variant="body2" color="textSecondary" sx={{ ml: 1 }}>
            - {fundCode} {fundTitle && `(${fundTitle})`}
          </Typography>
        )}
      </Typography>
      <Typography variant="body2" color="textSecondary" gutterBottom>
        {data.length} data points
        {fundCode && ` for fund ${fundCode}`}
        {startDate && endDate && ` from ${startDate} to ${endDate}`}
        {startDate && !endDate && ` from ${startDate} onwards`}
        {!startDate && endDate && ` up to ${endDate}`}
      </Typography>
      
      <Paper sx={{ p: 2, mt: 2 }}>
        <ResponsiveContainer width="100%" height={400}>
          {renderChart()}
        </ResponsiveContainer>
      </Paper>

      <Box mt={2}>
        <Typography variant="body2" color="textSecondary">
          <strong>Chart Type:</strong> {chartType.charAt(0).toUpperCase() + chartType.slice(1)} Chart
          <br />
          <strong>Data Points:</strong> {data.length}
          <br />
          <strong>X Axis:</strong> {xColumn.replace(/_/g, ' ').toUpperCase()}
          <br />
          <strong>Y Axis:</strong> {yColumn.replace(/_/g, ' ').toUpperCase()}
        </Typography>
      </Box>
    </Box>
  );
};
