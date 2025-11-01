// finance_tools/frontend/src/components/DataExplorer.tsx
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TableSortLabel,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  BarChart as ChartIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { dataApi, stockApi } from '../services/api';
import { FilterOptions, DataExplorerState, PaginatedResponse } from '../types';
import { PlotViewer } from './PlotViewer';
import { FilterDialog } from './FilterDialog';

const PAGE_SIZE_OPTIONS = [25, 50, 100, 200];

export const DataExplorer: React.FC = () => {
  const [dataType, setDataType] = useState<'etf' | 'stock'>('etf');
  
  const [state, setState] = useState<DataExplorerState>({
    page: 0,
    pageSize: 50,
    filters: [],
    sort: null,
    searchTerm: '',
  });

  const [showFilters, setShowFilters] = useState(false);
  const [showPlot, setShowPlot] = useState(false);
  const [plotData, setPlotData] = useState<{ x: string | number; y: number; label?: string }[]>([]);
  const [plotConfig, setPlotConfig] = useState<{ 
    xColumn: string; 
    yColumn: string; 
    fundCode: string;
    startDate: string;
    endDate: string;
  }>({
    xColumn: 'date',
    yColumn: 'price',
    fundCode: '',
    startDate: '',
    endDate: '',
  });

  const {
    data: recordsData,
    isLoading,
    error,
  } = useQuery<PaginatedResponse<any>>(
    ['records', dataType, state.page + 1, state.pageSize, state.filters, state.sort, state.searchTerm],
    () => {
      if (dataType === 'stock') {
        return stockApi.getRecords(
          state.page + 1,
          state.pageSize,
          state.filters,
          state.sort,
          state.searchTerm
        );
      }
      return dataApi.getRecords(
        state.page + 1,
        state.pageSize,
        state.filters,
        state.sort,
        state.searchTerm
      );
    },
    {
      keepPreviousData: true,
    }
  );

  const { data: columns } = useQuery(['columns', dataType], () => {
    if (dataType === 'stock') {
      return stockApi.getColumns();
    }
    return dataApi.getColumns();
  });
  const { data: funds } = useQuery<any[]>(['funds', dataType], async () => {
    if (dataType === 'stock') {
      const response = await stockApi.getSymbols();
      return response.symbols;
    }
    return await dataApi.getFunds();
  });

  const handlePageChange = (event: unknown, newPage: number) => {
    setState(prev => ({ ...prev, page: newPage }));
  };

  const handlePageSizeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setState(prev => ({
      ...prev,
      pageSize: parseInt(event.target.value, 10),
      page: 0,
    }));
  };

  const handleSort = (column: string) => {
    setState(prev => ({
      ...prev,
      sort: prev.sort?.column === column
        ? prev.sort.direction === 'asc'
          ? { column, direction: 'desc' as const }
          : null
        : { column, direction: 'asc' as const },
    }));
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setState(prev => ({ ...prev, searchTerm: event.target.value, page: 0 }));
  };

  const handleFilterAdd = (filter: FilterOptions) => {
    setState(prev => ({
      ...prev,
      filters: [...prev.filters, filter],
      page: 0,
    }));
  };

  const handleFilterRemove = (index: number) => {
    setState(prev => ({
      ...prev,
      filters: prev.filters.filter((_, i) => i !== index),
      page: 0,
    }));
  };

  const handleClearFilters = () => {
    setState(prev => ({
      ...prev,
      filters: [],
      searchTerm: '',
      page: 0,
    }));
  };

  const handlePlotData = async () => {
    try {
      const data = await dataApi.getPlotData(
        plotConfig.xColumn, 
        plotConfig.yColumn, 
        plotConfig.fundCode || undefined,
        plotConfig.startDate || undefined,
        plotConfig.endDate || undefined,
        state.filters
      );
      setPlotData(data);
      setShowPlot(true);
    } catch (error) {
      console.error('Failed to load plot data:', error);
    }
  };

  const handlePlotDialogOpen = () => {
    setShowPlot(true);
    // Load initial plot data
    handlePlotData();
  };

  const formatValue = (value: any, column: string) => {
    if (value === null || value === undefined) return '-';
    
    if (column === 'date' || column === 'created_at') {
      try {
        return new Date(value).toLocaleDateString();
      } catch {
        return value;
      }
    }
    
    if (typeof value === 'number') {
      return new Intl.NumberFormat().format(value);
    }
    
    return value.toString();
  };

  const getSortDirection = (column: string): 'asc' | 'desc' | undefined => {
    if (state.sort?.column === column) {
      return state.sort.direction;
    }
    return undefined;
  };

  const numericColumns = columns?.filter(col => 
    ['price', 'market_cap', 'number_of_investors', 'number_of_shares'].includes(col)
  ) || [];

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Failed to load data. Please try again.
      </Alert>
    );
  }

  return (
    <Box>
      {/* Tabs for ETF/Stock selection */}
      <Paper sx={{ mb: 3 }}>
        <Tabs 
          value={dataType === 'etf' ? 0 : 1} 
          onChange={(e, value) => setDataType(value === 0 ? 'etf' : 'stock')}
          indicatorColor="primary"
          textColor="primary"
        >
          <Tab label="ETFs" />
          <Tab label="Stocks" />
        </Tabs>
      </Paper>

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          {dataType === 'etf' ? 'ETF' : 'Stock'} Data Explorer
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<ChartIcon />}
            onClick={handlePlotDialogOpen}
            disabled={numericColumns.length < 2}
            sx={{ mr: 1 }}
          >
            Plot Data
          </Button>
          <Button
            variant="outlined"
            startIcon={<FilterIcon />}
            onClick={() => setShowFilters(true)}
            sx={{ mr: 1 }}
          >
            Filters ({state.filters.length})
          </Button>
          <Button
            variant="outlined"
            startIcon={<ClearIcon />}
            onClick={handleClearFilters}
            disabled={state.filters.length === 0 && !state.searchTerm}
          >
            Clear All
          </Button>
        </Box>
      </Box>

      {/* Search and Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder="Search records..."
                value={state.searchTerm}
                onChange={handleSearchChange}
                InputProps={{
                  startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Box display="flex" gap={1} flexWrap="wrap">
                {state.filters.map((filter, index) => (
                  <Chip
                    key={index}
                    label={`${filter.column} ${filter.operator} ${filter.value}`}
                    onDelete={() => handleFilterRemove(index)}
                    color="primary"
                    variant="outlined"
                    size="small"
                  />
                ))}
                {state.searchTerm && (
                  <Chip
                    label={`Search: ${state.searchTerm}`}
                    onDelete={() => setState(prev => ({ ...prev, searchTerm: '' }))}
                    color="secondary"
                    variant="outlined"
                    size="small"
                  />
                )}
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Data Table */}
      <Card>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                {columns?.map((column) => (
                  <TableCell key={column}>
                    <TableSortLabel
                      active={state.sort?.column === column}
                      direction={getSortDirection(column)}
                      onClick={() => handleSort(column)}
                    >
                      {column.replace(/_/g, ' ').toUpperCase()}
                    </TableSortLabel>
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={columns?.length || 1} align="center">
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : !recordsData ? (
                <TableRow>
                  <TableCell colSpan={columns?.length || 1} align="center">
                    <Typography variant="body2" color="textSecondary">
                      Loading data...
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : !recordsData.data || recordsData.data.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={columns?.length || 1} align="center">
                    <Typography variant="body2" color="textSecondary">
                      No records found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                recordsData.data.map((record: any) => (
                  <TableRow key={record.id} hover>
                    {columns?.map((column) => (
                      <TableCell key={column}>
                        {formatValue((record as any)[column], column)}
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        
        <TablePagination
          rowsPerPageOptions={PAGE_SIZE_OPTIONS}
          component="div"
          count={recordsData?.total || 0}
          rowsPerPage={state.pageSize}
          page={state.page}
          onPageChange={handlePageChange}
          onRowsPerPageChange={handlePageSizeChange}
        />
      </Card>

      {/* Filter Dialog */}
      <FilterDialog
        open={showFilters}
        onClose={() => setShowFilters(false)}
        onAddFilter={handleFilterAdd}
        columns={columns || []}
      />

      {/* Plot Dialog */}
      <Dialog open={showPlot} onClose={() => setShowPlot(false)} maxWidth="lg" fullWidth>
        <DialogTitle>Data Visualization</DialogTitle>
        <DialogContent>
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <Box mb={2}>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} md={3}>
                  <FormControl fullWidth>
                    <InputLabel>Fund</InputLabel>
                    <Select
                      value={plotConfig.fundCode}
                      onChange={(e) => setPlotConfig(prev => ({ ...prev, fundCode: e.target.value }))}
                      displayEmpty
                    >
                      <MenuItem value="">
                        <em>All Funds</em>
                      </MenuItem>
                      {funds?.map((fund: any) => (
                        <MenuItem key={dataType === 'stock' ? fund.symbol : fund.code} value={dataType === 'stock' ? fund.symbol : fund.code}>
                          {dataType === 'stock' ? fund.symbol : `${fund.code} - ${fund.title}`}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={3}>
                  <FormControl fullWidth>
                    <InputLabel>X Axis</InputLabel>
                    <Select
                      value={plotConfig.xColumn}
                      onChange={(e) => setPlotConfig(prev => ({ ...prev, xColumn: e.target.value }))}
                    >
                      {columns?.map((col) => (
                        <MenuItem key={col} value={col}>
                          {col.replace(/_/g, ' ').toUpperCase()}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={3}>
                  <FormControl fullWidth>
                    <InputLabel>Y Axis</InputLabel>
                    <Select
                      value={plotConfig.yColumn}
                      onChange={(e) => setPlotConfig(prev => ({ ...prev, yColumn: e.target.value }))}
                    >
                      {numericColumns.map((col) => (
                        <MenuItem key={col} value={col}>
                          {col.replace(/_/g, ' ').toUpperCase()}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Box display="flex" justifyContent="center" alignItems="center" height="100%">
                    <Button
                      variant="contained"
                      onClick={handlePlotData}
                      startIcon={<ChartIcon />}
                      disabled={!plotConfig.xColumn || !plotConfig.yColumn}
                      fullWidth
                    >
                      Update Plot
                    </Button>
                  </Box>
                </Grid>
              </Grid>
              
              <Box mt={2}>
                <Typography variant="h6" gutterBottom>
                  Date Range (Optional)
                </Typography>
                <Grid container spacing={2} alignItems="center">
                  <Grid item xs={12} md={6}>
                    <DatePicker
                      label="Start Date"
                      value={plotConfig.startDate ? new Date(plotConfig.startDate) : null}
                      onChange={(date) => setPlotConfig(prev => ({ 
                        ...prev, 
                        startDate: date ? date.toISOString().split('T')[0] : '' 
                      }))}
                      slotProps={{
                        textField: {
                          fullWidth: true
                        }
                      }}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <DatePicker
                      label="End Date"
                      value={plotConfig.endDate ? new Date(plotConfig.endDate) : null}
                      onChange={(date) => setPlotConfig(prev => ({ 
                        ...prev, 
                        endDate: date ? date.toISOString().split('T')[0] : '' 
                      }))}
                      slotProps={{
                        textField: {
                          fullWidth: true
                        }
                      }}
                    />
                  </Grid>
                </Grid>
                <Box mt={1}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setPlotConfig(prev => ({ 
                      ...prev, 
                      startDate: '', 
                      endDate: '' 
                    }))}
                  >
                    Clear Date Range
                  </Button>
                </Box>
              </Box>
            </Box>
          </LocalizationProvider>
          
          <PlotViewer 
            data={plotData} 
            xColumn={plotConfig.xColumn} 
            yColumn={plotConfig.yColumn}
            fundCode={plotConfig.fundCode}
             fundTitle={dataType === 'stock' ? funds?.find((f: any) => f.symbol === plotConfig.fundCode)?.symbol : funds?.find((f: any) => f.code === plotConfig.fundCode)?.title}
            startDate={plotConfig.startDate}
            endDate={plotConfig.endDate}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowPlot(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
