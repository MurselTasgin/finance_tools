// frontend/src/components/AnalysisResultsPanel.tsx
/**
 * Analysis Results Panel with Pagination and Filtering
 * 
 * Efficiently displays analysis results with:
 * - Server-side pagination
 * - Search functionality  
 * - Type and status filtering
 * - Optimized loading for thousands of records
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
  TextField,
  InputAdornment,
  TablePagination,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Assessment as AssessmentIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { useQuery, useQueryClient } from 'react-query';
import { analyticsApi } from '../services/api';
import AnalysisResultsViewer from './AnalysisResultsViewer';

interface AnalysisResultsPanelProps {
  onRerunRequest?: (analysisType: string, parameters: any) => void;
}

export const AnalysisResultsPanel: React.FC<AnalysisResultsPanelProps> = ({ onRerunRequest }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(20);
  const [selectedResult, setSelectedResult] = useState<any>(null);
  const [resultsDialogOpen, setResultsDialogOpen] = useState(false);
  const queryClient = useQueryClient();

  // Fetch analysis results with pagination
  const {
    data: resultsData,
    isLoading,
    error,
    refetch,
  } = useQuery(
    ['analysisResults', page + 1, rowsPerPage, searchTerm, typeFilter, statusFilter],
    () => analyticsApi.getCachedResults({
      page: page + 1,
      limit: rowsPerPage,
      analysis_type: typeFilter || undefined,
      status: statusFilter || undefined,
      search: searchTerm || undefined,
    }),
    {
      keepPreviousData: true,
      refetchInterval: 10000, // Refetch every 10 seconds
    }
  );

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleViewResult = async (resultId: number) => {
    try {
      const response = await fetch(`/api/analytics/results/${resultId}`);
      const data = await response.json();
      setSelectedResult(data);
      setResultsDialogOpen(true);
    } catch (error) {
      console.error('Error fetching result details:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'running':
        return 'info';
      default:
        return 'default';
    }
  };

  const getAnalysisTypeLabel = (type: string) => {
    const labels: { [key: string]: string } = {
      'etf_technical': 'ETF Technical',
      'etf_scan': 'ETF Scan',
      'stock_technical': 'Stock Technical',
    };
    return labels[type] || type;
  };

  return (
    <Box>
      <Card>
        <CardContent>
          <>
            <Box component="div" display="flex" justifyContent="space-between" alignItems="center" mb={3}>
              <Typography variant="h5">
                <AssessmentIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Analysis Results
              </Typography>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={() => refetch()}
              >
                Refresh
              </Button>
            </Box>

            {/* Filters Section */}
            <div style={{ display: 'flex', gap: '16px', marginBottom: '24px', flexWrap: 'wrap' }}>
              <TextField
                size="small"
                placeholder="Search analyses..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setPage(0); // Reset to first page on search
                }}
                sx={{ minWidth: 250 }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
              />

              <FormControl size="small" sx={{ minWidth: 150 }}>
                <InputLabel>Analysis Type</InputLabel>
                <Select
                  value={typeFilter}
                  label="Analysis Type"
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

              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  label="Status"
                  onChange={(e) => {
                    setStatusFilter(e.target.value);
                    setPage(0);
                  }}
                >
                  <MenuItem value="">All Status</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                  <MenuItem value="failed">Failed</MenuItem>
                  <MenuItem value="running">Running</MenuItem>
                </Select>
              </FormControl>
            </div>

            {/* Results Table */}
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                Error loading results: {(error as Error).message}
              </Alert>
            )}

            {isLoading && (
              <Box display="flex" justifyContent="center" py={4}>
                <CircularProgress />
              </Box>
            )}

            {!isLoading && resultsData && resultsData.results.length > 0 && (
              <>
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>ID</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Name</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell align="right">Results</TableCell>
                        <TableCell align="right">Time (ms)</TableCell>
                        <TableCell>Created At</TableCell>
                        <TableCell align="center">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {resultsData.results.map((result: any) => (
                        <TableRow key={result.id} hover>
                          <TableCell>{result.id}</TableCell>
                          <TableCell>
                            <Chip
                              label={getAnalysisTypeLabel(result.analysis_type)}
                              size="small"
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell>{result.analysis_name}</TableCell>
                          <TableCell>
                            <Chip
                              label={result.status}
                              size="small"
                              color={getStatusColor(result.status) as any}
                            />
                          </TableCell>
                          <TableCell align="right">
                            {result.result_count?.toLocaleString() || 0}
                          </TableCell>
                          <TableCell align="right">
                            {result.execution_time_ms?.toLocaleString() || 0}
                          </TableCell>
                          <TableCell>
                            {format(new Date(result.created_at), 'MMM dd, yyyy HH:mm')}
                          </TableCell>
                          <TableCell align="center">
                            <Tooltip title="View Results">
                              <IconButton
                                size="small"
                                onClick={() => handleViewResult(result.id)}
                                color="primary"
                              >
                                <ViewIcon />
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>

                <TablePagination
                  rowsPerPageOptions={[10, 20, 50, 100]}
                  component="div"
                  count={resultsData.total}
                  rowsPerPage={rowsPerPage}
                  page={page}
                  onPageChange={handleChangePage}
                  onRowsPerPageChange={handleChangeRowsPerPage}
                />
              </>
            )}

            {!isLoading && (!resultsData || resultsData.results.length === 0) && (
              <Alert severity="info">
                No analysis results found. Run some analyses to see results here.
              </Alert>
            )}
          </>
        </CardContent>
      </Card>

      {/* Results Dialog */}
      <Dialog
        open={resultsDialogOpen}
        onClose={() => setResultsDialogOpen(false)}
        maxWidth="xl"
        fullWidth
      >
        <DialogTitle>
          Analysis Results
        </DialogTitle>
        <DialogContent>
          {selectedResult && (
            <AnalysisResultsViewer
              result={selectedResult}
              onRerun={async (parameters) => {
                try {
                  // If onRerunRequest is provided for stock_scan, use it to navigate to form
                  if (onRerunRequest && selectedResult.analysis_type === 'stock_scan') {
                    onRerunRequest(selectedResult.analysis_type, parameters);
                    setResultsDialogOpen(false);
                    return;
                  }
                  
                  // Otherwise, start analysis via API
                  await analyticsApi.startAnalysis(
                    selectedResult.analysis_type,
                    selectedResult.analysis_name,
                    parameters
                  );
                  // Refresh the results list
                  queryClient.invalidateQueries('analysisResults');
                  // Close the results dialog
                  setResultsDialogOpen(false);
                  // Show success message
                  console.log('Analysis rerun started successfully');
                } catch (error) {
                  console.error('Failed to start rerun:', error);
                  // TODO: Show error message to user
                }
              }}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResultsDialogOpen(false)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AnalysisResultsPanel;

