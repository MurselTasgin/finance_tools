// finance_tools/frontend/src/components/AnalyticsDashboard.tsx
import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { ETFTechnicalAnalysisForm } from './ETFTechnicalAnalysisForm';
import { AnalysisResultsViewer } from './AnalysisResultsViewer';
import { ETFScanAnalysisForm } from './ETFScanAnalysisForm';
import { StockScanAnalysisForm } from './StockScanAnalysisForm';
import AnalysisJobsPanel from './AnalysisJobsPanel';
import AnalysisResultsPanel from './AnalysisResultsPanel';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Button,
  Tabs,
  Tab,
  Chip,
  Alert,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Stack,
} from '@mui/material';
import {
  Analytics as AnalyticsIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
  History as HistoryIcon,
  PlayArrow as PlayIcon,
  Search as SearchIcon,
  Timeline as TimelineIcon,
  ShowChart as ChartIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Favorite as FavoriteIcon,
  FavoriteBorder as FavoriteBorderIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { analyticsApi } from '../services/api';

interface AnalyticsCapabilities {
  etf_analytics: {
    technical_analysis: any;
    scan_analysis: any;
  };
  stock_analytics: {
    technical_analysis: any;
  };
  caching: any;
  history_tracking: any;
}

interface AnalysisResult {
  analysis_type: string;
  analysis_name: string;
  parameters: any;
  results: any;
  result_count: number;
  execution_time_ms: number;
  timestamp: string;
  error?: string;
}

interface HistoryItem {
  id: number;
  analysis_type: string;
  analysis_name: string;
  parameters: any;
  executed_at: string;
  execution_time_ms: number;
  is_favorite: boolean;
  access_count: number;
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
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export const AnalyticsDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [capabilities, setCapabilities] = useState<AnalyticsCapabilities | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Analysis state
  const [runningAnalysis, setRunningAnalysis] = useState<string | null>(null);
  const [analysisResults, setAnalysisResults] = useState<AnalysisResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<AnalysisResult | null>(null);
  const [resultsDialogOpen, setResultsDialogOpen] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState<{[key: string]: number}>({});

  // History state
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // Filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Analysis functions
  const viewResult = (result: AnalysisResult) => {
    setSelectedResult(result);
    setResultsDialogOpen(true);
  };

  const closeResultsDialog = () => {
    setResultsDialogOpen(false);
    setSelectedResult(null);
  };

  const rerunAnalysis = (historyItem: HistoryItem) => {
    runAnalysis(
      historyItem.analysis_type,
      historyItem.analysis_name,
      historyItem.parameters
    );
  };

  const handleExport = (result: AnalysisResult, format: string) => {
    // Implementation for exporting results
    console.log('Exporting result:', result.analysis_name, 'Format:', format);
    // This would implement actual export functionality
  };

  useEffect(() => {
    loadCapabilities();
    loadHistory();
  }, []);

  const loadCapabilities = async () => {
    try {
      setLoading(true);
      const response = await analyticsApi.getCapabilities();
      setCapabilities(response);
    } catch (err: any) {
      setError(err.message || 'Failed to load analytics capabilities');
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      setHistoryLoading(true);
      const response = await analyticsApi.getHistory({ limit: 20 });
      setHistory(response.history || []);
    } catch (err: any) {
      console.error('Failed to load history:', err);
    } finally {
      setHistoryLoading(false);
    }
  };

  const runAnalysis = async (analysisType: string, analysisName: string, parameters: any) => {
    try {
      setRunningAnalysis(analysisType);
      setError(null);

      // Start analysis task in background
      const response = await analyticsApi.startAnalysis(analysisType, analysisName, parameters);
      
      if (response.task_id) {
        // Show success message and navigate to Jobs tab
        alert(`✅ Analysis started! Task ID: ${response.task_id}\n\nView progress in the "Jobs & History" tab.`);
        setActiveTab(3); // Switch to Jobs & History tab
        return;
      }

      throw new Error("Failed to start analysis task");
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || err?.message || "Analysis failed";
      setError(errorMessage);
      console.error("Analysis error:", err);
    } finally {
      setRunningAnalysis(null);
    }
  };

  const toggleFavorite = async (historyId: number, currentFavorite: boolean) => {
    // For now, just update local state - in a real app, you'd call an API
    setHistory(prev =>
      prev.map(item =>
        item.id === historyId
          ? { ...item, is_favorite: !currentFavorite }
          : item
      )
    );
  };


  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading analytics capabilities...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
        <Button size="small" onClick={loadCapabilities} sx={{ ml: 2 }}>
          Retry
        </Button>
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        <AnalyticsIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
        Analytics Dashboard
      </Typography>

      {/* Progress Indicators for Running Analyses */}
      {runningAnalysis && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Box display="flex" alignItems="center" gap={2}>
            <CircularProgress size={20} />
            <Typography>
              Running {runningAnalysis.replace('_', ' ')} analysis...
            </Typography>
            <Box flexGrow={1} />
            <Typography variant="body2">
              {analysisProgress[runningAnalysis] || 0}% complete
            </Typography>
          </Box>
          <Box sx={{ width: '100%', mt: 1 }}>
            <Box
              sx={{
                height: 4,
                bgcolor: 'primary.light',
                borderRadius: 2,
                width: `${analysisProgress[runningAnalysis] || 0}%`,
                transition: 'width 0.3s ease-in-out',
              }}
            />
          </Box>
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Capabilities Overview */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <AssessmentIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Available Analytics
              </Typography>

              {capabilities && (
                <Box>
                  <Chip
                    label={`ETF Analysis`}
                    color="primary"
                    variant="outlined"
                    sx={{ mr: 1, mb: 1 }}
                  />
                  <Chip
                    label={`Stock Analysis`}
                    color="secondary"
                    variant="outlined"
                    sx={{ mr: 1, mb: 1 }}
                  />
                  <Chip
                    label={`Caching: ${capabilities.caching.ttl_hours}h`}
                    color="success"
                    variant="outlined"
                    sx={{ mb: 1 }}
                  />
                </Box>
              )}

              <Divider sx={{ my: 2 }} />

              <Typography variant="body2" color="text.secondary">
                Select an analysis type from the tabs above to configure and run technical analysis.
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <PlayIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Quick Actions
              </Typography>

              <Stack spacing={1}>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => setActiveTab(0)}
                  startIcon={<TrendingUpIcon />}
                >
                  ETF Technical Analysis
                </Button>

                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => setActiveTab(1)}
                  startIcon={<AssessmentIcon />}
                >
                  ETF Scan Analysis
                </Button>

                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => setActiveTab(2)}
                  startIcon={<TimelineIcon />}
                >
                  Stock Technical Analysis
                </Button>

                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => setActiveTab(3)}
                  startIcon={<SearchIcon />}
                >
                  Stock Scan Analysis
                </Button>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Results */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <HistoryIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Recent Results
              </Typography>

              {analysisResults.length > 0 ? (
                <Box>
                  {analysisResults.slice(0, 3).map((result, index) => (
                    <Box key={index} sx={{ mb: 1 }}>
                      <Typography variant="body2" noWrap>
                        {result.analysis_name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {new Date(result.timestamp).toLocaleString()}
                      </Typography>
                    </Box>
                  ))}
                  <Button size="small" onClick={() => setActiveTab(3)}>
                    View All Results
                  </Button>
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No recent results. Run an analysis to see results here.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Content Tabs */}
      <Paper sx={{ mt: 3 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
            <Tab label="ETF Technical" />
            <Tab label="ETF Scan" />
            <Tab label="Stock Technical" />
            <Tab label="Stock Scan" />
            <Tab label="Jobs & History" />
            <Tab label="Results & History" />
          </Tabs>
        </Box>

        <TabPanel value={activeTab} index={0}>
          <ETFTechnicalAnalysisPanel
            capabilities={capabilities}
            onRunAnalysis={runAnalysis}
            running={runningAnalysis === 'etf_technical'}
          />
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <ETFScanAnalysisPanel
            capabilities={capabilities}
            onRunAnalysis={runAnalysis}
            running={runningAnalysis === 'etf_scan'}
          />
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <StockTechnicalAnalysisPanel
            capabilities={capabilities}
            onRunAnalysis={runAnalysis}
            running={runningAnalysis === 'stock_technical'}
          />
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          <StockScanAnalysisPanel
            capabilities={capabilities}
            onRunAnalysis={runAnalysis}
            running={runningAnalysis === 'stock_scan'}
          />
        </TabPanel>

        <TabPanel value={activeTab} index={4}>
          <AnalysisJobsPanel />
        </TabPanel>

        <TabPanel value={activeTab} index={5}>
          <AnalysisResultsPanel />
        </TabPanel>
      </Paper>

      {/* Results Viewer Dialog */}
      <Dialog
        open={resultsDialogOpen}
        onClose={closeResultsDialog}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: { minHeight: '80vh' }
        }}
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">
              {selectedResult?.analysis_name || 'Analysis Results'}
            </Typography>
            <IconButton onClick={closeResultsDialog}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {selectedResult && (
            <AnalysisResultsViewer
              result={selectedResult}
              onExport={(format) => handleExport(selectedResult, format)}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={closeResultsDialog}>Close</Button>
          {selectedResult && (
            <Button
              variant="contained"
              startIcon={<DownloadIcon />}
              onClick={() => handleExport(selectedResult, 'csv')}
            >
              Export Results
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

// Placeholder components for each analysis type
const ETFTechnicalAnalysisPanel: React.FC<any> = ({ capabilities, onRunAnalysis, running }) => (
  <ETFTechnicalAnalysisForm 
    onRunAnalysis={(parameters) => onRunAnalysis('etf_technical', 'ETF Technical Analysis', parameters)} 
    running={running} 
  />
);

const ETFScanAnalysisPanel: React.FC<any> = ({ capabilities, onRunAnalysis, running }) => (
  <ETFScanAnalysisForm
    onRunAnalysis={(parameters) => onRunAnalysis('etf_scan', 'ETF Scan Analysis', parameters)}
    running={running}
  />
);

const StockTechnicalAnalysisPanel: React.FC<any> = ({ capabilities, onRunAnalysis, running }) => (
  <Box>
    <Typography variant="h6" gutterBottom>
      Stock Technical Analysis Configuration
    </Typography>
    <Alert severity="info" sx={{ mb: 2 }}>
      Stock Technical Analysis panel implementation in progress.
    </Alert>
    <Button
      variant="contained"
      disabled={running}
      startIcon={running ? <CircularProgress size={20} /> : <PlayIcon />}
      onClick={() => onRunAnalysis('stock_technical', 'Stock Technical Analysis', {
        symbols: ['AAPL'],
        indicators: ['EMA', 'RSI']
      })}
    >
      {running ? 'Running Analysis...' : 'Run Sample Analysis'}
    </Button>
  </Box>
);

const StockScanAnalysisPanel: React.FC<any> = ({ capabilities, onRunAnalysis, running }) => (
  <StockScanAnalysisForm
    onRunAnalysis={(parameters) => onRunAnalysis('stock_scan', 'Stock Scan Analysis', parameters)}
    running={running}
  />
);

const ResultsHistoryPanel: React.FC<any> = ({
  results, history, loading, searchTerm, onSearchChange,
  filterType, onFilterChange, onRerunAnalysis, onToggleFavorite, onViewResult,
  setSortBy, setSortOrder, setActiveTab, sortBy, sortOrder
}) => (
  <Box>
    <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
      <Typography variant="h6">
        Analysis Results & History
      </Typography>

      <Box display="flex" gap={2}>
        <TextField
          size="small"
          placeholder="Search analyses..."
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />

        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Filter</InputLabel>
          <Select
            value={filterType}
            label="Filter"
            onChange={(e: SelectChangeEvent) => onFilterChange(e.target.value)}
          >
            <MenuItem value="all">All Types</MenuItem>
            <MenuItem value="etf_technical">ETF Technical</MenuItem>
            <MenuItem value="etf_scan">ETF Scan</MenuItem>
            <MenuItem value="stock_technical">Stock Technical</MenuItem>
          </Select>
        </FormControl>
      </Box>
    </Box>

    {loading ? (
      <CircularProgress />
    ) : (
      <Grid container spacing={2}>
        {/* Recent Results */}
        <Grid item xs={12} md={6}>
          <Typography variant="h6" gutterBottom>
            Recent Results ({results.length})
          </Typography>
          {results.length > 0 ? (
            <List>
              {results.slice(0, 5).map((result: AnalysisResult, index: number) => (
                <ListItem
                  key={index}
                  divider
                  button
                  onClick={() => onViewResult(result)}
                >
                  <ListItemIcon>
                    <ChartIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary={result.analysis_name}
                    secondary={
                      <Box>
                        <Typography variant="body2">
                          {result.result_count} results • {result.execution_time_ms}ms
                        </Typography>
                        <Typography variant="caption">
                          {new Date(result.timestamp).toLocaleString()}
                        </Typography>
                      </Box>
                    }
                  />
                  <Tooltip title="View Details">
                    <IconButton size="small">
                      <ChartIcon />
                    </IconButton>
                  </Tooltip>
                </ListItem>
              ))}
              {results.length > 5 && (
                <ListItem>
                  <Button fullWidth onClick={() => setActiveTab(3)}>
                    View All Results ({results.length})
                  </Button>
                </ListItem>
              )}
            </List>
          ) : (
            <Typography color="text.secondary">No recent results</Typography>
          )}
        </Grid>

        {/* History */}
        <Grid item xs={12} md={6}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              Analysis History ({history.length})
            </Typography>

            <Box display="flex" gap={1}>
              <FormControl size="small" sx={{ minWidth: 100 }}>
                <InputLabel>Sort By</InputLabel>
                <Select
                  value={sortBy}
                  label="Sort By"
                  onChange={(e: SelectChangeEvent) => setSortBy(e.target.value)}
                >
                  <MenuItem value="date">Date</MenuItem>
                  <MenuItem value="name">Name</MenuItem>
                  <MenuItem value="type">Type</MenuItem>
                  <MenuItem value="execution_time">Execution Time</MenuItem>
                </Select>
              </FormControl>

              <Button
                size="small"
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              >
                {sortOrder === 'asc' ? '↑' : '↓'}
              </Button>
            </Box>
          </Box>

          {(() => {
            // Filter and sort history
            const filtered = history.filter((item: HistoryItem) => {
              const matchesSearch = item.analysis_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                                   item.analysis_type.toLowerCase().includes(searchTerm.toLowerCase());
              const matchesFilter = filterType === 'all' || item.analysis_type === filterType;
              return matchesSearch && matchesFilter;
            });

            // Sort results
            const sorted = [...filtered].sort((a, b) => {
              let aValue: any, bValue: any;

              switch (sortBy) {
                case 'date':
                  aValue = new Date(a.executed_at);
                  bValue = new Date(b.executed_at);
                  break;
                case 'name':
                  aValue = a.analysis_name.toLowerCase();
                  bValue = b.analysis_name.toLowerCase();
                  break;
                case 'type':
                  aValue = a.analysis_type.toLowerCase();
                  bValue = b.analysis_type.toLowerCase();
                  break;
                case 'execution_time':
                  aValue = a.execution_time_ms;
                  bValue = b.execution_time_ms;
                  break;
                default:
                  aValue = a.executed_at;
                  bValue = b.executed_at;
              }

              if (sortOrder === 'asc') {
                return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
              } else {
                return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
              }
            });

            return sorted.length > 0 ? (
              <List sx={{ maxHeight: 400, overflow: 'auto' }}>
                {sorted.slice(0, 10).map((item: HistoryItem) => (
                <ListItem key={item.id} divider>
                  <ListItemIcon>
                    <IconButton
                      size="small"
                      onClick={() => onToggleFavorite(item.id, item.is_favorite)}
                    >
                      {item.is_favorite ? <FavoriteIcon color="error" /> : <FavoriteBorderIcon />}
                    </IconButton>
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box display="flex" alignItems="center" gap={1}>
                        <Typography variant="body1">
                          {item.analysis_name}
                        </Typography>
                        {item.is_favorite && (
                          <Chip label="Favorite" size="small" color="primary" />
                        )}
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="body2">
                          {item.access_count} runs • {item.execution_time_ms}ms avg
                        </Typography>
                        <Typography variant="caption">
                          {new Date(item.executed_at).toLocaleString()}
                        </Typography>
                      </Box>
                    }
                  />
                  <Box display="flex" gap={1}>
                    <Tooltip title="Re-run Analysis">
                      <IconButton size="small" onClick={() => onRerunAnalysis(item)}>
                        <RefreshIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="View Details">
                      <IconButton size="small" onClick={() => onViewResult({
                        analysis_type: item.analysis_type,
                        analysis_name: item.analysis_name,
                        parameters: item.parameters,
                        results: null,
                        result_count: 0,
                        execution_time_ms: item.execution_time_ms,
                        timestamp: item.executed_at,
                      })}>
                        <ChartIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </ListItem>
              ))}
                {sorted.length > 10 && (
                  <ListItem>
                    <Button fullWidth onClick={() => setActiveTab(3)}>
                      View All History ({sorted.length})
                    </Button>
                  </ListItem>
                )}
              </List>
            ) : (
              <Typography color="text.secondary">No analysis history</Typography>
            );
          })()}
        </Grid>
      </Grid>
    )}
  </Box>
);

