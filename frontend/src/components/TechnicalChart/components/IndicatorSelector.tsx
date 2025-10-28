// TechnicalChart/components/IndicatorSelector.tsx
import React, { useState, useMemo } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  Chip,
  Box,
  Typography,
  Tabs,
  Tab,
  InputAdornment,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import TimelineIcon from '@mui/icons-material/Timeline';
import CheckIcon from '@mui/icons-material/Check';
import { IndicatorConfig } from '../types/chart.types';
import { getAllIndicators, getOverlayIndicators, getSubplotIndicators } from '../utils/indicatorConfigs';

export interface IndicatorSelectorProps {
  open: boolean;
  onClose: () => void;
  onSelectIndicator: (indicatorId: string, parameters: Record<string, any>) => void;
  selectedIndicators: string[]; // IDs of currently selected indicators
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
      id={`indicator-tabpanel-${index}`}
      aria-labelledby={`indicator-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 2 }}>{children}</Box>}
    </div>
  );
}

/**
 * Indicator Selector Dialog
 *
 * Allows users to browse and add indicators to the chart
 */
export const IndicatorSelector: React.FC<IndicatorSelectorProps> = ({
  open,
  onClose,
  onSelectIndicator,
  selectedIndicators,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [tabValue, setTabValue] = useState(0);

  const allIndicators = useMemo(() => getAllIndicators(), []);
  const overlayIndicators = useMemo(() => getOverlayIndicators(), []);
  const subplotIndicators = useMemo(() => getSubplotIndicators(), []);

  // Filter indicators based on search query
  const filterIndicators = (indicators: IndicatorConfig[]) => {
    if (!searchQuery.trim()) return indicators;

    const query = searchQuery.toLowerCase();
    return indicators.filter(
      (ind) =>
        ind.name.toLowerCase().includes(query) ||
        ind.description.toLowerCase().includes(query) ||
        ind.id.toLowerCase().includes(query)
    );
  };

  const filteredAll = useMemo(
    () => filterIndicators(allIndicators),
    [allIndicators, searchQuery]
  );

  const filteredOverlay = useMemo(
    () => filterIndicators(overlayIndicators),
    [overlayIndicators, searchQuery]
  );

  const filteredSubplot = useMemo(
    () => filterIndicators(subplotIndicators),
    [subplotIndicators, searchQuery]
  );

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleSelectIndicator = (indicator: IndicatorConfig) => {
    // Use default parameters when adding indicator
    onSelectIndicator(indicator.id, indicator.defaultParameters);
    onClose();
  };

  const isIndicatorSelected = (indicatorId: string) => {
    return selectedIndicators.includes(indicatorId);
  };

  const renderIndicatorList = (indicators: IndicatorConfig[]) => {
    if (indicators.length === 0) {
      return (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body2" color="text.secondary">
            No indicators found
          </Typography>
        </Box>
      );
    }

    return (
      <List sx={{ maxHeight: 400, overflow: 'auto' }}>
        {indicators.map((indicator) => {
          const isSelected = isIndicatorSelected(indicator.id);

          return (
            <ListItem key={indicator.id} disablePadding>
              <ListItemButton
                onClick={() => handleSelectIndicator(indicator)}
                disabled={isSelected}
                sx={{
                  '&:hover': {
                    backgroundColor: 'action.hover',
                  },
                }}
              >
                <ListItemIcon>
                  {indicator.type === 'overlay' ? (
                    <ShowChartIcon color="primary" />
                  ) : (
                    <TimelineIcon color="secondary" />
                  )}
                </ListItemIcon>

                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body1" fontWeight={500}>
                        {indicator.name}
                      </Typography>
                      {isSelected && (
                        <Chip
                          icon={<CheckIcon />}
                          label="Active"
                          size="small"
                          color="success"
                          sx={{ height: 20 }}
                        />
                      )}
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {indicator.description}
                      </Typography>
                      <Chip
                        label={indicator.type === 'overlay' ? 'Overlay' : 'Subplot'}
                        size="small"
                        variant="outlined"
                        sx={{ mt: 0.5, height: 18, fontSize: '0.7rem' }}
                      />
                    </Box>
                  }
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>
    );
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          minHeight: 500,
        },
      }}
    >
      <DialogTitle>
        <Typography variant="h6" component="div">
          Add Indicator
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Select an indicator to add to your chart
        </Typography>
      </DialogTitle>

      <DialogContent dividers>
        {/* Search bar */}
        <TextField
          fullWidth
          size="small"
          placeholder="Search indicators..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ mb: 2 }}
        />

        {/* Tabs for filtering by type */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="indicator types">
            <Tab label={`All (${filteredAll.length})`} />
            <Tab label={`Overlay (${filteredOverlay.length})`} />
            <Tab label={`Subplot (${filteredSubplot.length})`} />
          </Tabs>
        </Box>

        {/* Indicator lists */}
        <TabPanel value={tabValue} index={0}>
          {renderIndicatorList(filteredAll)}
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          {renderIndicatorList(filteredOverlay)}
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          {renderIndicatorList(filteredSubplot)}
        </TabPanel>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default IndicatorSelector;
