# ema_scanner.py
from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Iterable, Dict, List, Tuple, Optional

# ---------------------------
# Core indicator calculators
# ---------------------------

def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False, min_periods=period).mean()

def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)
    avg_gain = pd.Series(gain, index=close.index).rolling(window=period, min_periods=period).mean()
    avg_loss = pd.Series(loss, index=close.index).rolling(window=period, min_periods=period).mean()
    rs = avg_gain / (avg_loss.replace(0, np.nan))
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)

def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low),
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(window=period, min_periods=period).mean()

# ---------------------------
# Signal definitions (no look-ahead)
# ---------------------------

def crossed_above(a: pd.Series, b: pd.Series) -> pd.Series:
    # True on the bar where a crosses above b
    return (a > b) & (a.shift(1) <= b.shift(1))

def crossed_below(a: pd.Series, b: pd.Series) -> pd.Series:
    return (a < b) & (a.shift(1) >= b.shift(1))

@dataclass
class EMAParams:
    fast: int = 20
    slow: int = 50
    regime: int = 200
    vol_sma: int = 20
    atr_period: int = 14
    max_ext_atr: float = 1.5   # max (|Close-EMA20|/ATR) to avoid extended buys
    min_vol_mult: float = 1.2  # Volume must be >= this * SMA(volume)

def compute_indicators(df: pd.DataFrame, p: EMAParams) -> pd.DataFrame:
    out = df.copy()
    out["EMA_fast"] = ema(out["Close"], p.fast)
    out["EMA_slow"] = ema(out["Close"], p.slow)
    out["EMA_regime"] = ema(out["Close"], p.regime)
    out["ATR"] = atr(out["High"], out["Low"], out["Close"], p.atr_period)
    out["VolSMA"] = out["Volume"].rolling(p.vol_sma, min_periods=p.vol_sma).mean()
    out["RSI"] = rsi(out["Close"], 14)
    return out

def ema_signals(df: pd.DataFrame, p: EMAParams) -> pd.DataFrame:
    """
    Produces boolean columns for:
      - price x EMA_fast (e.g., 20)
      - EMA_fast x EMA_slow (e.g., 20/50)
      - regime filters
      - extended & volume filters
    """
    d = compute_indicators(df, p)

    # Primary crosses
    d["Sig_price_above_fast"] = crossed_above(d["Close"], d["EMA_fast"])
    d["Sig_price_below_fast"] = crossed_below(d["Close"], d["EMA_fast"])

    d["Sig_fast_above_slow"] = crossed_above(d["EMA_fast"], d["EMA_slow"])
    d["Sig_fast_below_slow"] = crossed_below(d["EMA_fast"], d["EMA_slow"])

    # Regime filters (trend context)
    d["Regime_Long"] = (d["Close"] > d["EMA_regime"]) & (d["EMA_slow"] > d["EMA_regime"])
    d["Regime_Short"] = (d["Close"] < d["EMA_regime"]) & (d["EMA_slow"] < d["EMA_regime"])

    # Slope filter on slow EMA (reduce fake flips)
    d["SlowEMA_SlopeUp"] = d["EMA_slow"] > d["EMA_slow"].shift(3)
    d["SlowEMA_SlopeDn"] = d["EMA_slow"] < d["EMA_slow"].shift(3)

    # Extension filter (avoid buying stretched moves)
    d["DistFast_ATR"] = (d["Close"] - d["EMA_fast"]).abs() / d["ATR"]
    d["NotExtended"] = d["DistFast_ATR"] < p.max_ext_atr

    # Volume confirmation
    d["VolConfirm"] = d["Volume"] >= (p.min_vol_mult * d["VolSMA"])

    # Composite entry conditions (you can tweak)
    d["LongEntry_price_x_fast"] = (
        d["Sig_price_above_fast"] & d["Regime_Long"] & d["SlowEMA_SlopeUp"] & d["NotExtended"] & d["VolConfirm"]
    )
    d["LongEntry_fast_x_slow"] = (
        d["Sig_fast_above_slow"] & d["Regime_Long"] & d["SlowEMA_SlopeUp"] & d["NotExtended"] & d["VolConfirm"]
    )

    d["ShortEntry_price_x_fast"] = (
        d["Sig_price_below_fast"] & d["Regime_Short"] & d["SlowEMA_SlopeDn"] & d["NotExtended"] & d["VolConfirm"]
    )
    d["ShortEntry_fast_x_slow"] = (
        d["Sig_fast_below_slow"] & d["Regime_Short"] & d["SlowEMA_SlopeDn"] & d["NotExtended"] & d["VolConfirm"]
    )

    # Golden/Death cross (slow/very-slow) – background info
    d["GoldenCross_50_200"] = crossed_above(ema(d["Close"], 50), ema(d["Close"], 200))
    d["DeathCross_50_200"]  = crossed_below(ema(d["Close"], 50), ema(d["Close"], 200))

    return d

# ---------------------------
# Simple vectorized backtest (entry on signal, exit on opposite)
# ---------------------------

@dataclass
class BacktestConfig:
    entry_col: str                    # e.g., "LongEntry_fast_x_slow"
    side: str = "long"                # "long" or "short"
    exit_on: str = "opposite"         # "opposite" or "ema_fast_cross"
    risk_stop_atr: float = 2.0        # optional stop: 2*ATR from entry
    take_profit_atr: Optional[float] = None

def backtest(df: pd.DataFrame, cfg: BacktestConfig, p: EMAParams) -> Dict[str, float]:
    d = df.copy()
    d = compute_indicators(d, p)
    entries = d[cfg.entry_col].fillna(False)

    # Define exit signal
    if cfg.exit_on == "opposite":
        if cfg.side == "long":
            exits = crossed_below(d["EMA_fast"], d["EMA_slow"]) | crossed_below(d["Close"], d["EMA_fast"])
        else:
            exits = crossed_above(d["EMA_fast"], d["EMA_slow"]) | crossed_above(d["Close"], d["EMA_fast"])
    else:
        if cfg.side == "long":
            exits = crossed_below(d["Close"], d["EMA_fast"])
        else:
            exits = crossed_above(d["Close"], d["EMA_fast"])

    # Build position series (1, 0, or -1)
    pos = pd.Series(0, index=d.index, dtype=float)
    in_trade = False
    entry_price = np.nan
    atr_series = d["ATR"]

    for i, (ts, row) in enumerate(d.iterrows()):
        if not in_trade and entries.iloc[i]:
            in_trade = True
            pos.iloc[i] = 1.0 if cfg.side == "long" else -1.0
            entry_price = row["Close"]
        elif in_trade:
            # risk stops / take profits
            if cfg.risk_stop_atr is not None and not np.isnan(atr_series.iloc[i]):
                stop = entry_price - cfg.risk_stop_atr * atr_series.iloc[i] if cfg.side == "long" else entry_price + cfg.risk_stop_atr * atr_series.iloc[i]
                if (cfg.side == "long" and row["Low"] <= stop) or (cfg.side == "short" and row["High"] >= stop):
                    in_trade = False
                    entry_price = np.nan
                    pos.iloc[i] = 0.0
                    continue
            if cfg.take_profit_atr is not None and not np.isnan(atr_series.iloc[i]):
                tp = entry_price + cfg.take_profit_atr * atr_series.iloc[i] if cfg.side == "long" else entry_price - cfg.take_profit_atr * atr_series.iloc[i]
                if (cfg.side == "long" and row["High"] >= tp) or (cfg.side == "short" and row["Low"] <= tp):
                    in_trade = False
                    entry_price = np.nan
                    pos.iloc[i] = 0.0
                    continue

            # exit condition
            if exits.iloc[i]:
                in_trade = False
                entry_price = np.nan
                pos.iloc[i] = 0.0
            else:
                pos.iloc[i] = 1.0 if cfg.side == "long" else -1.0

    # Compute returns
    ret = d["Close"].pct_change().fillna(0.0)
    strat_ret = ret * pos.shift(1).fillna(0.0)  # enter next bar open/close assumption simplified
    equity = (1 + strat_ret).cumprod()

    # Metrics
    cagr = equity.iloc[-1] ** (252/len(equity)) - 1 if len(equity) > 252 else equity.iloc[-1] - 1
    maxdd = ((equity / equity.cummax()) - 1).min()
    vol = strat_ret.std() * np.sqrt(252)
    sharpe = (strat_ret.mean() * 252) / (strat_ret.std() * np.sqrt(252) + 1e-12)

    return {
        "CAGR": float(cagr),
        "MaxDrawdown": float(maxdd),
        "Volatility": float(vol),
        "Sharpe": float(sharpe),
        "Trades": int(entries.sum()),
    }

# ---------------------------
# Convenience: run scanner on many tickers
# ---------------------------

def scan_signals(data_by_symbol: Dict[str, pd.DataFrame], p: EMAParams) -> pd.DataFrame:
    """
    data_by_symbol: { "AAPL": df, ... } each df must have OHLCV with DatetimeIndex
    Returns a compact table of today's signals per symbol.
    """
    rows = []
    for sym, df in data_by_symbol.items():
        d = ema_signals(df, p)
        last = d.iloc[-1]
        rows.append({
            "Symbol": sym,
            "Close": df["Close"].iloc[-1],
            f"price_x_EMA{p.fast}_bull": bool(last["Sig_price_above_fast"]),
            f"EMA{p.fast}_x_EMA{p.slow}_bull": bool(last["Sig_fast_above_slow"]),
            "Regime_Long": bool(last["Regime_Long"]),
            "NotExtended": bool(last["NotExtended"]),
            "VolConfirm": bool(last["VolConfirm"]),
            "RSI": float(last["RSI"]),
            "GoldenCross_50_200": bool(last["GoldenCross_50_200"]),
        })
    return pd.DataFrame(rows).set_index("Symbol")

# Optional helper (internet required):
def fetch_yf(symbol: str, period="1y", interval="1d") -> pd.DataFrame:
    import yfinance as yf
    df = yf.download(symbol, period=period, interval=interval, auto_adjust=False, progress=False)
    df = df.rename(columns=str.title)[["Open","High","Low","Close","Volume"]]
    return df.dropna()
