// finance_tools/frontend/src/components/DataRepository.tsx
import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Storage as StorageIcon,
  Schedule as ScheduleIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { databaseApi } from '../services/api';
import { DatabaseStats } from '../types';
import { format } from 'date-fns';

const StatCard: React.FC<{
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
}> = ({ title, value, icon, color = 'primary' }) => (
  <Card>
    <CardContent>
      <Box display="flex" alignItems="center" justifyContent="space-between">
        <Box>
          <Typography color="textSecondary" gutterBottom variant="body2">
            {title}
          </Typography>
          <Typography variant="h4" component="div" color={`${color}.main`}>
            {value}
          </Typography>
        </Box>
        <Box color={`${color}.main`}>{icon}</Box>
      </Box>
    </CardContent>
  </Card>
);

export const DataRepository: React.FC = () => {
  const {
    data: stats,
    isLoading: statsLoading,
    error: statsError,
  } = useQuery<DatabaseStats>('databaseStats', databaseApi.getStats, {
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return 'N/A';
    try {
      return format(new Date(dateString), 'MMM dd, yyyy');
    } catch {
      return 'Invalid Date';
    }
  };

  const getDateRange = () => {
    if (!stats?.dateRange) return 'N/A';
    const { start, end } = stats.dateRange;
    if (!start || !end) return 'N/A';
    return `${formatDate(start)} - ${formatDate(end)}`;
  };

  if (statsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (statsError) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Failed to load database statistics. Please try again.
      </Alert>
    );
  }

  return (
    <Box>
      <Box mb={3}>
        <Typography variant="h4" component="h1" gutterBottom>
          Data Repository
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Overview of your financial data repository
        </Typography>
      </Box>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Records"
            value={stats?.totalRecords?.toLocaleString() || 0}
            icon={<StorageIcon />}
            color="primary"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Unique Funds"
            value={stats?.fundCount || 0}
            icon={<TrendingUpIcon />}
            color="secondary"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Last Download"
            value={formatDate(stats?.lastDownloadDate)}
            icon={<ScheduleIcon />}
            color="success"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Data Range"
            value={getDateRange()}
            icon={<ScheduleIcon />}
            color="primary"
          />
        </Grid>
      </Grid>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Database Information
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Total Records
              </Typography>
              <Typography variant="h6">
                {stats?.totalRecords?.toLocaleString() || 0}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Unique Funds
              </Typography>
              <Typography variant="h6">
                {stats?.fundCount || 0}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Date Range
              </Typography>
              <Typography variant="body1">
                {getDateRange()}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Last Update
              </Typography>
              <Typography variant="body1">
                {formatDate(stats?.lastDownloadDate)}
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Box mt={3}>
        <Alert severity="info">
          <Typography variant="body2">
            <strong>Note:</strong> To download new data or manage downloads, 
            please use the <strong>Data Management</strong> tab.
          </Typography>
        </Alert>
      </Box>
    </Box>
  );
};

export default DataRepository;