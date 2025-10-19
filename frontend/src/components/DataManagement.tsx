// finance_tools/frontend/src/components/DataManagement.tsx
import React, { useState } from 'react';
import {
  Box,
  Card,
  Typography,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Storage as StorageIcon,
  Download as DownloadIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { databaseApi } from '../services/api';
import { DatabaseStats } from '../types';
import DataStatistics from './DataStatistics';
import DownloadJobs from './DownloadJobs';
import DataDistribution from './DataDistribution';

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
      id={`data-management-tabpanel-${index}`}
      aria-labelledby={`data-management-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export const DataManagement: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const {
    data: stats,
    isLoading: statsLoading,
    error: statsError,
  } = useQuery<DatabaseStats>('databaseStats', databaseApi.getStats, {
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  if (statsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (statsError) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Failed to load data management information. Please try again.
      </Alert>
    );
  }

  return (
    <Box>
      <Box mb={3}>
        <Typography variant="h4" component="h1" gutterBottom>
          Data Management
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Manage data downloads, view statistics, and monitor data distribution
        </Typography>
      </Box>

      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={activeTab}
            onChange={handleTabChange}
            aria-label="data management tabs"
            variant="scrollable"
            scrollButtons="auto"
          >
            <Tab
              icon={<StorageIcon />}
              label="Statistics"
              id="data-management-tab-0"
              aria-controls="data-management-tabpanel-0"
            />
            <Tab
              icon={<DownloadIcon />}
              label="Download Jobs"
              id="data-management-tab-1"
              aria-controls="data-management-tabpanel-1"
            />
            <Tab
              icon={<TimelineIcon />}
              label="Data Distribution"
              id="data-management-tab-2"
              aria-controls="data-management-tabpanel-2"
            />
          </Tabs>
        </Box>

        <TabPanel value={activeTab} index={0}>
          <DataStatistics stats={stats} />
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <DownloadJobs />
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <DataDistribution stats={stats} />
        </TabPanel>
      </Card>
    </Box>
  );
};

export default DataManagement;
