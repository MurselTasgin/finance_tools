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
  DialogTitle,
  DialogContent,
  DialogActions,
  ListItemText,
  ListItem,
  List,
  Slider,
  Tooltip,
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

interface Indicator {
  id: string;
  name: string;
  description: string;
  required_columns: string[];
  parameter_schema: Record<string, any>;
  capabilities: string[];
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
  initialParameters?: any;
  onParametersUsed?: () => void;
}

export const StockScanAnalysisForm: React.FC<StockScanAnalysisFormProps> = ({
  onRunAnalysis,
  running,
  initialParameters,
  onParametersUsed,
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
  const [availableIndicators, setAvailableIndicators] = useState<Indicator[]>([]);

  // Thresholds for BUY/SELL recommendations
  const [buyThreshold, setBuyThreshold] = useState(1.0);
  const [sellThreshold, setSellThreshold] = useState(1.0);

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

  // Load indicators and stock groups on mount
  useEffect(() => {
    loadIndicators();
    loadStockGroups();
  }, []);

  // Populate form when initialParameters is provided (e.g., from rerun)
  useEffect(() => {
    if (initialParameters && onParametersUsed) {
      // Only populate if indicators are loaded (needed for scanner reconstruction)
      const needsIndicators = initialParameters.scanner_configs && Object.keys(initialParameters.scanner_configs).length > 0;
      
      if (needsIndicators && availableIndicators.length === 0) {
        // Wait for indicators to load
        return;
      }
      
      // Populate form fields from initial parameters
      if (initialParameters.symbols) {
        setSpecificSymbols(initialParameters.symbols);
      }
      if (initialParameters.start_date) {
        setStartDate(initialParameters.start_date);
      }
      if (initialParameters.end_date) {
        setEndDate(initialParameters.end_date);
      }
      if (initialParameters.column) {
        setColumn(initialParameters.column);
      }
      if (initialParameters.sector) {
        setSector(initialParameters.sector);
      }
      if (initialParameters.industry) {
        setIndustry(initialParameters.industry);
      }
      if (initialParameters.buy_threshold !== undefined) {
        setBuyThreshold(initialParameters.buy_threshold);
      }
      if (initialParameters.sell_threshold !== undefined) {
        setSellThreshold(initialParameters.sell_threshold);
      }

      // Reconstruct selected scanners from scanner_configs and weights
      if (initialParameters.scanner_configs && initialParameters.weights) {
        const reconstructedScanners: SelectedScanner[] = [];
        
        Object.entries(initialParameters.scanner_configs).forEach(([scannerId, config]: [string, any]) => {
          const indicator = availableIndicators.find(i => i.id === scannerId);
          if (indicator) {
            reconstructedScanners.push({
              id: scannerId,
              name: indicator.name,
              weight: initialParameters.weights[scannerId] || 1.0,
              config: config,
            });
          } else {
            console.warn(`Could not find indicator with id: ${scannerId}`);
          }
        });
        
        console.log('Reconstructed scanners:', reconstructedScanners);
        setSelectedScanners(reconstructedScanners);
      }

      // Call onParametersUsed to clear the initial parameters
      onParametersUsed();
    }
  }, [initialParameters, onParametersUsed, availableIndicators]);

  const loadIndicators = async () => {
    try {
      const response = await stockApi.getIndicators();
      setAvailableIndicators(response.indicators || []);
    } catch (err) {
      console.error('Failed to load indicators:', err);
    }
  };

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
    const indicator = availableIndicators.find(s => s.id === scannerId);
    if (!indicator) return;

    // Build default config from parameter schema
    const defaultConfig: Record<string, any> = {};
    Object.entries(indicator.parameter_schema).forEach(([key, schema]: [string, any]) => {
      if (schema.default !== undefined) {
        defaultConfig[key] = schema.default;
      }
    });

    const newScanner: SelectedScanner = {
      id: scannerId,
      name: indicator.name,
      weight: 1.0,
      config: defaultConfig,
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
      buy_threshold: buyThreshold,
      sell_threshold: sellThreshold,
    };

    onRunAnalysis(parameters);
  };

  // Dynamic configuration form renderer
  const renderConfigForm = (scanner: SelectedScanner) => {
    const indicator = availableIndicators.find(i => i.id === scanner.id);
    if (!indicator) return null;

    return (
      <Stack spacing={2} sx={{ mt: 2 }}>
        <Typography variant="h6">{indicator.name}</Typography>
        {Object.entries(indicator.parameter_schema).map(([key, schema]: [string, any]) => {
          const value = editingScanner?.config?.[key] ?? schema.default;
          
          if (schema.type === 'integer') {
            return (
              <TextField
                key={key}
                label={schema.description || key}
                type="number"
                value={value}
                onChange={(e) => {
                  const numValue = parseInt(e.target.value) || schema.default;
                  setEditingScanner({
                    ...editingScanner!,
                    config: { ...editingScanner!.config, [key]: numValue },
                  });
                }}
                fullWidth
                inputProps={{ min: schema.min, max: schema.max }}
              />
            );
          } else if (schema.type === 'float') {
            return (
              <TextField
                key={key}
                label={schema.description || key}
                type="number"
                value={value}
                onChange={(e) => {
                  const numValue = parseFloat(e.target.value) || schema.default;
                  setEditingScanner({
                    ...editingScanner!,
                    config: { ...editingScanner!.config, [key]: numValue },
                  });
                }}
                fullWidth
                inputProps={{ min: schema.min, max: schema.max, step: '0.1' }}
              />
            );
          } else if (schema.type === 'array' && schema.items?.type === 'integer') {
            return (
              <TextField
                key={key}
                label={schema.description || key}
                value={JSON.stringify(value)}
                onChange={(e) => {
                  try {
                    const parsed = JSON.parse(e.target.value);
                    setEditingScanner({
                      ...editingScanner!,
                      config: { ...editingScanner!.config, [key]: parsed },
                    });
                  } catch {
                    // Invalid JSON, ignore
                  }
                }}
                fullWidth
                helperText="Enter as JSON array, e.g., [30, 60, 90]"
              />
            );
          }
          
          return (
            <TextField
              key={key}
              label={schema.description || key}
              value={value}
              onChange={(e) => {
                setEditingScanner({
                  ...editingScanner!,
                  config: { ...editingScanner!.config, [key]: e.target.value },
                });
              }}
              fullWidth
            />
          );
        })}
      </Stack>
    );
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

                {/* Recommendation Thresholds */}
                <Grid item xs={12}>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="subtitle2" gutterBottom sx={{ mb: 2 }}>
                    Recommendation Thresholds
                  </Typography>
                </Grid>

                {/* Buy Threshold */}
                <Grid item xs={12}>
                  <Box sx={{ px: 1 }}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                      <Tooltip title="Minimum score required for a BUY recommendation. Scores above this threshold indicate bullish signals." arrow>
                        <Typography variant="body2" color="text.secondary">
                          BUY Threshold (Score ≥ this value)
                        </Typography>
                      </Tooltip>
                      <TextField
                        type="number"
                        size="small"
                        value={buyThreshold}
                        onChange={(e) => setBuyThreshold(Number(e.target.value))}
                        inputProps={{ min: 0, max: 5, step: 0.1, style: { textAlign: 'right' } }}
                        sx={{ width: '100px' }}
                      />
                    </Box>
                    <Slider
                      value={buyThreshold}
                      onChange={(_, value) => setBuyThreshold(value as number)}
                      min={0}
                      max={5}
                      step={0.1}
                      marks={[
                        { value: 0, label: '0' },
                        { value: 0.5, label: '0.5' },
                        { value: 1, label: '1.0' },
                        { value: 2, label: '2.0' },
                        { value: 3, label: '3.0' },
                        { value: 5, label: '5.0' }
                      ]}
                      valueLabelDisplay="auto"
                      sx={{
                        '& .MuiSlider-markLabel': { fontSize: '0.7rem' },
                        '& .MuiSlider-thumb': { bgcolor: 'success.main' },
                        '& .MuiSlider-track': { bgcolor: 'success.main' },
                        '& .MuiSlider-rail': { bgcolor: 'grey.300' }
                      }}
                    />
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                      Higher values = more conservative (fewer BUY signals)
                    </Typography>
                  </Box>
                </Grid>

                {/* Sell Threshold */}
                <Grid item xs={12}>
                  <Box sx={{ px: 1 }}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                      <Tooltip title="Minimum absolute score required for a SELL recommendation. Scores below negative this value indicate bearish signals." arrow>
                        <Typography variant="body2" color="text.secondary">
                          SELL Threshold (Score ≤ -this value)
                        </Typography>
                      </Tooltip>
                      <TextField
                        type="number"
                        size="small"
                        value={sellThreshold}
                        onChange={(e) => setSellThreshold(Number(e.target.value))}
                        inputProps={{ min: 0, max: 5, step: 0.1, style: { textAlign: 'right' } }}
                        sx={{ width: '100px' }}
                      />
                    </Box>
                    <Slider
                      value={sellThreshold}
                      onChange={(_, value) => setSellThreshold(value as number)}
                      min={0}
                      max={5}
                      step={0.1}
                      marks={[
                        { value: 0, label: '0' },
                        { value: 0.5, label: '0.5' },
                        { value: 1, label: '1.0' },
                        { value: 2, label: '2.0' },
                        { value: 3, label: '3.0' },
                        { value: 5, label: '5.0' }
                      ]}
                      valueLabelDisplay="auto"
                      sx={{
                        '& .MuiSlider-markLabel': { fontSize: '0.7rem' },
                        '& .MuiSlider-thumb': { bgcolor: 'error.main' },
                        '& .MuiSlider-track': { bgcolor: 'error.main' },
                        '& .MuiSlider-rail': { bgcolor: 'grey.300' }
                      }}
                    />
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                      Higher values = more conservative (fewer SELL signals)
                    </Typography>
                  </Box>
                </Grid>

                {/* Threshold Explanation */}
                <Grid item xs={12}>
                  <Box sx={{ p: 1.5, bgcolor: 'info.lighter', borderRadius: 1, border: '1px solid', borderColor: 'info.light' }}>
                    <Typography variant="caption" color="text.secondary">
                      <strong>How it works:</strong><br />
                      • <strong style={{ color: '#2e7d32' }}>BUY</strong>: Score ≥ {buyThreshold.toFixed(1)} (bullish signals dominate)<br />
                      • <strong style={{ color: '#757575' }}>HOLD</strong>: Score between -{sellThreshold.toFixed(1)} and {buyThreshold.toFixed(1)} (neutral)<br />
                      • <strong style={{ color: '#d32f2f' }}>SELL</strong>: Score ≤ -{sellThreshold.toFixed(1)} (bearish signals dominate)
                    </Typography>
                  </Box>
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
            {availableIndicators.filter(s => !selectedScanners.find(selected => selected.id === s.id)).map(indicator => (
              <ListItem
                key={indicator.id}
                button
                onClick={() => {
                  addScanner(indicator.id);
                }}
              >
                <ListItemText
                  primary={indicator.name}
                  secondary={indicator.description}
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
          {editingScanner && renderConfigForm(editingScanner)}
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
