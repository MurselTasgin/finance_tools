# finance_tools/etfs/analysis/scanner.py
from __future__ import annotations

from typing import List, Dict, Optional, Any
import pandas as pd

from ...logging import get_logger
from .indicators.registry import registry
from .indicators.base import IndicatorConfig
from .scanner_types import EtfScanCriteria, EtfScanResult, EtfSuggestion


class EtfScanner:
    """Runs ETF scans using plugin-based indicators"""
    
    def __init__(self) -> None:
        self.logger = get_logger("etf_scanner")
    
    def scan(self, code_to_df: Dict[str, pd.DataFrame], criteria: EtfScanCriteria, scanner_configs: Optional[Dict[str, Any]] = None) -> List[EtfScanResult]:
        self.logger.info(f"🔍 Starting ETF scan for {len(code_to_df)} codes with column: {criteria.column}")
        results: List[EtfScanResult] = []
        
        for code, df in code_to_df.items():
            self.logger.info(f"🔍 Processing {code}")
            if df is None or df.empty:
                self.logger.warning(f"⚠️ Skipping {code} - DataFrame is empty")
                continue
            
            if criteria.column not in df.columns:
                self.logger.warning(f"⚠️ Skipping {code} - Column '{criteria.column}' not found in DataFrame")
                continue
            
            # Build indicator configurations from criteria and custom configs
            indicator_configs = self._build_indicator_configs(criteria, scanner_configs)
            
            # Enrich DataFrame with all indicators
            enriched = df.copy()
            indicators_snapshot = {}
            indicator_details = {}  # Store per-indicator details
            
            for indicator_id, config in indicator_configs.items():
                indicator = registry.get(indicator_id)
                if indicator is None:
                    self.logger.warning(f"⚠️ Unknown indicator: {indicator_id}")
                    continue
                
                # Calculate indicator
                try:
                    enriched = indicator.calculate(enriched, criteria.column, config)
                    
                    # Get snapshot
                    snapshot = indicator.get_snapshot(enriched, criteria.column, config)
                    indicators_snapshot.update(snapshot.values)
                    
                    # Store detailed info for this indicator
                    indicator_details[indicator_id] = {
                        "name": indicator.get_name(),
                        "id": indicator.get_id(),
                        "values": snapshot.values,
                    }
                except Exception as e:
                    self.logger.error(f"Error calculating {indicator_id}: {e}")
                    continue
            
            # Derive suggestion and score from all indicators (with per-indicator details)
            suggestion, score, components, indicator_details_full = self._derive_suggestion(enriched, criteria, indicator_configs, indicator_details)
            
            results.append(
                EtfScanResult(
                    code=code,
                    timestamp=pd.to_datetime(enriched.iloc[-1]["date"]).to_pydatetime() if "date" in enriched.columns else None,
                    last_value=float(enriched.iloc[-1][criteria.column]) if pd.notnull(enriched.iloc[-1][criteria.column]) else None,
                    suggestion=suggestion,
                    score=score,
                    indicators_snapshot=indicators_snapshot,
                    components=components,
                    indicator_details=indicator_details_full,
                )
            )
        
        # Sort by score
        results.sort(key=lambda r: r.score, reverse=True)
        return results
    
    def _build_indicator_configs(self, criteria: EtfScanCriteria, scanner_configs: Optional[Dict[str, Any]] = None) -> Dict[str, IndicatorConfig]:
        """Build indicator configurations dynamically from criteria and custom configs
        
        Uses the indicator registry to build configs - NO hardcoded indicator logic.
        Custom configs from UI override defaults but don't modify the registry.
        """
        configs = {}
        
        # Get all registered indicators
        all_indicators = registry.get_all()
        
        # For each indicator, check if it has weight > 0
        for indicator_id, indicator in all_indicators.items():
            # Get weight dynamically
            weight_attr = f"w_{indicator_id}"
            weight = getattr(criteria, weight_attr, 0.0)
            
            if weight <= 0:
                continue  # Skip indicators with zero weight
            
            # Get indicator name
            name = indicator.get_name()
            
            # Get parameter schema
            schema = indicator.get_parameter_schema()
            
            # Build parameters: use custom configs if provided, else use schema defaults
            parameters = {}
            if scanner_configs and indicator_id in scanner_configs:
                custom_config = scanner_configs[indicator_id]
                for param_name in schema.keys():
                    # Use custom value if provided, else use schema default
                    parameters[param_name] = custom_config.get(param_name, schema[param_name].get('default', None))
            else:
                # Use schema defaults only
                for param_name, param_schema in schema.items():
                    if 'default' in param_schema:
                        parameters[param_name] = param_schema['default']
            
            # Create config
            configs[indicator_id] = IndicatorConfig(
                name=name,
                parameters=parameters,
                weight=weight
            )
        
        return configs
    
    def _derive_suggestion(self, df: pd.DataFrame, criteria: EtfScanCriteria, indicator_configs: Dict, indicator_details: Dict) -> tuple:
        """Derive suggestion and score by aggregating indicator contributions
        
        Returns:
            Tuple of (suggestion, score, components, enhanced_indicator_details)
        """
        reasons = []
        components = {}
        total_score = 0.0
        enhanced_details = {}
        
        # Get explanations and scores from each indicator
        for indicator_id, config in indicator_configs.items():
            indicator = registry.get(indicator_id)
            if indicator is None:
                continue
            
            # Get explanation
            indicator_reasons = []
            try:
                explanation = indicator.explain(df, criteria.column, config)
                indicator_reasons = explanation
                reasons.extend(explanation)
                reasons.append("")  # Blank line between indicators
            except Exception as e:
                self.logger.error(f"Error explaining {indicator_id}: {e}")
            
            # Get score
            try:
                score_obj = indicator.get_score(df, criteria.column, config)
                if score_obj is not None:
                    components[indicator_id] = {
                        'raw': score_obj.raw,
                        'weight': score_obj.weight,
                        'contribution': score_obj.contribution
                    }
                    total_score += score_obj.contribution
                    
                    # Enhance indicator details with scoring info
                    enhanced_details[indicator_id] = {
                        "name": indicator_details.get(indicator_id, {}).get("name", indicator.get_name()),
                        "id": indicator_id,
                        "values": indicator_details.get(indicator_id, {}).get("values", {}),
                        "raw": float(score_obj.raw) if pd.notnull(score_obj.raw) else 0.0,
                        "weight": float(score_obj.weight) if pd.notnull(score_obj.weight) else 0.0,
                        "contribution": float(score_obj.contribution) if pd.notnull(score_obj.contribution) else 0.0,
                        "calculation_details": score_obj.calculation_details if score_obj.calculation_details else [],
                        "reasons": indicator_reasons
                    }
                else:
                    # Even without score, store what we can
                    enhanced_details[indicator_id] = {
                        "name": indicator_details.get(indicator_id, {}).get("name", indicator.get_name()),
                        "id": indicator_id,
                        "values": indicator_details.get(indicator_id, {}).get("values", {}),
                        "raw": 0.0,
                        "weight": 0.0,
                        "contribution": 0.0,
                        "calculation_details": [],
                        "reasons": indicator_reasons
                    }
            except Exception as e:
                self.logger.error(f"Error scoring {indicator_id}: {e}")
                # Store minimal info even on error
                enhanced_details[indicator_id] = {
                    "name": indicator_details.get(indicator_id, {}).get("name", indicator.get_name()),
                    "id": indicator_id,
                    "values": indicator_details.get(indicator_id, {}).get("values", {}),
                    "raw": 0.0,
                    "weight": 0.0,
                    "contribution": 0.0,
                    "calculation_details": [],
                    "reasons": []
                }
        
        # Add summary
        reasons.append("=" * 60)
        reasons.append(f"📊 TOTAL SCORE: {total_score:.3f}")
        reasons.append("=" * 60)
        
        # Determine recommendation
        if total_score >= criteria.score_buy_threshold:
            reasons.append("🚀 FINAL RECOMMENDATION: BUY")
            reasons.append(f"Reason: Score {total_score:.3f} >= Buy Threshold {criteria.score_buy_threshold}")
            recommendation = "buy"
        elif total_score <= -criteria.score_sell_threshold:
            reasons.append("🔻 FINAL RECOMMENDATION: SELL")
            reasons.append(f"Reason: Score {total_score:.3f} <= Sell Threshold {-criteria.score_sell_threshold}")
            recommendation = "sell"
        else:
            reasons.append("⏸️ FINAL RECOMMENDATION: HOLD")
            reasons.append(f"Reason: Score {total_score:.3f} between thresholds")
            recommendation = "hold"
        
        suggestion = EtfSuggestion(recommendation=recommendation, reasons=reasons)
        
        return suggestion, total_score, components, enhanced_details
