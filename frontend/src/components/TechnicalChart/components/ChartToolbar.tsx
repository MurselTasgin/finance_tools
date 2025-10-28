// TechnicalChart/components/ChartToolbar.tsx
import React from 'react';
import {
  Box,
  IconButton,
  Tooltip,
  ToggleButtonGroup,
  ToggleButton,
  Divider,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import CandlestickChartIcon from '@mui/icons-material/CandlestickChart';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import TimelineIcon from '@mui/icons-material/Timeline';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import HorizontalRuleIcon from '@mui/icons-material/HorizontalRule';
import StraightenIcon from '@mui/icons-material/Straighten';
import ViewWeekIcon from '@mui/icons-material/ViewWeek';
import DeleteSweepIcon from '@mui/icons-material/DeleteSweep';
import { ChartType, DrawingTool } from '../types/chart.types';
import { getColorScheme } from '../utils/colorSchemes';

export interface ChartToolbarProps {
  chartType: ChartType;
  onChartTypeChange: (chartType: ChartType) => void;
  onAddIndicator: () => void;
  activeDrawingTool?: DrawingTool | null;
  onDrawingToolChange?: (tool: DrawingTool | null) => void;
  onClearDrawings?: () => void;
  theme?: 'dark' | 'light';
}

/**
 * Chart Toolbar Component
 *
 * Provides quick access to chart controls and settings
 */
export const ChartToolbar: React.FC<ChartToolbarProps> = ({
  chartType,
  onChartTypeChange,
  onAddIndicator,
  activeDrawingTool = null,
  onDrawingToolChange,
  onClearDrawings,
  theme = 'dark',
}) => {
  const colorScheme = getColorScheme(theme);

  const handleChartTypeChange = (
    event: React.MouseEvent<HTMLElement>,
    newChartType: ChartType | null
  ) => {
    if (newChartType !== null) {
      onChartTypeChange(newChartType);
    }
  };

  const handleDrawingToolChange = (
    event: React.MouseEvent<HTMLElement>,
    newTool: DrawingTool | null
  ) => {
    if (!onDrawingToolChange) return;

    // Allow toggling off when the same tool is selected
    if (newTool === activeDrawingTool) {
      onDrawingToolChange(null);
    } else {
      onDrawingToolChange(newTool);
    }
  };

  return (
    <Box
      sx={{
        position: 'absolute',
        top: 8,
        right: 8,
        zIndex: 100,
        display: 'flex',
        gap: 1,
        alignItems: 'center',
        backgroundColor: `${colorScheme.background}CC`,
        backdropFilter: 'blur(8px)',
        borderRadius: 1,
        padding: 0.5,
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
      }}
    >
      {/* Drawing tool selector */}
      {onDrawingToolChange && (
        <>
          <ToggleButtonGroup
            value={activeDrawingTool}
            exclusive
            onChange={handleDrawingToolChange}
            size="small"
            sx={{
              '& .MuiToggleButton-root': {
                color: colorScheme.text,
                borderColor: colorScheme.grid,
                '&.Mui-selected': {
                  backgroundColor: colorScheme.crosshair,
                  color: colorScheme.background,
                  '&:hover': {
                    backgroundColor: colorScheme.crosshair,
                  },
                },
              },
            }}
          >
            <ToggleButton value="trendline" aria-label="trendline">
              <Tooltip title="Trendline">
                <TrendingUpIcon fontSize="small" />
              </Tooltip>
            </ToggleButton>
            <ToggleButton value="horizontal-line" aria-label="horizontal line">
              <Tooltip title="Horizontal Line">
                <HorizontalRuleIcon fontSize="small" />
              </Tooltip>
            </ToggleButton>
            <ToggleButton value="vertical-line" aria-label="vertical line">
              <Tooltip title="Vertical Line">
                <StraightenIcon fontSize="small" />
              </Tooltip>
            </ToggleButton>
            <ToggleButton value="parallel-channel" aria-label="parallel channel">
              <Tooltip title="Parallel Channel">
                <ViewWeekIcon fontSize="small" />
              </Tooltip>
            </ToggleButton>
          </ToggleButtonGroup>

          <Divider orientation="vertical" flexItem sx={{ mx: 0.5 }} />
        </>
      )}

      {/* Chart Type Selector */}
      <ToggleButtonGroup
        value={chartType}
        exclusive
        onChange={handleChartTypeChange}
        size="small"
        sx={{
          '& .MuiToggleButton-root': {
            color: colorScheme.text,
            borderColor: colorScheme.grid,
            '&.Mui-selected': {
              backgroundColor: colorScheme.crosshair,
              color: colorScheme.background,
              '&:hover': {
                backgroundColor: colorScheme.crosshair,
              },
            },
          },
        }}
      >
        <ToggleButton value="candlestick" aria-label="candlestick chart">
          <Tooltip title="Candlestick">
            <CandlestickChartIcon fontSize="small" />
          </Tooltip>
        </ToggleButton>
        <ToggleButton value="line" aria-label="line chart">
          <Tooltip title="Line Chart">
            <ShowChartIcon fontSize="small" />
          </Tooltip>
        </ToggleButton>
        <ToggleButton value="area" aria-label="area chart">
          <Tooltip title="Area Chart">
            <TimelineIcon fontSize="small" />
          </Tooltip>
        </ToggleButton>
      </ToggleButtonGroup>

      <Divider orientation="vertical" flexItem sx={{ mx: 0.5 }} />

      {/* Clear drawings */}
      {onClearDrawings && (
        <>
          <Tooltip title="Clear All Drawings">
            <span>
              <IconButton
                onClick={onClearDrawings}
                size="small"
                sx={{
                  color: colorScheme.text,
                  '&:hover': {
                    backgroundColor: `${colorScheme.crosshair}30`,
                  },
                }}
              >
                <DeleteSweepIcon fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>

          <Divider orientation="vertical" flexItem sx={{ mx: 0.5 }} />
        </>
      )}

      {/* Add Indicator Button */}
      <Tooltip title="Add Indicator">
        <IconButton
          onClick={onAddIndicator}
          size="small"
          sx={{
            color: colorScheme.text,
            '&:hover': {
              backgroundColor: `${colorScheme.crosshair}30`,
            },
          }}
        >
          <AddIcon fontSize="small" />
        </IconButton>
      </Tooltip>
    </Box>
  );
};

export default ChartToolbar;
