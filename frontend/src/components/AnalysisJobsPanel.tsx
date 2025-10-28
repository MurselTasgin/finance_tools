// frontend/src/components/AnalysisJobsPanel.tsx
/**
 * Analysis Jobs Panel
 * 
 * Displays all analysis tasks (active and completed) with real-time progress tracking.
 * Mirrors the DownloadJobs pattern to provide consistent UX for background task management.
 * 
 * Features:
 * - Real-time progress tracking for running analyses
 * - Task history with filtering and sorting
 * - Detailed logs and execution statistics
 * - Cancel running tasks
 * - Re-run completed/failed tasks
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Button,
  Grid,
  TextField,
  InputAdornment,
  TablePagination,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Collapse,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import AnalysisResultsViewer from './AnalysisResultsViewer';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Cancel as CancelIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
  Autorenew as RerunIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import { format, formatDistanceToNow } from 'date-fns';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { analyticsApi } from '../services/api';

interface AnalysisJobsPanelProps {
  onRerunRequest?: (analysisType: string, parameters: any) => void;
}

export const AnalysisJobsPanel: React.FC<AnalysisJobsPanelProps> = ({ onRerunRequest }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [expandedJobId, setExpandedJobId] = useState<string | null>(null);
  const [rerunDialogOpen, setRerunDialogOpen] = useState(false);
  const [selectedJobForRerun, setSelectedJobForRerun] = useState<any>(null);
  const [resultsDialogOpen, setResultsDialogOpen] = useState(false);
  const [selectedJobResults, setSelectedJobResults] = useState<any>(null);
  const queryClient = useQueryClient();

  // Fetch active tasks
  const { data: activeTasks } = useQuery(
    'analysisActiveTasks',
    analyticsApi.getActiveTasks,
    {
      refetchInterval: 2000, // Poll every 2 seconds
    }
  );

  // Fetch analysis history
  const {
    data: rawHistoryData,
    isLoading: historyLoading,
    error: historyError,
  } = useQuery(
    ['analysisHistory', page + 1, rowsPerPage, searchTerm, statusFilter, typeFilter],
    () => analyticsApi.getAnalysisHistory({
      page: page + 1,
      limit: rowsPerPage,
      analysis_type: typeFilter || undefined,
      status: statusFilter || undefined,
    }),
    {
      keepPreviousData: true,
      refetchInterval: 5000, // Refetch every 5 seconds to show updates
    }
  );

  // Check if job is active
  const isJobActive = (taskId: string): boolean => {
    return activeTasks?.tasks.some(task => task.task_id === taskId) || false;
  };

  // Fetch progress for expanded active job
  const { data: analysisProgress } = useQuery<any>(
    ['analysisProgress', expandedJobId],
    () => analyticsApi.getAnalysisProgress(),
    {
      refetchInterval: 1000, // Poll every second
      enabled: expandedJobId !== null && isJobActive(expandedJobId),
    }
  );

  // Fetch task details for expanded job
  const { data: jobDetails, isLoading: detailsLoading } = useQuery(
    ['analysisTaskDetails', expandedJobId],
    () => analyticsApi.getAnalysisTaskDetails(expandedJobId!),
    {
      enabled: expandedJobId !== null,
      refetchInterval: (data) => {
        if (!expandedJobId) return false;
        if (isJobActive(expandedJobId)) {
          return 2000; // Poll every 2 seconds for active jobs
        }
        return false; // Don't poll for completed jobs
      },
    }
  );

  // Cancel mutation
  const cancelMutation = useMutation(
    (taskId: string) => analyticsApi.cancelAnalysis(taskId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('analysisActiveTasks');
        queryClient.invalidateQueries('analysisHistory');
      },
      onError: (error: any) => {
        console.error('Cancel failed:', error);
      },
    }
  );

  // Rerun mutation
  const rerunMutation = useMutation(
    async () => {
      if (!selectedJobForRerun) return Promise.reject('No job selected');
      
      // If onRerunRequest is provided, use it to navigate to form with parameters
      if (onRerunRequest && selectedJobForRerun.analysis_type === 'stock_scan') {
        console.log('Rerun mutation - passing parameters:', {
          analysisType: selectedJobForRerun.analysis_type,
          parameters: selectedJobForRerun.parameters,
          hasScannerConfigs: !!selectedJobForRerun.parameters?.scanner_configs,
          hasWeights: !!selectedJobForRerun.parameters?.weights
        });
        
        onRerunRequest(selectedJobForRerun.analysis_type, selectedJobForRerun.parameters || {});
        setRerunDialogOpen(false);
        setSelectedJobForRerun(null);
        // Return a consistent response structure
        return { task_id: '', message: 'Navigating to form...' };
      }
      
      // Otherwise, use the API to rerun directly
      return await analyticsApi.startAnalysis(
        selectedJobForRerun.analysis_type,
        selectedJobForRerun.analysis_name,
        selectedJobForRerun.parameters || {}
      );
    },
    {
      onSuccess: () => {
        if (!selectedJobForRerun || selectedJobForRerun.analysis_type === 'stock_scan') {
          // For stock_scan, navigation is handled above
          return;
        }
        queryClient.invalidateQueries('analysisActiveTasks');
        queryClient.invalidateQueries('analysisHistory');
        setRerunDialogOpen(false);
        setSelectedJobForRerun(null);
      },
      onError: (error: any) => {
        console.error('Rerun failed:', error);
      },
    }
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'info';
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'cancelled':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <CircularProgress size={20} />;
      case 'completed':
        return <CheckCircleIcon />;
      case 'failed':
        return <ErrorIcon />;
      case 'cancelled':
        return <WarningIcon />;
      default:
        return <InfoIcon />;
    }
  };

  const formatDuration = (startTime: string | null, endTime: string | null) => {
    if (!startTime) return '-';
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const diffMs = end.getTime() - start.getTime();
    const diffSecs = Math.floor(diffMs / 1000);
    const hours = Math.floor(diffSecs / 3600);
    const minutes = Math.floor((diffSecs % 3600) / 60);
    const seconds = diffSecs % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m ${seconds}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    } else {
      return `${seconds}s`;
    }
  };

  const handleCancel = (taskId: string) => {
    if (window.confirm('Are you sure you want to cancel this analysis?')) {
      cancelMutation.mutate(taskId);
    }
  };

  const handleRerun = async (job: any) => {
    // Fetch complete task details to ensure we have all parameters
    let enhancedJob = job;
    try {
      const detailsResponse = await analyticsApi.getAnalysisTaskDetails(job.task_id);
      if (detailsResponse?.task_info?.parameters) {
        enhancedJob = {
          ...job,
          parameters: {
            ...job.parameters,
            ...detailsResponse.task_info.parameters,
            // Ensure scanner_configs and weights are included
            scanner_configs: detailsResponse.task_info.parameters.scanner_configs || job.parameters?.scanner_configs,
            weights: detailsResponse.task_info.parameters.weights || job.parameters?.weights,
          }
        };
      }
    } catch (error) {
      console.warn('Could not fetch task details for rerun, using job parameters:', error);
    }
    
    setSelectedJobForRerun(enhancedJob);
    setRerunDialogOpen(true);
  };

  const handleViewResults = async (job: any) => {
    try {
      // Fetch results from the API using result_id
      if (job.result_id) {
        const response = await fetch(`/api/analytics/results/${job.result_id}`);
        if (response.ok) {
          const resultData = await response.json();
          
          // Fetch task details to get complete parameter information
          let enhancedParameters = job.parameters || resultData.parameters || {};
          try {
            const detailsResponse = await analyticsApi.getAnalysisTaskDetails(job.task_id);
            if (detailsResponse?.task_info?.parameters) {
              enhancedParameters = detailsResponse.task_info.parameters;
            }
          } catch (error) {
            console.warn('Could not fetch task details:', error);
          }
          
          // Use the API response but enrich with complete parameters
          setSelectedJobResults({
            ...resultData,
            parameters: enhancedParameters
          });
        } else {
          console.error('Failed to fetch results:', response.statusText);
          // Fallback to job info
          setSelectedJobResults({
            analysis_type: job.analysis_type,
            analysis_name: job.analysis_name,
            parameters: job.parameters || {},
            results: [],
            result_count: 0,
            execution_time_ms: job.execution_time_ms || 0,
            timestamp: job.start_time || job.created_at,
            metadata: {}
          });
        }
      } else {
        // Use job data directly if no separate result_id
        setSelectedJobResults({
          analysis_type: job.analysis_type,
          analysis_name: job.analysis_name,
          parameters: job.parameters || {},
          results: job.results_data?.results || [],
          result_count: job.results_data?.result_count || 0,
          execution_time_ms: job.execution_time_ms || 0,
          timestamp: job.start_time || job.created_at,
          metadata: job.results_data?.metadata || {}
        });
      }
      setResultsDialogOpen(true);
    } catch (error) {
      console.error('Error fetching results:', error);
      // Fallback to basic job info
      setSelectedJobResults({
        analysis_type: job.analysis_type,
        analysis_name: job.analysis_name,
        parameters: job.parameters || {},
        results: [],
        result_count: 0,
        execution_time_ms: job.execution_time_ms || 0,
        timestamp: job.start_time || job.created_at,
        metadata: {}
      });
      setResultsDialogOpen(true);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 'bold' }}>
        🔍 Analysis Jobs & History
      </Typography>

      {/* Active Analysis Summary */}
      {activeTasks && activeTasks.active_tasks > 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>
          🚀 {activeTasks.active_tasks} analysis task(s) running
        </Alert>
      )}

      {/* Current Progress for Active Job */}
      {expandedJobId && isJobActive(expandedJobId) && analysisProgress && (
        <Card sx={{ mb: 2, bgcolor: '#f5f5f5' }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 1 }}>
              📊 Current Progress
            </Typography>
            <Box sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Box sx={{ flex: 1, mr: 2 }}>
                  <LinearProgress
                    variant="determinate"
                    value={analysisProgress.progress_percent || 0}
                    sx={{ height: 10, borderRadius: 5 }}
                  />
                </Box>
                <Typography variant="body2" sx={{ minWidth: 50 }}>
                  {analysisProgress.progress_percent || 0}%
                </Typography>
              </Box>
              <Typography variant="body2" color="textSecondary">
                {analysisProgress.progress_message}
              </Typography>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Search and Filter Bar */}
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} sm={4}>
          <TextField
            fullWidth
            placeholder="Search analyses..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setPage(0);
            }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            size="small"
          />
        </Grid>
        <Grid item xs={12} sm={3}>
          <FormControl fullWidth size="small">
            <InputLabel>Type</InputLabel>
            <Select
              value={typeFilter}
              label="Type"
              onChange={(e) => {
                setTypeFilter(e.target.value);
                setPage(0);
              }}
            >
              <MenuItem value="">All Types</MenuItem>
              <MenuItem value="etf_technical">ETF Technical</MenuItem>
              <MenuItem value="etf_scan">ETF Scan</MenuItem>
              <MenuItem value="stock_technical">Stock Technical</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} sm={3}>
          <FormControl fullWidth size="small">
            <InputLabel>Status</InputLabel>
            <Select
              value={statusFilter}
              label="Status"
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(0);
              }}
            >
              <MenuItem value="">All Statuses</MenuItem>
              <MenuItem value="running">Running</MenuItem>
              <MenuItem value="completed">Completed</MenuItem>
              <MenuItem value="failed">Failed</MenuItem>
              <MenuItem value="cancelled">Cancelled</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} sm={2}>
          <Button
            fullWidth
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => queryClient.invalidateQueries('analysisHistory')}
          >
            Refresh
          </Button>
        </Grid>
      </Grid>

      {/* Analysis Tasks Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead sx={{ bgcolor: '#f5f5f5' }}>
            <TableRow>
              <TableCell width="50px" />
              <TableCell>Name</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Progress</TableCell>
              <TableCell>Started</TableCell>
              <TableCell>Duration</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {historyLoading ? (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ py: 3 }}>
                  <CircularProgress />
                </TableCell>
              </TableRow>
            ) : rawHistoryData?.tasks?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ py: 3 }}>
                  <Typography color="textSecondary">
                    No analysis tasks found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              rawHistoryData?.tasks?.map((job) => (
                <React.Fragment key={job.task_id}>
                  <TableRow
                    sx={{
                      bgcolor: expandedJobId === job.task_id ? '#f9f9f9' : 'inherit',
                      '&:hover': { bgcolor: '#f9f9f9' },
                      cursor: 'pointer',
                    }}
                  >
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={() =>
                          setExpandedJobId(
                            expandedJobId === job.task_id ? null : job.task_id
                          )
                        }
                      >
                        {expandedJobId === job.task_id ? (
                          <ExpandLessIcon />
                        ) : (
                          <ExpandMoreIcon />
                        )}
                      </IconButton>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {job.analysis_name}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption" sx={{ textTransform: 'none' }}>
                        {job.analysis_type.replace('_', ' ').toUpperCase()}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={job.status.toUpperCase()}
                        color={getStatusColor(job.status)}
                        size="small"
                        icon={getStatusIcon(job.status)}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box sx={{ flex: 1, minWidth: 100 }}>
                          <LinearProgress
                            variant="determinate"
                            value={job.progress_percent || 0}
                            sx={{ height: 6, borderRadius: 3 }}
                          />
                        </Box>
                        <Typography variant="caption" sx={{ minWidth: 35 }}>
                          {job.progress_percent || 0}%
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">
                        {job.start_time
                          ? formatDistanceToNow(new Date(job.start_time), {
                              addSuffix: true,
                            })
                          : '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">
                        {formatDuration(job.start_time, job.end_time)}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      {job.status === 'running' ? (
                        <IconButton
                          size="small"
                          onClick={() => handleCancel(job.task_id)}
                          title="Cancel"
                          disabled={cancelMutation.isLoading}
                        >
                          <CancelIcon fontSize="small" />
                        </IconButton>
                      ) : job.status === 'completed' || job.status === 'failed' ? (
                        <Box display="flex" gap={1}>
                          {job.status === 'completed' && (
                            <IconButton
                              size="small"
                              onClick={() => handleViewResults(job)}
                              title="View Results"
                            >
                              <AssessmentIcon fontSize="small" />
                            </IconButton>
                          )}
                          <IconButton
                            size="small"
                            onClick={() => handleRerun(job)}
                            title="Re-run"
                            disabled={rerunMutation.isLoading}
                          >
                            <RerunIcon fontSize="small" />
                          </IconButton>
                        </Box>
                      ) : null}
                    </TableCell>
                  </TableRow>

                  {/* Expandable Row - Job Details */}
                  <TableRow>
                    <TableCell colSpan={8} sx={{ py: 0 }}>
                      <Collapse in={expandedJobId === job.task_id} timeout="auto">
                        <Box sx={{ p: 2, bgcolor: '#fafafa' }}>
                          {detailsLoading ? (
                            <CircularProgress />
                          ) : jobDetails ? (
                            <Grid container spacing={2}>
                              {/* Task Information */}
                              <Grid item xs={12} sm={6}>
                                <Typography variant="h6" sx={{ mb: 1 }}>
                                  📋 Task Information
                                </Typography>
                                <List dense>
                                  <ListItem>
                                    <ListItemText
                                      primary="Task ID"
                                      secondary={jobDetails.task_info?.task_id}
                                      primaryTypographyProps={{
                                        variant: 'caption',
                                      }}
                                      secondaryTypographyProps={{
                                        variant: 'caption',
                                        sx: { fontFamily: 'monospace' },
                                      }}
                                    />
                                  </ListItem>
                                  <ListItem>
                                    <ListItemText
                                      primary="Type"
                                      secondary={jobDetails.task_info?.analysis_type}
                                      primaryTypographyProps={{
                                        variant: 'caption',
                                      }}
                                    />
                                  </ListItem>
                                  <ListItem>
                                    <ListItemText
                                      primary="Status"
                                      secondary={jobDetails.task_info?.status}
                                      primaryTypographyProps={{
                                        variant: 'caption',
                                      }}
                                    />
                                  </ListItem>
                                  <ListItem>
                                    <ListItemText
                                      primary="Start Time"
                                      secondary={
                                        jobDetails.task_info?.start_time
                                          ? format(
                                              new Date(jobDetails.task_info.start_time),
                                              'PPpp'
                                            )
                                          : '-'
                                      }
                                      primaryTypographyProps={{
                                        variant: 'caption',
                                      }}
                                    />
                                  </ListItem>
                                  <ListItem>
                                    <ListItemText
                                      primary="Execution Time"
                                      secondary={
                                        jobDetails.task_info?.execution_time_ms
                                          ? `${(
                                              jobDetails.task_info.execution_time_ms / 1000
                                            ).toFixed(2)}s`
                                          : '-'
                                      }
                                      primaryTypographyProps={{
                                        variant: 'caption',
                                      }}
                                    />
                                  </ListItem>
                                </List>
                              </Grid>

                              {/* Statistics */}
                              <Grid item xs={12} sm={6}>
                                <Typography variant="h6" sx={{ mb: 1 }}>
                                  📊 Statistics
                                </Typography>
                                <List dense>
                                  <ListItem>
                                    <ListItemText
                                      primary="Total Logs"
                                      secondary={jobDetails.statistics?.total_logs || 0}
                                      primaryTypographyProps={{
                                        variant: 'caption',
                                      }}
                                    />
                                  </ListItem>
                                  <ListItem>
                                    <ListItemText
                                      primary="Success Logs"
                                      secondary={jobDetails.statistics?.success_logs || 0}
                                      primaryTypographyProps={{
                                        variant: 'caption',
                                      }}
                                    />
                                  </ListItem>
                                  <ListItem>
                                    <ListItemText
                                      primary="Error Logs"
                                      secondary={jobDetails.statistics?.error_logs || 0}
                                      primaryTypographyProps={{
                                        variant: 'caption',
                                      }}
                                    />
                                  </ListItem>
                                  {jobDetails.task_info?.error_message && (
                                    <ListItem>
                                      <ListItemText
                                        primary="Error Message"
                                        secondary={jobDetails.task_info.error_message}
                                        primaryTypographyProps={{
                                          variant: 'caption',
                                        }}
                                        secondaryTypographyProps={{
                                          variant: 'caption',
                                          sx: { color: 'error.main' },
                                        }}
                                      />
                                    </ListItem>
                                  )}
                                </List>
                              </Grid>

                              {/* Scanner Details - Only for ETF Scan Analysis */}
                              {job.analysis_type === 'etf_scan' && jobDetails.task_info?.parameters && (
                                <Grid item xs={12}>
                                  <Typography variant="h6" sx={{ mb: 1 }}>
                                    🔍 Scanner Configuration
                                  </Typography>
                                  <Box sx={{ p: 2, bgcolor: '#f0f0f0', borderRadius: 1 }}>
                                    <Grid container spacing={2}>
                                      {/* Selected Scanners */}
                                      <Grid item xs={12} sm={6}>
                                        <Typography variant="subtitle2" sx={{ mb: 1 }}>
                                          Selected Scanners
                                        </Typography>
                                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                          {(jobDetails.task_info.parameters.scanners || []).map((scanner: string) => (
                                            <Chip
                                              key={scanner}
                                              label={scanner.replace('_', ' ').toUpperCase()}
                                              size="small"
                                              color="primary"
                                              variant="outlined"
                                            />
                                          ))}
                                        </Box>
                                      </Grid>

                                      {/* Scanner Weights */}
                                      <Grid item xs={12} sm={6}>
                                        <Typography variant="subtitle2" sx={{ mb: 1 }}>
                                          Scanner Weights
                                        </Typography>
                                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                          {Object.entries(jobDetails.task_info.parameters.weights || {}).map(([scanner, weight]) => {
                                            const weightValue = typeof weight === 'number' ? weight : 0;
                                            return (
                                              <Chip
                                                key={scanner}
                                                label={`${scanner}: ${weightValue}`}
                                                size="small"
                                                color={weightValue > 0 ? 'primary' : 'default'}
                                                variant={weightValue > 0 ? 'filled' : 'outlined'}
                                              />
                                            );
                                          })}
                                        </Box>
                                      </Grid>

                                      {/* Actual Parameters Used */}
                                      {jobDetails.task_info.parameters.actual_parameters && (
                                        <Grid item xs={12}>
                                          <Typography variant="subtitle2" sx={{ mb: 1 }}>
                                            Parameters Used
                                          </Typography>
                                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                            {Object.entries(jobDetails.task_info.parameters.actual_parameters).map(([param, value]) => (
                                              <Chip
                                                key={param}
                                                label={`${param}: ${value}`}
                                                size="small"
                                                variant="outlined"
                                              />
                                            ))}
                                          </Box>
                                        </Grid>
                                      )}

                                      {/* Individual Scanner Parameters */}
                                      {jobDetails.task_info.parameters.scanner_configs && (
                                        <Grid item xs={12}>
                                          <Typography variant="subtitle2" sx={{ mb: 2 }}>
                                            Individual Scanner Parameters
                                          </Typography>
                                          <Grid container spacing={2}>
                                            {Object.entries(jobDetails.task_info.parameters.scanner_configs).map(([scanner, config]) => {
                                              const weight = jobDetails.task_info.parameters.weights?.[scanner] || 0;
                                              const weightValue = typeof weight === 'number' ? weight : 0;
                                              
                                              return (
                                                <Grid item xs={12} sm={6} md={4} key={scanner}>
                                                  <Card variant="outlined" sx={{ p: 1.5 }}>
                                                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                                      <Typography variant="subtitle2" sx={{ flexGrow: 1 }}>
                                                        {scanner.replace('_', ' ').toUpperCase()}
                                                      </Typography>
                                                      <Chip
                                                        label={`Weight: ${weightValue}`}
                                                        size="small"
                                                        color={weightValue > 0 ? 'primary' : 'default'}
                                                        variant={weightValue > 0 ? 'filled' : 'outlined'}
                                                      />
                                                    </Box>
                                                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                                                      {Object.entries(config as Record<string, any>).map(([param, value]) => (
                                                        <Box key={param} sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                                          <Typography variant="caption" color="textSecondary">
                                                            {param}:
                                                          </Typography>
                                                          <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                                                            {Array.isArray(value) ? value.join(', ') : String(value)}
                                                          </Typography>
                                                        </Box>
                                                      ))}
                                                    </Box>
                                                  </Card>
                                                </Grid>
                                              );
                                            })}
                                          </Grid>
                                        </Grid>
                                      )}

                                      {/* Scanner Summary */}
                                      {jobDetails.task_info.parameters.scanner_summary && (
                                        <Grid item xs={12}>
                                          <Typography variant="subtitle2" sx={{ mb: 1 }}>
                                            Execution Summary
                                          </Typography>
                                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                            <Chip
                                              label={`Total Scanners: ${jobDetails.task_info.parameters.scanner_summary.total_scanners}`}
                                              size="small"
                                              color="info"
                                            />
                                            <Chip
                                              label={`BUY: ${jobDetails.task_info.parameters.scanner_summary.buy_count}`}
                                              size="small"
                                              color="success"
                                            />
                                            <Chip
                                              label={`SELL: ${jobDetails.task_info.parameters.scanner_summary.sell_count}`}
                                              size="small"
                                              color="error"
                                            />
                                            <Chip
                                              label={`HOLD: ${jobDetails.task_info.parameters.scanner_summary.hold_count}`}
                                              size="small"
                                              color="default"
                                            />
                                            <Chip
                                              label={`Multi-Reason: ${jobDetails.task_info.parameters.scanner_summary.multi_reason_count}`}
                                              size="small"
                                              color="secondary"
                                            />
                                          </Box>
                                        </Grid>
                                      )}
                                    </Grid>
                                  </Box>
                                </Grid>
                              )}

                              {/* Progress Logs */}
                              {jobDetails.progress_logs &&
                                jobDetails.progress_logs.length > 0 && (
                                  <Grid item xs={12}>
                                    <Typography variant="h6" sx={{ mb: 1 }}>
                                      📝 Progress Logs
                                    </Typography>
                                    <List dense sx={{ maxHeight: 300, overflow: 'auto' }}>
                                      {jobDetails.progress_logs.map((log: any) => (
                                        <ListItem key={log.id}>
                                          <ListItemIcon sx={{ minWidth: 40 }}>
                                            {log.message_type === 'error' && (
                                              <ErrorIcon sx={{ color: 'error.main' }} />
                                            )}
                                            {log.message_type === 'success' && (
                                              <CheckCircleIcon
                                                sx={{ color: 'success.main' }}
                                              />
                                            )}
                                            {log.message_type === 'warning' && (
                                              <WarningIcon sx={{ color: 'warning.main' }} />
                                            )}
                                            {log.message_type === 'info' && (
                                              <InfoIcon sx={{ color: 'info.main' }} />
                                            )}
                                          </ListItemIcon>
                                          <ListItemText
                                            primary={log.message}
                                            secondary={`${format(
                                              new Date(log.timestamp),
                                              'HH:mm:ss'
                                            )} (${log.progress_percent}%)`}
                                            primaryTypographyProps={{
                                              variant: 'caption',
                                            }}
                                            secondaryTypographyProps={{
                                              variant: 'caption',
                                            }}
                                          />
                                        </ListItem>
                                      ))}
                                    </List>
                                  </Grid>
                                )}
                            </Grid>
                          ) : null}
                        </Box>
                      </Collapse>
                    </TableCell>
                  </TableRow>
                </React.Fragment>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Pagination */}
      <TablePagination
        rowsPerPageOptions={[5, 10, 25, 50]}
        component="div"
        count={rawHistoryData?.total || 0}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={(_, newPage) => setPage(newPage)}
        onRowsPerPageChange={(event) => {
          setRowsPerPage(parseInt(event.target.value, 10));
          setPage(0);
        }}
      />

      {/* Rerun Dialog */}
      <Dialog open={rerunDialogOpen} onClose={() => setRerunDialogOpen(false)}>
        <DialogTitle>Re-run Analysis</DialogTitle>
        <DialogContent>
          <Typography sx={{ mt: 1 }}>
            Are you sure you want to re-run "{selectedJobForRerun?.analysis_name}" with the same parameters?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRerunDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={() => rerunMutation.mutate()}
            variant="contained"
            disabled={rerunMutation.isLoading}
          >
            {rerunMutation.isLoading ? <CircularProgress size={20} /> : 'Re-run'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Results Dialog */}
      <Dialog 
        open={resultsDialogOpen} 
        onClose={() => setResultsDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Analysis Results
          <IconButton
            onClick={() => setResultsDialogOpen(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CancelIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent sx={{ p: 0 }}>
          {selectedJobResults && (
            <AnalysisResultsViewer
              result={selectedJobResults}
              onExport={(format) => {
                // TODO: Implement export functionality
                console.log('Export requested:', format);
              }}
              onRerun={async (parameters) => {
                try {
                  // If onRerunRequest is provided for stock_scan, use it to navigate to form
                  if (onRerunRequest && selectedJobResults.analysis_type === 'stock_scan') {
                    onRerunRequest(selectedJobResults.analysis_type, parameters);
                    setResultsDialogOpen(false);
                    return;
                  }
                  
                  // Otherwise, start analysis via API
                  await analyticsApi.startAnalysis(
                    selectedJobResults.analysis_type,
                    selectedJobResults.analysis_name,
                    parameters
                  );
                  // Refresh the jobs list
                  queryClient.invalidateQueries('analysisActiveTasks');
                  queryClient.invalidateQueries('analysisHistory');
                  // Close the results dialog
                  setResultsDialogOpen(false);
                  // Show success message (optional - you could add a snackbar here)
                  console.log('Analysis rerun started successfully');
                } catch (error) {
                  console.error('Failed to start rerun:', error);
                  // TODO: Show error message to user
                }
              }}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Error Handling */}
      {historyError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          Failed to load analysis history. Please try again.
        </Alert>
      )}
    </Box>
  );
};

export default AnalysisJobsPanel;
