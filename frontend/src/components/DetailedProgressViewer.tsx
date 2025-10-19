// finance_tools/frontend/src/components/DetailedProgressViewer.tsx
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Alert,
  IconButton,
  Tooltip,
  Collapse,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Schedule as ScheduleIcon,
  Storage as StorageIcon,
  Timeline as TimelineIcon,
  AccountBalance as FundIcon,
} from '@mui/icons-material';
import { DownloadProgress } from '../types';
import { format } from 'date-fns';

interface DetailedProgressViewerProps {
  progress: DownloadProgress;
}

const DetailedProgressViewer: React.FC<DetailedProgressViewerProps> = ({ progress }) => {
  const [showLogs, setShowLogs] = useState(false);
  const [showFundDetails, setShowFundDetails] = useState(false);

  const getMessageIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircleIcon color="success" fontSize="small" />;
      case 'warning':
        return <WarningIcon color="warning" fontSize="small" />;
      case 'error':
        return <ErrorIcon color="error" fontSize="small" />;
      default:
        return <InfoIcon color="info" fontSize="small" />;
    }
  };

  const getFundStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon color="success" fontSize="small" />;
      case 'no_data':
        return <WarningIcon color="warning" fontSize="small" />;
      case 'error':
        return <ErrorIcon color="error" fontSize="small" />;
      default:
        return <InfoIcon color="info" fontSize="small" />;
    }
  };

  const getFundStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'success';
      case 'no_data':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatTime = (timestamp: string) => {
    try {
      return format(new Date(timestamp), 'HH:mm:ss');
    } catch {
      return 'Invalid time';
    }
  };

  const totalFunds = progress.fund_progress ? Object.keys(progress.fund_progress).length : 0;
  const successfulFunds = progress.fund_progress 
    ? Object.values(progress.fund_progress).filter(fund => fund.status === 'success').length 
    : 0;
  const errorFunds = progress.fund_progress 
    ? Object.values(progress.fund_progress).filter(fund => fund.status === 'error').length 
    : 0;
  const noDataFunds = progress.fund_progress 
    ? Object.values(progress.fund_progress).filter(fund => fund.status === 'no_data').length 
    : 0;
  
  // Calculate total records from fund progress
  const totalRecordsFromFunds = progress.fund_progress 
    ? Object.values(progress.fund_progress).reduce((sum, fund) => sum + (fund.rows || 0), 0)
    : 0;

  return (
    <Box>
      {/* Chunk Information */}
      {progress.current_chunk_info && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <TimelineIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6">
                Current Chunk Progress
              </Typography>
            </Box>
            
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Date Range
                </Typography>
                <Typography variant="body1">
                  {progress.current_chunk_info.start_date} to {progress.current_chunk_info.end_date}
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Chunk Progress
                </Typography>
                <Box display="flex" alignItems="center" gap={1}>
                  <Typography variant="body1">
                    {progress.current_chunk_info.chunk_number} / {progress.current_chunk_info.total_chunks}
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={(progress.current_chunk_info.chunk_number / progress.current_chunk_info.total_chunks) * 100}
                    sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                  />
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Fund Progress Summary */}
      {progress.fund_progress && Object.keys(progress.fund_progress).length > 0 && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
              <Box display="flex" alignItems="center">
                <FundIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">
                  Fund Progress Summary
                </Typography>
              </Box>
              <IconButton
                onClick={() => setShowFundDetails(!showFundDetails)}
                size="small"
              >
                {showFundDetails ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            </Box>

            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={6} sm={2}>
                <Box textAlign="center">
                  <Typography variant="h6" color="primary">
                    {totalFunds}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Total Funds
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={2}>
                <Box textAlign="center">
                  <Typography variant="h6" color="success.main">
                    {successfulFunds}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Successful
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={2}>
                <Box textAlign="center">
                  <Typography variant="h6" color="warning.main">
                    {noDataFunds}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    No Data
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={2}>
                <Box textAlign="center">
                  <Typography variant="h6" color="error.main">
                    {errorFunds}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Errors
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Box textAlign="center">
                  <Typography variant="h6" color="info.main">
                    {totalRecordsFromFunds.toLocaleString()}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Records Downloaded
                  </Typography>
                </Box>
              </Grid>
            </Grid>

            <Collapse in={showFundDetails}>
              <Divider sx={{ mb: 2 }} />
              <List dense>
                {Object.entries(progress.fund_progress).map(([fundName, fundData]) => (
                  <ListItem key={fundName} sx={{ py: 0.5 }}>
                    <ListItemIcon>
                      {getFundStatusIcon(fundData.status)}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="body2" fontWeight="medium">
                            {fundName}
                          </Typography>
                          <Chip
                            label={fundData.status}
                            color={getFundStatusColor(fundData.status) as any}
                            size="small"
                          />
                          {fundData.rows > 0 && (
                            <Typography variant="caption" color="textSecondary">
                              ({fundData.rows} rows)
                            </Typography>
                          )}
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="caption" color="textSecondary">
                            {formatTime(fundData.timestamp)}
                          </Typography>
                          {fundData.error && (
                            <Typography variant="caption" color="error" display="block">
                              Error: {fundData.error}
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </Collapse>
          </CardContent>
        </Card>
      )}

      {/* Detailed Messages Log */}
      {progress.detailed_messages && progress.detailed_messages.length > 0 && (
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
            <Box display="flex" alignItems="center">
              <StorageIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6">
                Downloaded Records Log
              </Typography>
            </Box>
              <IconButton
                onClick={() => setShowLogs(!showLogs)}
                size="small"
              >
                {showLogs ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            </Box>

            <Collapse in={showLogs}>
              <Box
                sx={{
                  maxHeight: 300,
                  overflowY: 'auto',
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 1,
                  p: 1,
                }}
              >
                <List dense>
                  {(() => {
                    const filteredMessages = progress.detailed_messages
                      .filter(message => 
                        message.type === 'success' && message.message.includes('rows') ||
                        message.type === 'error' && message.message.includes('Error fetching data') ||
                        message.type === 'warning' && message.message.includes('No data found')
                      )
                      .slice(-20);
                    
                    if (filteredMessages.length === 0) {
                      return (
                        <ListItem>
                          <ListItemIcon>
                            <WarningIcon color="warning" fontSize="small" />
                          </ListItemIcon>
                          <ListItemText
                            primary="No downloaded records yet..."
                            secondary="Waiting for data to be fetched..."
                          />
                        </ListItem>
                      );
                    }
                    
                    return filteredMessages.map((message, index) => (
                      <ListItem key={index} sx={{ py: 0.5, px: 0 }}>
                        <ListItemIcon sx={{ minWidth: 32 }}>
                          {getMessageIcon(message.type)}
                        </ListItemIcon>
                        <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography 
                              variant="body2" 
                              sx={{ 
                                flexGrow: 1,
                                color: message.type === 'error' ? 'error.main' : 
                                       message.type === 'warning' ? 'warning.main' :
                                       message.type === 'success' ? 'success.main' : 'text.primary'
                              }}
                            >
                              {message.message}
                            </Typography>
                            <Typography variant="caption" color="textSecondary">
                              {formatTime(message.timestamp)}
                            </Typography>
                          </Box>
                        }
                        secondary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography variant="caption" color="textSecondary">
                              Chunk {message.chunk} • {message.progress}%
                            </Typography>
                            {message.type === 'success' && message.message.includes('rows') && (
                              <Chip 
                                label="Data" 
                                color="success" 
                                size="small" 
                                sx={{ height: 16, fontSize: '0.7rem' }}
                              />
                            )}
                            {message.type === 'error' && (
                              <Chip 
                                label="Error" 
                                color="error" 
                                size="small" 
                                sx={{ height: 16, fontSize: '0.7rem' }}
                              />
                            )}
                            {message.type === 'warning' && (
                              <Chip 
                                label="Warning" 
                                color="warning" 
                                size="small" 
                                sx={{ height: 16, fontSize: '0.7rem' }}
                              />
                            )}
                          </Box>
                        }
                      />
                    </ListItem>
                  ));
                  })()}
                </List>
              </Box>
            </Collapse>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default DetailedProgressViewer;
