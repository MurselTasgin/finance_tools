// finance_tools/frontend/src/components/FilterDialog.tsx
import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Grid,
  Box,
  Typography,
  Divider,
} from '@mui/material';
import { FilterOptions } from '../types';

interface FilterDialogProps {
  open: boolean;
  onClose: () => void;
  onAddFilter: (filter: FilterOptions) => void;
  columns: string[];
}

const OPERATORS = [
  { value: 'equals', label: 'Equals' },
  { value: 'contains', label: 'Contains' },
  { value: 'greater_than', label: 'Greater Than' },
  { value: 'less_than', label: 'Less Than' },
  { value: 'between', label: 'Between' },
];

export const FilterDialog: React.FC<FilterDialogProps> = ({
  open,
  onClose,
  onAddFilter,
  columns,
}) => {
  const [filter, setFilter] = useState<FilterOptions>({
    column: '',
    operator: 'equals',
    value: '',
  });

  const handleSubmit = () => {
    if (filter.column && filter.value) {
      onAddFilter(filter);
      setFilter({
        column: '',
        operator: 'equals',
        value: '',
      });
      onClose();
    }
  };

  const handleClose = () => {
    setFilter({
      column: '',
      operator: 'equals',
      value: '',
    });
    onClose();
  };

  const isValueRequired = filter.operator !== 'between';
  const isValue2Required = filter.operator === 'between';

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Add Filter</DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 2 }}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Column</InputLabel>
                <Select
                  value={filter.column}
                  onChange={(e) => setFilter(prev => ({ ...prev, column: e.target.value }))}
                >
                  {columns.map((col) => (
                    <MenuItem key={col} value={col}>
                      {col.replace(/_/g, ' ').toUpperCase()}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Operator</InputLabel>
                <Select
                  value={filter.operator}
                  onChange={(e) => setFilter(prev => ({ 
                    ...prev, 
                    operator: e.target.value as FilterOptions['operator'],
                    value2: undefined,
                  }))}
                >
                  {OPERATORS.map((op) => (
                    <MenuItem key={op.value} value={op.value}>
                      {op.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {isValueRequired && (
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Value"
                  value={filter.value}
                  onChange={(e) => setFilter(prev => ({ ...prev, value: e.target.value }))}
                  type={['price', 'market_cap', 'number_of_investors', 'number_of_shares'].includes(filter.column) ? 'number' : 'text'}
                />
              </Grid>
            )}

            {isValue2Required && (
              <>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="From"
                    value={filter.value}
                    onChange={(e) => setFilter(prev => ({ ...prev, value: e.target.value }))}
                    type={['price', 'market_cap', 'number_of_investors', 'number_of_shares'].includes(filter.column) ? 'number' : 'text'}
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="To"
                    value={filter.value2 || ''}
                    onChange={(e) => setFilter(prev => ({ ...prev, value2: e.target.value }))}
                    type={['price', 'market_cap', 'number_of_investors', 'number_of_shares'].includes(filter.column) ? 'number' : 'text'}
                  />
                </Grid>
              </>
            )}
          </Grid>

          <Divider sx={{ my: 2 }} />
          
          <Typography variant="body2" color="textSecondary">
            <strong>Filter Examples:</strong>
            <br />
            • <code>price greater_than 100</code> - Show records where price is above 100
            <br />
            • <code>title contains "ETF"</code> - Show records where title contains "ETF"
            <br />
            • <code>date between 2024-01-01 2024-12-31</code> - Show records within date range
          </Typography>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button 
          onClick={handleSubmit} 
          variant="contained"
          disabled={!filter.column || !filter.value || (isValue2Required && !filter.value2)}
        >
          Add Filter
        </Button>
      </DialogActions>
    </Dialog>
  );
};
