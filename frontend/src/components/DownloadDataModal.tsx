// finance_tools/frontend/src/components/DownloadDataModal.tsx
import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  TextField,
  Box,
  Typography,
  Alert,
  CircularProgress,
  Select,
  MenuItem,
  InputLabel,
  Chip,
  OutlinedInput,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { databaseApi } from '../services/api';
import { DatabaseStats } from '../types';

interface DownloadDataModalProps {
  open: boolean;
  onClose: () => void;
  onDownload: (startDate: string, endDate: string, kind: string, funds: string[]) => void;
  lastDownloadDate: string | null;
}

const DownloadDataModal: React.FC<DownloadDataModalProps> = ({
  open,
  onClose,
  onDownload,
  lastDownloadDate,
}) => {
  const [downloadOption, setDownloadOption] = useState<'last20' | 'custom'>('last20');
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [endDate, setEndDate] = useState<Date | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [kind, setKind] = useState<string>('BYF');
  const [funds, setFunds] = useState<string[]>([]);
  const [fundInput, setFundInput] = useState<string>('');

  // Set default dates when modal opens
  useEffect(() => {
    if (open) {
      const today = new Date();
      const twentyDaysAgo = new Date();
      twentyDaysAgo.setDate(today.getDate() - 20);
      
      setStartDate(twentyDaysAgo);
      setEndDate(today);
      setError(null);
    }
  }, [open]);

  const handleDownload = async () => {
    if (!startDate || !endDate) {
      setError('Please select both start and end dates');
      return;
    }

    if (startDate > endDate) {
      setError('Start date must be before end date');
      return;
    }

    setIsDownloading(true);
    setError(null);

    try {
      await onDownload(
        startDate.toISOString().split('T')[0],
        endDate.toISOString().split('T')[0],
        kind,
        funds
      );
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Download failed');
    } finally {
      setIsDownloading(false);
    }
  };

  const handleAddFund = () => {
    const fundCode = fundInput.trim().toUpperCase();
    if (fundCode && !funds.includes(fundCode)) {
      setFunds([...funds, fundCode]);
      setFundInput('');
    }
  };

  const handleRemoveFund = (fundToRemove: string) => {
    setFunds(funds.filter(fund => fund !== fundToRemove));
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      handleAddFund();
    }
  };

  const handleClose = () => {
    if (!isDownloading) {
      onClose();
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'No data available';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>Download Fund Data</DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 3 }}>
            <Typography variant="body2" color="text.secondary">
              Last data in database: <strong>{formatDate(lastDownloadDate)}</strong>
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Download fund data from TEFAS. You can specify the fund type and specific fund codes.
            </Typography>
          </Box>

          <FormControl component="fieldset" sx={{ mb: 3 }}>
            <FormLabel component="legend">Select download option:</FormLabel>
            <RadioGroup
              value={downloadOption}
              onChange={(e) => setDownloadOption(e.target.value as 'last20' | 'custom')}
            >
              <FormControlLabel
                value="last20"
                control={<Radio />}
                label="Download last 20 days of data"
              />
              <FormControlLabel
                value="custom"
                control={<Radio />}
                label="Specify custom date range"
              />
            </RadioGroup>
          </FormControl>

          {downloadOption === 'custom' && (
            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <DatePicker
                label="Start Date"
                value={startDate}
                onChange={(newValue) => setStartDate(newValue)}
                maxDate={new Date()}
                disabled={isDownloading}
                sx={{ flex: 1 }}
              />
              <DatePicker
                label="End Date"
                value={endDate}
                onChange={(newValue) => setEndDate(newValue)}
                maxDate={new Date()}
                disabled={isDownloading}
                sx={{ flex: 1 }}
              />
            </Box>
          )}

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Fund Type</InputLabel>
            <Select
              value={kind}
              onChange={(e) => setKind(e.target.value)}
              disabled={isDownloading}
            >
              <MenuItem value="YAT">YAT - Securities Mutual Funds</MenuItem>
              <MenuItem value="EMK">EMK - Pension Funds</MenuItem>
              <MenuItem value="BYF">BYF - Exchange Traded Funds</MenuItem>
            </Select>
          </FormControl>

          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Fund Codes (optional - leave empty to download all funds)
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
              <TextField
                label="Add Fund Code"
                value={fundInput}
                onChange={(e) => setFundInput(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isDownloading}
                size="small"
                sx={{ flex: 1 }}
                placeholder="e.g., NNF, YAC"
              />
              <Button
                onClick={handleAddFund}
                disabled={isDownloading || !fundInput.trim()}
                variant="outlined"
                size="small"
              >
                Add
              </Button>
            </Box>
            {funds.length > 0 && (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {funds.map((fund) => (
                  <Chip
                    key={fund}
                    label={fund}
                    onDelete={() => handleRemoveFund(fund)}
                    disabled={isDownloading}
                    size="small"
                  />
                ))}
              </Box>
            )}
          </Box>

          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={isDownloading}>
            Cancel
          </Button>
          <Button
            onClick={handleDownload}
            variant="contained"
            disabled={isDownloading || (downloadOption === 'custom' && (!startDate || !endDate))}
            startIcon={isDownloading ? <CircularProgress size={20} /> : null}
          >
            {isDownloading ? 'Downloading...' : 'Download Data'}
          </Button>
        </DialogActions>
      </Dialog>
    </LocalizationProvider>
  );
};

export default DownloadDataModal;
