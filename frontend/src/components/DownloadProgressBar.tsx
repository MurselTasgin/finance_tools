// finance_tools/frontend/src/components/DownloadProgressBar.tsx
import React from 'react';
import {
  Box,
  LinearProgress,
  Typography,
  Card,
  CardContent,
  Chip,
  Grid,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Download as DownloadIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { DownloadProgress } from '../types';
import { format } from 'date-fns';

interface DownloadProgressBarProps {
  progress: DownloadProgress;
}

const DownloadProgressBar: React.FC<DownloadProgressBarProps> = ({ progress }) => {
  console.log('DownloadProgressBar rendered with progress:', progress);
  
  const formatTime = (timeString: string | null) => {
    if (!timeString) return 'Calculating...';
    try {
      return format(new Date(timeString), 'HH:mm:ss');
    } catch {
      return 'Invalid time';
    }
  };

  const formatDuration = (startTime: string | null, endTime: string | null) => {
    if (!startTime) return '0s';
    try {
      const start = new Date(startTime);
      const end = endTime ? new Date(endTime) : new Date();
      const diffMs = end.getTime() - start.getTime();
      const diffSeconds = Math.floor(diffMs / 1000);
      
      if (diffSeconds < 60) return `${diffSeconds}s`;
      const minutes = Math.floor(diffSeconds / 60);
      const seconds = diffSeconds % 60;
      return `${minutes}m ${seconds}s`;
    } catch {
      return '0s';
    }
  };

  const getPhaseIcon = (phase: string) => {
    switch (phase) {
      case 'crawling':
        return <DownloadIcon color="primary" />;
      case 'saving':
        return <CircularProgress size={20} />;
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <ScheduleIcon color="action" />;
    }
  };

  const getPhaseColor = (phase: string) => {
    switch (phase) {
      case 'crawling':
        return 'primary';
      case 'saving':
        return 'info';
      case 'completed':
        return 'success';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getPhaseLabel = (phase: string) => {
    switch (phase) {
      case 'initializing':
        return 'Initializing';
      case 'crawling':
        return 'Crawling Data';
      case 'saving':
        return 'Saving to Database';
      case 'completed':
        return 'Completed';
      case 'error':
        return 'Error';
      default:
        return 'Unknown';
    }
  };

  if (!progress.isDownloading && progress.progress === 0) {
    return null;
  }

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          {getPhaseIcon(progress.current_phase)}
          <Typography variant="h6" sx={{ ml: 1, flexGrow: 1 }}>
            Download Progress
          </Typography>
          <Chip
            label={getPhaseLabel(progress.current_phase)}
            color={getPhaseColor(progress.current_phase) as any}
            size="small"
          />
        </Box>

        {/* Progress Bar */}
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2" color="text.secondary">
              {progress.status}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {progress.progress}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={progress.progress}
            sx={{ height: 8, borderRadius: 4 }}
          />
        </Box>

        {/* Statistics Grid */}
        <Grid container spacing={2}>
          <Grid item xs={6} sm={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="primary">
                {progress.records_downloaded.toLocaleString()}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Records Downloaded
              </Typography>
            </Box>
          </Grid>
          
          <Grid item xs={6} sm={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="text.primary">
                {progress.total_records.toLocaleString()}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Total Records
              </Typography>
            </Box>
          </Grid>
          
          <Grid item xs={6} sm={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="text.primary">
                {formatDuration(progress.start_time, null)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Elapsed Time
              </Typography>
            </Box>
          </Grid>
          
          <Grid item xs={6} sm={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="text.primary">
                {formatTime(progress.estimated_completion)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                ETA
              </Typography>
            </Box>
          </Grid>
        </Grid>

        {/* Rate Information */}
        {progress.records_downloaded > 0 && progress.start_time && (
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Rate: {Math.round(progress.records_downloaded / ((new Date().getTime() - new Date(progress.start_time).getTime()) / 1000))} records/sec
            </Typography>
          </Box>
        )}

        {/* Error Display */}
        {progress.current_phase === 'error' && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {progress.status}
          </Alert>
        )}

        {/* Success Message */}
        {progress.current_phase === 'completed' && (
          <Alert severity="success" sx={{ mt: 2 }}>
            {progress.status}
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default DownloadProgressBar;
