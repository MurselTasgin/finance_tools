// TechnicalChart/components/PriceInfoOverlay.tsx
import React, { useEffect, useState, useRef } from 'react';
import { Box, Typography } from '@mui/material';
import { createPortal } from 'react-dom';
import { CrosshairData, ProcessedChartData, AssetType } from '../types/chart.types';
import { formatPrice, formatVolume } from '../utils/chartHelpers';

interface PriceInfoOverlayProps {
  crosshairData: CrosshairData | null;
  data: ProcessedChartData | null;
  visible: boolean;
  assetType: AssetType;
  theme?: 'dark' | 'light';
}

/**
 * Floating price info overlay that follows the mouse cursor
 * Displays current price, % change, and previous price
 */
export const PriceInfoOverlay: React.FC<PriceInfoOverlayProps> = ({
  crosshairData,
  data,
  visible,
  assetType,
  theme = 'dark',
}) => {
  const [mousePosition, setMousePosition] = useState<{ x: number; y: number } | null>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const [offset, setOffset] = useState({ x: 15, y: 15 });
  const lastMousePositionRef = useRef<{ x: number; y: number } | null>(null);
  const lastCrosshairDataRef = useRef<CrosshairData | null>(null);
  const [showOverlay, setShowOverlay] = useState(false);
  const hideTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Keep track of last valid crosshair data and show overlay persistently
  useEffect(() => {
    if (crosshairData) {
      lastCrosshairDataRef.current = crosshairData;
      setShowOverlay(true);
      // Clear any pending hide timeout
      if (hideTimeoutRef.current) {
        clearTimeout(hideTimeoutRef.current);
        hideTimeoutRef.current = null;
      }
    } else if (lastCrosshairDataRef.current && showOverlay) {
      // When crosshairData becomes null, keep showing until mouse leaves chart area
      // Don't auto-hide - only hide when explicitly told to (via visible prop)
      // This prevents flickering
      if (hideTimeoutRef.current) {
        clearTimeout(hideTimeoutRef.current);
        hideTimeoutRef.current = null;
      }
    }

    return () => {
      if (hideTimeoutRef.current) {
        clearTimeout(hideTimeoutRef.current);
      }
    };
  }, [crosshairData, showOverlay]);

  // Track mouse movement globally to follow cursor
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const newPos = { x: e.clientX, y: e.clientY };
      setMousePosition(newPos);
      lastMousePositionRef.current = newPos;
      
      // Keep overlay visible as long as we have crosshair data or last known data
      if (crosshairData || lastCrosshairDataRef.current) {
        setShowOverlay(true);
        if (hideTimeoutRef.current) {
          clearTimeout(hideTimeoutRef.current);
          hideTimeoutRef.current = null;
        }
      }
      
      // Update offset calculation when mouse moves
      requestAnimationFrame(() => {
        if (overlayRef.current && visible && (crosshairData || lastCrosshairDataRef.current)) {
          const rect = overlayRef.current.getBoundingClientRect();
          const windowWidth = window.innerWidth;
          const windowHeight = window.innerHeight;
          
          // Position to the right and below cursor by default
          let xOffset = 15;
          let yOffset = 15;
          
          // If box would overflow right edge, position to the left
          if (e.clientX + rect.width + 15 > windowWidth) {
            xOffset = -rect.width - 15;
          }
          
          // If box would overflow bottom edge, position above
          if (e.clientY + rect.height + 15 > windowHeight) {
            yOffset = -rect.height - 15;
          }
          
          setOffset({ x: xOffset, y: yOffset });
        }
      });
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      if (hideTimeoutRef.current) {
        clearTimeout(hideTimeoutRef.current);
      }
    };
  }, [visible, crosshairData]);

  // Calculate price change and percentage
  // Use current or last crosshair data
  const activeCrosshairData = crosshairData || lastCrosshairDataRef.current;
  const priceInfo = React.useMemo(() => {
    if (!activeCrosshairData || !data || !activeCrosshairData.close) {
      return null;
    }

    const currentPrice = activeCrosshairData.close;
    
    // Find the previous data point to calculate change
    let previousPrice: number | null = null;
    const currentTime = activeCrosshairData.time;
    const timeValue = typeof currentTime === 'number' ? currentTime : new Date(currentTime as string).getTime() / 1000;
    
    // Find index of current point in ohlcv
    let currentIndex = -1;
    data.ohlcv.forEach((point, index) => {
      const pointTime = typeof point.time === 'number' ? point.time : new Date(point.time as string).getTime() / 1000;
      if (Math.abs(pointTime - timeValue) < 3600) { // Within 1 hour
        currentIndex = index;
      }
    });

    // Get previous price if we found current index and there's a previous point
    if (currentIndex > 0 && currentIndex < data.ohlcv.length) {
      previousPrice = data.ohlcv[currentIndex - 1].close;
    } else if (data.ohlcv.length > 0) {
      // Fallback: use the first data point as previous
      previousPrice = data.ohlcv[0].close;
    }

    if (previousPrice === null || previousPrice === undefined) {
      return {
        currentPrice,
        change: null,
        changePercent: null,
        previousPrice: null,
      };
    }

    const change = currentPrice - previousPrice;
    const changePercent = previousPrice !== 0 ? (change / previousPrice) * 100 : 0;

    return {
      currentPrice,
      change,
      changePercent,
      previousPrice,
    };
  }, [activeCrosshairData, data]);

  const colorScheme = {
    background: theme === 'dark' ? '#1E222D' : '#FFFFFF',
    text: theme === 'dark' ? '#D1D4DC' : '#131722',
    secondary: theme === 'dark' ? '#758696' : '#666666',
    border: theme === 'dark' ? '#2A2E39' : '#E0E0E0',
    positive: theme === 'dark' ? '#26A69A' : '#00A86B',
    negative: theme === 'dark' ? '#EF5350' : '#DC143C',
  };

  // Get volume or number_of_investors
  const volumeInfo = React.useMemo(() => {
    if (!activeCrosshairData || !data) return null;

    if (assetType === 'stock') {
      // For stocks, show volume
      if (activeCrosshairData.volume !== undefined && activeCrosshairData.volume !== null) {
        return {
          label: 'Volume',
          value: activeCrosshairData.volume,
        };
      }
    } else if (assetType === 'etf') {
      // For ETFs, prioritize number_of_investors
      // First try to get from indicators (could be raw or EMA)
      const investorsKey = Object.keys(activeCrosshairData.indicators || {}).find(
        key => {
          const lowerKey = key.toLowerCase();
          return lowerKey === 'number_of_investors' || 
                 lowerKey.startsWith('number_of_investors');
        }
      );
      
      if (investorsKey && activeCrosshairData.indicators[investorsKey] !== undefined) {
        // Prefer raw number_of_investors over EMA if both exist
        const rawKey = Object.keys(activeCrosshairData.indicators || {}).find(
          k => k.toLowerCase() === 'number_of_investors'
        );
        const keyToUse = rawKey || investorsKey;
        
        return {
          label: 'Number of Investors',
          value: activeCrosshairData.indicators[keyToUse],
        };
      }

      // Also try to get from data at current time index
      if (activeCrosshairData.time && data.ohlcv) {
        // Find matching data point - we need to check the raw API data
        // For now, fall back to volume if available
      }

      // Fallback: if we have volume in activeCrosshairData, show it
      if (activeCrosshairData.volume !== undefined && activeCrosshairData.volume !== null) {
        return {
          label: 'Volume',
          value: activeCrosshairData.volume,
        };
      }
    }

    return null;
  }, [activeCrosshairData, data, assetType]);

  // Debug logging
  useEffect(() => {
    if (visible && activeCrosshairData) {
      console.debug('📊 PriceInfoOverlay visibility check:', {
        visible,
        showOverlay,
        hasCrosshairData: !!crosshairData,
        hasLastCrosshairData: !!lastCrosshairDataRef.current,
        hasActiveCrosshairData: !!activeCrosshairData,
        hasData: !!data,
        hasPriceInfo: !!priceInfo,
        currentPrice: priceInfo?.currentPrice,
        crosshairClose: activeCrosshairData?.close,
        mousePosition,
        lastMousePosition: lastMousePositionRef.current,
        displayPosition: mousePosition || lastMousePositionRef.current,
      });
    }
  }, [visible, crosshairData, activeCrosshairData, data, priceInfo, mousePosition, showOverlay]);

  // Always track mouse even if data isn't ready yet (prevents flickering)
  // Only hide if explicitly not visible OR if we have no data at all
  if (!visible) {
    return null;
  }

  // Use last known mouse position if current is null but we have crosshair data
  const displayPosition = mousePosition || lastMousePositionRef.current;
  
  // Render if we have crosshair data (current or last known) and data is available
  // Make showOverlay less strict - if we have data, show it
  if (!activeCrosshairData || !data) {
    return null;
  }

  // Only require displayPosition if we don't have any crosshair data history
  // If we have activeCrosshairData, we can position it even without exact mouse position
  if (!displayPosition && !lastMousePositionRef.current && !activeCrosshairData) {
    return null;
  }

  // If we don't have price info, try to show something anyway using crosshairData directly
  if (!priceInfo || priceInfo.currentPrice === undefined) {
    // Try to use activeCrosshairData.close directly as fallback
    if (activeCrosshairData.close !== undefined) {
      const fallbackContent = (
        <Box
          ref={overlayRef}
          sx={{
            position: 'fixed',
            left: displayPosition ? `${displayPosition.x + offset.x}px` : '50%',
            top: displayPosition ? `${displayPosition.y + offset.y}px` : '50%',
            zIndex: 10000,
            backgroundColor: colorScheme.background,
            border: `1px solid ${colorScheme.border}`,
            borderRadius: 1,
            padding: 1.5,
            minWidth: 200,
            maxWidth: 300,
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            pointerEvents: 'none',
            backdropFilter: 'blur(8px)',
            transition: 'none',
            transform: 'translateZ(0)',
            isolation: 'isolate',
            display: 'block',
            opacity: 1,
            visibility: 'visible',
          }}
        >
          <Typography variant="caption" sx={{ color: colorScheme.secondary, fontSize: '0.7rem' }}>
            {activeCrosshairData.time ? (typeof activeCrosshairData.time === 'number' 
              ? new Date(activeCrosshairData.time * 1000).toLocaleString()
              : new Date(activeCrosshairData.time as string).toLocaleString()) : 'N/A'}
          </Typography>
          <Typography variant="body2" sx={{ color: colorScheme.text, fontSize: '1rem', fontWeight: 600 }}>
            {formatPrice(activeCrosshairData.close)}
          </Typography>
        </Box>
      );
      
      if (typeof window !== 'undefined' && typeof document !== 'undefined') {
        return createPortal(fallbackContent, document.body);
      }
      return fallbackContent;
    }
    return null;
  }

  const isPositive = priceInfo.change !== null && priceInfo.change >= 0;
  const changeColor = priceInfo.change === null ? colorScheme.secondary : (isPositive ? colorScheme.positive : colorScheme.negative);

  // Render in a portal to ensure it's above everything
  // Force visibility with explicit display and opacity
  const overlayContent = (
    <Box
      ref={overlayRef}
      sx={{
        position: 'fixed',
        left: displayPosition ? `${displayPosition.x + offset.x}px` : '50%',
        top: displayPosition ? `${displayPosition.y + offset.y}px` : '50%',
        zIndex: 99999, // Extremely high z-index to ensure it's on top of everything (including MUI dialogs)
        backgroundColor: colorScheme.background,
        border: `1px solid ${colorScheme.border}`,
        borderRadius: 1,
        padding: 1.5,
        minWidth: 200,
        maxWidth: 300,
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        pointerEvents: 'none',
        backdropFilter: 'blur(8px)',
        transition: 'none',
        transform: 'translateZ(0)',
        isolation: 'isolate', // Create new stacking context
        // Force visibility - ensure these properties can't be overridden
        display: 'block',
        opacity: 1,
        visibility: 'visible',
      }}
    >
      {/* Time/Date */}
      <Typography
        variant="caption"
        sx={{
          color: colorScheme.secondary,
          fontSize: '0.7rem',
          display: 'block',
          mb: 1,
          fontWeight: 500,
        }}
      >
        {activeCrosshairData.time && typeof activeCrosshairData.time === 'number'
          ? new Date(activeCrosshairData.time * 1000).toLocaleString()
          : activeCrosshairData.time
          ? new Date(activeCrosshairData.time as string).toLocaleString()
          : 'N/A'}
      </Typography>

      {/* Current Price */}
      <Typography
        variant="body2"
        sx={{
          color: colorScheme.text,
          fontSize: '1rem',
          fontWeight: 600,
          display: 'block',
          mb: 0.5,
        }}
      >
        {formatPrice(priceInfo.currentPrice)}
      </Typography>

      {/* Change and Previous Price */}
      {priceInfo.change !== null && priceInfo.previousPrice !== null && (
        <>
          <Typography
            variant="caption"
            sx={{
              color: changeColor,
              fontSize: '0.85rem',
              fontWeight: 600,
              display: 'block',
              mb: 0.25,
            }}
          >
            {isPositive ? '+' : ''}{formatPrice(priceInfo.change)} ({isPositive ? '+' : ''}{priceInfo.changePercent.toFixed(2)}%)
          </Typography>

          <Typography
            variant="caption"
            sx={{
              color: colorScheme.secondary,
              fontSize: '0.75rem',
              display: 'block',
              mb: 0.5,
            }}
          >
            Previous: {formatPrice(priceInfo.previousPrice)}
          </Typography>
        </>
      )}

      {/* Volume or Number of Investors */}
      {volumeInfo && (
        <Typography
          variant="caption"
          sx={{
            color: colorScheme.secondary,
            fontSize: '0.75rem',
            display: 'block',
            borderTop: `1px solid ${colorScheme.border}`,
            pt: 0.5,
            mt: 0.5,
          }}
        >
          <strong>{volumeInfo.label}:</strong>{' '}
          <span style={{ color: colorScheme.text }}>
            {assetType === 'stock' 
              ? formatVolume(volumeInfo.value)
              : volumeInfo.value.toLocaleString()}
          </span>
        </Typography>
      )}
    </Box>
  );

  // Use portal to render at document body level, ensuring it's above all other content
  // Always use portal to avoid any parent container clipping
  if (typeof window !== 'undefined' && typeof document !== 'undefined') {
    const portalTarget = document.body;
    if (portalTarget) {
      return createPortal(overlayContent, portalTarget);
    }
  }
  
  // Fallback if portal isn't available (shouldn't happen in browser)
  return overlayContent;
};

export default PriceInfoOverlay;

