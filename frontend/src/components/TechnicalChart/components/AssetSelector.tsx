// TechnicalChart/components/AssetSelector.tsx
import React, { useState, useMemo, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Tabs,
  Tab,
  Box,
  Typography,
  CircularProgress,
  InputAdornment,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import { AssetType } from '../types/chart.types';
import { dataApi, stockApi } from '../../../services/api';
import { useQuery } from 'react-query';

interface AssetSelectorProps {
  open: boolean;
  onClose: () => void;
  onSelectAsset: (assetType: AssetType, identifier: string) => void;
  currentAssetType: AssetType;
  currentIdentifier: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`asset-tabpanel-${index}`}
      aria-labelledby={`asset-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 2 }}>{children}</Box>}
    </div>
  );
}

export const AssetSelector: React.FC<AssetSelectorProps> = ({
  open,
  onClose,
  onSelectAsset,
  currentAssetType,
  currentIdentifier,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [tabValue, setTabValue] = useState<number>(currentAssetType === 'stock' ? 0 : 1);

  // Fetch stocks with error handling
  const {
    data: stocksData,
    isLoading: stocksLoading,
    error: stocksError,
  } = useQuery<{ symbols: Array<{ symbol: string }> }>(
    ['stockSymbols'],
    () => stockApi.getSymbols(),
    { 
      enabled: open && tabValue === 0,
      onError: (err) => {
        console.error('Error fetching stocks:', err);
      }
    }
  );

  // Fetch ETFs with error handling
  const {
    data: etfsData,
    isLoading: etfsLoading,
    error: etfsError,
  } = useQuery<any[]>(
    ['etfFunds'],
    () => dataApi.getFunds(),
    { 
      enabled: open && tabValue === 1,
      onError: (err) => {
        console.error('Error fetching ETFs:', err);
      }
    }
  );

  const stocks = useMemo(() => {
    if (!stocksData?.symbols) return [];
    return stocksData.symbols.map((s) => s.symbol);
  }, [stocksData]);

  const etfs = useMemo(() => {
    if (!etfsData || !Array.isArray(etfsData)) return [];
    // Handle different possible formats
    return etfsData
      .map((f) => f.code || f.fund_code || f.symbol || f.id)
      .filter((code) => code != null && code !== '');
  }, [etfsData]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    setSearchQuery(''); // Clear search when switching tabs
  };

  const handleSelect = (assetType: AssetType, identifier: string) => {
    onSelectAsset(assetType, identifier);
    onClose();
    setSearchQuery('');
  };

  // Filter assets based on search query
  const filteredStocks = useMemo(() => {
    if (!searchQuery.trim()) return stocks;
    const query = searchQuery.toUpperCase();
    return stocks.filter((symbol) => symbol.includes(query));
  }, [stocks, searchQuery]);

  const filteredETFs = useMemo(() => {
    if (!searchQuery.trim()) return etfs;
    const query = searchQuery.toUpperCase();
    return etfs.filter((code) => code.includes(query));
  }, [etfs, searchQuery]);

  useEffect(() => {
    if (open) {
      setTabValue(currentAssetType === 'stock' ? 0 : 1);
      setSearchQuery('');
    }
  }, [open, currentAssetType]);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          backgroundColor: '#131722',
          color: '#D1D4DC',
        },
      }}
    >
      <DialogTitle sx={{ borderBottom: '1px solid #2A2E39', pb: 2 }}>
        <Typography variant="h6" sx={{ color: '#D1D4DC', fontWeight: 600 }}>
          Select Asset
        </Typography>
      </DialogTitle>

      <DialogContent sx={{ pt: 2 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          sx={{
            borderBottom: '1px solid #2A2E39',
            mb: 2,
            '& .MuiTab-root': {
              color: '#758696',
              '&.Mui-selected': {
                color: '#2196F3',
              },
            },
            '& .MuiTabs-indicator': {
              backgroundColor: '#2196F3',
            },
          }}
        >
          <Tab label="Stocks" />
          <Tab label="ETFs" />
        </Tabs>

        <TextField
          fullWidth
          size="small"
          placeholder={tabValue === 0 ? 'Search stocks...' : 'Search ETFs...'}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon sx={{ color: '#758696' }} />
              </InputAdornment>
            ),
            sx: {
              color: '#D1D4DC',
              backgroundColor: '#1E222D',
              '& .MuiOutlinedInput-notchedOutline': {
                borderColor: '#2A2E39',
              },
              '&:hover .MuiOutlinedInput-notchedOutline': {
                borderColor: '#3A3F4E',
              },
              '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                borderColor: '#2196F3',
              },
            },
          }}
          sx={{ mb: 2 }}
        />

        <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
          <TabPanel value={tabValue} index={0}>
            {stocksError ? (
              <Typography variant="body2" sx={{ color: '#F44336', textAlign: 'center', py: 4 }}>
                Error loading stocks. Please try again.
              </Typography>
            ) : stocksLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress size={32} sx={{ color: '#2196F3' }} />
              </Box>
            ) : filteredStocks.length === 0 ? (
              <Typography variant="body2" sx={{ color: '#758696', textAlign: 'center', py: 4 }}>
                {searchQuery ? 'No stocks found' : 'No stocks available'}
              </Typography>
            ) : (
              <List sx={{ p: 0 }}>
                {filteredStocks.map((symbol) => (
                  <ListItem key={symbol} disablePadding>
                    <ListItemButton
                      onClick={() => handleSelect('stock', symbol)}
                      selected={symbol === currentIdentifier && currentAssetType === 'stock'}
                      sx={{
                        '&.Mui-selected': {
                          backgroundColor: '#2196F330',
                          '&:hover': {
                            backgroundColor: '#2196F340',
                          },
                        },
                        '&:hover': {
                          backgroundColor: '#1E222D',
                        },
                      }}
                    >
                      <ListItemText
                        primary={symbol}
                        primaryTypographyProps={{
                          sx: {
                            color: symbol === currentIdentifier && currentAssetType === 'stock' 
                              ? '#2196F3' 
                              : '#D1D4DC',
                            fontWeight: symbol === currentIdentifier && currentAssetType === 'stock' 
                              ? 600 
                              : 400,
                          },
                        }}
                      />
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            )}
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            {etfsError ? (
              <Typography variant="body2" sx={{ color: '#F44336', textAlign: 'center', py: 4 }}>
                Error loading ETFs. Please try again.
              </Typography>
            ) : etfsLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress size={32} sx={{ color: '#2196F3' }} />
              </Box>
            ) : filteredETFs.length === 0 ? (
              <Typography variant="body2" sx={{ color: '#758696', textAlign: 'center', py: 4 }}>
                {searchQuery ? 'No ETFs found' : 'No ETFs available'}
              </Typography>
            ) : (
              <List sx={{ p: 0 }}>
                {filteredETFs.map((code) => (
                  <ListItem key={code} disablePadding>
                    <ListItemButton
                      onClick={() => handleSelect('etf', code)}
                      selected={code === currentIdentifier && currentAssetType === 'etf'}
                      sx={{
                        '&.Mui-selected': {
                          backgroundColor: '#2196F330',
                          '&:hover': {
                            backgroundColor: '#2196F340',
                          },
                        },
                        '&:hover': {
                          backgroundColor: '#1E222D',
                        },
                      }}
                    >
                      <ListItemText
                        primary={code}
                        primaryTypographyProps={{
                          sx: {
                            color: code === currentIdentifier && currentAssetType === 'etf' 
                              ? '#2196F3' 
                              : '#D1D4DC',
                            fontWeight: code === currentIdentifier && currentAssetType === 'etf' 
                              ? 600 
                              : 400,
                          },
                        }}
                      />
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            )}
          </TabPanel>
        </Box>
      </DialogContent>
    </Dialog>
  );
};

export default AssetSelector;

