// frontend/src/components/UnifiedScanAnalysisPanel.tsx
import React, { useEffect, useMemo, useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  ToggleButtonGroup,
  ToggleButton,
  Alert,
  Divider,
} from '@mui/material';
import { ETFScanAnalysisForm } from './ETFScanAnalysisForm';
import { StockScanAnalysisForm } from './StockScanAnalysisForm';

type AssetType = 'etf' | 'stock';

interface UnifiedScanAnalysisPanelProps {
  onRunAnalysis: (analysisType: string, analysisName: string, parameters: any) => void;
  runningAnalysis?: string | null;
  rerunData?: {
    assetType: AssetType;
    parameters: any;
  } | null;
  onRerunConsumed?: () => void;
}

export const UnifiedScanAnalysisPanel: React.FC<UnifiedScanAnalysisPanelProps> = ({
  onRunAnalysis,
  runningAnalysis,
  rerunData,
  onRerunConsumed,
}) => {
  const [assetType, setAssetType] = useState<AssetType>(rerunData?.assetType ?? 'etf');

  useEffect(() => {
    if (rerunData) {
      setAssetType(rerunData.assetType);
    }
  }, [rerunData]);

  const isRunningEtf = runningAnalysis === 'etf_scan';
  const isRunningStock = runningAnalysis === 'stock_scan';

  const etfInitialParameters = useMemo(
    () => (rerunData?.assetType === 'etf' ? rerunData.parameters : undefined),
    [rerunData]
  );

  const stockInitialParameters = useMemo(
    () => (rerunData?.assetType === 'stock' ? rerunData.parameters : undefined),
    [rerunData]
  );

  const handleParametersUsed = () => {
    onRerunConsumed?.();
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Unified Scan Analysis
        </Typography>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Choose between ETF and Stock scanners, configure the indicator weights and parameters,
          and run a unified scan analysis. Results will appear in the shared results panel and can
          be re-run directly from the results viewer.
        </Typography>

        <ToggleButtonGroup
          color="primary"
          exclusive
          value={assetType}
          onChange={(_, value) => {
            if (value) {
              setAssetType(value);
            }
          }}
          sx={{ mb: 2 }}
        >
          <ToggleButton value="etf">ETF Scan</ToggleButton>
          <ToggleButton value="stock">Stock Scan</ToggleButton>
        </ToggleButtonGroup>

        <Divider sx={{ mb: 3 }} />

        {assetType === 'etf' ? (
          <ETFScanAnalysisForm
            onRunAnalysis={(parameters) => onRunAnalysis('etf_scan', 'ETF Scan Analysis', parameters)}
            running={isRunningEtf}
            initialParameters={etfInitialParameters}
            onParametersUsed={handleParametersUsed}
          />
        ) : (
          <StockScanAnalysisForm
            onRunAnalysis={(parameters) => onRunAnalysis('stock_scan', 'Stock Scan Analysis', parameters)}
            running={isRunningStock}
            initialParameters={stockInitialParameters}
            onParametersUsed={handleParametersUsed}
          />
        )}

        {(isRunningEtf || isRunningStock) && (
          <Alert severity="info" sx={{ mt: 3 }}>
            Scan analysis in progress… Check the Jobs &amp; History tab for real-time updates.
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default UnifiedScanAnalysisPanel;
