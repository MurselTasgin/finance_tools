// finance_tools/frontend/src/components/DownloadTaskDetails.tsx
import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  IconButton,
  Tooltip,
  CircularProgress,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Storage as StorageIcon,
  Timeline as TimelineIcon,
  AccountBalance as FundIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { databaseApi } from '../services/api';
import { format } from 'date-fns';

interface DownloadTaskDetailsProps {
  taskId: string;
  onClose: () => void;
}

const DownloadTaskDetails: React.FC<DownloadTaskDetailsProps> = ({ taskId, onClose }) => {
  const [expandedSections, setExpandedSections] = useState<{
    progressLogs: boolean;
    statistics: boolean;
    taskInfo: boolean;
  }>({
    progressLogs: true,
    statistics: true,
    taskInfo: true,
  });

  const { data, isLoading, error, refetch } = useQuery(
    ['downloadTaskDetails', taskId],
    () => databaseApi.getDownloadTaskDetails(taskId),
    {
      refetchInterval: 5000, // Refetch every 5 seconds for live updates
    }
  );

  const handleSectionToggle = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const getMessageIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircleIcon color="success" fontSize="small" />;
      case 'warning':
        return <WarningIcon color="warning" fontSize="small" />;
      case 'error':
        return <ErrorIcon color="error" fontSize="small" />;
      default:
        return <InfoIcon color="info" fontSize="small" />;
    }
  };

  const getMessageColor = (type: string) => {
    switch (type) {
      case 'success':
        return 'success.main';
      case 'warning':
        return 'warning.main';
      case 'error':
        return 'error.main';
      default:
        return 'text.primary';
    }
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  const formatTime = (timestamp: string) => {
    try {
      return format(new Date(timestamp), 'HH:mm:ss');
    } catch {
      return 'Invalid time';
    }
  };

  const formatDateTime = (timestamp: string) => {
    try {
      return format(new Date(timestamp), 'yyyy-MM-dd HH:mm:ss');
    } catch {
      return 'Invalid date';
    }
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Failed to load download task details. Please try again.
      </Alert>
    );
  }

  if (!data) {
    return (
      <Alert severity="warning" sx={{ mb: 2 }}>
        Download task not found.
      </Alert>
    );
  }

  const { task_info, progress_logs, statistics } = data;

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">
          Download Task Details
        </Typography>
        <Box>
          <Tooltip title="Refresh">
            <IconButton onClick={() => refetch()} size="small">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Task Information */}
      <Accordion 
        expanded={expandedSections.taskInfo}
        onChange={() => handleSectionToggle('taskInfo')}
        sx={{ mb: 2 }}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box display="flex" alignItems="center">
            <TimelineIcon sx={{ mr: 1 }} />
            <Typography variant="h6">Task Information</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Task ID
              </Typography>
              <Typography variant="body1" fontFamily="monospace">
                {task_info.task_id}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Status
              </Typography>
              <Chip
                label={task_info.status}
                color={task_info.status === 'completed' ? 'success' : 
                       task_info.status === 'failed' ? 'error' : 'warning'}
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Date Range
              </Typography>
              <Typography variant="body1">
                {task_info.start_date} to {task_info.end_date}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Fund Type
              </Typography>
              <Typography variant="body1">
                {task_info.kind}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Start Time
              </Typography>
              <Typography variant="body1">
                {formatDateTime(task_info.start_time)}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                End Time
              </Typography>
              <Typography variant="body1">
                {task_info.end_time ? formatDateTime(task_info.end_time) : 'Still running...'}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Records Downloaded
              </Typography>
              <Typography variant="h6" color="primary">
                {task_info.records_downloaded.toLocaleString()}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Total Records
              </Typography>
              <Typography variant="h6" color="primary">
                {task_info.total_records.toLocaleString()}
              </Typography>
            </Grid>
            {task_info.funds && task_info.funds.length > 0 && (
              <Grid item xs={12}>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Funds
                </Typography>
                <Box display="flex" flexWrap="wrap" gap={1}>
                  {task_info.funds.map((fund, index) => (
                    <Chip key={index} label={fund} size="small" />
                  ))}
                </Box>
              </Grid>
            )}
            {task_info.error_message && (
              <Grid item xs={12}>
                <Alert severity="error">
                  <Typography variant="body2">
                    <strong>Error:</strong> {task_info.error_message}
                  </Typography>
                </Alert>
              </Grid>
            )}
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Statistics */}
      <Accordion 
        expanded={expandedSections.statistics}
        onChange={() => handleSectionToggle('statistics')}
        sx={{ mb: 2 }}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box display="flex" alignItems="center">
            <StorageIcon sx={{ mr: 1 }} />
            <Typography variant="h6">Statistics</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={6} sm={3}>
              <Box textAlign="center">
                <Typography variant="h6" color="primary">
                  {statistics.total_messages}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Total Messages
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Box textAlign="center">
                <Typography variant="h6" color="success.main">
                  {statistics.success_messages}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Success
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Box textAlign="center">
                <Typography variant="h6" color="warning.main">
                  {statistics.warning_messages}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Warnings
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Box textAlign="center">
                <Typography variant="h6" color="error.main">
                  {statistics.error_messages}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Errors
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Box textAlign="center">
                <Typography variant="h6" color="info.main">
                  {statistics.total_records_from_logs.toLocaleString()}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Records from Logs
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Box textAlign="center">
                <Typography variant="h6" color="text.primary">
                  {formatDuration(statistics.duration_seconds)}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Duration
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Progress Logs */}
      <Accordion 
        expanded={expandedSections.progressLogs}
        onChange={() => handleSectionToggle('progressLogs')}
        sx={{ mb: 2 }}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box display="flex" alignItems="center">
            <FundIcon sx={{ mr: 1 }} />
            <Typography variant="h6">Progress Logs ({progress_logs.length})</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
            <Table stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>Time</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Message</TableCell>
                  <TableCell>Fund</TableCell>
                  <TableCell>Records</TableCell>
                  <TableCell>Chunk</TableCell>
                  <TableCell>Progress</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {progress_logs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell>
                      <Typography variant="caption">
                        {formatTime(log.timestamp)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box display="flex" alignItems="center">
                        {getMessageIcon(log.message_type)}
                        <Typography variant="caption" sx={{ ml: 1 }}>
                          {log.message_type}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          color: getMessageColor(log.message_type),
                          maxWidth: 300,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}
                      >
                        {log.message}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">
                        {log.fund_name || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">
                        {log.records_count ? log.records_count.toLocaleString() : '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">
                        {log.chunk_number}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">
                        {log.progress_percent}%
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};

export default DownloadTaskDetails;
