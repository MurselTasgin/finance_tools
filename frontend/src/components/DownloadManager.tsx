// finance_tools/frontend/src/components/DownloadManager.tsx
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
  CircularProgress,
  IconButton,
  Tooltip,
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
  Error as ErrorIcon,
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
import DetailedProgressViewer from './DetailedProgressViewer';

interface DownloadManagerProps {
  downloadProgress: DownloadProgress | undefined;
  activeTasks: { active_tasks: number; tasks: any[] } | undefined;
}

export const DownloadManager: React.FC<DownloadManagerProps> = ({ 
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

      {isDownloading && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Current Download Progress
            </Typography>
            
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
                <Typography variant="body1">
                  {downloadProgress?.records_downloaded || 0} / {downloadProgress?.total_records || 0}
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Phase
                </Typography>
                <Chip
                  label={downloadProgress?.current_phase || 'Unknown'}
                  color="primary"
                  size="small"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Task ID
                </Typography>
                <Typography variant="body2" fontFamily="monospace">
                  {downloadProgress?.task_id || 'N/A'}
                </Typography>
              </Grid>
            </Grid>

            {downloadProgress?.error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {downloadProgress.error}
              </Alert>
            )}

            {/* Detailed Progress Information */}
            {downloadProgress && <DetailedProgressViewer progress={downloadProgress} />}
          </CardContent>
        </Card>
      )}

      {hasActiveTasks && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Active Download Tasks
            </Typography>
            {activeTasks?.tasks.map((task, index) => (
              <Box key={task.task_id || index}>
                <Box display="flex" justifyContent="space-between" alignItems="center" py={1}>
                  <Box>
                    <Typography variant="body1">
                      {task.kind} funds from {task.start_date} to {task.end_date}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Started: {new Date(task.start_time).toLocaleString()}
                    </Typography>
                    {task.funds && task.funds.length > 0 && (
                      <Typography variant="body2" color="textSecondary">
                        Funds: {task.funds.join(', ')}
                      </Typography>
                    )}
                  </Box>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Chip
                      label={task.status}
                      color={task.status === 'running' ? 'warning' : 'success'}
                      size="small"
                    />
                    {task.status === 'running' && (
                      <CircularProgress size={20} />
                    )}
                  </Box>
                </Box>
                {index < (activeTasks?.tasks.length || 0) - 1 && <Divider />}
              </Box>
            ))}
          </CardContent>
        </Card>
      )}

      {!isDownloading && !hasActiveTasks && (
        <Card>
          <CardContent>
            <Box textAlign="center" py={4}>
              <DownloadIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                No Active Downloads
              </Typography>
              <Typography variant="body2" color="textSecondary" paragraph>
                Start a new download to begin collecting data from TEFAS
              </Typography>
              <Button
                variant="contained"
                startIcon={<DownloadIcon />}
                onClick={() => setShowDownloadModal(true)}
                size="large"
              >
                Start Download
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      <DownloadDataModal
        open={showDownloadModal}
        onClose={() => setShowDownloadModal(false)}
        onDownload={handleDownload}
        lastDownloadDate={null}
      />
    </Box>
  );
};

export default DownloadManager;
