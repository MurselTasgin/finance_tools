// frontend/src/components/AnalysisResultsViewer.tsx
/**
 * Flexible Analysis Results Viewer
 * 
 * Displays analysis results in different formats based on the analysis type:
 * - Tables with sorting for structured data
 * - Charts for time series and numerical data
 * - Cards for summary information
 * - JSON viewer for raw data
 */

import React, { useState, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Button,
  Grid,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  InputAdornment,
  TableSortLabel,
  TablePagination,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  TableChart as TableIcon,
  BarChart as ChartIcon,
  DataObject as JsonIcon,
  Search as SearchIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface AnalysisResult {
  analysis_type: string;
  analysis_name: string;
  parameters: any;
  results: any[];
  result_count: number;
  execution_time_ms: number;
  timestamp: string;
  metadata?: any;
}

interface AnalysisResultsViewerProps {
  result: AnalysisResult;
  onExport?: (format: string) => void;
  onRerun?: (parameters: any) => void;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ p: 2 }}>{children}</Box>}
    </div>
  );
}

export const AnalysisResultsViewer: React.FC<AnalysisResultsViewerProps> = ({ result, onExport, onRerun }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<string>('');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);

  // Additional filters
  const [scoreFilter, setScoreFilter] = useState<string>('all'); // 'all', 'positive', 'negative', 'zero'
  const [recommendationFilter, setRecommendationFilter] = useState<string>('all'); // 'all', 'BUY', 'SELL', 'HOLD'
  const [symbolFilter, setSymbolFilter] = useState<string>('');

  // Rerun dialog
  const [rerunDialogOpen, setRerunDialogOpen] = useState(false);
  const [editedParameters, setEditedParameters] = useState<any>(null);


  // Process results based on analysis type
  const processedResults = useMemo(() => {
    if (!result.results || !Array.isArray(result.results)) {
      return [];
    }

    let processed = [...result.results];

    // Apply search filter
    if (searchTerm) {
      processed = processed.filter((item: any) => {
        return JSON.stringify(item).toLowerCase().includes(searchTerm.toLowerCase());
      });
    }
    
    // Apply score filter
    if (scoreFilter !== 'all') {
      processed = processed.filter((item: any) => {
        const score = item.score || 0;
        switch (scoreFilter) {
          case 'positive':
            return score > 0;
          case 'negative':
            return score < 0;
          case 'zero':
            return score === 0;
          default:
            return true;
        }
      });
    }
    
    // Apply recommendation filter
    if (recommendationFilter !== 'all') {
      processed = processed.filter((item: any) => {
        return item.recommendation === recommendationFilter;
      });
    }
    
    // Apply symbol filter
    if (symbolFilter) {
      processed = processed.filter((item: any) => {
        const symbol = item.symbol || item.code || '';
        return symbol.toLowerCase().includes(symbolFilter.toLowerCase());
      });
    }

    // Apply sorting
    if (sortField) {
      processed.sort((a: any, b: any) => {
        const aValue = a[sortField];
        const bValue = b[sortField];
        
        if (aValue === bValue) return 0;
        
        const comparison = aValue < bValue ? -1 : 1;
        return sortOrder === 'asc' ? comparison : -comparison;
      });
    }

    return processed;
  }, [result.results, searchTerm, sortField, sortOrder, scoreFilter, recommendationFilter, symbolFilter]);

  // Get paginated results
  const paginatedResults = useMemo(() => {
    const startIndex = page * rowsPerPage;
    const endIndex = startIndex + rowsPerPage;
    return processedResults.slice(startIndex, endIndex);
  }, [processedResults, page, rowsPerPage]);

  // Pagination handlers
  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };


  // Determine if data is suitable for charts
  const isChartable = useMemo(() => {
    if (!result.results || result.results.length === 0) return false;
    
    const firstItem = result.results[0];
    if (typeof firstItem === 'object' && firstItem !== null) {
      const keys = Object.keys(firstItem);
      // Check if we have numeric fields suitable for charts
      return keys.some(key => 
        typeof firstItem[key] === 'number' || 
        (typeof firstItem[key] === 'string' && !isNaN(Number(firstItem[key])))
      );
    }
    return false;
  }, [result.results]);

  // Prepare chart data
  const chartData = useMemo(() => {
    if (!isChartable || !result.results) return [];
    
    return result.results.map((item: any, index: number) => {
      const chartItem: any = { index };
      
      // Convert numeric fields for charting
      Object.keys(item).forEach(key => {
        const value = item[key];
        if (typeof value === 'number') {
          chartItem[key] = value;
        } else if (typeof value === 'string' && !isNaN(Number(value))) {
          chartItem[key] = Number(value);
        } else {
          chartItem[key] = value;
        }
      });
      
      return chartItem;
    });
  }, [result.results, isChartable]);

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const renderTable = () => {
    if (!result.results || result.results.length === 0) {
      return (
        <Alert severity="info">
          No results to display
        </Alert>
      );
    }

    // Special rendering for ETF scan results
    if (result.analysis_type === 'etf_scan') {
      return renderEtfScanTable();
    }

    // Special rendering for Stock scan results (same as ETF scan)
    if (result.analysis_type === 'stock_scan') {
      return renderStockScanTable();
    }

    const firstItem = result.results[0];
    if (typeof firstItem !== 'object' || firstItem === null) {
      return (
        <Alert severity="warning">
          Results are not in a table format
        </Alert>
      );
    }

    const columns = Object.keys(firstItem);

    return (
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            Results ({processedResults.length} items)
          </Typography>
          <Box display="flex" gap={2} alignItems="center">
            <TextField
              size="small"
              placeholder="Search results..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(0); // Reset to first page on search
              }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Sort by</InputLabel>
              <Select
                value={sortField}
                label="Sort by"
                onChange={(e) => {
                  setSortField(e.target.value);
                  setPage(0); // Reset to first page on sort change
                }}
              >
                <MenuItem value="">No sorting</MenuItem>
                {columns.map(col => (
                  <MenuItem key={col} value={col}>{col}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </Box>

        <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
          <Table stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell>
                  <TableSortLabel
                    active={sortField === (result.analysis_type === 'stock_scan' ? 'symbol' : 'code')}
                    direction={sortField === (result.analysis_type === 'stock_scan' ? 'symbol' : 'code') ? sortOrder : 'asc'}
                    onClick={() => handleSort(result.analysis_type === 'stock_scan' ? 'symbol' : 'code')}
                  >
                    {result.analysis_type === 'stock_scan' ? 'Symbol' : 'Code'}
                  </TableSortLabel>
                </TableCell>
                <TableCell>
                  <TableSortLabel
                    active={sortField === 'recommendation'}
                    direction={sortField === 'recommendation' ? sortOrder : 'asc'}
                    onClick={() => handleSort('recommendation')}
                  >
                    Recommendation
                  </TableSortLabel>
                </TableCell>
                <TableCell>
                  <TableSortLabel
                    active={sortField === 'score'}
                    direction={sortField === 'score' ? sortOrder : 'asc'}
                    onClick={() => handleSort('score')}
                  >
                    Score
                  </TableSortLabel>
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedResults.map((item: any, index: number) => (
                <TableRow key={page * rowsPerPage + index} hover>
                  {columns.map((column) => (
                    <TableCell key={column}>
                      {typeof item[column] === 'number' ? 
                        item[column].toLocaleString() : 
                        String(item[column] || '-')
                      }
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <TablePagination
          rowsPerPageOptions={[25, 50, 100, 200]}
          component="div"
          count={processedResults.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Box>
    );
  };

  const renderStockScanTable = () => {
    return renderEtfScanTable();  // Use ETF table format with symbols instead of codes
  };

  const renderEtfScanTable = () => {
    return (
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2} flexWrap="wrap" gap={2}>
          <Typography variant="h6">
            {result.analysis_type === 'stock_scan' ? 'Stock' : 'ETF'} Scan Results ({processedResults.length} items)
          </Typography>
        </Box>
        
        {/* Advanced Filters */}
        <Box display="flex" gap={2} alignItems="center" mb={2} flexWrap="wrap">
          <TextField
            size="small"
            placeholder={`Search by ${result.analysis_type === 'stock_scan' ? 'symbol' : 'code'}...`}
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
          />
          
          <TextField
            size="small"
            placeholder="Filter by symbol..."
            value={symbolFilter}
            onChange={(e) => {
              setSymbolFilter(e.target.value);
              setPage(0);
            }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
          
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Score Filter</InputLabel>
            <Select
              value={scoreFilter}
              label="Score Filter"
              onChange={(e) => {
                setScoreFilter(e.target.value);
                setPage(0);
              }}
            >
              <MenuItem value="all">All Scores</MenuItem>
              <MenuItem value="positive">Positive (&gt;0)</MenuItem>
              <MenuItem value="negative">Negative (&lt;0)</MenuItem>
              <MenuItem value="zero">Zero (=0)</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Recommendation</InputLabel>
            <Select
              value={recommendationFilter}
              label="Recommendation"
              onChange={(e) => {
                setRecommendationFilter(e.target.value);
                setPage(0);
              }}
            >
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="BUY">BUY</MenuItem>
              <MenuItem value="SELL">SELL</MenuItem>
              <MenuItem value="HOLD">HOLD</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Sort by</InputLabel>
            <Select
              value={sortField}
              label="Sort by"
              onChange={(e) => {
                setSortField(e.target.value);
                setPage(0);
              }}
            >
              <MenuItem value="">No sorting</MenuItem>
              <MenuItem value={result.analysis_type === 'stock_scan' ? 'symbol' : 'code'}>{result.analysis_type === 'stock_scan' ? 'Symbol' : 'Code'}</MenuItem>
              <MenuItem value="score">Score</MenuItem>
              <MenuItem value="recommendation">Recommendation</MenuItem>
            </Select>
          </FormControl>
        </Box>

        <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
          <Table stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell>
                  <TableSortLabel
                    active={sortField === (result.analysis_type === 'stock_scan' ? 'symbol' : 'code')}
                    direction={sortField === (result.analysis_type === 'stock_scan' ? 'symbol' : 'code') ? sortOrder : 'asc'}
                    onClick={() => handleSort(result.analysis_type === 'stock_scan' ? 'symbol' : 'code')}
                  >
                    {result.analysis_type === 'stock_scan' ? 'Symbol' : 'Code'}
                  </TableSortLabel>
                </TableCell>
                <TableCell>
                  <TableSortLabel
                    active={sortField === 'recommendation'}
                    direction={sortField === 'recommendation' ? sortOrder : 'asc'}
                    onClick={() => handleSort('recommendation')}
                  >
                    Recommendation
                  </TableSortLabel>
                </TableCell>
                <TableCell>
                  <TableSortLabel
                    active={sortField === 'score'}
                    direction={sortField === 'score' ? sortOrder : 'asc'}
                    onClick={() => handleSort('score')}
                  >
                    Score
                  </TableSortLabel>
                </TableCell>
                <TableCell>
                  <TableSortLabel
                    active={sortField === 'last_value'}
                    direction={sortField === 'last_value' ? sortOrder : 'asc'}
                    onClick={() => handleSort('last_value')}
                  >
                    Last Value
                  </TableSortLabel>
                </TableCell>
                <TableCell>Indicator Analysis</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedResults.map((item: any, index: number) => (
                <TableRow key={page * rowsPerPage + index} hover>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                      {item.symbol || item.code}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={item.recommendation}
                      color={
                        item.recommendation === 'BUY' ? 'success' :
                        item.recommendation === 'SELL' ? 'error' : 'default'
                      }
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        fontWeight: 'bold',
                        color: item.score > 0 ? 'success.main' : item.score < 0 ? 'error.main' : 'text.primary'
                      }}
                    >
                      {item.score?.toFixed(3) || 'N/A'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {item.last_value ? item.last_value.toFixed(2) : 'N/A'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ maxWidth: 500, maxHeight: 250, overflow: 'auto' }}>
                      {item.indicator_details ? (
                        // New grouped structure: show each indicator with its values, contribution, and reasons
                        Object.entries(item.indicator_details).map(([indicatorId, indData]: [string, any]) => (
                          <Box key={indicatorId} sx={{ mb: 2, p: 1, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
                            <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 0.5, color: 'primary.main' }}>
                              {indData.name || indicatorId}
                            </Typography>
                            
                            {/* Technical Indicator Values */}
                            {indData.values && Object.keys(indData.values).length > 0 && (
                              <Box sx={{ mb: 1 }}>
                                <Typography variant="caption" color="textSecondary" sx={{ fontWeight: 'bold' }}>
                                  Values:
                                </Typography>
                                {Object.entries(indData.values).map(([key, value]: [string, any]) => (
                                  <Box key={key} sx={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', pl: 1 }}>
                                    <Typography variant="caption" color="textSecondary">
                                      {key.replace('_', ' ')}:
                                    </Typography>
                                    <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                                      {typeof value === 'number' && !isNaN(value) ? value.toFixed(2) : 'N/A'}
                                    </Typography>
                                  </Box>
                                ))}
                              </Box>
                            )}

                            {/* Score Calculation Details */}
                            {indData.calculation_details && indData.calculation_details.length > 0 && (
                              <Box sx={{ mb: 1, p: 1, bgcolor: 'action.hover', borderRadius: 1 }}>
                                <Typography variant="caption" color="textSecondary" sx={{ fontWeight: 'bold', display: 'block', mb: 0.5 }}>
                                  Score Calculation Details:
                                </Typography>
                                <Box sx={{ pl: 1, fontFamily: 'monospace' }}>
                                  {indData.calculation_details.map((detail: string, detailIndex: number) => (
                                    <Typography
                                      key={detailIndex}
                                      variant="caption"
                                      display="block"
                                      sx={{
                                        fontSize: '0.7rem',
                                        lineHeight: 1.4,
                                        whiteSpace: 'pre',
                                        color: detail.includes('Step') ? 'primary.main' : 'text.secondary',
                                        fontWeight: detail.includes('Step') ? 'bold' : 'normal'
                                      }}
                                    >
                                      {detail}
                                    </Typography>
                                  ))}
                                </Box>
                              </Box>
                            )}

                            {/* Score Contribution */}
                            {(indData.contribution !== undefined || indData.weight > 0) && (
                              <Box sx={{ mb: 1 }}>
                                <Typography variant="caption" color="textSecondary" sx={{ fontWeight: 'bold' }}>
                                  Contribution: {typeof indData.contribution === 'number' ? indData.contribution.toFixed(3) : 'N/A'}
                                </Typography>
                                {indData.raw !== undefined && indData.weight > 0 && (
                                  <Typography variant="caption" color="textSecondary" sx={{ fontSize: '0.65rem', pl: 1, display: 'block' }}>
                                    (Raw: {indData.raw.toFixed(3)} × Weight: {indData.weight} = {indData.contribution.toFixed(3)})
                                  </Typography>
                                )}
                              </Box>
                            )}
                            
                            {/* Reasons/Explanations */}
                            {indData.reasons && indData.reasons.length > 0 && (
                              <Box>
                                <Typography variant="caption" color="textSecondary" sx={{ fontWeight: 'bold' }}>
                                  Analysis:
                                </Typography>
                                <Box sx={{ pl: 1 }}>
                                  {indData.reasons.map((reason: string, reasonIndex: number) => (
                                    reason && (
                                      <Typography 
                                        key={reasonIndex} 
                                        variant="caption" 
                                        display="block" 
                                        sx={{ 
                                          mb: 0.25,
                                          fontSize: '0.7rem',
                                          fontFamily: reason.startsWith('  •') ? 'monospace' : 'inherit',
                                          color: reason.includes('BUY') ? 'success.main' : reason.includes('SELL') ? 'error.main' : 'text.secondary'
                                        }}
                                      >
                                        {reason}
                                      </Typography>
                                    )
                                  ))}
                                </Box>
                              </Box>
                            )}
                          </Box>
                        ))
                      ) : (
                        // Fallback to old structure for backward compatibility
                        <Box>
                          <Typography variant="caption" color="textSecondary">
                            {item.indicators_snapshot || item.components ? 'Using legacy format' : 'No indicator data'}
                          </Typography>
                        </Box>
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <TablePagination
          rowsPerPageOptions={[25, 50, 100, 200]}
          component="div"
          count={processedResults.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Box>
    );
  };

  const renderChart = () => {
    if (!isChartable || chartData.length === 0) {
      return (
        <Alert severity="info">
          Data is not suitable for charting
        </Alert>
      );
    }

    const numericColumns = Object.keys(chartData[0]).filter(key => 
      key !== 'index' && typeof chartData[0][key] === 'number'
    );

    if (numericColumns.length === 0) {
      return (
        <Alert severity="info">
          No numeric data available for charting
        </Alert>
      );
    }

    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          Data Visualization
        </Typography>
        <Box height={400}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="index" />
              <YAxis />
              <RechartsTooltip />
              <Legend />
              {numericColumns.slice(0, 5).map((column, index) => (
                <Line
                  key={column}
                  type="monotone"
                  dataKey={column}
                  stroke={`hsl(${index * 60}, 70%, 50%)`}
                  strokeWidth={2}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </Box>
      </Box>
    );
  };

  const renderJson = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        Raw Data (JSON)
      </Typography>
      <Paper sx={{ p: 2, bgcolor: '#f5f5f5' }}>
        <pre style={{ 
          margin: 0, 
          fontSize: '12px', 
          overflow: 'auto',
          maxHeight: '500px'
        }}>
          {JSON.stringify(result, null, 2)}
        </pre>
      </Paper>
    </Box>
  );

  const renderSummary = () => (
    <Grid container spacing={2} sx={{ mb: 3 }}>
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Analysis Type
            </Typography>
            <Typography variant="h6">
              {result.analysis_type.replace('_', ' ').toUpperCase()}
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Results Count
            </Typography>
            <Typography variant="h6">
              {result.result_count || result.results?.length || 0}
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Execution Time
            </Typography>
            <Typography variant="h6">
              {result.execution_time_ms}ms
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Timestamp
            </Typography>
            <Typography variant="h6">
              {new Date(result.timestamp).toLocaleString()}
            </Typography>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderScannerConfiguration = () => {
    if (
      !result.parameters ||
      (result.analysis_type !== 'etf_scan' && result.analysis_type !== 'stock_scan')
    ) {
      return null;
    }

    const {
      scanners = [],
      scanner_configs = {},
      weights = {},
      actual_parameters,
      scanner_summary,
      symbols = [],
      specific_codes = [],
      fund_type,
      include_keywords,
      exclude_keywords,
      case_sensitive,
      buy_threshold,
      sell_threshold,
      score_threshold,
      start_date,
      end_date,
      column,
      sector,
      industry,
    } = result.parameters;

    const isStock = result.analysis_type === 'stock_scan';
    const keywordListIncluded = Array.isArray(include_keywords) ? include_keywords : [];
    const keywordListExcluded = Array.isArray(exclude_keywords) ? exclude_keywords : [];
    const totalScanners = scanner_summary?.total_scanners ?? scanners.length;
    const buyCount = scanner_summary?.buy_count ?? (result as any).buy_count ?? 0;
    const sellCount = scanner_summary?.sell_count ?? (result as any).sell_count ?? 0;
    const holdCount = scanner_summary?.hold_count ?? (result as any).hold_count ?? 0;
    const multiReasonCount = scanner_summary?.multi_reason_count ?? (result as any).multi_reason_count ?? 0;

    return (
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography
            variant="h6"
            sx={{ mb: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
          >
            <span>{isStock ? 'Stock' : 'ETF'} Scan Configuration</span>
            {onRerun && (
              <Button
                size="small"
                variant="outlined"
                onClick={() => {
                  setEditedParameters(result.parameters);
                  setRerunDialogOpen(true);
                }}
                startIcon={<SearchIcon />}
              >
                Rerun with Same Setup
              </Button>
            )}
          </Typography>
          <Grid container spacing={2}>
            {/* Assets Selection */}
            <Grid item xs={12} sm={6} md={4}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                {isStock ? 'Stocks Analyzed' : 'Funds Analyzed'}
              </Typography>
              {isStock ? (
                symbols.length > 0 ? (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {symbols.map((symbol: string, idx: number) => (
                      <Chip key={idx} label={symbol} size="small" color="primary" variant="outlined" />
                    ))}
                  </Box>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    All available stocks
                  </Typography>
                )
              ) : specific_codes.length > 0 ? (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {specific_codes.map((code: string, idx: number) => (
                    <Chip key={idx} label={code} size="small" color="primary" variant="outlined" />
                  ))}
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Fund Type: {fund_type || 'All'}
                </Typography>
              )}
            </Grid>

            {/* Analysis Settings */}
            <Grid item xs={12} sm={6} md={4}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Analysis Settings
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                <Chip label={`Start: ${start_date || 'N/A'}`} size="small" variant="outlined" />
                <Chip label={`End: ${end_date || 'N/A'}`} size="small" variant="outlined" />
                <Chip label={`Column: ${column || (isStock ? 'close' : 'price')}`} size="small" variant="outlined" />
                {isStock && sector && <Chip label={`Sector: ${sector}`} size="small" variant="outlined" />}
                {isStock && industry && <Chip label={`Industry: ${industry}`} size="small" variant="outlined" />}
                {!isStock && fund_type && <Chip label={`Fund Type: ${fund_type}`} size="small" variant="outlined" />}
              </Box>
            </Grid>

            {/* Thresholds */}
            <Grid item xs={12} sm={6} md={4}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Thresholds
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                {isStock ? (
                  <>
                    <Chip label={`Buy ≥ ${buy_threshold ?? 1}`} size="small" color="success" variant="outlined" />
                    <Chip label={`Sell ≤ ${sell_threshold ?? 1}`} size="small" color="error" variant="outlined" />
                  </>
                ) : (
                  <Chip
                    label={`Score Threshold ≥ ${score_threshold ?? 0}`}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                )}
                {typeof case_sensitive === 'boolean' && !isStock && (
                  <Chip
                    label={`Keywords: ${case_sensitive ? 'Case Sensitive' : 'Case Insensitive'}`}
                    size="small"
                    variant="outlined"
                  />
                )}
              </Box>
            </Grid>

            {/* Keyword Filters */}
            {!isStock && (keywordListIncluded.length > 0 || keywordListExcluded.length > 0) && (
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                  Keyword Filters
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {keywordListIncluded.map((kw: string, idx: number) => (
                    <Chip key={`inc-${idx}`} label={`Include: ${kw}`} size="small" color="success" variant="outlined" />
                  ))}
                  {keywordListExcluded.map((kw: string, idx: number) => (
                    <Chip key={`exc-${idx}`} label={`Exclude: ${kw}`} size="small" color="error" variant="outlined" />
                  ))}
                </Box>
              </Grid>
            )}

            {/* Selected Scanners */}
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Selected Scanners
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {scanners.map((scanner: string) => (
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
                {Object.entries(weights).map(([scanner, weight]) => {
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

            {/* Individual Scanner Parameters */}
            {scanner_configs && Object.keys(scanner_configs).length > 0 && (
              <Grid item xs={12}>
                <Typography variant="subtitle2" sx={{ mb: 2 }}>
                  Individual Scanner Parameters
                </Typography>
                <Grid container spacing={2}>
                  {Object.entries(scanner_configs).map(([scanner, config]) => {
                    const weight = weights?.[scanner] || 0;
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

            {/* Actual Parameters Used */}
            {actual_parameters && (
              <Grid item xs={12}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                  Parameters Used
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {Object.entries(actual_parameters).map(([param, value]) => (
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

            {/* Summary */}
            <Grid item xs={12}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Execution Summary
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                <Chip label={`Total Scanners: ${totalScanners}`} size="small" color="info" />
                <Chip label={`BUY: ${buyCount}`} size="small" color="success" />
                <Chip label={`SELL: ${sellCount}`} size="small" color="error" />
                <Chip label={`HOLD: ${holdCount}`} size="small" color="default" />
                {multiReasonCount > 0 && (
                  <Chip label={`Multi-Reason: ${multiReasonCount}`} size="small" color="secondary" />
                )}
                <Chip label={`Execution: ${result.execution_time_ms || 0}ms`} size="small" variant="outlined" />
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    );
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        <AssessmentIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        {result.analysis_name}
      </Typography>

      {renderSummary()}

      {renderScannerConfiguration()}

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
          <Tab icon={<TableIcon />} label="Table" />
          {isChartable && <Tab icon={<ChartIcon />} label="Charts" />}
          <Tab icon={<JsonIcon />} label="Raw Data" />
        </Tabs>
      </Box>

      <TabPanel value={activeTab} index={0}>
        {renderTable()}
      </TabPanel>

      {isChartable && (
        <TabPanel value={activeTab} index={1}>
          {renderChart()}
        </TabPanel>
      )}

      <TabPanel value={activeTab} index={isChartable ? 2 : 1}>
        {renderJson()}
      </TabPanel>

      {/* Export Actions */}
      <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
        <Button
          variant="outlined"
          onClick={() => onExport?.('csv')}
        >
          Export CSV
        </Button>
        <Button
          variant="outlined"
          onClick={() => onExport?.('json')}
        >
          Export JSON
        </Button>
      </Box>

      {/* Rerun Dialog */}
      <Dialog
        open={rerunDialogOpen}
        onClose={() => setRerunDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Preview & Edit Rerun Parameters
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Alert severity="info" sx={{ mb: 2 }}>
              Review and edit the analysis parameters below. Click "Confirm Rerun" to start a new analysis with these settings.
            </Alert>

            {editedParameters && (
              <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
                <pre style={{
                  margin: 0,
                  fontSize: '12px',
                  overflow: 'auto',
                  maxHeight: '400px',
                  fontFamily: 'monospace'
                }}>
                  {JSON.stringify(editedParameters, null, 2)}
                </pre>
              </Paper>
            )}

            <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
              Note: Advanced parameter editing will be available in a future update. For now, you can review the parameters that will be used for the rerun.
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRerunDialogOpen(false)} color="inherit">
            Cancel
          </Button>
          <Button
            onClick={() => {
              if (onRerun && editedParameters) {
                onRerun(editedParameters);
                setRerunDialogOpen(false);
              }
            }}
            variant="contained"
            color="primary"
            startIcon={<SearchIcon />}
          >
            Confirm Rerun
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AnalysisResultsViewer;
