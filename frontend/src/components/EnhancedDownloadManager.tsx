// finance_tools/frontend/src/components/EnhancedDownloadManager.tsx
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  LinearProgress,
  Alert,
  Divider,
  Collapse,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import {
  Download as DownloadIcon,
  Cancel as CancelIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Speed as SpeedIcon,
  Schedule as ScheduleIcon,
  Storage as StorageIcon,
} from '@mui/icons-material';
import { useMutation, useQueryClient } from 'react-query';
import { databaseApi } from '../services/api';
import { DownloadProgress } from '../types';
import DownloadDataModal from './DownloadDataModal';

interface EnhancedDownloadManagerProps {
  downloadProgress: DownloadProgress | undefined;
  activeTasks: { active_tasks: number; tasks: any[] } | undefined;
}

export const EnhancedDownloadManager: React.FC<EnhancedDownloadManagerProps> = ({ 
  downloadProgress, 
  activeTasks 
}) => {
  const [showDownloadModal, setShowDownloadModal] = useState(false);
  const [showDetailedProgress, setShowDetailedProgress] = useState(false);
  const queryClient = useQueryClient();

  const downloadMutation = useMutation(
    ({ startDate, endDate, kind, funds }: { startDate: string; endDate: string; kind: string; funds: string[] }) =>
      databaseApi.downloadData(startDate, endDate, kind, funds),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('databaseStats');
        queryClient.invalidateQueries('downloadProgress');
        queryClient.invalidateQueries('activeTasks');
      },
      onError: (error) => {
        console.error('Download failed:', error);
      },
    }
  );

  const cancelMutation = useMutation(
    (taskId: string) => databaseApi.cancelTask(taskId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('downloadProgress');
        queryClient.invalidateQueries('activeTasks');
      },
      onError: (error) => {
        console.error('Cancel failed:', error);
      },
    }
  );

  const isStuck = (startTime: string) => {
    const start = new Date(startTime);
    const now = new Date();
    const diffMinutes = (now.getTime() - start.getTime()) / (1000 * 60);
    return diffMinutes > 30;
  };

  const formatDuration = (startTime: string) => {
    const start = new Date(startTime);
    const now = new Date();
    const diffMs = now.getTime() - start.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMinutes / 60);
    
    if (diffHours > 0) {
      return `${diffHours}h ${diffMinutes % 60}m`;
    }
    return `${diffMinutes}m`;
  };

  const formatRecordsPerMinute = (rpm: number) => {
    if (rpm < 1) return '< 1/min';
    if (rpm < 1000) return `${Math.round(rpm)}/min`;
    return `${(rpm / 1000).toFixed(1)}k/min`;
  };

  const handleDownload = (startDate: string, endDate: string, kind: string, funds: string[]) => {
    downloadMutation.mutate({ startDate, endDate, kind, funds });
    setShowDownloadModal(false);
  };

  const isDownloading = downloadProgress?.is_downloading || false;
  const hasActiveTasks = (activeTasks?.active_tasks || 0) > 0;


  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" gutterBottom>
          Download Manager
        </Typography>
        <Button
          variant="contained"
          startIcon={<DownloadIcon />}
          onClick={() => setShowDownloadModal(true)}
          disabled={isDownloading || hasActiveTasks}
          size="large"
        >
          New Download
        </Button>
      </Box>

      {/* Total Downloaded Records Summary */}
      {downloadProgress && ((downloadProgress.records_downloaded || 0) > 0 || (downloadProgress.total_records || 0) > 0) && (
        <Card sx={{ mb: 3, bgcolor: 'primary.50' }}>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="center" mb={2}>
              <StorageIcon sx={{ mr: 2, fontSize: 32, color: 'primary.main' }} />
              <Box textAlign="center">
                <Typography variant="h3" color="primary" fontWeight="bold">
                  {(downloadProgress.records_downloaded || 0).toLocaleString()}
                </Typography>
                <Typography variant="h6" color="text.secondary">
                  Records Downloaded (Live)
                </Typography>
                {downloadProgress.total_records > 0 && (
                  <Typography variant="body2" color="info.main" sx={{ mt: 1 }}>
                    {Math.round(((downloadProgress.records_downloaded || 0) / downloadProgress.total_records) * 100)}% of {downloadProgress.total_records.toLocaleString()} total target
                  </Typography>
                )}
                {downloadProgress.current_chunk_info && (
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Chunks Completed: {Math.max(0, downloadProgress.current_chunk_info.chunk_number - 1)} / {downloadProgress.current_chunk_info.total_chunks} 
                    (Currently: Chunk {downloadProgress.current_chunk_info.chunk_number})
                  </Typography>
                )}
                {(downloadProgress.records_downloaded || 0) > 0 && (
                  <Box display="flex" alignItems="center" justifyContent="center" sx={{ mt: 1 }}>
                    <Box
                      sx={{
                        width: 8,
                        height: 8,
                        bgcolor: 'success.main',
                        borderRadius: '50%',
                        mr: 1,
                        animation: 'pulse 2s infinite',
                        '@keyframes pulse': {
                          '0%': { opacity: 1 },
                          '50%': { opacity: 0.5 },
                          '100%': { opacity: 1 },
                        },
                      }}
                    />
                    <Typography variant="caption" color="success.main">
                      Live updates with each chunk
                    </Typography>
                  </Box>
                )}
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Current Download Progress */}
      {(isDownloading || (activeTasks && activeTasks.active_tasks > 0)) && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Current Download Progress
              </Typography>
              <Box>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => setShowDetailedProgress(!showDetailedProgress)}
                  endIcon={showDetailedProgress ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                  sx={{ mr: 1 }}
                >
                  Details
                </Button>
                <Button
                  variant="outlined"
                  color="error"
                  size="small"
                  startIcon={<CancelIcon />}
                  onClick={() => downloadProgress?.task_id && cancelMutation.mutate(downloadProgress.task_id)}
                  disabled={cancelMutation.isLoading}
                >
                  Cancel
                </Button>
              </Box>
            </Box>
            
            {/* Stuck Task Warning */}
            {downloadProgress?.start_time && isStuck(downloadProgress.start_time) && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                <Box display="flex" alignItems="center">
                  <WarningIcon sx={{ mr: 1 }} />
                  <Typography variant="body2">
                    This task has been running for {formatDuration(downloadProgress.start_time)} and may be stuck.
                    Consider cancelling and retrying.
                  </Typography>
                </Box>
              </Alert>
            )}
            
            <Box mb={2}>
              <Box display="flex" justifyContent="space-between" mb={1}>
                <Typography variant="body2" color="textSecondary">
                  Progress
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  {downloadProgress?.progress || 0}%
                </Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={downloadProgress?.progress || 0} 
                sx={{ mb: 1 }}
              />
            </Box>

            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Status
                </Typography>
                <Typography variant="body1">
                  {downloadProgress?.status || 'Unknown'}
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Records Downloaded
                </Typography>
                <Box sx={{ p: 2, bgcolor: 'primary.50', borderRadius: 1, textAlign: 'center' }}>
                  <Typography variant="h4" color="primary" fontWeight="bold">
                    {(downloadProgress?.records_downloaded || 0).toLocaleString()}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    of {(downloadProgress?.total_records || 0).toLocaleString()} total
                  </Typography>
                  {(downloadProgress?.records_downloaded || 0) > 0 && (
                    <Typography variant="caption" color="success.main" display="block" sx={{ mt: 1 }}>
                      ✓ Updating in real-time
                    </Typography>
                  )}
                </Box>
              </Grid>
            </Grid>

            {/* Detailed Progress Information */}
            <Collapse in={showDetailedProgress}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle2" gutterBottom>
                Detailed Progress Information
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <Box display="flex" alignItems="center" mb={1}>
                    <SpeedIcon sx={{ mr: 1, color: 'text.secondary' }} />
                    <Typography variant="body2" color="textSecondary">
                      Processing Rate
                    </Typography>
                  </Box>
                  <Typography variant="body1">
                    {downloadProgress?.records_per_minute 
                      ? formatRecordsPerMinute(downloadProgress.records_per_minute)
                      : 'Calculating...'
                    }
                  </Typography>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Box display="flex" alignItems="center" mb={1}>
                    <ScheduleIcon sx={{ mr: 1, color: 'text.secondary' }} />
                    <Typography variant="body2" color="textSecondary">
                      Estimated Remaining
                    </Typography>
                  </Box>
                  <Typography variant="body1">
                    {downloadProgress?.estimated_remaining_minutes 
                      ? `${Math.round(downloadProgress.estimated_remaining_minutes)} minutes`
                      : 'Calculating...'
                    }
                  </Typography>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Box display="flex" alignItems="center" mb={1}>
                    <StorageIcon sx={{ mr: 1, color: 'text.secondary' }} />
                    <Typography variant="body2" color="textSecondary">
                      Last Activity
                    </Typography>
                  </Box>
                  <Typography variant="body1">
                    {downloadProgress?.last_activity 
                      ? new Date(downloadProgress.last_activity).toLocaleTimeString()
                      : 'Unknown'
                    }
                  </Typography>
                </Grid>
              </Grid>

              {/* Downloaded Records Log */}
              {downloadProgress?.detailed_messages && downloadProgress.detailed_messages.length > 0 && (
                <Box mt={2}>
                  <Typography variant="subtitle2" gutterBottom>
                    Downloaded Records Log
                  </Typography>
                  <List dense>
                    {downloadProgress.detailed_messages
                      .filter(message => message.type === 'success' && message.message.includes('rows'))
                      .slice(-8)
                      .map((message, index) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <CheckCircleIcon color="success" fontSize="small" />
                          </ListItemIcon>
                          <ListItemText
                            primary={message.message}
                            secondary={`${new Date(message.timestamp).toLocaleTimeString()} - Chunk ${message.chunk}`}
                          />
                        </ListItem>
                      ))}
                    {downloadProgress.detailed_messages.filter(message => message.type === 'success' && message.message.includes('rows')).length === 0 && (
                      <ListItem>
                        <ListItemIcon>
                          <WarningIcon color="warning" fontSize="small" />
                        </ListItemIcon>
                        <ListItemText
                          primary="No records downloaded yet..."
                          secondary="Waiting for data to be fetched..."
                        />
                      </ListItem>
                    )}
                  </List>
                </Box>
              )}
            </Collapse>
          </CardContent>
        </Card>
      )}

      {/* Active Tasks */}
      {activeTasks && (activeTasks.tasks.length > 0 || activeTasks.active_tasks > 0) && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Active Tasks ({activeTasks.active_tasks})
            </Typography>
            
            {activeTasks.tasks.map((task) => (
              <Card key={task.task_id} variant="outlined" sx={{ mb: 2 }}>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                    <Typography variant="subtitle1">
                      Task {task.task_id.substring(0, 8)}...
                    </Typography>
                    <Box>
                      {task.is_stuck && (
                        <Chip 
                          label="STUCK" 
                          color="error" 
                          size="small" 
                          sx={{ mr: 1 }}
                        />
                      )}
                      <Button
                        variant="outlined"
                        color="error"
                        size="small"
                        startIcon={<CancelIcon />}
                        onClick={() => cancelMutation.mutate(task.task_id)}
                        disabled={cancelMutation.isLoading}
                      >
                        Cancel
                      </Button>
                    </Box>
                  </Box>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={3}>
                      <Typography variant="body2" color="textSecondary">
                        Duration
                      </Typography>
                      <Typography variant="body1">
                        {formatDuration(task.start_time)}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} md={3}>
                      <Typography variant="body2" color="textSecondary">
                        Date Range
                      </Typography>
                      <Typography variant="body1">
                        {task.start_date} to {task.end_date}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} md={3}>
                      <Typography variant="body2" color="textSecondary">
                        Kind
                      </Typography>
                      <Typography variant="body1">
                        {task.kind}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} md={3}>
                      <Typography variant="body2" color="textSecondary">
                        Status
                      </Typography>
                      <Chip
                        label={task.status}
                        color={task.status === 'running' ? 'primary' : 'default'}
                        size="small"
                      />
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Download Modal */}
      <DownloadDataModal
        open={showDownloadModal}
        onClose={() => setShowDownloadModal(false)}
        onDownload={handleDownload}
        loading={downloadMutation.isLoading}
        lastDownloadDate={null}
      />
    </Box>
  );
};

export default EnhancedDownloadManager;
