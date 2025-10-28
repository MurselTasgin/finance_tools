// finance_tools/frontend/src/components/AnalyticsDashboard.tsx
import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { AnalysisResultsViewer } from './AnalysisResultsViewer';
import { UnifiedScanAnalysisPanel } from './UnifiedScanAnalysisPanel';
import { UnifiedTechnicalAnalysisPanel, TechnicalAnalysisInitialState } from './UnifiedTechnicalAnalysisPanel';
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
  IconButton,
  Stack,
} from '@mui/material';
import {
  Analytics as AnalyticsIcon,
  Assessment as AssessmentIcon,
  History as HistoryIcon,
  ShowChart as ChartIcon,
  Download as DownloadIcon,
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
  const [selectedResult, setSelectedResult] = useState<AnalysisResult | null>(null);
  const [resultsDialogOpen, setResultsDialogOpen] = useState(false);
  const [technicalRerunData, setTechnicalRerunData] = useState<TechnicalAnalysisInitialState | null>(null);

  // Rerun state - for pre-populating forms when rerunning analyses
  const [rerunScanData, setRerunScanData] = useState<{ assetType: 'stock' | 'etf'; parameters: any } | null>(null);

  const closeResultsDialog = () => {
    setResultsDialogOpen(false);
    setSelectedResult(null);
  };

  // Handler for rerunning from results viewer - navigates to form with pre-filled parameters
  const handleRerunWithParameters = (analysisType: string, parameters: any) => {
    console.log('Rerun requested with parameters:', {
      analysisType,
      parameters,
      hasScannerConfigs: !!parameters?.scanner_configs,
      hasWeights: !!parameters?.weights,
      scannerIds: parameters?.scanner_configs ? Object.keys(parameters.scanner_configs) : []
    });
    
    setRerunScanData(null);
    setTechnicalRerunData(null);

    const toTechnicalState = (asset: 'stock' | 'etf', params: any): TechnicalAnalysisInitialState => {
      const idFromArray = asset === 'stock'
        ? (Array.isArray(params?.symbols) ? params.symbols[0] : undefined)
        : (Array.isArray(params?.codes) ? params.codes[0] : undefined);
      const identifier =
        (params?.identifier as string | undefined) ||
        idFromArray ||
        (asset === 'stock' ? (params?.symbol as string | undefined) : (params?.code as string | undefined)) ||
        (asset === 'stock' ? 'AAPL' : 'NNF');

      return {
        assetType: asset,
        identifier,
        start_date: params?.start_date || params?.startDate,
        end_date: params?.end_date || params?.endDate,
        interval: params?.interval,
        indicators: params?.indicators || params?.scanner_configs || undefined,
      };
    };

    // Navigate to the appropriate tab based on analysis type
    switch (analysisType) {
      case 'stock_scan':
        setRerunScanData({ assetType: 'stock', parameters });
        setActiveTab(1); // Unified Scan tab
        break;
      case 'etf_scan':
        setRerunScanData({ assetType: 'etf', parameters });
        setActiveTab(1); // Unified Scan tab
        break;
      case 'stock_technical':
        setTechnicalRerunData(toTechnicalState('stock', parameters));
        setActiveTab(0); // Unified Technical tab
        break;
      case 'etf_technical':
        setTechnicalRerunData(toTechnicalState('etf', parameters));
        setActiveTab(0); // Unified Technical tab
        break;
      default:
        console.warn('Unknown analysis type:', analysisType);
    }
  };

  const handleExport = (result: AnalysisResult, format: string) => {
    // Implementation for exporting results
    console.log('Exporting result:', result.analysis_name, 'Format:', format);
    // This would implement actual export functionality
  };

  useEffect(() => {
    loadCapabilities();
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
                <ChartIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Quick Actions
              </Typography>

              <Stack spacing={1}>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => setActiveTab(0)}
                  startIcon={<ChartIcon />}
                >
                  Technical Analysis
                </Button>

                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => setActiveTab(1)}
                  startIcon={<AssessmentIcon />}
                >
                  Scan Analysis
                </Button>

                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => setActiveTab(2)}
                  startIcon={<HistoryIcon />}
                >
                  Jobs &amp; History
                </Button>

                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => setActiveTab(3)}
                  startIcon={<AnalyticsIcon />}
                >
                  Results &amp; History
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

              <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                Launch scan or technical analyses to populate results. Completed runs are available in the
                Results &amp; History tab.
              </Typography>
              <Button size="small" onClick={() => setActiveTab(3)}>
                Open Results &amp; History
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Content Tabs */}
      <Paper sx={{ mt: 3 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
            <Tab label="Technical Analysis" />
            <Tab label="Scan Analysis" />
            <Tab label="Jobs & History" />
            <Tab label="Results & History" />
          </Tabs>
        </Box>

        <TabPanel value={activeTab} index={0}>
          <UnifiedTechnicalAnalysisPanel
            initialState={technicalRerunData}
            onInitialStateConsumed={() => setTechnicalRerunData(null)}
          />
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <UnifiedScanAnalysisPanel
            onRunAnalysis={runAnalysis}
            runningAnalysis={runningAnalysis}
            rerunData={rerunScanData}
            onRerunConsumed={() => setRerunScanData(null)}
          />
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <AnalysisJobsPanel onRerunRequest={handleRerunWithParameters} />
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          <AnalysisResultsPanel onRerunRequest={handleRerunWithParameters} />
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
              onRerun={(parameters) =>
                selectedResult &&
                handleRerunWithParameters(selectedResult.analysis_type, parameters)
              }
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
