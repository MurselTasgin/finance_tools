// finance_tools/frontend/src/components/DataExplorer.tsx
import React, { useState, useEffect } from 'react';
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
  IconButton,
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
  Divider,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  BarChart as ChartIcon,
  Clear as ClearIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { dataApi } from '../services/api';
import { FundRecord, FilterOptions, SortOptions, DataExplorerState } from '../types';
import { PlotViewer } from './PlotViewer';
import { FilterDialog } from './FilterDialog';

const PAGE_SIZE_OPTIONS = [25, 50, 100, 200];

export const DataExplorer: React.FC = () => {
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
  const [plotConfig, setPlotConfig] = useState<{ xColumn: string; yColumn: string }>({
    xColumn: 'date',
    yColumn: 'price',
  });

  const {
    data: recordsData,
    isLoading,
    error,
    refetch,
  } = useQuery(
    ['records', state.page + 1, state.pageSize, state.filters, state.sort, state.searchTerm],
    () =>
      dataApi.getRecords(
        state.page + 1,
        state.pageSize,
        state.filters,
        state.sort,
        state.searchTerm
      ),
    {
      keepPreviousData: true,
    }
  );

  const { data: columns } = useQuery('columns', dataApi.getColumns);

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
      const data = await dataApi.getPlotData(plotConfig.xColumn, plotConfig.yColumn, state.filters);
      setPlotData(data);
      setShowPlot(true);
    } catch (error) {
      console.error('Failed to load plot data:', error);
    }
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
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Data Explorer
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<ChartIcon />}
            onClick={handlePlotData}
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
              ) : recordsData?.data.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={columns?.length || 1} align="center">
                    <Typography variant="body2" color="textSecondary">
                      No records found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                recordsData?.data.map((record) => (
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
          <Box mb={2}>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={6}>
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
              <Grid item xs={6}>
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
            </Grid>
          </Box>
          <PlotViewer data={plotData} xColumn={plotConfig.xColumn} yColumn={plotConfig.yColumn} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowPlot(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
