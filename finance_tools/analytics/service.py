# finance_tools/analytics/service.py
"""
Analytics service for ETF and Stock analysis with caching and history tracking.

This service provides a unified interface for running technical analysis on both
ETF and stock data, with built-in caching and history tracking capabilities.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import asdict

from sqlalchemy.orm import Session

from ..logging import get_logger
from ..config import get_config
from ..etfs.tefas.models import AnalysisResult, UserAnalysisHistory
from ..etfs.analysis import EtfAnalyzer, EtfScanner, IndicatorRequest, KeywordFilter
from ..stocks.analytics.technical_analysis import TechnicalAnalysisTool
from ..stocks.analysis import (
    StockScanner,
    StockIndicatorRequest,
    StockIndicatorResult,
    StockScanCriteria
)


class AnalyticsService:
    """Unified service for ETF and Stock analytics with caching."""

    def __init__(self):
        self.logger = get_logger("analytics_service")
        self.config = get_config()
        self.etf_analyzer = EtfAnalyzer()
        self.etf_scanner = EtfScanner()
        self.stock_analyzer = TechnicalAnalysisTool()
        self.stock_scanner = StockScanner()

        # Cache settings
        self.cache_ttl_hours = 24  # Results cached for 24 hours

    def run_etf_technical_analysis(
        self,
        db_session: Session,
        codes: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        column: str = "price",
        indicators: Optional[Dict[str, Dict]] = None,
        include_keywords: Optional[List[str]] = None,
        exclude_keywords: Optional[List[str]] = None,
        case_sensitive: bool = False,
        fund_type: Optional[str] = None,
        user_id: Optional[str] = None,
        save_results: bool = True
    ) -> Dict[str, Any]:
        """
        Run ETF technical analysis with caching and history tracking.

        Args:
            db_session: Database session
            codes: Fund codes to analyze
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            column: Column to analyze (price, market_cap, etc.)
            indicators: Technical indicators configuration
            include_keywords: Keywords to include in title filter
            exclude_keywords: Keywords to exclude from title filter
            case_sensitive: Case sensitive keyword matching
            user_id: User identifier for tracking
            save_results: Whether to save results to database

        Returns:
            Analysis results with metadata
        """
        start_time = time.time()

        try:
            # Check cache first
            cache_key = self._generate_cache_key(
                "etf_technical", codes, start_date, end_date, column, indicators,
                include_keywords, exclude_keywords, case_sensitive
            )

            # Skip cache for task-based analysis to ensure fresh results
            # cached_result = self._get_cached_result(db_session, cache_key)
            # if cached_result:
            #     self.logger.info(f"Returning cached ETF technical analysis for {cache_key}")
            #     return cached_result

            # Parse dates
            start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
            end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

            # Build keyword filter
            keyword_filter = KeywordFilter(
                include_keywords=include_keywords,
                exclude_keywords=exclude_keywords,
                case_sensitive=case_sensitive
            )

            # Default indicators if none provided
            if not indicators:
                indicators = {
                    "ema": {"windows": [20, 50]},
                    "rsi": {"window": 14},
                    "macd": {"window_slow": 26, "window_fast": 12, "window_sign": 9}
                }

            # Create analysis request
            request = IndicatorRequest(
                codes=codes,
                start=start,
                end=end,
                column=column,
                indicators=indicators,
                keyword_filter=keyword_filter,
                fund_type=fund_type
            )

            # Execute analysis
            results = self.etf_analyzer.analyze(request)

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Format results for response with proper JSON serialization
            def serialize_dataframe(df):
                """Convert DataFrame to JSON-serializable format."""
                if hasattr(df, 'to_dict'):
                    # Convert timestamps to strings for JSON serialization
                    df_copy = df.copy()
                    if 'date' in df_copy.columns:
                        df_copy['date'] = df_copy['date'].astype(str)
                    return df_copy.to_dict('index')
                return str(df)
            
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "code": result.code,
                    "data": serialize_dataframe(result.data),
                    "data_shape": result.data.shape if hasattr(result.data, 'shape') else None
                })

            response_data = {
                "analysis_type": "etf_technical",
                "analysis_name": "ETF Technical Analysis",
                "parameters": {
                    "codes": codes,
                    "start_date": start_date,
                    "end_date": end_date,
                    "column": column,
                    "indicators": indicators,
                    "include_keywords": include_keywords,
                    "exclude_keywords": exclude_keywords,
                    "case_sensitive": case_sensitive
                },
                "results": formatted_results,
                "result_count": len(formatted_results),
                "execution_time_ms": execution_time_ms,
                "timestamp": datetime.utcnow().isoformat()
            }

            # Save results if requested
            if save_results:
                self._save_analysis_result(
                    db_session, "etf_technical", "ETF Technical Analysis",
                    response_data["parameters"], response_data, execution_time_ms,
                    len(formatted_results), user_id
                )

                # Track in history
                self._track_analysis_history(
                    db_session, "etf_technical", "ETF Technical Analysis",
                    response_data["parameters"], execution_time_ms, user_id
                )

            return response_data

        except Exception as e:
            self.logger.error(f"Error in ETF technical analysis: {str(e)}")
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_response = {
                "analysis_type": "etf_technical",
                "analysis_name": "ETF Technical Analysis",
                "error": str(e),
                "execution_time_ms": execution_time_ms,
                "timestamp": datetime.utcnow().isoformat()
            }
            return error_response

    def run_etf_scan_analysis(
        self,
        db_session: Session,
        fund_type: Optional[str] = None,
        specific_codes: Optional[List[str]] = None,
        scanners: Optional[List[str]] = None,
        scanner_configs: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        column: str = "price",
        ema_short: int = 20,
        ema_long: int = 50,
        macd_slow: int = 26,
        macd_fast: int = 12,
        macd_sign: int = 9,
        rsi_window: int = 14,
        rsi_lower: float = 30.0,
        rsi_upper: float = 70.0,
        weights: Optional[Dict[str, float]] = None,
        buy_threshold: float = 1.0,
        sell_threshold: float = 1.0,
        include_keywords: Optional[List[str]] = None,
        exclude_keywords: Optional[List[str]] = None,
        case_sensitive: bool = False,
        user_id: Optional[str] = None,
        save_results: bool = True
    ) -> Dict[str, Any]:
        """
        Run ETF scan analysis for buy/sell/hold recommendations.

        Args:
            db_session: Database session
            fund_type: Type of fund (e.g., "etf", "stock")
            specific_codes: Specific codes to scan (e.g., ["FRAK", "FRAX"])
            scanners: List of scanner names to run
            scanner_configs: Configuration for specific scanners
            score_threshold: Minimum score for recommendations
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            column: Column to analyze
            ema_short: Short EMA window
            ema_long: Long EMA window
            macd_slow, macd_fast, macd_sign: MACD parameters
            rsi_window, rsi_lower, rsi_upper: RSI parameters
            weights: Scoring weights for different indicators
            buy_threshold: Threshold for buy recommendations
            sell_threshold: Threshold for sell recommendations
            include_keywords: Keywords to include in title filter
            exclude_keywords: Keywords to exclude from title filter
            case_sensitive: Case sensitive keyword matching
            user_id: User identifier for tracking
            save_results: Whether to save results to database

        Returns:
            Scan results with recommendations
        """
        start_time = time.time()

        try:
            # Check cache first
            cache_key = self._generate_cache_key(
                "etf_scan", specific_codes, start_date, end_date, column, {
                    "ema_short": ema_short, "ema_long": ema_long,
                    "macd": [macd_slow, macd_fast, macd_sign],
                    "rsi": [rsi_window, rsi_lower, rsi_upper],
                    "weights": weights, "thresholds": [buy_threshold, sell_threshold]
                }, include_keywords, exclude_keywords, case_sensitive
            )

            # Skip cache for task-based analysis to ensure fresh results
            # cached_result = self._get_cached_result(db_session, cache_key)
            # if cached_result:
            #     self.logger.info(f"Returning cached ETF scan for {cache_key}")
            #     # Handle nested cached results - extract the actual results if needed
            #     if isinstance(cached_result.get('results'), dict) and 'results' in cached_result['results']:
            #         # This is a nested cached result, extract the inner results
            #         cached_result['results'] = cached_result['results']['results']
            #     return cached_result

            # Build indicators based on selected scanners and their configurations
            indicators = {}
            
            # Map scanner IDs to their indicator configurations using UI parameters
            if scanners and scanner_configs:
                for scanner_id in scanners:
                    config = scanner_configs.get(scanner_id, {})
                    
                    if scanner_id == 'ema_cross':
                        short = config.get('short', ema_short)
                        long = config.get('long', ema_long)
                        indicators["ema"] = {"windows": [short, long]}
                        indicators["ema_cross"] = {"short": short, "long": long}
                    elif scanner_id == 'macd':
                        slow = config.get('slow', macd_slow)
                        fast = config.get('fast', macd_fast)
                        signal = config.get('signal', macd_sign)
                        indicators["macd"] = {"window_slow": slow, "window_fast": fast, "window_sign": signal}
                    elif scanner_id == 'rsi':
                        window = config.get('window', rsi_window)
                        indicators["rsi"] = {"window": window}
                    elif scanner_id == 'momentum':
                        windows = config.get('windows', [30, 60, 90, 180, 360])
                        indicators["momentum"] = {"windows": windows}
                    elif scanner_id == 'daily_momentum':
                        windows = config.get('windows', [30, 60, 90, 180, 360])
                        indicators["daily_momentum"] = {"windows": windows}
                    elif scanner_id == 'supertrend':
                        hl_factor = config.get('hl_factor', 0.05)
                        atr_period = config.get('atr_period', 10)
                        multiplier = config.get('multiplier', 3.0)
                        indicators["supertrend"] = {"hl_factor": hl_factor, "atr_period": atr_period, "multiplier": multiplier}
            else:
                # Fallback to default indicators if no scanners specified
                indicators = {
                    "ema": {"windows": [ema_short, ema_long]},
                    "ema_cross": {"short": ema_short, "long": ema_long},
                    "macd": {"window_slow": macd_slow, "window_fast": macd_fast, "window_sign": macd_sign},
                    "rsi": {"window": rsi_window},
                }

            # Default weights if none provided, using only selected scanners
            if weights is None:
                weights = {}
                if 'ema_cross' in (scanners or []):
                    weights["ema_cross"] = 1.0
                if 'macd' in (scanners or []):
                    weights["macd"] = 1.0
                if 'rsi' in (scanners or []):
                    weights["rsi"] = 1.0
                if 'momentum' in (scanners or []):
                    weights["momentum"] = 1.0
                if 'daily_momentum' in (scanners or []):
                    weights["daily_momentum"] = 1.0
                if 'supertrend' in (scanners or []):
                    weights["supertrend"] = 1.0

            # Get data for scanning
            technical_results = self.run_etf_technical_analysis(
                db_session, specific_codes, start_date, end_date, column, indicators,
                include_keywords, exclude_keywords, case_sensitive, fund_type, user_id, save_results=False
            )

            if "error" in technical_results:
                return technical_results

            # Extract results from technical analysis and prepare for scanning
            import pandas as pd
            from ..etfs.analysis import EtfScanCriteria
            
            indicator_results = technical_results.get("results", [])
            
            # Convert to DataFrame mapping for scanner
            code_to_df = {}
            if isinstance(indicator_results, list) and len(indicator_results) > 0:
                # Results are dicts with 'code' and 'data' keys
                for result_dict in indicator_results:
                    if isinstance(result_dict, dict) and 'code' in result_dict and 'data' in result_dict:
                        code = result_dict['code']
                        data = result_dict['data']
                        
                        # Convert dict data back to DataFrame if needed
                        if isinstance(data, dict):
                            # data is already in dict('index') format, convert back to DataFrame
                            code_to_df[code] = pd.DataFrame.from_dict(data, orient='index')
                        elif hasattr(data, 'to_frame'):
                            code_to_df[code] = data
            
            if not code_to_df:
                # Return empty results if no data
                execution_time_ms = int((time.time() - start_time) * 1000)
                return {
                    "analysis_type": "etf_scan",
                    "analysis_name": "ETF Scan Analysis",
                    "parameters": {
                        "codes": specific_codes,
                        "start_date": start_date,
                        "end_date": end_date,
                        "column": column,
                    },
                    "results": [],
                    "result_count": 0,
                    "execution_time_ms": execution_time_ms,
                    "timestamp": datetime.utcnow().isoformat(),
                }

            # Extract parameters from scanner configurations
            ema_short_actual = ema_short
            ema_long_actual = ema_long
            macd_slow_actual = macd_slow
            macd_fast_actual = macd_fast
            macd_sign_actual = macd_sign
            rsi_window_actual = rsi_window
            
            if scanners and scanner_configs:
                for scanner_id in scanners:
                    config = scanner_configs.get(scanner_id, {})
                    if scanner_id == 'ema_cross':
                        ema_short_actual = config.get('short', ema_short)
                        ema_long_actual = config.get('long', ema_long)
                    elif scanner_id == 'macd':
                        macd_slow_actual = config.get('slow', macd_slow)
                        macd_fast_actual = config.get('fast', macd_fast)
                        macd_sign_actual = config.get('signal', macd_sign)
                    elif scanner_id == 'rsi':
                        rsi_window_actual = config.get('window', rsi_window)

            # Map frontend scanner weights to backend weight keys
            # Frontend sends: {'ema_cross': 2.0, 'macd': 1.5, 'rsi': 1.0}
            # Backend expects: {'w_ema': 2.0, 'w_macd': 1.5, 'w_rsi': 1.0}
            scanner_weight_mapping = {
                'ema_cross': 'w_ema',
                'macd': 'w_macd', 
                'rsi': 'w_rsi',
                'momentum': 'w_momentum',
                'daily_momentum': 'w_momentum_daily',
                'supertrend': 'w_supertrend'
            }
            
            # Convert frontend weights to backend format
            backend_weights = {}
            for scanner_id, weight in weights.items():
                if scanner_id in scanner_weight_mapping:
                    backend_key = scanner_weight_mapping[scanner_id]
                    backend_weights[backend_key] = weight
            
            # Run the scanner with the configured criteria using only selected scanners
            criteria = EtfScanCriteria(
                column=column,
                ema_short=ema_short_actual,
                ema_long=ema_long_actual,
                macd_slow=macd_slow_actual,
                macd_fast=macd_fast_actual,
                macd_sign=macd_sign_actual,
                rsi_window=rsi_window_actual,
                rsi_lower=rsi_lower,
                rsi_upper=rsi_upper,
                # Use mapped weights for selected scanners, set others to 0
                w_ema_cross=backend_weights.get("w_ema", 0.0) if 'ema_cross' in (scanners or []) else 0.0,
                w_macd=backend_weights.get("w_macd", 0.0) if 'macd' in (scanners or []) else 0.0,
                w_rsi=backend_weights.get("w_rsi", 0.0) if 'rsi' in (scanners or []) else 0.0,
                w_momentum=backend_weights.get("w_momentum", 0.0) if 'momentum' in (scanners or []) else 0.0,
                w_momentum_daily=backend_weights.get("w_momentum_daily", 0.0) if 'daily_momentum' in (scanners or []) else 0.0,
                w_supertrend=backend_weights.get("w_supertrend", 0.0) if 'supertrend' in (scanners or []) else 0.0,
                score_buy_threshold=max(score_threshold, 1.0),  # Ensure minimum threshold of 1.0
                score_sell_threshold=max(score_threshold, 1.0),  # Ensure minimum threshold of 1.0
            )
            
            # Log detailed scanner execution information
            self.logger.info("🔍 ETF Scan Analysis - Scanner Configuration Details:")
            self.logger.info(f"  📊 Selected Scanners: {scanners or 'None'}")
            self.logger.info(f"  ⚙️  Scanner Configurations:")
            if scanners and scanner_configs:
                for scanner_id in scanners:
                    config = scanner_configs.get(scanner_id, {})
                    # Map scanner IDs to weight keys
                    weight_key = f"w_{scanner_id}" if scanner_id != 'ema_cross' else "w_ema"
                    weight = weights.get(weight_key, 0.0)
                    self.logger.info(f"    • {scanner_id}: config={config}, weight={weight}")
            else:
                self.logger.info("    • Using default configurations")
            
            self.logger.info(f"  🎯 Scan Criteria:")
            self.logger.info(f"    • Column: {criteria.column}")
            self.logger.info(f"    • EMA: {criteria.ema_short}/{criteria.ema_long} (weight: {criteria.w_ema_cross})")
            self.logger.info(f"    • MACD: {criteria.macd_fast}/{criteria.macd_slow}/{criteria.macd_sign} (weight: {criteria.w_macd})")
            self.logger.info(f"    • RSI: {criteria.rsi_window} window, {criteria.rsi_lower}-{criteria.rsi_upper} range (weight: {criteria.w_rsi})")
            self.logger.info(f"    • Momentum: weight {criteria.w_momentum}")
            self.logger.info(f"    • Daily Momentum: weight {criteria.w_momentum_daily}")
            self.logger.info(f"    • Supertrend: weight {criteria.w_supertrend}")
            self.logger.info(f"    • Score Thresholds: buy>={criteria.score_buy_threshold}, sell<={criteria.score_sell_threshold}")
            
            # Perform the scan
            scan_results = self.etf_scanner.scan(code_to_df, criteria)
            
            # Log scan execution summary
            self.logger.info(f"🔍 Scan completed: {len(scan_results)} results generated")
            
            # Format results for API response
            formatted_results = []
            buy_count = 0
            sell_count = 0
            hold_count = 0
            multi_reason_count = 0
            
            for scan_result in scan_results:
                recommendation = scan_result.suggestion.recommendation.upper()
                reasons = scan_result.suggestion.reasons
                
                # Count recommendations
                if recommendation == "BUY":
                    buy_count += 1
                elif recommendation == "SELL":
                    sell_count += 1
                else:
                    hold_count += 1
                
                # Count multiple reasons
                if len(reasons) > 1:
                    multi_reason_count += 1
                
                # Debug logging for first result
                if len(formatted_results) == 0:
                    self.logger.info(f"🔍 DEBUG - First scan result for {scan_result.code}:")
                    self.logger.info(f"  • Components type: {type(scan_result.components)}")
                    self.logger.info(f"  • Components value: {scan_result.components}")
                    self.logger.info(f"  • Indicators type: {type(scan_result.indicators_snapshot)}")
                    self.logger.info(f"  • Indicators value: {scan_result.indicators_snapshot}")
                    self.logger.info(f"  • Reasons count: {len(reasons)}")
                    self.logger.info(f"  • Reasons sample: {reasons[:3] if len(reasons) > 3 else reasons}")
                
                formatted_results.append({
                    "code": scan_result.code,
                    "recommendation": recommendation,
                    "score": float(scan_result.score),
                    "reasons": reasons,
                    "components": dict(scan_result.components) if scan_result.components else {},  # Ensure it's a dict
                    "indicators_snapshot": dict(scan_result.indicators_snapshot) if scan_result.indicators_snapshot else {},  # Ensure it's a dict
                    "timestamp": scan_result.timestamp.isoformat() if scan_result.timestamp else None,
                    "last_value": scan_result.last_value,
                })
            
            # Log detailed results summary
            self.logger.info(f"📊 Scan Results Summary:")
            self.logger.info(f"  • Total Results: {len(scan_results)}")
            self.logger.info(f"  • BUY: {buy_count}, SELL: {sell_count}, HOLD: {hold_count}")
            self.logger.info(f"  • Results with Multiple Reasons: {multi_reason_count}")
            
            # Log top 5 results with their reasons
            if scan_results:
                self.logger.info(f"  🏆 Top 5 Results:")
                for i, result in enumerate(scan_results[:5]):
                    reasons_str = "; ".join(result.suggestion.reasons) if result.suggestion.reasons else "No specific reasons"
                    self.logger.info(f"    {i+1}. {result.code}: {result.suggestion.recommendation.upper()} [score={result.score:.3f}] - {reasons_str}")
            
            # Log reason distribution
            all_reasons = []
            for result in scan_results:
                all_reasons.extend(result.suggestion.reasons)
            if all_reasons:
                reason_counts = {}
                for reason in all_reasons:
                    reason_counts[reason] = reason_counts.get(reason, 0) + 1
                self.logger.info(f"  📈 Most Common Reasons:")
                for reason, count in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                    self.logger.info(f"    • {reason}: {count} occurrences")

            execution_time_ms = int((time.time() - start_time) * 1000)

            response_data = {
                "analysis_type": "etf_scan",
                "analysis_name": "ETF Scan Analysis",
                "parameters": {
                    "codes": specific_codes,
                    "start_date": start_date,
                    "end_date": end_date,
                    "column": column,
                    "fund_type": fund_type,
                    "scanners": scanners,
                    "scanner_configs": scanner_configs,
                    "weights": weights,
                    "score_threshold": score_threshold,
                    "include_keywords": include_keywords,
                    "exclude_keywords": exclude_keywords,
                    "case_sensitive": case_sensitive,
                    # Actual parameters used in analysis
                    "actual_parameters": {
                        "ema_short": ema_short_actual,
                        "ema_long": ema_long_actual,
                        "macd_slow": macd_slow_actual,
                        "macd_fast": macd_fast_actual,
                        "macd_sign": macd_sign_actual,
                        "rsi_window": rsi_window_actual,
                        "rsi_lower": rsi_lower,
                        "rsi_upper": rsi_upper,
                    },
                    # Scanner execution summary
                    "scanner_summary": {
                        "total_scanners": len(scanners) if scanners else 0,
                        "active_scanners": [s for s in (scanners or []) if weights.get(s, 0) > 0],
                        "buy_count": buy_count,
                        "sell_count": sell_count,
                        "hold_count": hold_count,
                        "multi_reason_count": multi_reason_count,
                    }
                },
                "results": sorted(formatted_results, key=lambda x: x["score"], reverse=True),
                "result_count": len(formatted_results),
                "execution_time_ms": execution_time_ms,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Save results if requested
            if save_results:
                # Create parameters with scanner details for database storage
                db_parameters = {
                    "codes": specific_codes,
                    "start_date": start_date,
                    "end_date": end_date,
                    "column": column,
                    "fund_type": fund_type,
                    "scanners": scanners,
                    "scanner_configs": scanner_configs,
                    "weights": weights,
                    "score_threshold": score_threshold,
                    "include_keywords": include_keywords,
                    "exclude_keywords": exclude_keywords,
                    "case_sensitive": case_sensitive,
                    # Actual parameters used in analysis
                    "actual_parameters": {
                        "ema_short": ema_short_actual,
                        "ema_long": ema_long_actual,
                        "macd_slow": macd_slow_actual,
                        "macd_fast": macd_fast_actual,
                        "macd_sign": macd_sign_actual,
                        "rsi_window": rsi_window_actual,
                        "rsi_lower": rsi_lower,
                        "rsi_upper": rsi_upper,
                    },
                    # Scanner execution summary
                    "scanner_summary": {
                        "total_scanners": len(scanners) if scanners else 0,
                        "active_scanners": [s for s in (scanners or []) if weights.get(f"w_{s}" if s != 'ema_cross' else "w_ema", 0) > 0],
                        "buy_count": buy_count,
                        "sell_count": sell_count,
                        "hold_count": hold_count,
                        "multi_reason_count": multi_reason_count,
                    }
                }
                
                self._save_analysis_result(
                    db_session, "etf_scan", "ETF Scan Analysis",
                    db_parameters, response_data, execution_time_ms,
                    len(formatted_results), user_id
                )

            return response_data

        except Exception as e:
            self.logger.error(f"Error in ETF scan analysis: {str(e)}")
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_response = {
                "analysis_type": "etf_scan",
                "analysis_name": "ETF Scan Analysis",
                "error": str(e),
                "execution_time_ms": execution_time_ms,
                "timestamp": datetime.utcnow().isoformat()
            }
            return error_response

    def run_stock_scan_analysis(
        self,
        db_session: Session,
        symbols: Optional[List[str]] = None,
        scanners: Optional[List[str]] = None,
        scanner_configs: Optional[Dict[str, Any]] = None,
        weights: Optional[Dict[str, float]] = None,
        buy_threshold: Optional[float] = None,
        sell_threshold: Optional[float] = None,
        score_threshold: Optional[float] = None,  # Deprecated: kept for backward compatibility
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        column: str = "close",
        sector: Optional[str] = None,
        industry: Optional[str] = None,
        user_id: Optional[str] = None,
        save_results: bool = True
    ) -> Dict[str, Any]:
        """
        Run stock scan analysis for buy/sell/hold recommendations using plugin-based indicators.
        
        This method performs stock scanning with dynamically selected indicators.
        All indicator parameters are extracted from the indicator registry - NO hardcoded logic.

        Args:
            db_session: Database session
            symbols: Specific symbols to scan (optional - scans all if not provided)
            scanners: List of indicator IDs to include (e.g., ['ema_cross', 'macd', 'rsi'])
            scanner_configs: Per-indicator configuration dict (e.g., {'ema_cross': {'short': 20, 'long': 50}})
            weights: Per-indicator weights for scoring (e.g., {'ema_cross': 2.0, 'macd': 1.5})
            buy_threshold: Minimum score for BUY recommendation (default: 1.0)
            sell_threshold: Minimum absolute score for SELL recommendation (default: 1.0)
            score_threshold: Deprecated - use buy_threshold and sell_threshold instead
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            column: Column to analyze (default: 'close')
            sector: Filter by sector (optional)
            industry: Filter by industry (optional)
            user_id: User identifier for tracking (optional)
            save_results: Whether to save results to database (default: True)

        Returns:
            Dict with scan results including recommendations and detailed indicator breakdowns

        Note:
            All indicator-specific parameters are handled dynamically via scanner_configs.
            The system uses the plugin-based indicator registry - any new indicator automatically
            becomes available without code changes.
        """
        start_time = time.time()

        try:
            # Parse dates
            start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
            end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

            # Build indicators dynamically using the registry - NO hardcoded indicator logic
            from ..stocks.analysis.indicators import registry as indicator_registry
            
            indicators = {}
            keyword_filter = None  # No keyword filtering for stocks yet
            
            if scanners:
                for scanner_id in scanners:
                    indicator = indicator_registry.get(scanner_id)
                    if indicator is None:
                        self.logger.warning(f"⚠️ Unknown indicator: {scanner_id}")
                        continue
                    
                    # Get parameter schema from the indicator
                    schema = indicator.get_parameter_schema()
                    
                    # Build config from scanner_configs, using schema defaults as fallback
                    config = {}
                    if scanner_configs and scanner_id in scanner_configs:
                        user_config = scanner_configs[scanner_id]
                        for param_name, param_schema in schema.items():
                            config[param_name] = user_config.get(param_name, param_schema.get('default', None))
                    else:
                        # Use schema defaults
                        for param_name, param_schema in schema.items():
                            if 'default' in param_schema:
                                config[param_name] = param_schema['default']
                    
                    indicators[scanner_id] = config

            # Fetch stock data from database
            self.logger.info(f"📊 Fetching stock data for {len(symbols) if symbols else 'all'} symbols")
            from ..stocks.analysis import StockDataRetriever
            
            retriever = StockDataRetriever()
            df_all = retriever.fetch_info(
                symbols=symbols,
                start=start,
                end=end,
                sector=sector,
                industry=industry
            )
            
            self.logger.info(f"📊 Fetched {len(df_all)} rows of stock data")
            
            if df_all.empty:
                self.logger.warning("⚠️ No stock data available")
                return {
                    "analysis_type": "stock_scan",
                    "analysis_name": "Stock Scan Analysis",
                    "parameters": {"symbols": symbols, "start_date": start_date, "end_date": end_date, "column": column},
                    "results": [],
                    "result_count": 0,
                    "execution_time_ms": int((time.time() - start_time) * 1000),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            
            # Convert to symbol-to-DataFrame mapping
            import pandas as pd
            symbol_to_df = {}
            for symbol in df_all['symbol'].unique():
                symbol_df = df_all[df_all['symbol'] == symbol].copy()
                # Keep date as a column (not index) because scanner needs it
                # Sort by date to ensure proper time series order
                if 'date' in symbol_df.columns:
                    symbol_df = symbol_df.sort_values('date')
                symbol_to_df[symbol] = symbol_df
            
            self.logger.info(f"📊 Prepared symbol_to_df with {len(symbol_to_df)} symbols")
            
            # Debug: Log first symbol's structure
            if symbol_to_df:
                first_symbol = list(symbol_to_df.keys())[0]
                first_df = symbol_to_df[first_symbol]
                self.logger.info(f"📊 Sample symbol '{first_symbol}' - Columns: {list(first_df.columns)}, Rows: {len(first_df)}, Date range: {first_df['date'].min()} to {first_df['date'].max()}")

            if not symbol_to_df:
                execution_time_ms = int((time.time() - start_time) * 1000)
                return {
                    "analysis_type": "stock_scan",
                    "analysis_name": "Stock Scan Analysis",
                    "parameters": {"symbols": symbols, "start_date": start_date, "end_date": end_date, "column": column},
                    "results": [],
                    "result_count": 0,
                    "execution_time_ms": execution_time_ms,
                    "timestamp": datetime.utcnow().isoformat(),
                }

            # Build scan criteria dynamically - NO hardcoded indicator names
            from ..stocks.analysis.indicators import registry as indicator_registry
            
            # Prepare weights: if not provided, default to 1.0 for all selected scanners
            if weights is None:
                weights = {scanner_id: 1.0 for scanner_id in (scanners or [])}
            
            # Determine thresholds (with backward compatibility)
            # If buy_threshold/sell_threshold not provided, fall back to score_threshold
            final_buy_threshold = buy_threshold if buy_threshold is not None else (score_threshold if score_threshold is not None else 1.0)
            final_sell_threshold = sell_threshold if sell_threshold is not None else (score_threshold if score_threshold is not None else 1.0)

            # Ensure minimum threshold of 0.0
            final_buy_threshold = max(final_buy_threshold, 0.0)
            final_sell_threshold = max(final_sell_threshold, 0.0)

            # Create criteria with base parameters
            # Note: StockScanCriteria has defaults for all parameters
            criteria = StockScanCriteria(
                column=column,
                score_buy_threshold=final_buy_threshold,
                score_sell_threshold=final_sell_threshold,
            )
            
            # Dynamically set weights for ALL registered indicators
            # Weight = value from weights dict if provided, else 1.0 if selected, 0.0 if not
            all_indicator_ids = indicator_registry.get_all_ids()
            for indicator_id in all_indicator_ids:
                weight_attr = f"w_{indicator_id}"
                # Check if this indicator is in the selected scanners list
                is_selected = scanners and indicator_id in scanners
                weight_value = weights.get(indicator_id, 1.0 if is_selected else 0.0)
                # Dynamically set the weight attribute
                setattr(criteria, weight_attr, weight_value)

            # Perform the scan with custom scanner configs
            scan_results = self.stock_scanner.scan(symbol_to_df, criteria, scanner_configs)

            # Format results for API response
            formatted_results = []
            buy_count = 0
            sell_count = 0
            hold_count = 0

            for scan_result in scan_results:
                recommendation = scan_result.suggestion.recommendation.upper()
                
                if recommendation == "BUY":
                    buy_count += 1
                elif recommendation == "SELL":
                    sell_count += 1
                else:
                    hold_count += 1
                
                # Clean components - they are now dicts with raw, weight, contribution
                import math
                import pandas as pd
                clean_components = {}
                if scan_result.components:
                    for k, v in scan_result.components.items():
                        if isinstance(v, dict) and "contribution" in v:
                            # New format: {"raw": x, "weight": y, "contribution": z}
                            clean_components[k] = {
                                "raw": float(v["raw"]) if v.get("raw") is not None and pd.notnull(v["raw"]) else 0.0,
                                "weight": float(v["weight"]) if v.get("weight") is not None and pd.notnull(v["weight"]) else 0.0,
                                "contribution": float(v["contribution"]) if v.get("contribution") is not None and pd.notnull(v["contribution"]) else 0.0
                            }
                        else:
                            # Old format: just a number
                            if v is not None and not math.isnan(v):
                                clean_components[k] = {"contribution": float(v), "raw": 0.0, "weight": 0.0}
                
                clean_indicators = {}
                if scan_result.indicators_snapshot:
                    for k, v in scan_result.indicators_snapshot.items():
                        if v is not None and not math.isnan(v):
                            clean_indicators[k] = float(v)
                
                # Prepare indicator_details (already in correct format from scanner)
                clean_indicator_details = {}
                if scan_result.indicator_details:
                    for ind_id, ind_data in scan_result.indicator_details.items():
                        # Clean values dict
                        clean_values = {}
                        if isinstance(ind_data.get("values"), dict):
                            for k, v in ind_data["values"].items():
                                if v is not None and not math.isnan(v):
                                    clean_values[k] = float(v)
                        
                        clean_indicator_details[ind_id] = {
                            "name": ind_data.get("name", ind_id),
                            "id": ind_data.get("id", ind_id),
                            "values": clean_values,
                            "raw": float(ind_data.get("raw", 0.0)) if not math.isnan(ind_data.get("raw", 0)) else 0.0,
                            "weight": float(ind_data.get("weight", 0.0)) if not math.isnan(ind_data.get("weight", 0)) else 0.0,
                            "contribution": float(ind_data.get("contribution", 0.0)) if not math.isnan(ind_data.get("contribution", 0)) else 0.0,
                            "calculation_details": ind_data.get("calculation_details", []),
                            "reasons": ind_data.get("reasons", [])
                        }
                
                formatted_results.append({
                    "symbol": scan_result.symbol,
                    "recommendation": recommendation,
                    "score": float(scan_result.score),
                    "reasons": scan_result.suggestion.reasons,
                    "components": clean_components,
                    "indicators_snapshot": clean_indicators,
                    "indicator_details": clean_indicator_details,  # New: grouped per-indicator data
                    "timestamp": scan_result.timestamp.isoformat() if scan_result.timestamp else None,
                    "last_value": scan_result.last_value,
                })

            execution_time_ms = int((time.time() - start_time) * 1000)

            response_data = {
                "analysis_type": "stock_scan",
                "analysis_name": "Stock Scan Analysis",
                "parameters": {
                    "symbols": symbols,
                    "start_date": start_date,
                    "end_date": end_date,
                    "column": column,
                    "sector": sector,
                    "industry": industry,
                    "scanners": scanners,
                    "scanner_configs": scanner_configs,
                    "weights": weights,
                    "buy_threshold": final_buy_threshold,
                    "sell_threshold": final_sell_threshold,
                },
                "results": sorted(formatted_results, key=lambda x: x["score"], reverse=True),
                "result_count": len(formatted_results),
                "buy_count": buy_count,
                "sell_count": sell_count,
                "hold_count": hold_count,
                "execution_time_ms": execution_time_ms,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Save results if requested
            if save_results:
                self._save_analysis_result(
                    db_session, "stock_scan", "Stock Scan Analysis",
                    response_data["parameters"], response_data, execution_time_ms,
                    len(formatted_results), user_id
                )

                self._track_analysis_history(
                    db_session, "stock_scan", "Stock Scan Analysis",
                    response_data["parameters"], execution_time_ms, user_id
                )

            return response_data

        except Exception as e:
            self.logger.error(f"Error in stock scan analysis: {str(e)}")
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_response = {
                "analysis_type": "stock_scan",
                "analysis_name": "Stock Scan Analysis",
                "error": str(e),
                "execution_time_ms": execution_time_ms,
                "timestamp": datetime.utcnow().isoformat()
            }
            return error_response

    def run_stock_technical_analysis(
        self,
        db_session: Session,
        symbols: List[str],
        indicators: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "1y",
        user_id: Optional[str] = None,
        save_results: bool = True,
        **indicator_params
    ) -> Dict[str, Any]:
        """
        Run stock technical analysis.

        Args:
            db_session: Database session
            symbols: Stock symbols to analyze
            indicators: List of indicators to calculate
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            period: Period for data (if dates not provided)
            user_id: User identifier for tracking
            save_results: Whether to save results to database
            **indicator_params: Additional parameters for indicators

        Returns:
            Analysis results
        """
        start_time = time.time()

        try:
            # Check cache first
            cache_key = self._generate_cache_key(
                "stock_technical", symbols, start_date, end_date, None,
                {"indicators": indicators, "period": period, **indicator_params}
            )

            cached_result = self._get_cached_result(db_session, cache_key)
            if cached_result:
                self.logger.info(f"Returning cached stock technical analysis for {cache_key}")
                return cached_result

            # Get stock data (this would integrate with YFinanceDownloader)
            # For now, we'll simulate getting the data
            from ..stocks.data_downloaders import YFinanceDownloader

            downloader = YFinanceDownloader()
            stock_data_result = downloader.download(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                period=period
            )

            if stock_data_result.metadata.get('error'):
                raise Exception(f"Failed to download stock data: {stock_data_result.metadata['error']}")

            stock_df = stock_data_result.as_df()

            # Run technical analysis
            analysis_result = self.stock_analyzer.execute(
                data=stock_df,
                indicators=indicators,
                **indicator_params
            )

            if not analysis_result.success:
                raise Exception(f"Technical analysis failed: {analysis_result.error}")

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Format results
            response_data = {
                "analysis_type": "stock_technical",
                "analysis_name": "Stock Technical Analysis",
                "parameters": {
                    "symbols": symbols,
                    "start_date": start_date,
                    "end_date": end_date,
                    "period": period,
                    "indicators": indicators,
                    **indicator_params
                },
                "results": {
                    "data": analysis_result.data.to_dict('index') if hasattr(analysis_result.data, 'to_dict') else str(analysis_result.data),
                    "metadata": analysis_result.metadata
                },
                "execution_time_ms": execution_time_ms,
                "timestamp": datetime.utcnow().isoformat()
            }

            # Save results if requested
            if save_results:
                self._save_analysis_result(
                    db_session, "stock_technical", "Stock Technical Analysis",
                    response_data["parameters"], response_data, execution_time_ms, 1, user_id
                )

            return response_data

        except Exception as e:
            self.logger.error(f"Error in stock technical analysis: {str(e)}")
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_response = {
                "analysis_type": "stock_technical",
                "analysis_name": "Stock Technical Analysis",
                "error": str(e),
                "execution_time_ms": execution_time_ms,
                "timestamp": datetime.utcnow().isoformat()
            }
            return error_response

    def get_analysis_history(
        self,
        db_session: Session,
        user_id: Optional[str] = None,
        analysis_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get analysis history for user or all users."""
        query = db_session.query(UserAnalysisHistory)

        if user_id:
            query = query.filter(UserAnalysisHistory.user_id == user_id)

        if analysis_type:
            query = query.filter(UserAnalysisHistory.analysis_type == analysis_type)

        # Order by most recent first
        history_records = query.order_by(UserAnalysisHistory.executed_at.desc()).limit(limit).all()

        return [
            {
                "id": record.id,
                "analysis_type": record.analysis_type,
                "analysis_name": record.analysis_name,
                "parameters": record.parameters,
                "executed_at": record.executed_at.isoformat(),
                "execution_time_ms": record.execution_time_ms,
                "result_id": record.result_id,
                "is_favorite": bool(record.is_favorite),
                "access_count": record.access_count
            }
            for record in history_records
        ]

    def get_cached_results(
        self,
        db_session: Session,
        analysis_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get cached analysis results."""
        query = db_session.query(AnalysisResult)

        if analysis_type:
            query = query.filter(AnalysisResult.analysis_type == analysis_type)

        # Only return non-expired results
        now = datetime.utcnow()
        query = query.filter(
            (AnalysisResult.expires_at.is_(None)) | (AnalysisResult.expires_at > now)
        )

        # Order by most recent first
        cached_results = query.order_by(AnalysisResult.created_at.desc()).limit(limit).all()

        return [
            {
                "id": result.id,
                "analysis_type": result.analysis_type,
                "analysis_name": result.analysis_name,
                "parameters": result.parameters,
                "result_count": result.result_count,
                "execution_time_ms": result.execution_time_ms,
                "status": result.status,
                "created_at": result.created_at.isoformat(),
                "expires_at": result.expires_at.isoformat() if result.expires_at else None
            }
            for result in cached_results
        ]

    def _generate_cache_key(
        self,
        analysis_type: str,
        codes_or_symbols: Optional[List[str]],
        start_date: Optional[str],
        end_date: Optional[str],
        column: Optional[str],
        indicators: Optional[Dict],
        include_keywords: Optional[List[str]] = None,
        exclude_keywords: Optional[List[str]] = None,
        case_sensitive: bool = False
    ) -> str:
        """Generate a cache key for the analysis parameters."""
        key_parts = [
            analysis_type,
            str(sorted(codes_or_symbols or [])),
            start_date or "",
            end_date or "",
            column or "",
            json.dumps(indicators or {}, sort_keys=True),
            str(sorted(include_keywords or [])),
            str(sorted(exclude_keywords or [])),
            str(case_sensitive)
        ]
        return "|".join(key_parts)

    def _get_cached_result(self, db_session: Session, cache_key: str) -> Optional[Dict[str, Any]]:
        """Check if we have a cached result for the given parameters."""
        # For now, we'll implement a simple time-based cache check
        # In a real implementation, you'd want to hash the parameters more robustly

        # Check if we have a recent result with similar parameters
        # This is a simplified version - in production, you'd want proper parameter matching
        cutoff_time = datetime.utcnow() - timedelta(hours=self.cache_ttl_hours)

        cached_result = db_session.query(AnalysisResult).filter(
            AnalysisResult.created_at >= cutoff_time,
            AnalysisResult.status == 'completed'
        ).first()

        if cached_result:
            return {
                "analysis_type": cached_result.analysis_type,
                "analysis_name": cached_result.analysis_name,
                "parameters": cached_result.parameters,
                "results": cached_result.results_data,
                "result_count": cached_result.result_count,
                "execution_time_ms": cached_result.execution_time_ms,
                "timestamp": cached_result.created_at.isoformat(),
                "cached": True
            }

        return None

    def _save_analysis_result(
        self,
        db_session: Session,
        analysis_type: str,
        analysis_name: str,
        parameters: Dict,
        results_data: Dict,
        execution_time_ms: int,
        result_count: int,
        user_id: Optional[str] = None
    ) -> int:
        """Save analysis result to database with cache expiration."""
        expires_at = datetime.utcnow() + timedelta(hours=self.cache_ttl_hours)

        # Clean the data for JSON serialization
        import math
        import copy
        
        def clean_for_json(obj):
            """Clean data for JSON serialization by replacing nan and inf values."""
            if isinstance(obj, dict):
                return {k: clean_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_for_json(item) for item in obj]
            elif isinstance(obj, float):
                if math.isnan(obj):
                    return None
                elif math.isinf(obj):
                    return None
                else:
                    return obj
            else:
                return obj
        
        # Clean the results_data
        cleaned_results_data = clean_for_json(copy.deepcopy(results_data))
        
        # Debug: Check what's being saved
        self.logger.info(f"🔍 Saving analysis result - Type: {analysis_type}")
        if 'results' in cleaned_results_data and cleaned_results_data['results']:
            first_result = cleaned_results_data['results'][0]
            self.logger.info(f"📊 First result keys: {list(first_result.keys())}")
            enhanced_fields = ['components', 'indicators_snapshot', 'reasons']
            for field in enhanced_fields:
                if field in first_result:
                    value = first_result[field]
                    self.logger.info(f"  ✅ {field}: Present (type: {type(value)})")
                    if field == 'reasons':
                        self.logger.info(f"      Count: {len(value)}")
                        self.logger.info(f"      Sample: {value[:3] if len(value) > 3 else value}")
                    elif field in ['components', 'indicators_snapshot']:
                        self.logger.info(f"      Keys: {list(value.keys()) if isinstance(value, dict) else 'Not a dict'}")
                        self.logger.info(f"      Values: {value}")
                else:
                    self.logger.info(f"  ❌ {field}: Missing")

        result_record = AnalysisResult(
            analysis_type=analysis_type,
            analysis_name=analysis_name,
            parameters=parameters,
            results_data=cleaned_results_data,
            result_count=result_count,
            execution_time_ms=execution_time_ms,
            expires_at=expires_at,
            user_id=user_id
        )

        db_session.add(result_record)
        db_session.commit()

        return result_record.id

    def _track_analysis_history(
        self,
        db_session: Session,
        analysis_type: str,
        analysis_name: str,
        parameters: Dict,
        execution_time_ms: int,
        user_id: Optional[str] = None
    ) -> None:
        """Track analysis execution in history."""
        history_record = UserAnalysisHistory(
            user_id=user_id,
            analysis_type=analysis_type,
            analysis_name=analysis_name,
            parameters=parameters,
            execution_time_ms=execution_time_ms
        )

        db_session.add(history_record)
        db_session.commit()
