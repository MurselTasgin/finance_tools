// finance_tools/frontend/src/components/DownloadJobs.tsx
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
} from '@mui/material';
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
  Download as DownloadIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { databaseApi, stockApi } from '../services/api';
import { DownloadProgress, DatabaseStats } from '../types';
import DownloadDataModal from './DownloadDataModal';

export const DownloadJobs: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [expandedJobId, setExpandedJobId] = useState<string | null>(null);
  const [showDownloadModal, setShowDownloadModal] = useState(false);
  const queryClient = useQueryClient();

  // Fetch database stats (needed for lastDownloadDate)
  const { data: stats } = useQuery<DatabaseStats>(
    'databaseStats',
    databaseApi.getStats,
    {
      refetchInterval: 30000, // Refetch every 30 seconds
    }
  );

  // Fetch active tasks first (needed for isJobActive function)
  const { data: activeTasks } = useQuery(
    'activeTasks',
    databaseApi.getActiveTasks,
    {
      refetchInterval: 2000, // Poll every 2 seconds
    }
  );

  // Fetch unified download history (both TEFAS and Stock)
  const {
    data: rawHistoryData,
    isLoading: historyLoading,
    error: historyError,
  } = useQuery(
    ['downloadHistory', page + 1, rowsPerPage, searchTerm, statusFilter],
    () => databaseApi.getDownloadHistory({
      page: page + 1,
      pageSize: rowsPerPage,
      search: searchTerm,
      status: statusFilter || undefined,
    }),
    {
      keepPreviousData: true,
      refetchInterval: 5000, // Refetch every 5 seconds to show running jobs
    }
  );

  // Enrich history data with display information
  const historyData = React.useMemo(() => {
    if (!rawHistoryData) return undefined;
    
    const enrichedDownloads = (rawHistoryData.downloads || []).map(d => {
      // Determine data type and create display info
      const dataType = (d.data_type || 'tefas').toUpperCase() === 'STOCK' ? 'Stock' : 'TEFAS';
      
      let displayInfo;
      if (dataType === 'Stock') {
        // For stocks: show symbol count and interval
        const symbolCount = d.symbols?.length || 0;
        const interval = d.kind || '1d';
        displayInfo = `${symbolCount} symbols - ${interval}`;
      } else {
        // For TEFAS: show fund type and count
        const fundCount = d.funds?.length || 0;
        const kind = d.kind || 'BYF';
        displayInfo = fundCount > 0 ? `${kind} - ${fundCount} funds` : `${kind} - All funds`;
      }
      
      return {
        ...d,
        data_type: dataType,
        display_info: displayInfo,
      };
    });
    
    return {
      downloads: enrichedDownloads,
      total: rawHistoryData.total,
      page: rawHistoryData.page,
      pageSize: rawHistoryData.pageSize,
    };
  }, [rawHistoryData]);
  
  const refetchHistory = () => {
    queryClient.invalidateQueries('downloadHistory');
  };

  // Helper function to check if job is active (defined after activeTasks)
  const isJobActive = (taskId: string): boolean => {
    return activeTasks?.tasks.some(task => task.task_id === taskId) || false;
  };

  // Get the data type of the expanded job
  const expandedJobDataType = expandedJobId 
    ? historyData?.downloads.find(d => d.task_id === expandedJobId)?.data_type || 'tefas'
    : 'tefas';

  // Fetch download progress for the expanded active job (calls the correct API based on job type)
  const { data: downloadProgress } = useQuery<DownloadProgress>(
    ['downloadProgress', expandedJobDataType],
    () => expandedJobDataType === 'stock' ? stockApi.getDownloadProgress() : databaseApi.getDownloadProgress(),
    {
      refetchInterval: 1000, // Poll every second
      enabled: expandedJobId !== null && isJobActive(expandedJobId),
    }
  );

  // Fetch detailed logs for expanded job (both active and completed)
  const { data: jobDetails, isLoading: detailsLoading } = useQuery(
    ['downloadTaskDetails', expandedJobId],
    () => databaseApi.getDownloadTaskDetails(expandedJobId!),
    {
      enabled: expandedJobId !== null,  // Poll for ALL expanded jobs (active or completed)
      refetchInterval: (data) => {
        if (!expandedJobId) return false;
        
        // For active jobs, poll every 2 seconds for real-time logs
        if (isJobActive(expandedJobId)) {
          return 2000;  // Fast polling for active jobs
        }
        
        // For completed/failed/cancelled jobs, don't poll
        const status = historyData?.downloads.find(d => d.task_id === expandedJobId)?.status;
        return (status === 'running') ? 5000 : false;
      },
    }
  );

  // TEFAS Download mutation
  const downloadMutation = useMutation(
    ({ startDate, endDate, kind, funds }: { startDate: string; endDate: string; kind: string; funds: string[] }) =>
      databaseApi.downloadData(startDate, endDate, kind, funds),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('databaseStats');
        queryClient.invalidateQueries('downloadHistory');
        queryClient.invalidateQueries('activeTasks');
        setShowDownloadModal(false);
      },
      onError: (error) => {
        console.error('TEFAS download failed:', error);
      },
    }
  );

  // Stock Download mutation
  const stockDownloadMutation = useMutation(
    ({ symbols, startDate, endDate, interval }: { symbols: string[]; startDate: string; endDate: string; interval: string }) =>
      stockApi.downloadData(symbols, startDate, endDate, interval),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('databaseStats');
        queryClient.invalidateQueries('downloadHistory');
        queryClient.invalidateQueries('activeTasks');
        setShowDownloadModal(false);
      },
      onError: (error) => {
        console.error('Stock download failed:', error);
      },
    }
  );

  // Cancel mutation
  const cancelMutation = useMutation(
    (taskId: string) => databaseApi.cancelTask(taskId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('downloadHistory');
        queryClient.invalidateQueries('activeTasks');
      },
    }
  );

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleDownload = (startDate: string, endDate: string, kind: string, funds: string[]) => {
    downloadMutation.mutate({ startDate, endDate, kind, funds });
  };

  const handleDownloadStocks = (symbols: string[], startDate: string, endDate: string, interval: string) => {
    stockDownloadMutation.mutate({ symbols, startDate, endDate, interval });
  };

  const getStatusChip = (status: string, taskId: string) => {
    const isActive = isJobActive(taskId);
    
    if (isActive || status === 'running') {
      return (
        <Chip 
          icon={<CircularProgress size={16} />} 
          label="Running" 
          color="warning" 
          size="small" 
        />
      );
    }
    
    switch (status) {
      case 'completed':
        return <Chip icon={<CheckCircleIcon />} label="Completed" color="success" size="small" />;
      case 'failed':
        return <Chip icon={<ErrorIcon />} label="Failed" color="error" size="small" />;
      case 'cancelled':
        return <Chip icon={<CancelIcon />} label="Cancelled" color="default" size="small" />;
      default:
        return <Chip label={status} size="small" />;
    }
  };

  const formatDuration = (startTime: string, endTime?: string) => {
    if (!endTime) {
      const start = new Date(startTime);
      const now = new Date();
      const diffMs = now.getTime() - start.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      if (diffMins < 60) return `${diffMins}m (in progress)`;
      const hours = Math.floor(diffMins / 60);
      const mins = diffMins % 60;
      return `${hours}h ${mins}m (in progress)`;
    }
    const start = new Date(startTime);
    const end = new Date(endTime);
    const diffMs = end.getTime() - start.getTime();
    const diffMins = Math.round(diffMs / 60000);
    if (diffMins < 60) return `${diffMins}m`;
    const hours = Math.floor(diffMins / 60);
    const mins = diffMins % 60;
    return `${hours}h ${mins}m`;
  };

  const formatTime = (timestamp: string) => {
    try {
      return format(new Date(timestamp), 'HH:mm:ss');
    } catch {
      return 'Invalid time';
    }
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

  const renderJobDetails = (job: any) => {
    const isActive = isJobActive(job.task_id);

    // Helper function to calculate total records from progress logs
    const getRecordsFromLogs = (logs: any[]) => {
      if (!logs || logs.length === 0) return 0;
      return logs.reduce((total, log) => {
        return total + (log.records_count || 0);
      }, 0);
    };

    if (isActive) {
      // Show real-time progress for active jobs
      return (
        <Box sx={{ p: 3, bgcolor: 'grey.50' }}>
          <Typography variant="h6" gutterBottom>
            Real-Time Progress
          </Typography>

          {downloadProgress && (
            <>
              {/* Progress Bar */}
              <Box sx={{ mb: 3 }}>
                <Box display="flex" justifyContent="space-between" mb={1}>
                  <Typography variant="body2" color="text.secondary">
                    {downloadProgress.status}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {downloadProgress.progress}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={downloadProgress.progress}
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </Box>

              {/* Statistics */}
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={6} md={3}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h5" color="primary">
                        {(() => {
                          // Use records from progress logs if available, otherwise fallback to API progress
                          const logsRecords = jobDetails && jobDetails.progress_logs ? getRecordsFromLogs(jobDetails.progress_logs) : 0;
                          const apiRecords = downloadProgress.records_downloaded || 0;
                          return Math.max(logsRecords, apiRecords).toLocaleString();
                        })()}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Records Downloaded
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h5" color="success.main">
                        {downloadProgress.symbols_completed || 0} / {downloadProgress.symbols_total || 0}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Symbols Completed
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h6">
                        {downloadProgress.current_chunk_info ? 
                          `${downloadProgress.current_chunk_info.chunk_number}/${downloadProgress.current_chunk_info.total_chunks}` 
                          : downloadProgress.symbols_completed || 0}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {downloadProgress.current_chunk_info ? 'Chunks Progress' : 'Current Item'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h6" color="text.primary">
                        {downloadProgress.current_phase || 'Initializing'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Current Phase
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Recent Messages */}
              {/* Real-time Progress Logs from Database */}
              {jobDetails && jobDetails.progress_logs && jobDetails.progress_logs.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Progress Logs (Real-time)
                  </Typography>
                  <Paper variant="outlined" sx={{ maxHeight: 400, overflowY: 'auto', p: 2 }}>
                    <List dense>
                      {jobDetails.progress_logs.map((log) => (
                        <ListItem key={log.id} sx={{ py: 0.5 }}>
                          <ListItemIcon sx={{ minWidth: 36 }}>
                            {getMessageIcon(log.message_type)}
                          </ListItemIcon>
                          <ListItemText
                            primary={log.message}
                            secondary={
                              <span>
                                {formatTime(log.timestamp)}
                                {log.records_count && ` • ${log.records_count} records`}
                                {log.fund_name && ` • ${log.fund_name}`}
                                {log.chunk_number > 0 && ` • Chunk ${log.chunk_number}`}
                              </span>
                            }
                            primaryTypographyProps={{ variant: 'body2' }}
                            secondaryTypographyProps={{ variant: 'caption' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                </Box>
              )}
              
              {/* Fallback to in-memory messages if no DB logs yet */}
              {(!jobDetails || !jobDetails.progress_logs || jobDetails.progress_logs.length === 0) && 
               downloadProgress.detailed_messages && downloadProgress.detailed_messages.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Recent Activity (In-Memory)
                  </Typography>
                  <Paper variant="outlined" sx={{ maxHeight: 300, overflowY: 'auto', p: 2 }}>
                    <List dense>
                      {downloadProgress.detailed_messages.slice(-10).reverse().map((msg, idx) => (
                        <ListItem key={idx} sx={{ py: 0.5 }}>
                          <ListItemIcon sx={{ minWidth: 36 }}>
                            {getMessageIcon(msg.type)}
                          </ListItemIcon>
                          <ListItemText
                            primary={msg.message}
                            secondary={formatTime(msg.timestamp)}
                            primaryTypographyProps={{ variant: 'body2' }}
                            secondaryTypographyProps={{ variant: 'caption' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                </Box>
              )}

              {/* Cancel Button */}
              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<CancelIcon />}
                  onClick={() => cancelMutation.mutate(job.task_id)}
                  disabled={cancelMutation.isLoading}
                >
                  Cancel Download
                </Button>
              </Box>
            </>
          )}

          {!downloadProgress && (
            <Alert severity="info">
              Loading progress information...
            </Alert>
          )}
        </Box>
      );
    } else {
      // Show detailed logs for completed jobs
      if (detailsLoading) {
        return (
          <Box sx={{ p: 3, display: 'flex', justifyContent: 'center' }}>
            <CircularProgress />
          </Box>
        );
      }

      if (!jobDetails) {
        return (
          <Box sx={{ p: 3 }}>
            <Alert severity="warning">No details available for this job.</Alert>
          </Box>
        );
      }

      return (
        <Box sx={{ p: 3, bgcolor: 'grey.50' }}>
          <Grid container spacing={3}>
            {/* Summary Statistics */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Job Summary
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6} md={3}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h5" color={job.status === 'completed' ? 'success.main' : 'error.main'}>
                        {(() => {
                          const dbRecords = jobDetails.task_info.records_downloaded || 0;
                          const logsRecords = getRecordsFromLogs(jobDetails.progress_logs || []);
                          return Math.max(dbRecords, logsRecords).toLocaleString();
                        })()}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Records Downloaded
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h5">
                        {jobDetails.statistics.total_messages}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Total Messages
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h5" color="success.main">
                        {jobDetails.statistics.success_messages}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Successful Operations
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h5" color="error.main">
                        {jobDetails.statistics.error_messages}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Errors
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Grid>

            {/* Error Message if failed */}
            {job.status === 'failed' && jobDetails.task_info.error_message && (
              <Grid item xs={12}>
                <Alert severity="error">
                  <Typography variant="subtitle2" gutterBottom>
                    Error Details:
                  </Typography>
                  <Typography variant="body2">
                    {jobDetails.task_info.error_message}
                  </Typography>
                </Alert>
              </Grid>
            )}

            {/* Progress Logs */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Progress Logs ({jobDetails.progress_logs.length} messages)
              </Typography>
              <Paper variant="outlined" sx={{ maxHeight: 400, overflowY: 'auto' }}>
                <List dense>
                  {jobDetails.progress_logs.map((log: any) => (
                    <ListItem key={log.id} sx={{ py: 1, borderBottom: '1px solid', borderColor: 'divider' }}>
                      <ListItemIcon sx={{ minWidth: 36 }}>
                        {getMessageIcon(log.message_type)}
                      </ListItemIcon>
                      <ListItemText
                        primary={log.message}
                        secondary={
                          <span>
                            {formatTime(log.timestamp)}
                            {log.records_count && ` • ${log.records_count} records`}
                            {log.fund_name && ` • ${log.fund_name}`}
                            {log.chunk_number > 0 && ` • Chunk ${log.chunk_number}`}
                          </span>
                        }
                        primaryTypographyProps={{ variant: 'body2' }}
                        secondaryTypographyProps={{ variant: 'caption' }}
                      />
                    </ListItem>
                  ))}
                </List>
              </Paper>
            </Grid>
          </Grid>
        </Box>
      );
    }
  };

  if (historyLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (historyError) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Failed to load download jobs. Please try again.
      </Alert>
    );
  }

  const jobs = historyData?.downloads || [];
  const total = historyData?.total || 0;

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h5" gutterBottom>
            Download Jobs
          </Typography>
          <Typography variant="body2" color="text.secondary">
            View and manage all download jobs (active and completed)
          </Typography>
        </Box>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => {
              refetchHistory();
              queryClient.invalidateQueries('activeTasks');
            }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<DownloadIcon />}
            onClick={() => setShowDownloadModal(true)}
          >
            New Download
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                placeholder="Search jobs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  label="Status"
                >
                  <MenuItem value="">All Status</MenuItem>
                  <MenuItem value="running">Running</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                  <MenuItem value="failed">Failed</MenuItem>
                  <MenuItem value="cancelled">Cancelled</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={5}>
              <Typography variant="body2" color="textSecondary">
                {total} job{total !== 1 ? 's' : ''} found
                {activeTasks && activeTasks.active_tasks > 0 && (
                  <Chip 
                    label={`${activeTasks.active_tasks} active`} 
                    color="warning" 
                    size="small" 
                    sx={{ ml: 1 }}
                  />
                )}
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Jobs Table */}
      <Card>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell width="50px"></TableCell>
                <TableCell>Date Range</TableCell>
                <TableCell>Data Type</TableCell>
                <TableCell>Details</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Duration</TableCell>
                <TableCell>Records</TableCell>
                <TableCell>Started</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {jobs.map((job) => (
                <React.Fragment key={job.id}>
                  <TableRow 
                    hover 
                    sx={{ 
                      cursor: 'pointer',
                      bgcolor: expandedJobId === job.task_id ? 'action.selected' : 'inherit'
                    }}
                    onClick={() => setExpandedJobId(expandedJobId === job.task_id ? null : job.task_id)}
                  >
                    <TableCell>
                      <IconButton size="small">
                        {expandedJobId === job.task_id ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                      </IconButton>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {job.start_date} - {job.end_date}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={job.data_type || 'TEFAS'} 
                        size="small" 
                        variant="outlined"
                        color={job.data_type === 'Stock' ? 'primary' : 'secondary'}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="textSecondary">
                        {job.display_info || (job.funds?.length > 0 ? job.funds.join(', ') : 'All funds')}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {getStatusChip(job.status, job.task_id)}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {formatDuration(job.start_time, job.end_time)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {job.records_downloaded.toLocaleString()}
                        {job.total_records > 0 && (
                          <span style={{ color: 'text.secondary' }}> / {job.total_records.toLocaleString()}</span>
                        )}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {format(new Date(job.start_time), 'MMM dd, HH:mm')}
                      </Typography>
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell colSpan={8} sx={{ p: 0, borderBottom: expandedJobId === job.task_id ? 1 : 0 }}>
                      <Collapse in={expandedJobId === job.task_id} timeout="auto" unmountOnExit>
                        {renderJobDetails(job)}
                      </Collapse>
                    </TableCell>
                  </TableRow>
                </React.Fragment>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <TablePagination
          rowsPerPageOptions={[5, 10, 25, 50]}
          component="div"
          count={total}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Card>

      {jobs.length === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          No download jobs found. Click "New Download" to start your first job.
        </Alert>
      )}

      {/* Download Modal */}
      <DownloadDataModal
        open={showDownloadModal}
        onClose={() => setShowDownloadModal(false)}
        onDownload={handleDownload}
        onDownloadStocks={handleDownloadStocks}
        lastDownloadDate={stats?.lastDownloadDate || null}
        loading={downloadMutation.isLoading || stockDownloadMutation.isLoading}
      />
    </Box>
  );
};

export default DownloadJobs;

