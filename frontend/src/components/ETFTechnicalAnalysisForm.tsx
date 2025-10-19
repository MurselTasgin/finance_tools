// finance_tools/frontend/src/components/ETFTechnicalAnalysisForm.tsx
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
  Chip,
  Stack,
  Alert,
  Divider,
  FormControlLabel,
  Switch,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  TrendingUp as TrendingUpIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';

interface ETFTechnicalAnalysisFormProps {
  onRunAnalysis: (parameters: any) => void;
  running: boolean;
}

interface IndicatorConfig {
  ema: {
    windows: number[];
  };
  rsi: {
    window: number;
  };
  macd: {
    window_slow: number;
    window_fast: number;
    window_sign: number;
  };
  momentum: {
    windows: number[];
  };
  daily_momentum: {
    windows: number[];
  };
  supertrend: {
    hl_factor: number;
    atr_period: number;
    multiplier: number;
  };
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
  const [indicators, setIndicators] = useState<IndicatorConfig>({
    ema: { windows: [20, 50] },
    rsi: { window: 14 },
    macd: { window_slow: 26, window_fast: 12, window_sign: 9 },
    momentum: { windows: [30, 60, 90, 180, 360] },
    daily_momentum: { windows: [30, 60, 90, 180, 360] },
    supertrend: { hl_factor: 0.05, atr_period: 10, multiplier: 3.0 },
  });

  // UI state
  const [newKeyword, setNewKeyword] = useState('');
  const [activeTab, setActiveTab] = useState(0);

  const availableColumns = [
    { value: 'price', label: 'Price' },
    { value: 'market_cap', label: 'Market Cap' },
    { value: 'number_of_investors', label: 'Number of Investors' },
    { value: 'number_of_shares', label: 'Number of Shares' },
  ];

  const addCode = () => {
    if (codes.length < 10) {
      setCodes([...codes, '']);
    }
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

  const updateIndicator = (indicatorType: keyof IndicatorConfig, field: string, value: any) => {
    setIndicators(prev => ({
      ...prev,
      [indicatorType]: {
        ...prev[indicatorType],
        [field]: value,
      },
    }));
  };

  const updateArrayField = (indicatorType: keyof IndicatorConfig, field: string, index: number, value: any) => {
    setIndicators(prev => ({
      ...prev,
      [indicatorType]: {
        ...prev[indicatorType],
        [field]: (prev[indicatorType] as any)[field].map((item: any, i: number) =>
          i === index ? value : item
        ),
      },
    }));
  };

  const addArrayItem = (indicatorType: keyof IndicatorConfig, field: string) => {
    setIndicators(prev => ({
      ...prev,
      [indicatorType]: {
        ...prev[indicatorType],
        [field]: [...(prev[indicatorType] as any)[field], 0],
      },
    }));
  };


  const handleSubmit = () => {
    const parameters = {
      codes: codes.filter(code => code.trim() !== ''),
      start_date: startDate,
      end_date: endDate,
      column,
      indicators,
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

              <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                <Button
                  variant={activeTab === 0 ? 'contained' : 'text'}
                  onClick={() => setActiveTab(0)}
                >
                  Moving Averages
                </Button>
                <Button
                  variant={activeTab === 1 ? 'contained' : 'text'}
                  onClick={() => setActiveTab(1)}
                  sx={{ ml: 1 }}
                >
                  Momentum
                </Button>
                <Button
                  variant={activeTab === 2 ? 'contained' : 'text'}
                  onClick={() => setActiveTab(2)}
                  sx={{ ml: 1 }}
                >
                  Trend
                </Button>
              </Box>

              {/* Moving Averages Tab */}
              {activeTab === 0 && (
                <Box mt={2}>
                  <Grid container spacing={3}>
                    <Grid item xs={12} md={4}>
                      <Typography variant="subtitle1" gutterBottom>
                        EMA (Exponential Moving Average)
                      </Typography>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Windows: {indicators.ema.windows.join(', ')}
                      </Typography>
                      <Stack spacing={1}>
                        {indicators.ema.windows.map((window, index) => (
                          <TextField
                            key={index}
                            size="small"
                            type="number"
                            label={`EMA Window ${index + 1}`}
                            value={window}
                            onChange={(e) => updateArrayField('ema', 'windows', index, parseInt(e.target.value))}
                            inputProps={{ min: 1, max: 200 }}
                          />
                        ))}
                        <Button
                          size="small"
                          startIcon={<AddIcon />}
                          onClick={() => addArrayItem('ema', 'windows')}
                        >
                          Add EMA Window
                        </Button>
                      </Stack>
                    </Grid>

                    <Grid item xs={12} md={4}>
                      <Typography variant="subtitle1" gutterBottom>
                        RSI (Relative Strength Index)
                      </Typography>
                      <TextField
                        fullWidth
                        type="number"
                        label="RSI Window"
                        value={indicators.rsi.window}
                        onChange={(e) => updateIndicator('rsi', 'window', parseInt(e.target.value))}
                        inputProps={{ min: 2, max: 100 }}
                        helperText="Typical range: 14"
                      />
                    </Grid>

                    <Grid item xs={12} md={4}>
                      <Typography variant="subtitle1" gutterBottom>
                        MACD
                      </Typography>
                      <Stack spacing={1}>
                        <TextField
                          size="small"
                          type="number"
                          label="Slow EMA"
                          value={indicators.macd.window_slow}
                          onChange={(e) => updateIndicator('macd', 'window_slow', parseInt(e.target.value))}
                          inputProps={{ min: 1, max: 100 }}
                        />
                        <TextField
                          size="small"
                          type="number"
                          label="Fast EMA"
                          value={indicators.macd.window_fast}
                          onChange={(e) => updateIndicator('macd', 'window_fast', parseInt(e.target.value))}
                          inputProps={{ min: 1, max: 50 }}
                        />
                        <TextField
                          size="small"
                          type="number"
                          label="Signal Line"
                          value={indicators.macd.window_sign}
                          onChange={(e) => updateIndicator('macd', 'window_sign', parseInt(e.target.value))}
                          inputProps={{ min: 1, max: 50 }}
                        />
                      </Stack>
                    </Grid>
                  </Grid>
                </Box>
              )}

              {/* Momentum Tab */}
              {activeTab === 1 && (
                <Box mt={2}>
                  <Grid container spacing={3}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle1" gutterBottom>
                        Momentum Indicators
                      </Typography>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Windows: {indicators.momentum.windows.join(', ')}
                      </Typography>
                      <Stack spacing={1}>
                        {indicators.momentum.windows.map((window, index) => (
                          <TextField
                            key={index}
                            size="small"
                            type="number"
                            label={`Momentum Window ${index + 1}`}
                            value={window}
                            onChange={(e) => updateArrayField('momentum', 'windows', index, parseInt(e.target.value))}
                            inputProps={{ min: 1, max: 1000 }}
                          />
                        ))}
                        <Button
                          size="small"
                          startIcon={<AddIcon />}
                          onClick={() => addArrayItem('momentum', 'windows')}
                        >
                          Add Momentum Window
                        </Button>
                      </Stack>
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle1" gutterBottom>
                        Daily Momentum
                      </Typography>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Windows: {indicators.daily_momentum.windows.join(', ')}
                      </Typography>
                      <Stack spacing={1}>
                        {indicators.daily_momentum.windows.map((window, index) => (
                          <TextField
                            key={index}
                            size="small"
                            type="number"
                            label={`Daily Momentum Window ${index + 1}`}
                            value={window}
                            onChange={(e) => updateArrayField('daily_momentum', 'windows', index, parseInt(e.target.value))}
                            inputProps={{ min: 1, max: 1000 }}
                          />
                        ))}
                        <Button
                          size="small"
                          startIcon={<AddIcon />}
                          onClick={() => addArrayItem('daily_momentum', 'windows')}
                        >
                          Add Daily Momentum Window
                        </Button>
                      </Stack>
                    </Grid>
                  </Grid>
                </Box>
              )}

              {/* Trend Tab */}
              {activeTab === 2 && (
                <Box mt={2}>
                  <Typography variant="subtitle1" gutterBottom>
                    Supertrend Indicator
                  </Typography>
                  <Grid container spacing={3}>
                    <Grid item xs={12} md={4}>
                      <TextField
                        fullWidth
                        type="number"
                        label="HL Factor"
                        value={indicators.supertrend.hl_factor}
                        onChange={(e) => updateIndicator('supertrend', 'hl_factor', parseFloat(e.target.value))}
                        inputProps={{ min: 0.01, max: 1.0, step: 0.01 }}
                        helperText="Typical range: 0.05"
                      />
                    </Grid>
                    <Grid item xs={12} md={4}>
                      <TextField
                        fullWidth
                        type="number"
                        label="ATR Period"
                        value={indicators.supertrend.atr_period}
                        onChange={(e) => updateIndicator('supertrend', 'atr_period', parseInt(e.target.value))}
                        inputProps={{ min: 1, max: 100 }}
                        helperText="Typical range: 10"
                      />
                    </Grid>
                    <Grid item xs={12} md={4}>
                      <TextField
                        fullWidth
                        type="number"
                        label="Multiplier"
                        value={indicators.supertrend.multiplier}
                        onChange={(e) => updateIndicator('supertrend', 'multiplier', parseFloat(e.target.value))}
                        inputProps={{ min: 0.1, max: 10.0, step: 0.1 }}
                        helperText="Typical range: 3.0"
                      />
                    </Grid>
                  </Grid>
                </Box>
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
