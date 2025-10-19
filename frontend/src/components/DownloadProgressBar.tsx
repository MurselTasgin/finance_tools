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

  if (!progress.is_downloading && progress.progress === 0) {
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
            <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'primary.50', borderRadius: 1 }}>
              <Typography variant="h5" color="primary" fontWeight="bold">
                {(progress.records_downloaded || 0).toLocaleString()}
              </Typography>
              <Typography variant="caption" color="text.secondary" fontWeight="medium">
                Records Downloaded
              </Typography>
              {(progress.records_downloaded || 0) > 0 && (
                <Box display="flex" alignItems="center" justifyContent="center" sx={{ mt: 0.5 }}>
                  <Box
                    sx={{
                      width: 6,
                      height: 6,
                      bgcolor: 'success.main',
                      borderRadius: '50%',
                      mr: 0.5,
                      animation: 'pulse 2s infinite',
                      '@keyframes pulse': {
                        '0%': { opacity: 1 },
                        '50%': { opacity: 0.5 },
                        '100%': { opacity: 1 },
                      },
                    }}
                  />
                  <Typography variant="caption" color="success.main">
                    Live Updates
                  </Typography>
                </Box>
              )}
            </Box>
          </Grid>
          
          <Grid item xs={6} sm={3}>
            <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="h5" color="text.primary" fontWeight="bold">
                {(progress.total_records || 0).toLocaleString()}
              </Typography>
              <Typography variant="caption" color="text.secondary" fontWeight="medium">
                Total Records Target
              </Typography>
              {(progress.total_records || 0) > 0 && (
                <Typography variant="caption" color="info.main" display="block">
                  {Math.round(((progress.records_downloaded || 0) / (progress.total_records || 1)) * 100)}% Complete
                </Typography>
              )}
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

        {/* Chunk Progress Row */}
        {progress.current_chunk_info && (
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'info.50', borderRadius: 1 }}>
                <Typography variant="h6" color="info.main" fontWeight="bold">
                  {Math.max(0, progress.current_chunk_info.chunk_number - 1)} / {progress.current_chunk_info.total_chunks}
                </Typography>
                <Typography variant="caption" color="text.secondary" fontWeight="medium">
                  Chunks Completed
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                  Currently processing chunk {progress.current_chunk_info.chunk_number}
                </Typography>
              </Box>
            </Grid>
          </Grid>
        )}

        {/* Rate Information */}
        {(progress.records_downloaded || 0) > 0 && progress.start_time && (
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Rate: {Math.round((progress.records_downloaded || 0) / ((new Date().getTime() - new Date(progress.start_time).getTime()) / 1000))} records/sec
            </Typography>
          </Box>
        )}

        {/* Chunk Information */}
        {progress.current_chunk_info && (
          <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Chunks Completed: {Math.max(0, progress.current_chunk_info.chunk_number - 1)} / {progress.current_chunk_info.total_chunks}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Current Chunk: {progress.current_chunk_info.chunk_number} of {progress.current_chunk_info.total_chunks}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Date Range: {progress.current_chunk_info.start_date} to {progress.current_chunk_info.end_date}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Total Records Target
                </Typography>
                <Typography variant="h6" color="primary">
                  {(progress.total_records || 0).toLocaleString()}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Expected total records to download
                </Typography>
              </Grid>
            </Grid>
          </Box>
        )}

        {/* Fund Progress Summary */}
        {progress.fund_progress && Object.keys(progress.fund_progress).length > 0 && (
          <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Fund Progress: {Object.values(progress.fund_progress).filter(f => f.status === 'success').length} / {Object.keys(progress.fund_progress).length} successful
                </Typography>
                {Object.values(progress.fund_progress).some(f => f.status === 'error') && (
                  <Typography variant="body2" color="error">
                    {Object.values(progress.fund_progress).filter(f => f.status === 'error').length} funds with errors
                  </Typography>
                )}
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Records from Funds:
                </Typography>
                <Typography variant="h6" color="primary">
                  {Object.values(progress.fund_progress).reduce((sum, fund) => sum + (fund.rows || 0), 0).toLocaleString()}
                </Typography>
              </Grid>
            </Grid>
          </Box>
        )}

        {/* Downloaded Records Log */}
        {progress.detailed_messages && progress.detailed_messages.length > 0 && (
          <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Downloaded Records Log:
            </Typography>
            <Box sx={{ maxHeight: 120, overflowY: 'auto' }}>
              {progress.detailed_messages
                .filter(message => message.type === 'success' && message.message.includes('rows'))
                .slice(-8)
                .map((message, index) => (
                  <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                    <Typography 
                      variant="caption" 
                      sx={{ 
                        color: 'success.main',
                        fontSize: '0.75rem',
                        fontWeight: 'medium'
                      }}
                    >
                      {message.message}
                    </Typography>
                    <Typography variant="caption" color="textSecondary" sx={{ fontSize: '0.7rem' }}>
                      {formatTime(message.timestamp)}
                    </Typography>
                  </Box>
                ))}
              {progress.detailed_messages.filter(message => message.type === 'success' && message.message.includes('rows')).length === 0 && (
                <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                  No records downloaded yet...
                </Typography>
              )}
            </Box>
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
