// finance_tools/frontend/src/components/DownloadHistory.tsx
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
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { useQuery } from 'react-query';
import { databaseApi } from '../services/api';
import DownloadTaskDetails from './DownloadTaskDetails';

// Removed unused interface - using type from API response

export const DownloadHistory: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  const {
    data: historyData,
    isLoading,
    error,
    refetch,
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
    }
  );

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const getStatusChip = (status: string) => {
    switch (status) {
      case 'completed':
        return <Chip icon={<CheckCircleIcon />} label="Completed" color="success" size="small" />;
      case 'failed':
        return <Chip icon={<ErrorIcon />} label="Failed" color="error" size="small" />;
      case 'running':
        return <Chip icon={<ScheduleIcon />} label="Running" color="warning" size="small" />;
      default:
        return <Chip label={status} size="small" />;
    }
  };

  const formatDuration = (startTime: string, endTime?: string) => {
    if (!endTime) return 'In progress';
    const start = new Date(startTime);
    const end = new Date(endTime);
    const diffMs = end.getTime() - start.getTime();
    const diffMins = Math.round(diffMs / 60000);
    return `${diffMins} minutes`;
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
        Failed to load download history. Please try again.
      </Alert>
    );
  }

  const downloads = historyData?.downloads || [];
  const total = historyData?.total || 0;

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" gutterBottom>
          Download History
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => refetch()}
        >
          Refresh
        </Button>
      </Box>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                placeholder="Search downloads..."
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
                  displayEmpty
                >
                  <MenuItem value="">All Status</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                  <MenuItem value="failed">Failed</MenuItem>
                  <MenuItem value="running">Running</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={5}>
              <Typography variant="body2" color="textSecondary">
                {total} download{total !== 1 ? 's' : ''} found
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Card>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Date Range</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Funds</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Duration</TableCell>
                <TableCell>Records</TableCell>
                <TableCell>Started</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {downloads.map((item) => (
                <TableRow key={item.id} hover>
                  <TableCell>
                    <Typography variant="body2">
                      {item.start_date} - {item.end_date}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip label={item.kind} size="small" variant="outlined" />
                  </TableCell>
                  <TableCell>
                    {item.funds.length > 0 ? (
                      <Typography variant="body2">
                        {item.funds.join(', ')}
                      </Typography>
                    ) : (
                      <Typography variant="body2" color="textSecondary">
                        All funds
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    {getStatusChip(item.status)}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {formatDuration(item.start_time, item.end_time)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {item.records_downloaded.toLocaleString()}
                      {item.total_records > 0 && (
                        <span> / {item.total_records.toLocaleString()}</span>
                      )}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {format(new Date(item.start_time), 'MMM dd, yyyy HH:mm')}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <IconButton 
                      size="small" 
                      title="View Details"
                      onClick={() => {
                        setSelectedTaskId(item.task_id);
                        setShowDetails(true);
                      }}
                    >
                      <VisibilityIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
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

      {downloads.length === 0 && !isLoading && (
        <Alert severity="info">
          No download history found. Start your first download to see it here.
        </Alert>
      )}

      {/* Download Task Details Modal */}
      {showDetails && selectedTaskId && (
        <Card sx={{ mt: 2 }}>
          <CardContent>
            <DownloadTaskDetails 
              taskId={selectedTaskId}
              onClose={() => {
                setShowDetails(false);
                setSelectedTaskId(null);
              }}
            />
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default DownloadHistory;