// finance_tools/frontend/src/components/ETFScanAnalysisForm.tsx
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Stack,
  Alert,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
  Chip,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Slider,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Search as SearchIcon,
  Settings as SettingsIcon,
  PlayArrow as PlayIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { CircularProgress } from '@mui/material';

interface SelectedScanner {
  id: string;
  name: string;
  weight: number;
  config?: Record<string, any>;
}

interface ETFScanAnalysisFormProps {
  onRunAnalysis: (parameters: any) => void;
  running: boolean;
}

const AVAILABLE_SCANNERS = [
  {
    id: 'ema_cross',
    name: 'EMA Crossover',
    description: 'Exponential Moving Average crossover signals',
    defaultConfig: { short: 20, long: 50 }
  },
  {
    id: 'macd',
    name: 'MACD',
    description: 'Moving Average Convergence Divergence',
    defaultConfig: { slow: 26, fast: 12, signal: 9 }
  },
  {
    id: 'rsi',
    name: 'RSI',
    description: 'Relative Strength Index',
    defaultConfig: { window: 14, lower: 30, upper: 70 }
  },
  {
    id: 'momentum',
    name: 'Momentum',
    description: 'Price momentum indicator',
    defaultConfig: { windows: [30, 60, 90, 180, 360] }
  },
  {
    id: 'daily_momentum',
    name: 'Daily Momentum',
    description: 'Daily price momentum indicator',
    defaultConfig: { windows: [30, 60, 90, 180, 360] }
  },
  {
    id: 'supertrend',
    name: 'Supertrend',
    description: 'Supertrend technical indicator',
    defaultConfig: { hl_factor: 0.05, atr_period: 10, multiplier: 3.0 }
  },
];

export const ETFScanAnalysisForm: React.FC<ETFScanAnalysisFormProps> = ({
  onRunAnalysis,
  running,
}) => {
  // Basic parameters
  const [fundType, setFundType] = useState<'all' | 'BYF' | 'YAT' | 'EMK'>('all');
  const [specificCodes, setSpecificCodes] = useState<string[]>([]);
  const [startDate, setStartDate] = useState('2025-09-29');
  const [endDate, setEndDate] = useState('2025-10-17');
  const [column, setColumn] = useState('price');

  // Scanner management
  const [selectedScanners, setSelectedScanners] = useState<SelectedScanner[]>([]);
  const [showAddScanner, setShowAddScanner] = useState(false);
  const [editingScannerIndex, setEditingScannerIndex] = useState<number | null>(null);
  const [editingScanner, setEditingScanner] = useState<SelectedScanner | null>(null);

  // Threshold
  const [scoreThreshold, setScoreThreshold] = useState(0.0);

  // Filters
  const [includeKeywords, setIncludeKeywords] = useState<string[]>([]);
  const [excludeKeywords, setExcludeKeywords] = useState<string[]>([]);
  const [caseSensitive, setCaseSensitive] = useState(false);
  const [newKeyword, setNewKeyword] = useState('');
  const [newSpecificCode, setNewSpecificCode] = useState('');

  const availableColumns = [
    { value: 'price', label: 'Price' },
    { value: 'market_cap', label: 'Market Cap' },
    { value: 'number_of_investors', label: 'Number of Investors' },
    { value: 'number_of_shares', label: 'Number of Shares' },
  ];

  // Scanner management functions
  const addScanner = (scannerId: string) => {
    const scannerDef = AVAILABLE_SCANNERS.find(s => s.id === scannerId);
    if (!scannerDef) return;

    const newScanner: SelectedScanner = {
      id: scannerId,
      name: scannerDef.name,
      weight: 1.0,
      config: { ...scannerDef.defaultConfig }
    };

    setSelectedScanners([...selectedScanners, newScanner]);
    setShowAddScanner(false);
  };

  const removeScanner = (index: number) => {
    setSelectedScanners(selectedScanners.filter((_, i) => i !== index));
  };

  const updateScannerWeight = (index: number, weight: number) => {
    const updated = [...selectedScanners];
    updated[index].weight = weight;
    setSelectedScanners(updated);
  };

  const startEditScanner = (index: number) => {
    setEditingScannerIndex(index);
    setEditingScanner({ ...selectedScanners[index] });
  };

  const saveEditedScanner = () => {
    if (editingScannerIndex !== null && editingScanner) {
      const updated = [...selectedScanners];
      updated[editingScannerIndex] = editingScanner;
      setSelectedScanners(updated);
      setEditingScannerIndex(null);
      setEditingScanner(null);
    }
  };

  const cancelEditScanner = () => {
    setEditingScannerIndex(null);
    setEditingScanner(null);
  };

  // Fund code management
  const addSpecificCode = () => {
    if (newSpecificCode.trim() === '') return;
    setSpecificCodes([...specificCodes, newSpecificCode.trim().toUpperCase()]);
    setNewSpecificCode('');
  };

  const removeSpecificCode = (index: number) => {
    setSpecificCodes(specificCodes.filter((_, i) => i !== index));
  };

  // Keyword management
  const addKeyword = (type: 'include' | 'exclude') => {
    if (newKeyword.trim() === '') return;
    if (type === 'include') {
      setIncludeKeywords([...includeKeywords, newKeyword.trim()]);
    } else {
      setExcludeKeywords([...excludeKeywords, newKeyword.trim()]);
    }
    setNewKeyword('');
  };

  const removeKeyword = (index: number, type: 'include' | 'exclude') => {
    if (type === 'include') {
      setIncludeKeywords(includeKeywords.filter((_, i) => i !== index));
    } else {
      setExcludeKeywords(excludeKeywords.filter((_, i) => i !== index));
    }
  };

  const handleSubmit = () => {
    if (selectedScanners.length === 0) {
      alert('Please select at least one scanner');
      return;
    }

    // Build scanner configurations
    const scannerConfigs: Record<string, any> = {};
    const weights: Record<string, number> = {};

    selectedScanners.forEach(scanner => {
      scannerConfigs[scanner.id] = scanner.config;
      weights[scanner.id] = scanner.weight;
    });

    const parameters = {
      fund_type: fundType === 'all' ? null : fundType,
      specific_codes: specificCodes.length > 0 ? specificCodes : undefined,
      start_date: startDate,
      end_date: endDate,
      column,
      include_keywords: includeKeywords.length > 0 ? includeKeywords : undefined,
      exclude_keywords: excludeKeywords.length > 0 ? excludeKeywords : undefined,
      case_sensitive: caseSensitive,
      scanners: Object.keys(scannerConfigs),
      scanner_configs: scannerConfigs,
      weights,
      score_threshold: scoreThreshold,
    };

    onRunAnalysis(parameters);
  };

  const totalWeight = selectedScanners.reduce((sum, s) => sum + s.weight, 0);

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        <SearchIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        ETF Scan Analysis Configuration
      </Typography>

      <Grid container spacing={3}>
        {/* Fund Selection */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <SettingsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Fund Selection
              </Typography>

              {/* Fund Type */}
              <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                <InputLabel>Fund Type</InputLabel>
                <Select
                  value={fundType}
                  label="Fund Type"
                  onChange={(e: SelectChangeEvent) => setFundType(e.target.value as any)}
                >
                  <MenuItem value="all">All Funds</MenuItem>
                  <MenuItem value="BYF">BYF - Stock Funds</MenuItem>
                  <MenuItem value="YAT">YAT - Foreign Funds</MenuItem>
                  <MenuItem value="EMK">EMK - Real Estate Funds</MenuItem>
                </Select>
              </FormControl>

              {fundType === 'all' && (
                <Alert severity="info" sx={{ mb: 2 }}>
                  Will scan ALL funds of all types (BYF, YAT, EMK)
                </Alert>
              )}

              {/* Specific Codes */}
              <Typography variant="subtitle2" gutterBottom>
                Or Specify Specific Fund Codes
              </Typography>
              <Box display="flex" gap={1} mb={2}>
                <TextField
                  size="small"
                  fullWidth
                  value={newSpecificCode}
                  onChange={(e) => setNewSpecificCode(e.target.value)}
                  placeholder="Enter fund code (e.g., NNF)"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      addSpecificCode();
                    }
                  }}
                />
                <Button size="small" onClick={addSpecificCode}>
                  Add
                </Button>
              </Box>
              <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: 2 }}>
                {specificCodes.map((code, index) => (
                  <Chip
                    key={index}
                    label={code}
                    onDelete={() => removeSpecificCode(index)}
                    color="primary"
                    variant="outlined"
                  />
                ))}
              </Stack>

              <Divider sx={{ my: 2 }} />

              {/* Date Range */}
              <Typography variant="subtitle2" gutterBottom>
                Analysis Period
              </Typography>
              <Grid container spacing={2} mb={2}>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Start Date"
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                    size="small"
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="End Date"
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                    size="small"
                  />
                </Grid>
              </Grid>

              {/* Column Selection */}
              <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                <InputLabel>Column to Analyze</InputLabel>
                <Select
                  value={column}
                  label="Column to Analyze"
                  onChange={(e: SelectChangeEvent) => setColumn(e.target.value)}
                >
                  {availableColumns.map(col => (
                    <MenuItem key={col.value} value={col.value}>
                      {col.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </CardContent>
          </Card>
        </Grid>

        {/* Scanner Selection */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <InfoIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Select Scanners
              </Typography>

              <Alert severity="info" sx={{ mb: 2 }}>
                Select one or more scanners. Each scanner will be weighted and combined to produce a final score for each fund.
              </Alert>

              {/* Scanners Table */}
              {selectedScanners.length > 0 && (
                <>
                  <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                    Selected Scanners ({selectedScanners.length})
                  </Typography>
                  <TableContainer component={Paper} sx={{ mb: 2 }}>
                    <Table size="small">
                      <TableHead>
                        <TableRow sx={{ bgcolor: 'primary.light' }}>
                          <TableCell>Scanner</TableCell>
                          <TableCell align="right">Weight</TableCell>
                          <TableCell align="right">%</TableCell>
                          <TableCell align="center">Actions</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {selectedScanners.map((scanner, index) => (
                          <TableRow key={index}>
                            <TableCell>{scanner.name}</TableCell>
                            <TableCell align="right">{scanner.weight.toFixed(2)}</TableCell>
                            <TableCell align="right">
                              {((scanner.weight / totalWeight) * 100).toFixed(1)}%
                            </TableCell>
                            <TableCell align="center">
                              <Tooltip title="Edit Scanner">
                                <IconButton
                                  size="small"
                                  onClick={() => startEditScanner(index)}
                                  color="primary"
                                >
                                  <EditIcon />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Remove Scanner">
                                <IconButton
                                  size="small"
                                  onClick={() => removeScanner(index)}
                                  color="error"
                                >
                                  <DeleteIcon />
                                </IconButton>
                              </Tooltip>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </>
              )}

              {/* Add Scanner Button */}
              <Button
                fullWidth
                variant="outlined"
                startIcon={<AddIcon />}
                onClick={() => setShowAddScanner(true)}
                sx={{ mb: 2 }}
              >
                Add Scanner
              </Button>

              {selectedScanners.length === 0 && (
                <Alert severity="warning">
                  Please select at least one scanner to run the analysis
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Filters */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Filters (Optional)
              </Typography>

              {/* Include Keywords */}
              <Typography variant="subtitle2" gutterBottom>
                Include Keywords
              </Typography>
              <Box display="flex" gap={1} mb={1}>
                <TextField
                  size="small"
                  fullWidth
                  value={newKeyword}
                  onChange={(e) => setNewKeyword(e.target.value)}
                  placeholder="Enter keyword"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      addKeyword('include');
                    }
                  }}
                />
                <Button size="small" onClick={() => addKeyword('include')}>
                  Add
                </Button>
              </Box>
              <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: 2 }}>
                {includeKeywords.map((kw, index) => (
                  <Chip
                    key={index}
                    label={kw}
                    onDelete={() => removeKeyword(index, 'include')}
                    color="primary"
                  />
                ))}
              </Stack>

              {/* Exclude Keywords */}
              <Typography variant="subtitle2" gutterBottom>
                Exclude Keywords
              </Typography>
              <Box display="flex" gap={1} mb={1}>
                <TextField
                  size="small"
                  fullWidth
                  value={newKeyword}
                  onChange={(e) => setNewKeyword(e.target.value)}
                  placeholder="Enter keyword"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      addKeyword('exclude');
                    }
                  }}
                />
                <Button size="small" onClick={() => addKeyword('exclude')}>
                  Add
                </Button>
              </Box>
              <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: 2 }}>
                {excludeKeywords.map((kw, index) => (
                  <Chip
                    key={index}
                    label={kw}
                    onDelete={() => removeKeyword(index, 'exclude')}
                    color="error"
                  />
                ))}
              </Stack>

              <Divider sx={{ my: 2 }} />

              {/* Case Sensitivity */}
              <FormControl fullWidth size="small">
                <InputLabel>Keyword Matching</InputLabel>
                <Select
                  value={caseSensitive ? 'case' : 'nocase'}
                  label="Keyword Matching"
                  onChange={(e: SelectChangeEvent) => setCaseSensitive(e.target.value === 'case')}
                >
                  <MenuItem value="nocase">Case Insensitive</MenuItem>
                  <MenuItem value="case">Case Sensitive</MenuItem>
                </Select>
              </FormControl>
            </CardContent>
          </Card>
        </Grid>

        {/* Threshold */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Results Filter
              </Typography>

              <Typography variant="subtitle2" gutterBottom>
                Score Threshold
              </Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                Only show funds with a score greater than or equal to this threshold
              </Typography>

              <Box sx={{ px: 2 }}>
                <Slider
                  value={scoreThreshold}
                  onChange={(e, value) => setScoreThreshold(value as number)}
                  min={-5}
                  max={5}
                  step={0.1}
                  marks={[
                    { value: -5, label: '-5' },
                    { value: 0, label: '0' },
                    { value: 5, label: '5' },
                  ]}
                  valueLabelDisplay="auto"
                  valueLabelFormat={(value) => value.toFixed(1)}
                />
              </Box>

              <Alert severity="info" sx={{ mt: 2 }}>
                Current Threshold: <strong>{scoreThreshold.toFixed(2)}</strong>
              </Alert>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Run Button */}
      <Box display="flex" justifyContent="flex-end" mt={3} gap={2}>
        <Button
          variant="contained"
          disabled={running || selectedScanners.length === 0}
          startIcon={running ? <CircularProgress size={20} /> : <PlayIcon />}
          onClick={handleSubmit}
          size="large"
        >
          {running ? 'Running Scan...' : 'Run ETF Scan Analysis'}
        </Button>
      </Box>

      {/* Add Scanner Dialog */}
      <Dialog open={showAddScanner} onClose={() => setShowAddScanner(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Select Scanner to Add</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 2 }}>
            {AVAILABLE_SCANNERS.map(scanner => (
              <Paper
                key={scanner.id}
                onClick={() => {
                  addScanner(scanner.id);
                  setShowAddScanner(false);
                }}
                sx={{
                  p: 2,
                  cursor: 'pointer',
                  '&:hover': { bgcolor: 'action.hover', boxShadow: 2 },
                  transition: 'all 0.2s',
                }}
              >
                <Typography variant="subtitle1">{scanner.name}</Typography>
                <Typography variant="body2" color="textSecondary">
                  {scanner.description}
                </Typography>
              </Paper>
            ))}
          </Stack>
        </DialogContent>
      </Dialog>

      {/* Edit Scanner Dialog */}
      <Dialog open={editingScannerIndex !== null} onClose={cancelEditScanner} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Scanner: {editingScanner?.name}</DialogTitle>
        <DialogContent>
          {editingScanner && (
            <Stack spacing={2} sx={{ mt: 2 }}>
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Weight
                </Typography>
                <TextField
                  fullWidth
                  size="small"
                  type="number"
                  inputProps={{ step: 0.1, min: 0 }}
                  value={editingScanner.weight}
                  onChange={(e) =>
                    setEditingScanner({
                      ...editingScanner,
                      weight: parseFloat(e.target.value) || 0,
                    })
                  }
                />
              </Box>

              {editingScanner.id === 'ema_cross' && editingScanner.config && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    EMA Periods
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <TextField
                        fullWidth
                        size="small"
                        label="Short"
                        type="number"
                        value={editingScanner.config.short}
                        onChange={(e) =>
                          setEditingScanner({
                            ...editingScanner,
                            config: {
                              ...editingScanner.config,
                              short: parseInt(e.target.value) || 20,
                            },
                          })
                        }
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <TextField
                        fullWidth
                        size="small"
                        label="Long"
                        type="number"
                        value={editingScanner.config.long}
                        onChange={(e) =>
                          setEditingScanner({
                            ...editingScanner,
                            config: {
                              ...editingScanner.config,
                              long: parseInt(e.target.value) || 50,
                            },
                          })
                        }
                      />
                    </Grid>
                  </Grid>
                </Box>
              )}

              {editingScanner.id === 'macd' && editingScanner.config && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    MACD Parameters
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={4}>
                      <TextField
                        fullWidth
                        size="small"
                        label="Slow"
                        type="number"
                        value={editingScanner.config.slow}
                        onChange={(e) =>
                          setEditingScanner({
                            ...editingScanner,
                            config: {
                              ...editingScanner.config,
                              slow: parseInt(e.target.value) || 26,
                            },
                          })
                        }
                      />
                    </Grid>
                    <Grid item xs={4}>
                      <TextField
                        fullWidth
                        size="small"
                        label="Fast"
                        type="number"
                        value={editingScanner.config.fast}
                        onChange={(e) =>
                          setEditingScanner({
                            ...editingScanner,
                            config: {
                              ...editingScanner.config,
                              fast: parseInt(e.target.value) || 12,
                            },
                          })
                        }
                      />
                    </Grid>
                    <Grid item xs={4}>
                      <TextField
                        fullWidth
                        size="small"
                        label="Signal"
                        type="number"
                        value={editingScanner.config.signal}
                        onChange={(e) =>
                          setEditingScanner({
                            ...editingScanner,
                            config: {
                              ...editingScanner.config,
                              signal: parseInt(e.target.value) || 9,
                            },
                          })
                        }
                      />
                    </Grid>
                  </Grid>
                </Box>
              )}

              {editingScanner.id === 'rsi' && editingScanner.config && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    RSI Parameters
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        size="small"
                        label="Window"
                        type="number"
                        value={editingScanner.config.window}
                        onChange={(e) =>
                          setEditingScanner({
                            ...editingScanner,
                            config: {
                              ...editingScanner.config,
                              window: parseInt(e.target.value) || 14,
                            },
                          })
                        }
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <TextField
                        fullWidth
                        size="small"
                        label="Lower Threshold"
                        type="number"
                        value={editingScanner.config.lower}
                        onChange={(e) =>
                          setEditingScanner({
                            ...editingScanner,
                            config: {
                              ...editingScanner.config,
                              lower: parseFloat(e.target.value) || 30,
                            },
                          })
                        }
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <TextField
                        fullWidth
                        size="small"
                        label="Upper Threshold"
                        type="number"
                        value={editingScanner.config.upper}
                        onChange={(e) =>
                          setEditingScanner({
                            ...editingScanner,
                            config: {
                              ...editingScanner.config,
                              upper: parseFloat(e.target.value) || 70,
                            },
                          })
                        }
                      />
                    </Grid>
                  </Grid>
                </Box>
              )}

              {editingScanner.id === 'supertrend' && editingScanner.config && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Supertrend Parameters
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <TextField
                        fullWidth
                        size="small"
                        label="HL Factor"
                        type="number"
                        inputProps={{ step: 0.01 }}
                        value={editingScanner.config.hl_factor}
                        onChange={(e) =>
                          setEditingScanner({
                            ...editingScanner,
                            config: {
                              ...editingScanner.config,
                              hl_factor: parseFloat(e.target.value) || 0.05,
                            },
                          })
                        }
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <TextField
                        fullWidth
                        size="small"
                        label="ATR Period"
                        type="number"
                        value={editingScanner.config.atr_period}
                        onChange={(e) =>
                          setEditingScanner({
                            ...editingScanner,
                            config: {
                              ...editingScanner.config,
                              atr_period: parseInt(e.target.value) || 10,
                            },
                          })
                        }
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        size="small"
                        label="Multiplier"
                        type="number"
                        inputProps={{ step: 0.1 }}
                        value={editingScanner.config.multiplier}
                        onChange={(e) =>
                          setEditingScanner({
                            ...editingScanner,
                            config: {
                              ...editingScanner.config,
                              multiplier: parseFloat(e.target.value) || 3.0,
                            },
                          })
                        }
                      />
                    </Grid>
                  </Grid>
                </Box>
              )}
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={cancelEditScanner}>Cancel</Button>
          <Button onClick={saveEditedScanner} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
