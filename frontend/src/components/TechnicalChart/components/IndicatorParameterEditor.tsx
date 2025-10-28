// TechnicalChart/components/IndicatorParameterEditor.tsx
import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  FormControl,
  FormLabel,
  Slider,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Alert,
} from '@mui/material';
import { IndicatorConfig, ParameterDefinition } from '../types/chart.types';
import { getIndicatorById, validateIndicatorParameters } from '../utils/indicatorConfigs';

export interface IndicatorParameterEditorProps {
  open: boolean;
  indicatorId: string | null;
  currentParameters: Record<string, any>;
  onClose: () => void;
  onSave: (indicatorId: string, parameters: Record<string, any>) => void;
}

/**
 * Indicator Parameter Editor Dialog
 *
 * Allows users to configure indicator parameters
 */
export const IndicatorParameterEditor: React.FC<IndicatorParameterEditorProps> = ({
  open,
  indicatorId,
  currentParameters,
  onClose,
  onSave,
}) => {
  const [parameters, setParameters] = useState<Record<string, any>>({});
  const [errors, setErrors] = useState<string[]>([]);

  const indicator: IndicatorConfig | undefined = indicatorId
    ? getIndicatorById(indicatorId)
    : undefined;

  // Initialize parameters when dialog opens
  useEffect(() => {
    if (indicator) {
      // Merge current parameters with defaults
      const initialParams = { ...indicator.defaultParameters, ...currentParameters };
      setParameters(initialParams);
      setErrors([]);
    }
  }, [indicator, currentParameters, indicatorId]);

  const handleParameterChange = (key: string, value: any) => {
    setParameters((prev) => ({ ...prev, [key]: value }));
    setErrors([]); // Clear errors when user makes changes
  };

  const handleSave = () => {
    if (!indicator) return;

    // Validate parameters
    const validation = validateIndicatorParameters(indicator.id, parameters);

    if (!validation.valid) {
      setErrors(validation.errors);
      return;
    }

    onSave(indicator.id, parameters);
    onClose();
  };

  const handleReset = () => {
    if (indicator) {
      setParameters({ ...indicator.defaultParameters });
      setErrors([]);
    }
  };

  const renderParameterInput = (def: ParameterDefinition) => {
    const value = parameters[def.key] ?? def.defaultValue;

    switch (def.type) {
      case 'number':
        return (
          <FormControl fullWidth key={def.key} sx={{ mb: 3 }}>
            <FormLabel sx={{ mb: 1 }}>
              <Typography variant="body2" fontWeight={500}>
                {def.label}
              </Typography>
              {def.description && (
                <Typography variant="caption" color="text.secondary">
                  {def.description}
                </Typography>
              )}
            </FormLabel>

            {/* Show slider for bounded numeric values */}
            {def.min !== undefined && def.max !== undefined ? (
              <Box sx={{ px: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Slider
                    value={Number(value)}
                    onChange={(_, newValue) =>
                      handleParameterChange(def.key, newValue)
                    }
                    min={def.min}
                    max={def.max}
                    step={def.step || 1}
                    valueLabelDisplay="auto"
                    marks={[
                      { value: def.min, label: String(def.min) },
                      { value: def.max, label: String(def.max) },
                    ]}
                    sx={{ flex: 1 }}
                  />
                  <TextField
                    type="number"
                    value={value}
                    onChange={(e) =>
                      handleParameterChange(def.key, Number(e.target.value))
                    }
                    inputProps={{
                      min: def.min,
                      max: def.max,
                      step: def.step || 1,
                    }}
                    sx={{ width: 80 }}
                    size="small"
                  />
                </Box>
              </Box>
            ) : (
              <TextField
                type="number"
                value={value}
                onChange={(e) =>
                  handleParameterChange(def.key, Number(e.target.value))
                }
                inputProps={{
                  min: def.min,
                  max: def.max,
                  step: def.step || 1,
                }}
                size="small"
                fullWidth
              />
            )}
          </FormControl>
        );

      case 'select':
        return (
          <FormControl fullWidth key={def.key} sx={{ mb: 3 }}>
            <FormLabel sx={{ mb: 1 }}>
              <Typography variant="body2" fontWeight={500}>
                {def.label}
              </Typography>
              {def.description && (
                <Typography variant="caption" color="text.secondary">
                  {def.description}
                </Typography>
              )}
            </FormLabel>
            <Select
              value={value}
              onChange={(e) => handleParameterChange(def.key, e.target.value)}
              size="small"
            >
              {def.options?.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        );

      case 'boolean':
        return (
          <FormControl fullWidth key={def.key} sx={{ mb: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={Boolean(value)}
                  onChange={(e) =>
                    handleParameterChange(def.key, e.target.checked)
                  }
                />
              }
              label={
                <Box>
                  <Typography variant="body2" fontWeight={500}>
                    {def.label}
                  </Typography>
                  {def.description && (
                    <Typography variant="caption" color="text.secondary">
                      {def.description}
                    </Typography>
                  )}
                </Box>
              }
            />
          </FormControl>
        );

      default:
        return null;
    }
  };

  if (!indicator) {
    return null;
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          minHeight: 400,
        },
      }}
    >
      <DialogTitle>
        <Typography variant="h6" component="div">
          Configure {indicator.name}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {indicator.description}
        </Typography>
      </DialogTitle>

      <DialogContent dividers>
        {errors.length > 0 && (
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="body2" fontWeight={500}>
              Please fix the following errors:
            </Typography>
            <ul style={{ margin: '8px 0 0 0', paddingLeft: 20 }}>
              {errors.map((error, index) => (
                <li key={index}>
                  <Typography variant="caption">{error}</Typography>
                </li>
              ))}
            </ul>
          </Alert>
        )}

        <Box sx={{ py: 1 }}>
          {indicator.parameterDefinitions.map((def) =>
            renderParameterInput(def)
          )}
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={handleReset} color="inherit">
          Reset to Default
        </Button>
        <Box sx={{ flex: 1 }} />
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSave} variant="contained" color="primary">
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default IndicatorParameterEditor;
