// TechnicalChart/components/AssetHeader.tsx
import React from 'react';
import { Box, Typography, IconButton, Tooltip } from '@mui/material';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import { AssetType } from '../types/chart.types';
import { getColorScheme } from '../utils/colorSchemes';

interface AssetHeaderProps {
  assetType: AssetType;
  identifier: string;
  onAssetChange?: () => void;
  theme?: 'dark' | 'light';
}

/**
 * Asset Header Component
 * Displays the ticker/ETF name in the top left with asset selection capability
 */
export const AssetHeader: React.FC<AssetHeaderProps> = ({
  assetType,
  identifier,
  onAssetChange,
  theme = 'dark',
}) => {
  const colorScheme = getColorScheme(theme);
  // Use crosshair color as secondary since ColorScheme doesn't have secondary property
  const secondaryColor = theme === 'dark' ? '#758696' : '#666666';
  
  const assetTypeLabel = assetType === 'stock' ? 'Stock' : 'ETF';
  const displayName = identifier || 'N/A';

  return (
    <Box
      sx={{
        position: 'absolute',
        top: 8,
        left: 8,
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        backgroundColor: `${colorScheme.background}CC`,
        backdropFilter: 'blur(8px)',
        borderRadius: 1,
        padding: '6px 12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
      }}
    >
      <Typography
        variant="body2"
        sx={{
          color: colorScheme.text,
          fontWeight: 600,
          fontSize: '0.875rem',
          fontFamily: 'monospace',
        }}
      >
        {displayName}
      </Typography>
      
      <Typography
        variant="caption"
        sx={{
          color: secondaryColor,
          fontSize: '0.7rem',
          textTransform: 'uppercase',
          opacity: 0.7,
        }}
      >
        {assetTypeLabel}
      </Typography>

      {onAssetChange && (
        <Tooltip title="Change Asset">
          <IconButton
            onClick={onAssetChange}
            size="small"
            sx={{
              color: colorScheme.text,
              padding: '2px',
              marginLeft: 0.5,
              '&:hover': {
                backgroundColor: `${colorScheme.crosshair}30`,
              },
            }}
          >
            <SwapHorizIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      )}
    </Box>
  );
};

export default AssetHeader;

