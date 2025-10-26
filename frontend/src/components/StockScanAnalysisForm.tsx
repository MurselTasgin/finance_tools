// finance_tools/frontend/src/components/StockScanAnalysisForm.tsx
import React, { useState, useEffect } from 'react';
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
  Chip,
  Dialog,
  Tooltip,
  DialogTitle,
  DialogContent,
  DialogActions,
  Slider,
  ListItemText,
  ListItem,
  List,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  Settings as SettingsIcon,
  PlayArrow as PlayIcon,
  Group as GroupIcon,
  Save as SaveIcon,
  Analytics as AssessmentIcon,
  Edit as EditIcon,
} from '@mui/icons-material';
import { CircularProgress } from '@mui/material';
import { stockApi } from '../services/api';

interface SelectedScanner {
  id: string;
  name: string;
  weight: number;
  config?: Record<string, any>;
}

interface StockGroup {
  id: number;
  name: string;
  description: string;
  symbols: string[];
}

interface StockScanAnalysisFormProps {
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
  {
    id: 'volume',
    name: 'Volume Analysis',
    description: 'On-Balance Volume and Volume SMA',
    defaultConfig: { window: 20 }
  },
  {
    id: 'stochastic',
    name: 'Stochastic',
    description: 'Stochastic Oscillator',
    defaultConfig: { k_period: 14, d_period: 3 }
  },
  {
    id: 'atr',
    name: 'ATR',
    description: 'Average True Range (Volatility)',
    defaultConfig: { window: 14 }
  },
  {
    id: 'adx',
    name: 'ADX',
    description: 'Average Directional Index (Trend Strength)',
    defaultConfig: { window: 14 }
  },
];

export const StockScanAnalysisForm: React.FC<StockScanAnalysisFormProps> = ({
  onRunAnalysis,
  running,
}) => {
  // Basic parameters
  const [specificSymbols, setSpecificSymbols] = useState<string[]>([]);
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
  const [startDate, setStartDate] = useState('2024-01-01');
  const [endDate, setEndDate] = useState('2024-12-31');
  const [column, setColumn] = useState('close');
  const [sector, setSector] = useState('');
  const [editingScannerIndex, setEditingScannerIndex] = useState<number | null>(null);
  const [editingScanner, setEditingScanner] = useState<SelectedScanner | null>(null);
  const [industry, setIndustry] = useState('');

  // Scanner management
  const [selectedScanners, setSelectedScanners] = useState<SelectedScanner[]>([]);
  const [showAddScanner, setShowAddScanner] = useState(false);

  // Threshold
  const [scoreThreshold] = useState(0.0);

  // Stock management
  const [newSymbol, setNewSymbol] = useState('');
  const [stockGroups, setStockGroups] = useState<StockGroup[]>([]);
  const [newGroupName, setNewGroupName] = useState('');
  const [newGroupDescription, setNewGroupDescription] = useState('');
  const [showGroupDialog, setShowGroupDialog] = useState(false);

  const availableColumns = [
    { value: 'close', label: 'Close Price' },
    { value: 'open', label: 'Open Price' },
    { value: 'high', label: 'High Price' },
    { value: 'low', label: 'Low Price' },
  ];

  // Load stock groups on mount
  useEffect(() => {
    loadStockGroups();
  }, []);

  const loadStockGroups = async () => {
    try {
      const response = await stockApi.getGroups();
      setStockGroups(response.groups || []);
    } catch (err) {
      console.error('Failed to load stock groups:', err);
    }
  };

  const handleGroupSelect = (groupId: number | null) => {
    setSelectedGroupId(groupId);
    if (groupId !== null) {
      const group = stockGroups.find(g => g.id === groupId);
      if (group) {
        setSpecificSymbols(group.symbols);
      }
    }
  };

  const createStockGroup = async () => {
    if (!newGroupName.trim() || specificSymbols.length === 0) {
      alert('Please provide a group name and add at least one stock');
      return;
    }

    try {
      const response = await stockApi.createGroup(newGroupName, newGroupDescription, specificSymbols);
      setStockGroups([...stockGroups, response]);
      setShowGroupDialog(false);
      setNewGroupName('');
      setNewGroupDescription('');
    } catch (err) {
      console.error('Failed to create stock group:', err);
      alert('Failed to create stock group');
    }
  };

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

  const openConfigDialog = (index: number) => {
    if (index >= 0 && index < selectedScanners.length) {
      setEditingScannerIndex(index);
      setEditingScanner({ ...selectedScanners[index] });
    }
  };

  const saveConfigChanges = () => {
    if (editingScannerIndex !== null && editingScanner && editingScannerIndex >= 0 && editingScannerIndex < selectedScanners.length) {
      const updated = [...selectedScanners];
      updated[editingScannerIndex] = editingScanner;
      setSelectedScanners(updated);
    }
    setEditingScannerIndex(null);
    setEditingScanner(null);
  };

  // Symbol management
  const addSymbol = () => {
    if (newSymbol.trim() === '') return;
    setSpecificSymbols([...specificSymbols, newSymbol.trim().toUpperCase()]);
    setNewSymbol('');
  };

  const removeSymbol = (index: number) => {
    setSpecificSymbols(specificSymbols.filter((_, i) => i !== index));
  };

  const handleSubmit = () => {
    if (selectedScanners.length === 0) {
      alert('Please select at least one scanner');
      return;
    }

    if (specificSymbols.length === 0) {
      alert('Please add at least one stock symbol');
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
      symbols: specificSymbols,
      start_date: startDate,
      end_date: endDate,
      column,
      sector: sector || undefined,
      industry: industry || undefined,
      scanners: Object.keys(scannerConfigs),
      scanner_configs: scannerConfigs,
      weights,
      score_threshold: scoreThreshold,
    };

    onRunAnalysis(parameters);
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        <SearchIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        Stock Scan Analysis Configuration
      </Typography>

      <Grid container spacing={3}>
        {/* Stock Selection */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <SettingsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Stock Selection
              </Typography>

              {/* Stock Groups */}
              <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                <InputLabel>Select Stock Group</InputLabel>
                <Select
                  value={selectedGroupId ? String(selectedGroupId) : ''}
                  label="Select Stock Group"
                  onChange={(e: SelectChangeEvent) => handleGroupSelect(e.target.value ? Number(e.target.value) : null)}
                >
                  <MenuItem value="">
                    <em>None (Manual Entry)</em>
                  </MenuItem>
                  {stockGroups.map(group => (
                    <MenuItem key={group.id} value={group.id}>
                      {group.name} ({group.symbols.length} stocks)
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {selectedGroupId && (
                <Button
                  size="small"
                  startIcon={<DeleteIcon />}
                  onClick={() => handleGroupSelect(null)}
                  sx={{ mb: 2 }}
                >
                  Clear Selection
                </Button>
              )}

              <Divider sx={{ my: 2 }} />

              {/* Individual Symbols */}
              <Typography variant="subtitle2" gutterBottom>
                Add Individual Stock Symbols
              </Typography>
              <Box display="flex" gap={1} mb={2}>
                <TextField
                  size="small"
                  fullWidth
                  value={newSymbol}
                  onChange={(e) => setNewSymbol(e.target.value)}
                  placeholder="Enter stock symbol (e.g., AAPL)"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      addSymbol();
                    }
                  }}
                />
                <Button size="small" onClick={addSymbol}>
                  Add
                </Button>
              </Box>

              {/* Symbol List */}
              {specificSymbols.length > 0 && (
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Selected Stocks ({specificSymbols.length}):
                  </Typography>
                  <Box display="flex" flexWrap="wrap" gap={0.5} mt={1}>
                    {specificSymbols.map((symbol, index) => (
                      <Chip
                        key={index}
                        label={symbol}
                        size="small"
                        onDelete={() => removeSymbol(index)}
                        sx={{ mr: 0.5 }}
                      />
                    ))}
                  </Box>
                </Box>
              )}

              <Divider sx={{ my: 2 }} />

              {/* Save as Group Button */}
              {specificSymbols.length > 0 && (
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<GroupIcon />}
                  onClick={() => setShowGroupDialog(true)}
                >
                  Save as Stock Group
                </Button>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Date & Column Selection */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <SettingsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Analysis Parameters
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    type="date"
                    label="Start Date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    size="small"
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    type="date"
                    label="End Date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    size="small"
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Analysis Column</InputLabel>
                    <Select value={column} label="Analysis Column" onChange={(e) => setColumn(e.target.value)}>
                      {availableColumns.map(col => (
                        <MenuItem key={col.value} value={col.value}>{col.label}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    size="small"
                    label="Sector (Optional)"
                    value={sector}
                    onChange={(e) => setSector(e.target.value)}
                    placeholder="e.g., Technology"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    size="small"
                    label="Industry (Optional)"
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                    placeholder="e.g., Software"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Selected Scanners */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">
                  <AssessmentIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Selected Scanners ({selectedScanners.length})
                </Typography>
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={<AddIcon />}
                  onClick={() => setShowAddScanner(true)}
                >
                  Add Scanner
                </Button>
              </Box>

              {selectedScanners.length === 0 && (
                <Alert severity="info">
                  No scanners selected. Click "Add Scanner" to add indicators.
                </Alert>
              )}

              {selectedScanners.length > 0 && (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Scanner</TableCell>
                        <TableCell>Weight</TableCell>
                        <TableCell>Configuration</TableCell>
                        <TableCell align="right">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {selectedScanners.map((scanner, index) => (
                        <TableRow key={index}>
                          <TableCell>
                            <Typography variant="body2" fontWeight="bold">
                              {scanner.name}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Slider
                              value={scanner.weight}
                              onChange={(e, value) => updateScannerWeight(index, value as number)}
                              min={0}
                              max={5}
                              step={0.1}
                              marks={[
                                { value: 0, label: '0' },
                                { value: 2.5, label: '2.5' },
                                { value: 5, label: '5' }
                              ]}
                              sx={{ width: 150 }}
                            />
                            <Typography variant="caption">{scanner.weight.toFixed(1)}</Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="caption" color="text.secondary">
                              {JSON.stringify(scanner.config)}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Tooltip title="Edit Configuration">
                              <IconButton size="small" onClick={() => openConfigDialog(index)}>
                                <EditIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Remove Scanner">
                              <IconButton size="small" onClick={() => removeScanner(index)}>
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Add Scanner Dialog */}
      <Dialog open={showAddScanner} onClose={() => setShowAddScanner(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Select Scanner to Add</DialogTitle>
        <DialogContent>
          <List>
            {AVAILABLE_SCANNERS.filter(s => !selectedScanners.find(selected => selected.id === s.id)).map(scanner => (
              <ListItem
                key={scanner.id}
                button
                onClick={() => {
                  addScanner(scanner.id);
                }}
              >
                <ListItemText
                  primary={scanner.name}
                  secondary={scanner.description}
                />
              </ListItem>
            ))}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowAddScanner(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>

      {/* Save Stock Group Dialog */}
      <Dialog open={showGroupDialog} onClose={() => setShowGroupDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Save Stock Group</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Group Name"
              fullWidth
              value={newGroupName}
              onChange={(e) => setNewGroupName(e.target.value)}
              required
            />
            <TextField
              label="Description (Optional)"
              fullWidth
              multiline
              rows={3}
              value={newGroupDescription}
              onChange={(e) => setNewGroupDescription(e.target.value)}
            />
            <Typography variant="body2" color="text.secondary">
              {specificSymbols.length} stocks will be saved: {specificSymbols.join(', ')}
            </Typography>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowGroupDialog(false)}>Cancel</Button>
          <Button onClick={createStockGroup} variant="contained" startIcon={<SaveIcon />}>
            Save Group
          </Button>
        </DialogActions>
      </Dialog>

      {/* Scanner Configuration Dialog */}
      <Dialog open={editingScanner !== null} onClose={() => { setEditingScanner(null); setEditingScannerIndex(null); }} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Scanner Configuration</DialogTitle>
        <DialogContent>
          {editingScanner && (
            <Stack spacing={2} sx={{ mt: 2 }}>
              <Typography variant="h6">{editingScanner.name}</Typography>
              {editingScanner.id === 'ema_cross' && (
                <>
                  <TextField
                    label="Short EMA Period"
                    type="number"
                    value={editingScanner.config?.short || 20}
                    onChange={(e) => setEditingScanner({ ...editingScanner, config: { ...editingScanner.config, short: parseInt(e.target.value) || 20 } })}
                    fullWidth
                  />
                  <TextField
                    label="Long EMA Period"
                    type="number"
                    value={editingScanner.config?.long || 50}
                    onChange={(e) => setEditingScanner({ ...editingScanner, config: { ...editingScanner.config, long: parseInt(e.target.value) || 50 } })}
                    fullWidth
                  />
                </>
              )}
              {editingScanner.id === 'macd' && (
                <>
                  <TextField
                    label="Fast Period"
                    type="number"
                    value={editingScanner.config?.fast || 12}
                    onChange={(e) => setEditingScanner({ ...editingScanner, config: { ...editingScanner.config, fast: parseInt(e.target.value) || 12 } })}
                    fullWidth
                  />
                  <TextField
                    label="Slow Period"
                    type="number"
                    value={editingScanner.config?.slow || 26}
                    onChange={(e) => setEditingScanner({ ...editingScanner, config: { ...editingScanner.config, slow: parseInt(e.target.value) || 26 } })}
                    fullWidth
                  />
                  <TextField
                    label="Signal Period"
                    type="number"
                    value={editingScanner.config?.signal || 9}
                    onChange={(e) => setEditingScanner({ ...editingScanner, config: { ...editingScanner.config, signal: parseInt(e.target.value) || 9 } })}
                    fullWidth
                  />
                </>
              )}
              {editingScanner.id === 'rsi' && (
                <>
                  <TextField
                    label="RSI Period"
                    type="number"
                    value={editingScanner.config?.window || 14}
                    onChange={(e) => setEditingScanner({ ...editingScanner, config: { ...editingScanner.config, window: parseInt(e.target.value) || 14 } })}
                    fullWidth
                  />
                  <TextField
                    label="Lower Threshold"
                    type="number"
                    value={editingScanner.config?.lower || 30}
                    onChange={(e) => setEditingScanner({ ...editingScanner, config: { ...editingScanner.config, lower: parseFloat(e.target.value) || 30 } })}
                    fullWidth
                  />
                  <TextField
                    label="Upper Threshold"
                    type="number"
                    value={editingScanner.config?.upper || 70}
                    onChange={(e) => setEditingScanner({ ...editingScanner, config: { ...editingScanner.config, upper: parseFloat(e.target.value) || 70 } })}
                    fullWidth
                  />
                </>
              )}
              {editingScanner.id === 'volume' && (
                <TextField
                  label="Volume SMA Period"
                  type="number"
                  value={editingScanner.config?.window || 20}
                  onChange={(e) => setEditingScanner({ ...editingScanner, config: { ...editingScanner.config, window: parseInt(e.target.value) || 20 } })}
                  fullWidth
                />
              )}
              {editingScanner.id === 'stochastic' && (
                <>
                  <TextField
                    label="K Period"
                    type="number"
                    value={editingScanner.config?.k_period || 14}
                    onChange={(e) => setEditingScanner({ ...editingScanner, config: { ...editingScanner.config, k_period: parseInt(e.target.value) || 14 } })}
                    fullWidth
                  />
                  <TextField
                    label="D Period"
                    type="number"
                    value={editingScanner.config?.d_period || 3}
                    onChange={(e) => setEditingScanner({ ...editingScanner, config: { ...editingScanner.config, d_period: parseInt(e.target.value) || 3 } })}
                    fullWidth
                  />
                </>
              )}
              {editingScanner.id === 'atr' && (
                <TextField
                  label="ATR Period"
                  type="number"
                  value={editingScanner.config?.window || 14}
                  onChange={(e) => setEditingScanner({ ...editingScanner, config: { ...editingScanner.config, window: parseInt(e.target.value) || 14 } })}
                  fullWidth
                />
              )}
              {editingScanner.id === 'adx' && (
                <TextField
                  label="ADX Period"
                  type="number"
                  value={editingScanner.config?.window || 14}
                  onChange={(e) => setEditingScanner({ ...editingScanner, config: { ...editingScanner.config, window: parseInt(e.target.value) || 14 } })}
                  fullWidth
                />
              )}
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setEditingScanner(null); setEditingScannerIndex(null); }}>Cancel</Button>
          <Button onClick={saveConfigChanges} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>

      {/* Run Analysis Button */}
      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          size="large"
          onClick={handleSubmit}
          disabled={running || selectedScanners.length === 0 || specificSymbols.length === 0}
          startIcon={running ? <CircularProgress size={20} /> : <PlayIcon />}
        >
          {running ? 'Running Analysis...' : 'Run Stock Scan Analysis'}
        </Button>
      </Box>
    </Box>
  );
};

