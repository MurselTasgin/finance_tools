// finance_tools/frontend/src/components/DataRepository.tsx
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  LinearProgress,
  Alert,
  Chip,
  Divider,
  CircularProgress,
} from '@mui/material';
import {
  Download as DownloadIcon,
  Storage as StorageIcon,
  Schedule as ScheduleIcon,
  TrendingUp as TrendingUpIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { databaseApi } from '../services/api';
import { DatabaseStats, DownloadProgress } from '../types';
import { format } from 'date-fns';
import DownloadDataModal from './DownloadDataModal';
import DownloadProgressBar from './DownloadProgressBar';

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
  const [downloadProgress, setDownloadProgress] = useState<DownloadProgress>({
    isDownloading: false,
    progress: 0,
    status: '',
    records_downloaded: 0,
    total_records: 0,
    start_time: null,
    estimated_completion: null,
    current_phase: '',
  });
  const [showDownloadModal, setShowDownloadModal] = useState(false);

  const queryClient = useQueryClient();

  const {
    data: stats,
    isLoading: statsLoading,
    error: statsError,
    refetch: refetchStats,
  } = useQuery<DatabaseStats>('databaseStats', databaseApi.getStats, {
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Poll download progress only when downloading
  const {
    data: downloadProgressData,
    refetch: refetchProgress,
  } = useQuery<DownloadProgress>('downloadProgress', databaseApi.getDownloadProgress, {
    refetchInterval: downloadProgress.isDownloading ? 1000 : false, // Poll every second only when downloading
    enabled: downloadProgress.isDownloading, // Only enabled when downloading
  });

  const downloadMutation = useMutation(
    ({ startDate, endDate, kind, funds }: { startDate: string; endDate: string; kind: string; funds: string[] }) =>
      databaseApi.downloadData(startDate, endDate, kind, funds),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('databaseStats');
        // Progress will be updated via polling
      },
      onError: (error) => {
        setDownloadProgress({
          isDownloading: false,
          progress: 0,
          status: `Download failed: ${error}`,
          records_downloaded: 0,
          total_records: 0,
          start_time: null,
          estimated_completion: null,
          current_phase: 'error',
        });
      },
    }
  );

  // Sync local progress with server progress
  React.useEffect(() => {
    if (downloadProgressData) {
      console.log('Download progress data received:', downloadProgressData);
      // Always update progress data from server
      setDownloadProgress(downloadProgressData);
      
      // If download completed successfully, refresh stats
      if (!downloadProgressData.isDownloading && downloadProgressData.progress === 100) {
        queryClient.invalidateQueries('databaseStats');
      }
    }
  }, [downloadProgressData, queryClient]);

  const handleDownloadClick = () => {
    setShowDownloadModal(true);
  };

  const handleDownload = async (startDate: string, endDate: string, kind: string, funds: string[]) => {
    setDownloadProgress({
      isDownloading: true,
      progress: 0,
      status: 'Starting download...',
      records_downloaded: 0,
      total_records: 0,
      start_time: new Date().toISOString(),
      estimated_completion: null,
      current_phase: 'initializing',
    });

    try {
      await downloadMutation.mutateAsync({ startDate, endDate, kind, funds });
    } catch (error) {
      console.error('Download error:', error);
    }
  };

  const handleCloseModal = () => {
    setShowDownloadModal(false);
  };

  const handleRefresh = () => {
    refetchStats();
  };

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return 'Never';
    try {
      return format(new Date(dateString), 'PPpp');
    } catch {
      return 'Invalid date';
    }
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat().format(num);
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
      {/* Download Progress Bar */}
      {downloadProgress.isDownloading && (
        <DownloadProgressBar progress={downloadProgress} />
      )}

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Data Repository
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            sx={{ mr: 1 }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<DownloadIcon />}
            onClick={handleDownloadClick}
            disabled={downloadProgress.isDownloading}
            color="primary"
          >
            {downloadProgress.isDownloading ? 'Downloading...' : 'Download Data'}
          </Button>
        </Box>
      </Box>

      {downloadProgress.isDownloading && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Box>
            <Typography variant="body2" gutterBottom>
              {downloadProgress.status}
            </Typography>
            <LinearProgress
              variant="determinate"
              value={downloadProgress.progress}
              sx={{ mt: 1 }}
            />
          </Box>
        </Alert>
      )}

      {downloadProgress.status && !downloadProgress.isDownloading && (
        <Alert
          severity={downloadProgress.progress === 100 ? 'success' : 'error'}
          sx={{ mb: 2 }}
        >
          {downloadProgress.status}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Records"
            value={formatNumber(stats?.totalRecords || 0)}
            icon={<StorageIcon />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Unique Funds"
            value={formatNumber(stats?.fundCount || 0)}
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
            value={
              stats?.dateRange.start && stats?.dateRange.end
                ? `${format(new Date(stats.dateRange.start), 'MMM dd')} - ${format(
                    new Date(stats.dateRange.end),
                    'MMM dd, yyyy'
                  )}`
                : 'No data'
            }
            icon={<ScheduleIcon />}
            color="warning"
          />
        </Grid>
      </Grid>

      <Box mt={4}>
        <Typography variant="h6" gutterBottom>
          Database Information
        </Typography>
        <Card>
          <CardContent>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Box mb={2}>
                  <Typography variant="body2" color="textSecondary">
                    Data Source
                  </Typography>
                  <Chip label="TEFAS Database" color="primary" size="small" />
                </Box>
                <Box mb={2}>
                  <Typography variant="body2" color="textSecondary">
                    Last Updated
                  </Typography>
                  <Typography variant="body1">
                    {formatDate(stats?.lastDownloadDate)}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={6}>
                <Box mb={2}>
                  <Typography variant="body2" color="textSecondary">
                    Record Count
                  </Typography>
                  <Typography variant="body1">
                    {formatNumber(stats?.totalRecords || 0)} records
                  </Typography>
                </Box>
                <Box mb={2}>
                  <Typography variant="body2" color="textSecondary">
                    Fund Count
                  </Typography>
                  <Typography variant="body1">
                    {formatNumber(stats?.fundCount || 0)} unique funds
                  </Typography>
                </Box>
              </Grid>
            </Grid>
            <Divider sx={{ my: 2 }} />
            <Typography variant="body2" color="textSecondary">
              Use the "Download Data" button to fetch the latest fund data from TEFAS.
              This includes both investment funds (YAT) and pension funds (EMK).
              The process may take several minutes depending on the amount of data.
            </Typography>
          </CardContent>
        </Card>
      </Box>

      <DownloadDataModal
        open={showDownloadModal}
        onClose={handleCloseModal}
        onDownload={handleDownload}
        lastDownloadDate={stats?.lastDownloadDate || null}
      />
    </Box>
  );
};
