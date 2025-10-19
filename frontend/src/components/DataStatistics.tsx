// finance_tools/frontend/src/components/DataStatistics.tsx
import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  LinearProgress,
  Alert,
  Divider,
} from '@mui/material';
import {
  Storage as StorageIcon,
  Schedule as ScheduleIcon,
  TrendingUp as TrendingUpIcon,
  Download as DownloadIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { useQuery } from 'react-query';
import { databaseApi, stockApi } from '../services/api';
import { DatabaseStats, DownloadProgress } from '../types';

interface DataStatisticsProps {
  stats: DatabaseStats | undefined;
  downloadProgress?: DownloadProgress | undefined;
  activeTasks?: { active_tasks: number; tasks: any[] } | undefined;
}

const StatCard: React.FC<{
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  subtitle?: string;
}> = ({ title, value, icon, color = 'primary', subtitle }) => (
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
          {subtitle && (
            <Typography variant="body2" color="textSecondary">
              {subtitle}
            </Typography>
          )}
        </Box>
        <Box color={`${color}.main`}>{icon}</Box>
      </Box>
    </CardContent>
  </Card>
);

export const DataStatistics: React.FC<DataStatisticsProps> = ({ 
  stats, 
  downloadProgress, 
  activeTasks 
}) => {
  const {
    data: downloadStats,
  } = useQuery('downloadStatistics', databaseApi.getDownloadStatistics, {
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const {
    data: stockStats,
  } = useQuery('stockStats', stockApi.getStats, {
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

  const getDownloadStatus = () => {
    if (!downloadProgress) return { status: 'Unknown', color: 'default' as const };
    
    if (downloadProgress.is_downloading) {
      return { status: 'Downloading...', color: 'warning' as const };
    } else if (downloadProgress.error) {
      return { status: 'Error', color: 'error' as const };
    } else if (downloadProgress.current_phase === 'completed') {
      return { status: 'Completed', color: 'success' as const };
    } else {
      return { status: 'Ready', color: 'default' as const };
    }
  };

  const downloadStatus = getDownloadStatus();

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Database Statistics
      </Typography>
      
      <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
        TEFAS Fund Data
      </Typography>
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Fund Records"
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
            subtitle="Most recent data"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Downloads"
            value={activeTasks?.active_tasks || 0}
            icon={<DownloadIcon />}
            color="warning"
            subtitle="Currently running"
          />
        </Grid>
      </Grid>

      <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
        Stock Data
      </Typography>
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Stock Records"
            value={stockStats?.totalRecords?.toLocaleString() || 0}
            icon={<StorageIcon />}
            color="primary"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Unique Symbols"
            value={stockStats?.symbolCount || 0}
            icon={<TrendingUpIcon />}
            color="secondary"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Stock Date Range"
            value={
              stockStats?.dateRange?.start && stockStats?.dateRange?.end
                ? `${formatDate(stockStats.dateRange.start)} - ${formatDate(stockStats.dateRange.end)}`
                : 'No data'
            }
            icon={<ScheduleIcon />}
            color="success"
            subtitle="Coverage period"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Stock Downloads"
            value={stockStats?.downloads?.total_downloads || 0}
            icon={<DownloadIcon />}
            color="success"
            subtitle={`${stockStats?.downloads?.successful_downloads || 0} successful`}
          />
        </Grid>
      </Grid>

      <Divider sx={{ my: 3 }} />

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Data Coverage
              </Typography>
              <Box mb={2}>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Date Range
                </Typography>
                <Typography variant="h6">
                  {getDateRange()}
                </Typography>
              </Box>
              <Box mb={2}>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Data Freshness
                </Typography>
                <Typography variant="body1">
                  {stats?.lastDownloadDate 
                    ? `Last updated ${formatDate(stats.lastDownloadDate)}`
                    : 'No data available'
                  }
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Download Status
              </Typography>
              <Box display="flex" alignItems="center" mb={2}>
                <Chip
                  label={downloadStatus.status}
                  color={downloadStatus.color}
                  icon={downloadStatus.color === 'success' ? <CheckCircleIcon /> : 
                        downloadStatus.color === 'error' ? <ErrorIcon /> : 
                        downloadStatus.color === 'warning' ? <DownloadIcon /> : undefined}
                />
              </Box>
              
              {downloadProgress?.is_downloading && (
                <Box>
                  <Box display="flex" justifyContent="space-between" mb={1}>
                    <Typography variant="body2" color="textSecondary">
                      Progress
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      {downloadProgress.progress}%
                    </Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={downloadProgress.progress} 
                    sx={{ mb: 1 }}
                  />
                  <Typography variant="body2" color="textSecondary">
                    {downloadProgress.records_downloaded} / {downloadProgress.total_records} records
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    {downloadProgress.status}
                  </Typography>
                </Box>
              )}

              {downloadProgress?.error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {downloadProgress.error}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {downloadStats && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Download Statistics
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="textSecondary">
                  Total Downloads
                </Typography>
                <Typography variant="h6">
                  {downloadStats.total_downloads}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="textSecondary">
                  Successful
                </Typography>
                <Typography variant="h6" color="success.main">
                  {downloadStats.successful_downloads}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="textSecondary">
                  Failed
                </Typography>
                <Typography variant="h6" color="error.main">
                  {downloadStats.failed_downloads}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="textSecondary">
                  Records Downloaded
                </Typography>
                <Typography variant="h6">
                  {downloadStats.total_records_downloaded?.toLocaleString() || 0}
                </Typography>
              </Grid>
            </Grid>
            {downloadStats.date_range?.start && downloadStats.date_range?.end && (
              <Box mt={2}>
                <Typography variant="body2" color="textSecondary">
                  Download Period: {formatDate(downloadStats.date_range.start)} - {formatDate(downloadStats.date_range.end)}
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {activeTasks && activeTasks.tasks.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Active Download Tasks
            </Typography>
            {activeTasks.tasks.map((task, index) => (
              <Box key={task.task_id || index}>
                <Box display="flex" justifyContent="space-between" alignItems="center" py={1}>
                  <Box>
                    <Typography variant="body1">
                      {task.kind} funds from {task.start_date} to {task.end_date}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Started: {formatDate(task.start_time)}
                    </Typography>
                  </Box>
                  <Chip
                    label={task.status}
                    color={task.status === 'running' ? 'warning' : 'success'}
                    size="small"
                  />
                </Box>
                {index < activeTasks.tasks.length - 1 && <Divider />}
              </Box>
            ))}
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default DataStatistics;
