// TechnicalChart/components/PanelResizer.tsx
import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Box } from '@mui/material';
import DragIndicatorIcon from '@mui/icons-material/DragIndicator';
import { getColorScheme } from '../utils/colorSchemes';

export interface PanelResizerProps {
  panelId: string;
  adjacentPanelId: string;
  onResize: (panelId: string, adjacentPanelId: string, deltaPercent: number) => void;
  theme?: 'dark' | 'light';
  containerHeight: number;
}

/**
 * Panel Resizer Component
 *
 * Draggable divider between chart panels that allows resizing
 */
export const PanelResizer: React.FC<PanelResizerProps> = ({
  panelId,
  adjacentPanelId,
  onResize,
  theme = 'dark',
  containerHeight,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const startYRef = useRef<number>(0);
  const colorScheme = getColorScheme(theme);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
    startYRef.current = e.clientY;
  }, []);

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isDragging) return;

      const deltaY = e.clientY - startYRef.current;
      const deltaPercent = (deltaY / containerHeight) * 100;

      if (Math.abs(deltaPercent) > 0.1) {
        // Only update if change is significant
        onResize(panelId, adjacentPanelId, deltaPercent);
        startYRef.current = e.clientY;
      }
    },
    [isDragging, panelId, adjacentPanelId, onResize, containerHeight]
  );

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  // Add global mouse event listeners during drag
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'ns-resize';

      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
        document.body.style.cursor = '';
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  return (
    <Box
      onMouseDown={handleMouseDown}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      sx={{
        position: 'relative',
        width: '100%',
        height: 6,
        cursor: 'ns-resize',
        backgroundColor: isDragging || isHovered
          ? colorScheme.crosshair
          : colorScheme.grid,
        transition: 'background-color 0.2s ease',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: isDragging ? 1000 : 10,
        '&:hover': {
          backgroundColor: colorScheme.crosshair,
        },
      }}
    >
      {/* Drag indicator icon */}
      {(isHovered || isDragging) && (
        <DragIndicatorIcon
          sx={{
            fontSize: 16,
            color: colorScheme.text,
            opacity: 0.6,
          }}
        />
      )}

      {/* Invisible extended hit area for easier grabbing */}
      <Box
        sx={{
          position: 'absolute',
          top: -4,
          left: 0,
          right: 0,
          height: 14,
          cursor: 'ns-resize',
        }}
      />
    </Box>
  );
};

export default PanelResizer;
