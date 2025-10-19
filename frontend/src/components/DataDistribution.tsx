// finance_tools/frontend/src/components/DataDistribution.tsx
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { useQuery } from 'react-query';
import { databaseApi } from '../services/api';
import { DatabaseStats } from '../types';

interface DataDistributionProps {
  stats: DatabaseStats | undefined;
}

// Removed unused interface

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export const DataDistribution: React.FC<DataDistributionProps> = ({ stats }) => {
  const [chartType, setChartType] = useState<'daily' | 'monthly' | 'yearly'>('monthly');
  const [dataType, setDataType] = useState<'records' | 'funds'>('records');

  const {
    data: distributionData,
    isLoading: distributionLoading,
    error: distributionError,
  } = useQuery(
    ['dataDistribution', chartType],
    () => databaseApi.getDataDistribution(chartType),
    {
      enabled: dataType === 'records',
    }
  );

  const {
    data: fundDistributionData,
    isLoading: fundDistributionLoading,
    error: fundDistributionError,
  } = useQuery(
    'fundTypeDistribution',
    () => databaseApi.getFundTypeDistribution(),
    {
      enabled: dataType === 'funds',
    }
  );

  const formatXAxisLabel = (value: string) => {
    switch (chartType) {
      case 'daily':
        return new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      case 'monthly':
        return new Date(value + '-01').toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
      case 'yearly':
        return value;
      default:
        return value;
    }
  };

  const renderChart = () => {
    if (dataType === 'funds') {
      if (fundDistributionLoading) {
        return (
          <Box display="flex" justifyContent="center" alignItems="center" height={400}>
            <CircularProgress />
          </Box>
        );
      }

      if (fundDistributionError) {
        return (
          <Alert severity="error">
            Failed to load fund distribution data.
          </Alert>
        );
      }

      const fundData = fundDistributionData?.distribution || [];
      
      if (fundData.length === 0) {
        return (
          <Alert severity="info">
            No fund distribution data available.
          </Alert>
        );
      }

      return (
        <ResponsiveContainer width="100%" height={400}>
          <PieChart>
            <Pie
              data={fundData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {fundData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      );
    }

    if (distributionLoading) {
      return (
        <Box display="flex" justifyContent="center" alignItems="center" height={400}>
          <CircularProgress />
        </Box>
      );
    }

    if (distributionError) {
      return (
        <Alert severity="error">
          Failed to load data distribution.
        </Alert>
      );
    }

    const data = distributionData?.distribution || [];
    
    if (data.length === 0) {
      return (
        <Alert severity="info">
          No data distribution available for the selected period.
        </Alert>
      );
    }

    return (
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="period" 
            tickFormatter={formatXAxisLabel}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis />
          <Tooltip 
            labelFormatter={(label) => `Period: ${formatXAxisLabel(label)}`}
            formatter={(value: number) => [value.toLocaleString(), 'Records']}
          />
          <Bar dataKey="count" fill="#8884d8" />
        </BarChart>
      </ResponsiveContainer>
    );
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Data Distribution Analysis
      </Typography>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Data Overview
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Total Records
                  </Typography>
                  <Typography variant="h6">
                    {stats?.totalRecords?.toLocaleString() || 0}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Unique Funds
                  </Typography>
                  <Typography variant="h6">
                    {stats?.fundCount || 0}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Date Range
                  </Typography>
                  <Typography variant="body2">
                    {stats?.dateRange?.start && stats?.dateRange?.end
                      ? `${new Date(stats.dateRange.start).toLocaleDateString()} - ${new Date(stats.dateRange.end).toLocaleDateString()}`
                      : 'N/A'
                    }
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Last Update
                  </Typography>
                  <Typography variant="body2">
                    {stats?.lastDownloadDate
                      ? new Date(stats.lastDownloadDate).toLocaleDateString()
                      : 'N/A'
                    }
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Chart Controls
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>Time Period</InputLabel>
                    <Select
                      value={chartType}
                      onChange={(e) => setChartType(e.target.value as any)}
                    >
                      <MenuItem value="daily">Daily</MenuItem>
                      <MenuItem value="monthly">Monthly</MenuItem>
                      <MenuItem value="yearly">Yearly</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>Data Type</InputLabel>
                    <Select
                      value={dataType}
                      onChange={(e) => setDataType(e.target.value as any)}
                    >
                      <MenuItem value="records">Records Count</MenuItem>
                      <MenuItem value="funds">Fund Distribution</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {dataType === 'funds' ? 'Fund Type Distribution' : `${chartType.charAt(0).toUpperCase() + chartType.slice(1)} Data Distribution`}
          </Typography>
          {renderChart()}
        </CardContent>
      </Card>
    </Box>
  );
};

export default DataDistribution;