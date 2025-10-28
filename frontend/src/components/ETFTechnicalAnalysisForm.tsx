// finance_tools/frontend/src/components/ETFTechnicalAnalysisForm.tsx
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
  Chip,
  Stack,
  Alert,
  Divider,
  FormControlLabel,
  Switch,
  IconButton,
  CircularProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  TrendingUp as TrendingUpIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { analyticsApi } from '../services/api';

interface ETFTechnicalAnalysisFormProps {
  onRunAnalysis: (parameters: any) => void;
  running: boolean;
}

interface IndicatorDefinition {
  id: string;
  name: string;
  description: string;
  required_columns: string[];
  parameter_schema: Record<string, any>;
  capabilities: string[];
  asset_types: string[];
}

export const ETFTechnicalAnalysisForm: React.FC<ETFTechnicalAnalysisFormProps> = ({
  onRunAnalysis,
  running,
}) => {
  // Basic parameters
  const [codes, setCodes] = useState<string[]>(['NNF', 'YAC']);
  const [startDate, setStartDate] = useState('2025-09-29');
  const [endDate, setEndDate] = useState('2025-10-17');
  const [column, setColumn] = useState('price');
  const [userId, setUserId] = useState('demo_user');

  // Filter parameters
  const [includeKeywords, setIncludeKeywords] = useState<string[]>([]);
  const [excludeKeywords, setExcludeKeywords] = useState<string[]>([]);
  const [caseSensitive, setCaseSensitive] = useState(false);

  // Indicator configurations
  const [availableIndicators, setAvailableIndicators] = useState<IndicatorDefinition[]>([]);
  const [indicatorConfigs, setIndicatorConfigs] = useState<Record<string, any>>({});
  const [enabledIndicators, setEnabledIndicators] = useState<Record<string, boolean>>({});
  const [loadingIndicators, setLoadingIndicators] = useState(false);
  const [indicatorError, setIndicatorError] = useState<string | null>(null);

  // UI state
  const [newKeyword, setNewKeyword] = useState('');

  const availableColumns = [
    { value: 'price', label: 'Price' },
    { value: 'market_cap', label: 'Market Cap' },
    { value: 'number_of_investors', label: 'Number of Investors' },
    { value: 'number_of_shares', label: 'Number of Shares' },
  ];

  useEffect(() => {
    loadIndicators();
  }, []);

  const loadIndicators = async () => {
    try {
      setLoadingIndicators(true);
      setIndicatorError(null);
      const response = await analyticsApi.getIndicators('etf');
      const indicators = response.indicators || [];
      setAvailableIndicators(indicators);

      const defaults: Record<string, any> = {};
      const enabled: Record<string, boolean> = {};

      indicators.forEach((indicator: IndicatorDefinition) => {
        enabled[indicator.id] = true;
        const config: Record<string, any> = {};
        Object.entries(indicator.parameter_schema || {}).forEach(([key, schema]: [string, any]) => {
          if (schema && schema.default !== undefined) {
            config[key] = schema.default;
          }
        });
        defaults[indicator.id] = config;
      });

      setIndicatorConfigs(defaults);
      setEnabledIndicators(enabled);
    } catch (err) {
      console.error('Failed to load ETF indicators:', err);
      setIndicatorError('Failed to load ETF indicators');
    } finally {
      setLoadingIndicators(false);
    }
  };

  const addCode = () => {
    if (codes.length < 10) {
      setCodes([...codes, '']);
    }
  };

  const updateIndicatorParam = (indicatorId: string, param: string, value: any) => {
    setIndicatorConfigs(prev => ({
      ...prev,
      [indicatorId]: {
        ...(prev[indicatorId] || {}),
        [param]: value,
      },
    }));
  };

  const toggleIndicator = (indicatorId: string, enabled: boolean) => {
    setEnabledIndicators(prev => ({
      ...prev,
      [indicatorId]: enabled,
    }));
  };

  const renderIndicatorFields = (indicator: IndicatorDefinition) => {
    const schemaEntries = Object.entries(indicator.parameter_schema || {});
    const isEnabled = enabledIndicators[indicator.id] ?? true;
    const currentConfig = indicatorConfigs[indicator.id] || {};

    if (schemaEntries.length === 0) {
      return (
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          No configurable parameters.
        </Typography>
      );
    }

    return (
      <Stack spacing={2} sx={{ mt: 2 }}>
        {schemaEntries.map(([key, schema]: [string, any]) => {
          const value = currentConfig[key] ?? schema.default ?? '';

          if (schema.type === 'integer') {
            return (
              <TextField
                key={key}
                label={schema.description || key}
                type="number"
                value={value}
                onChange={(e) => {
                  const parsed = parseInt(e.target.value, 10);
                  updateIndicatorParam(indicator.id, key, Number.isNaN(parsed) ? schema.default : parsed);
                }}
                fullWidth
                inputProps={{ min: schema.min, max: schema.max }}
                disabled={!isEnabled}
              />
            );
          }

          if (schema.type === 'float') {
            return (
              <TextField
                key={key}
                label={schema.description || key}
                type="number"
                value={value}
                onChange={(e) => {
                  const parsed = parseFloat(e.target.value);
                  updateIndicatorParam(indicator.id, key, Number.isNaN(parsed) ? schema.default : parsed);
                }}
                fullWidth
                inputProps={{ min: schema.min, max: schema.max, step: schema.step || 0.1 }}
                disabled={!isEnabled}
              />
            );
          }

          if (schema.type === 'array') {
            const textValue = Array.isArray(value) ? JSON.stringify(value) : JSON.stringify(schema.default || []);
            return (
              <TextField
                key={key}
                label={schema.description || key}
                value={textValue}
                onChange={(e) => {
                  try {
                    const parsed = JSON.parse(e.target.value);
                    if (Array.isArray(parsed)) {
                      updateIndicatorParam(indicator.id, key, parsed);
                    }
                  } catch {
                    // Ignore invalid JSON
                  }
                }}
                fullWidth
                helperText="Enter as JSON array, e.g., [20, 50]"
                disabled={!isEnabled}
              />
            );
          }

          if (schema.type === 'boolean') {
            return (
              <FormControlLabel
                key={key}
                control={
                  <Switch
                    checked={Boolean(value)}
                    onChange={(e) => updateIndicatorParam(indicator.id, key, e.target.checked)}
                    disabled={!isEnabled}
                  />
                }
                label={schema.description || key}
              />
            );
          }

          return (
            <TextField
              key={key}
              label={schema.description || key}
              value={value}
              onChange={(e) => updateIndicatorParam(indicator.id, key, e.target.value)}
              fullWidth
              disabled={!isEnabled}
            />
          );
        })}
      </Stack>
    );
  };

  const updateCode = (index: number, value: string) => {
    const newCodes = [...codes];
    newCodes[index] = value.toUpperCase();
    setCodes(newCodes);
  };

  const removeCode = (index: number) => {
    if (codes.length > 1) {
      setCodes(codes.filter((_, i) => i !== index));
    }
  };

  const addKeyword = (type: 'include' | 'exclude') => {
    if (newKeyword.trim()) {
      if (type === 'include') {
        setIncludeKeywords([...includeKeywords, newKeyword.trim()]);
      } else {
        setExcludeKeywords([...excludeKeywords, newKeyword.trim()]);
      }
      setNewKeyword('');
    }
  };

  const removeKeyword = (type: 'include' | 'exclude', index: number) => {
    if (type === 'include') {
      setIncludeKeywords(includeKeywords.filter((_, i) => i !== index));
    } else {
      setExcludeKeywords(excludeKeywords.filter((_, i) => i !== index));
    }
  };


  const handleSubmit = () => {
    const activeIndicators = Object.fromEntries(
      Object.entries(indicatorConfigs).filter(([indicatorId]) => enabledIndicators[indicatorId])
    );

    const parameters = {
      codes: codes.filter(code => code.trim() !== ''),
      start_date: startDate,
      end_date: endDate,
      column,
      indicators: activeIndicators,
      include_keywords: includeKeywords.length > 0 ? includeKeywords : undefined,
      exclude_keywords: excludeKeywords.length > 0 ? excludeKeywords : undefined,
      case_sensitive: caseSensitive,
      user_id: userId,
    };

    onRunAnalysis(parameters);
  };

  const canSubmit = codes.some(code => code.trim() !== '') && startDate && endDate;

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        <TrendingUpIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        ETF Technical Analysis Configuration
      </Typography>

      <Grid container spacing={3}>
        {/* Basic Parameters */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <SettingsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Basic Parameters
              </Typography>

              {/* Fund Codes */}
              <Box mb={3}>
                <Typography variant="subtitle2" gutterBottom>
                  Fund Codes
                </Typography>
                <Stack spacing={1}>
                  {codes.map((code, index) => (
                    <Box key={index} display="flex" alignItems="center">
                      <TextField
                        size="small"
                        fullWidth
                        value={code}
                        onChange={(e) => updateCode(index, e.target.value)}
                        placeholder={`Fund code ${index + 1}`}
                        inputProps={{ maxLength: 10 }}
                      />
                      {codes.length > 1 && (
                        <IconButton
                          size="small"
                          onClick={() => removeCode(index)}
                          color="error"
                        >
                          <DeleteIcon />
                        </IconButton>
                      )}
                    </Box>
                  ))}
                  {codes.length < 10 && (
                    <Button
                      size="small"
                      startIcon={<AddIcon />}
                      onClick={addCode}
                      variant="outlined"
                    >
                      Add Fund Code
                    </Button>
                  )}
                </Stack>
              </Box>

              <Divider sx={{ my: 2 }} />

              {/* Date Range */}
              <Grid container spacing={2} mb={2}>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Start Date"
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    InputLabelProps={{ shrink: true }}
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
                  />
                </Grid>
              </Grid>

              {/* Column Selection */}
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Analysis Column</InputLabel>
                <Select
                  value={column}
                  label="Analysis Column"
                  onChange={(e: SelectChangeEvent) => setColumn(e.target.value)}
                >
                  {availableColumns.map((col) => (
                    <MenuItem key={col.value} value={col.value}>
                      {col.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* User ID */}
              <TextField
                fullWidth
                label="User ID (Optional)"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                helperText="For tracking analysis history"
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Filters */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Title Filtering
              </Typography>

              {/* Include Keywords */}
              <Box mb={3}>
                <Typography variant="subtitle2" gutterBottom>
                  Include Keywords
                </Typography>
                <Box display="flex" mb={1}>
                  <TextField
                    size="small"
                    value={newKeyword}
                    onChange={(e) => setNewKeyword(e.target.value)}
                    placeholder="Add keyword..."
                    onKeyPress={(e) => e.key === 'Enter' && addKeyword('include')}
                  />
                  <Button
                    size="small"
                    onClick={() => addKeyword('include')}
                    disabled={!newKeyword.trim()}
                  >
                    Add
                  </Button>
                </Box>
                <Stack direction="row" spacing={1} flexWrap="wrap">
                  {includeKeywords.map((keyword, index) => (
                    <Chip
                      key={index}
                      label={keyword}
                      size="small"
                      onDelete={() => removeKeyword('include', index)}
                    />
                  ))}
                </Stack>
              </Box>

              {/* Exclude Keywords */}
              <Box mb={3}>
                <Typography variant="subtitle2" gutterBottom>
                  Exclude Keywords
                </Typography>
                <Box display="flex" mb={1}>
                  <TextField
                    size="small"
                    value={newKeyword}
                    onChange={(e) => setNewKeyword(e.target.value)}
                    placeholder="Add keyword..."
                    onKeyPress={(e) => e.key === 'Enter' && addKeyword('exclude')}
                  />
                  <Button
                    size="small"
                    onClick={() => addKeyword('exclude')}
                    disabled={!newKeyword.trim()}
                  >
                    Add
                  </Button>
                </Box>
                <Stack direction="row" spacing={1} flexWrap="wrap">
                  {excludeKeywords.map((keyword, index) => (
                    <Chip
                      key={index}
                      label={keyword}
                      size="small"
                      onDelete={() => removeKeyword('exclude', index)}
                      color="secondary"
                    />
                  ))}
                </Stack>
              </Box>

              <FormControlLabel
                control={
                  <Switch
                    checked={caseSensitive}
                    onChange={(e) => setCaseSensitive(e.target.checked)}
                  />
                }
                label="Case Sensitive Matching"
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Technical Indicators */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Technical Indicators Configuration
              </Typography>

              {indicatorError && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {indicatorError}
                </Alert>
              )}

              {loadingIndicators ? (
                <Box display="flex" justifyContent="center" py={4}>
                  <CircularProgress />
                </Box>
              ) : (
                <Stack spacing={3}>
                  {availableIndicators.length === 0 ? (
                    <Typography variant="body2" color="text.secondary">
                      No indicators available.
                    </Typography>
                  ) : (
                    availableIndicators.map((indicator) => (
                      <Box
                        key={indicator.id}
                        p={2}
                        sx={{
                          border: '1px solid',
                          borderColor: 'divider',
                          borderRadius: 1,
                        }}
                      >
                        <Stack
                          direction={{ xs: 'column', sm: 'row' }}
                          spacing={1}
                          justifyContent="space-between"
                          alignItems={{ xs: 'flex-start', sm: 'center' }}
                        >
                          <Box>
                            <Typography variant="subtitle1">{indicator.name}</Typography>
                            <Typography variant="body2" color="text.secondary">
                              {indicator.description}
                            </Typography>
                            {indicator.required_columns?.length > 0 && (
                              <Typography variant="caption" color="text.secondary">
                                Requires: {indicator.required_columns.join(', ')}
                              </Typography>
                            )}
                          </Box>
                          <FormControlLabel
                            control={
                              <Switch
                                checked={enabledIndicators[indicator.id] ?? true}
                                onChange={(e) => toggleIndicator(indicator.id, e.target.checked)}
                              />
                            }
                            label={(enabledIndicators[indicator.id] ?? true) ? 'Enabled' : 'Disabled'}
                          />
                        </Stack>

                        {renderIndicatorFields(indicator)}
                      </Box>
                    ))
                  )}
                </Stack>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Submit Button */}
        <Grid item xs={12}>
          <Box display="flex" justifyContent="center" mt={2}>
            <Button
              variant="contained"
              size="large"
              onClick={handleSubmit}
              disabled={!canSubmit || running}
              startIcon={running ? undefined : <TrendingUpIcon />}
              sx={{ minWidth: 200 }}
            >
              {running ? 'Running Analysis...' : 'Run ETF Technical Analysis'}
            </Button>
          </Box>

          {!canSubmit && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              Please provide at least one fund code and valid date range.
            </Alert>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};
