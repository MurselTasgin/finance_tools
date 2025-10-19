// finance_tools/frontend/src/components/DownloadDataModal.tsx
import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
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
  Tabs,
  Tab,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

interface DownloadDataModalProps {
  open: boolean;
  onClose: () => void;
  onDownload: (startDate: string, endDate: string, kind: string, funds: string[]) => void;
  onDownloadStocks?: (symbols: string[], startDate: string, endDate: string, interval: string) => void;
  lastDownloadDate: string | null;
  loading?: boolean;
}

const DownloadDataModal: React.FC<DownloadDataModalProps> = ({
  open,
  onClose,
  onDownload,
  onDownloadStocks,
  lastDownloadDate,
  loading = false,
}) => {
  // Tab selection: 'tefas' or 'stocks'
  const [dataType, setDataType] = useState<'tefas' | 'stocks'>('tefas');
  
  // TEFAS-specific states
  const [downloadOption, setDownloadOption] = useState<'last20' | 'custom'>('last20');
  const [kind, setKind] = useState<string>('BYF');
  const [funds, setFunds] = useState<string[]>([]);
  const [fundInput, setFundInput] = useState<string>('');
  
  // Stock-specific states
  const [symbols, setSymbols] = useState<string[]>([]);
  const [symbolInput, setSymbolInput] = useState<string>('');
  const [interval, setInterval] = useState<string>('1d');
  
  // Common states
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [endDate, setEndDate] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Confirmation dialog state
  const [showClearConfirmation, setShowClearConfirmation] = useState(false);
  const [clearType, setClearType] = useState<'funds' | 'symbols'>('symbols');

  // Set default dates and clear previous selections when modal opens
  useEffect(() => {
    if (open) {
      const today = new Date();
      const twentyDaysAgo = new Date();
      twentyDaysAgo.setDate(today.getDate() - 20);
      
      setStartDate(twentyDaysAgo);
      setEndDate(today);
      setError(null);
      
      // Clear previous selections
      setFunds([]);
      setSymbols([]);
      setFundInput('');
      setSymbolInput('');
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

    setError(null);

    try {
      if (dataType === 'tefas') {
        await onDownload(
          startDate.toISOString().split('T')[0],
          endDate.toISOString().split('T')[0],
          kind,
          funds
        );
      } else {
        // Stock download
        if (symbols.length === 0) {
          setError('Please add at least one stock symbol');
          return;
        }
        if (onDownloadStocks) {
          await onDownloadStocks(
            symbols,
            startDate.toISOString().split('T')[0],
            endDate.toISOString().split('T')[0],
            interval
          );
        }
      }
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Download failed');
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

  const handleAddSymbol = () => {
    const symbolCode = symbolInput.trim().toUpperCase();
    if (symbolCode && !symbols.includes(symbolCode)) {
      setSymbols([...symbols, symbolCode]);
      setSymbolInput('');
    }
  };

  const handleRemoveSymbol = (symbolToRemove: string) => {
    setSymbols(symbols.filter(symbol => symbol !== symbolToRemove));
  };

  const handleClearAllClick = (type: 'funds' | 'symbols', event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    setClearType(type);
    setShowClearConfirmation(true);
  };

  const handleClearConfirm = () => {
    if (clearType === 'funds') {
      setFunds([]);
    } else {
      setSymbols([]);
    }
    setShowClearConfirmation(false);
  };

  const handleClearCancel = () => {
    setShowClearConfirmation(false);
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      if (dataType === 'tefas') {
        handleAddFund();
      } else {
        handleAddSymbol();
      }
    }
  };

  const handleClose = () => {
    if (!loading) {
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
      {/* Confirmation Dialog */}
      <Dialog
        open={showClearConfirmation}
        onClose={handleClearCancel}
        aria-labelledby="clear-confirmation-dialog"
      >
        <DialogTitle id="clear-confirmation-dialog">
          Clear All {clearType === 'funds' ? 'Funds' : 'Symbols'}?
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to clear all {clearType === 'funds' ? 'fund codes' : 'stock symbols'}? 
            This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClearCancel} color="primary">
            Cancel
          </Button>
          <Button onClick={handleClearConfirm} color="error" variant="contained">
            Clear All
          </Button>
        </DialogActions>
      </Dialog>

      {/* Main Download Dialog */}
      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>Download Data</DialogTitle>
        <DialogContent>
          {/* Tab selector */}
          <Tabs 
            value={dataType} 
            onChange={(_, newValue) => setDataType(newValue)} 
            sx={{ mb: 3, borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab label="TEFAS Funds" value="tefas" />
            <Tab label="Stocks" value="stocks" />
          </Tabs>

          <Box sx={{ mb: 3 }}>
            <Typography variant="body2" color="text.secondary">
              Last data in database: <strong>{formatDate(lastDownloadDate)}</strong>
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {dataType === 'tefas' 
                ? 'Download fund data from TEFAS. You can specify the fund type and specific fund codes.'
                : 'Download stock data using yfinance. Enter stock symbols (e.g., AAPL, MSFT, GOOGL).'}
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
                disabled={loading}
                slotProps={{ textField: { sx: { flex: 1 } } }}
              />
              <DatePicker
                label="End Date"
                value={endDate}
                onChange={(newValue) => setEndDate(newValue)}
                maxDate={new Date()}
                disabled={loading}
                slotProps={{ textField: { sx: { flex: 1 } } }}
              />
            </Box>
          )}

          {/* TEFAS-specific fields */}
          {dataType === 'tefas' && (
            <>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Fund Type</InputLabel>
                <Select
                  value={kind}
                  onChange={(e) => setKind(e.target.value)}
                  disabled={loading}
                  label="Fund Type"
                >
                  <MenuItem value="YAT">YAT - Securities Mutual Funds</MenuItem>
                  <MenuItem value="EMK">EMK - Pension Funds</MenuItem>
                  <MenuItem value="BYF">BYF - Exchange Traded Funds</MenuItem>
                </Select>
              </FormControl>

              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Fund Codes (optional - leave empty to download all funds)
                  </Typography>
                  {funds.length > 0 && (
                    <Button
                      onClick={(e) => handleClearAllClick('funds', e)}
                      disabled={loading}
                      size="small"
                      color="error"
                      variant="text"
                    >
                      Clear All
                    </Button>
                  )}
                </Box>
                <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                  <TextField
                    label="Add Fund Code"
                    value={fundInput}
                    onChange={(e) => setFundInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={loading}
                    size="small"
                    sx={{ flex: 1 }}
                    placeholder="e.g., NNF, YAC"
                  />
                  <Button
                    onClick={handleAddFund}
                    disabled={loading || !fundInput.trim()}
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
                        disabled={loading}
                        size="small"
                      />
                    ))}
                  </Box>
                )}
              </Box>
            </>
          )}

          {/* Stock-specific fields */}
          {dataType === 'stocks' && (
            <>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Data Interval</InputLabel>
                <Select
                  value={interval}
                  onChange={(e) => setInterval(e.target.value)}
                  disabled={loading}
                  label="Data Interval"
                >
                  <MenuItem value="1d">1 Day</MenuItem>
                  <MenuItem value="1h">1 Hour</MenuItem>
                  <MenuItem value="5m">5 Minutes</MenuItem>
                  <MenuItem value="1wk">1 Week</MenuItem>
                  <MenuItem value="1mo">1 Month</MenuItem>
                </Select>
              </FormControl>

              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Stock Symbols (required)
                  </Typography>
                  {symbols.length > 0 && (
                    <Button
                      onClick={(e) => handleClearAllClick('symbols', e)}
                      disabled={loading}
                      size="small"
                      color="error"
                      variant="text"
                    >
                      Clear All
                    </Button>
                  )}
                </Box>
                <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                  <TextField
                    label="Add Stock Symbol"
                    value={symbolInput}
                    onChange={(e) => setSymbolInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={loading}
                    size="small"
                    sx={{ flex: 1 }}
                    placeholder="e.g., AAPL, MSFT, GOOGL"
                  />
                  <Button
                    onClick={handleAddSymbol}
                    disabled={loading || !symbolInput.trim()}
                    variant="outlined"
                    size="small"
                  >
                    Add
                  </Button>
                </Box>
                {symbols.length > 0 && (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {symbols.map((symbol) => (
                      <Chip
                        key={symbol}
                        label={symbol}
                        onDelete={() => handleRemoveSymbol(symbol)}
                        disabled={loading}
                        size="small"
                        color="primary"
                      />
                    ))}
                  </Box>
                )}
              </Box>
            </>
          )}

          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={loading}>
            Cancel
          </Button>
          <Button
            onClick={handleDownload}
            variant="contained"
            disabled={loading || (downloadOption === 'custom' && (!startDate || !endDate)) || (dataType === 'stocks' && symbols.length === 0)}
            startIcon={loading ? <CircularProgress size={20} /> : null}
          >
            {loading ? 'Downloading...' : 'Download Data'}
          </Button>
        </DialogActions>
      </Dialog>
    </LocalizationProvider>
  );
};

export default DownloadDataModal;
