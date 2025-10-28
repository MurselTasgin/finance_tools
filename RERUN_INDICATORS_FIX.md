# Stock Scan Analysis Rerun - Indicators Selection Fix

## Issue
When clicking "Rerun" on a Stock Scan Analysis job, all parameters (dates, stocks, thresholds) were correctly populated, but the selected indicators/scanners were not being reconstructed in the form.

## Root Cause
The form population logic in `StockScanAnalysisForm` was executing before the available indicators were loaded from the API. When trying to reconstruct scanners from `initialParameters`, it couldn't match indicator IDs because the `availableIndicators` array was still empty.

## Changes Made

### 1. **StockScanAnalysisForm.tsx** - Wait for Indicators to Load
**File:** `frontend/src/components/StockScanAnalysisForm.tsx`  
**Lines:** 127-189

- Added check to ensure indicators are loaded before reconstructing scanners
- If `initialParameters` includes scanner configurations but `availableIndicators` is empty, the useEffect waits
- Added console warnings when indicators can't be found
- Added console logging for debugging scanner reconstruction

**Key Changes:**
```typescript
// Only populate if indicators are loaded (needed for scanner reconstruction)
const needsIndicators = initialParameters.scanner_configs && Object.keys(initialParameters.scanner_configs).length > 0;

if (needsIndicators && availableIndicators.length === 0) {
  // Wait for indicators to load
  return;
}
```

### 2. **AnalysisJobsPanel.tsx** - Fetch Complete Task Details for Rerun
**File:** `frontend/src/components/AnalysisJobsPanel.tsx`  
**Lines:** 254-277

- Modified `handleRerun` to fetch complete task details before showing rerun dialog
- Ensures all scanner configurations and weights are included in parameters
- Falls back to basic job parameters if details can't be fetched

**Key Changes:**
```typescript
const handleRerun = async (job: any) => {
  // Fetch complete task details to ensure we have all parameters
  let enhancedJob = job;
  try {
    const detailsResponse = await analyticsApi.getAnalysisTaskDetails(job.task_id);
    if (detailsResponse?.task_info?.parameters) {
      enhancedJob = {
        ...job,
        parameters: {
          ...job.parameters,
          ...detailsResponse.task_info.parameters,
          // Ensure scanner_configs and weights are included
          scanner_configs: detailsResponse.task_info.parameters.scanner_configs || job.parameters?.scanner_configs,
          weights: detailsResponse.task_info.parameters.weights || job.parameters?.weights,
        }
      };
    }
  } catch (error) {
    console.warn('Could not fetch task details for rerun, using job parameters:', error);
  }
  
  setSelectedJobForRerun(enhancedJob);
  setRerunDialogOpen(true);
};
```

### 3. **AnalysisJobsPanel.tsx** - Added Debug Logging
**File:** `frontend/src/components/AnalysisJobsPanel.tsx`  
**Lines:** 168-173

- Added console logging to verify parameters being passed during rerun
- Logs scanner configurations and weights availability

### 4. **AnalyticsDashboard.tsx** - Added Debug Logging
**File:** `frontend/src/components/AnalyticsDashboard.tsx`  
**Lines:** 157-163

- Added console logging in `handleRerunWithParameters` to debug parameter passing
- Logs analysis type, parameters, and scanner configuration availability

### 5. **AnalysisJobsPanel.tsx** - Enhanced Results View with Complete Parameters
**File:** `frontend/src/components/AnalysisJobsPanel.tsx`  
**Lines:** 267-282

- Modified `handleViewResults` to fetch task details and enrich result data with complete parameters
- Ensures results dialog shows all scanner information correctly

## How It Works Now

1. **User clicks "Rerun" on a job:**
   - System fetches complete task details from the API
   - Ensures all scanner configurations and weights are included in parameters
   - Opens rerun confirmation dialog

2. **User confirms rerun:**
   - Parameters (including complete scanner configs and weights) are passed to `handleRerunWithParameters`
   - User is redirected to Stock Scan Analysis tab (tab 3)

3. **Form population:**
   - Basic fields (symbols, dates, thresholds) are populated immediately
   - Scanner reconstruction waits for indicators to load
   - Once indicators are available, scanners are reconstructed from `scanner_configs` and `weights`
   - Each scanner includes its configuration and weight from the original run

4. **Form display:**
   - All parameters are visible and editable
   - Selected scanners show with their weights and configurations
   - User can modify any parameter before running the analysis

## Benefits

1. **Complete Parameter Restoration:** All original parameters including scanner configurations are preserved
2. **Proper Timing:** Scanner reconstruction waits for indicators to be loaded
3. **Better Debugging:** Console logs help identify issues with parameter passing
4. **Enhanced Data:** Task details are fetched to ensure complete parameter information
5. **Robust Fallbacks:** System gracefully handles cases where complete details can't be fetched

## Testing

To test the fix:
1. Run a Stock Scan Analysis with multiple indicators
2. Wait for it to complete
3. Click "Rerun" in Jobs & History tab
4. Verify that all indicators are selected with their original configurations and weights
5. Check console logs to verify parameters are being passed correctly

