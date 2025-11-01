# EMA PRICE and EMA CROSS Calculation

## How They're Calculated

### EMA PRICE (Line 334)
**Formula:** `ema_price_comp = clip((price - EMA_short) / EMA_short, -0.1, 0.1)`

**Example:**
- Price: $100
- EMA-20: $95
- Calculation: (100 - 95) / 95 = 0.0526
- Result: 0.0526 (price is 5.26% above the short EMA = bullish signal)

**Interpretation:**
- **Positive value**: Price is above the short EMA (bullish)
- **Negative value**: Price is below the short EMA (bearish)
- **Clipped** to range [-0.1, 0.1] to prevent extreme values

### EMA CROSS (Line 336)
**Formula:** `ema_cross_comp = clip((EMA_short - EMA_long) / EMA_long, -0.1, 0.1)`

**Example:**
- EMA-20: $95
- EMA-50: $90
- Calculation: (95 - 90) / 90 = 0.0556
- Result: 0.0556 (short EMA is 5.56% above long EMA = bullish trend)

**Interpretation:**
- **Positive value**: Short EMA above long EMA (uptrend)
- **Negative value**: Short EMA below long EMA (downtrend)
- **Clipped** to range [-0.1, 0.1]

## How They Contribute to the Score

### Both use the SAME weight (`w_ema_cross`)

```python
# From scanner.py lines 397-409
if criteria.w_ema_cross > 0 and (pd.notnull(ema_price_comp) or pd.notnull(ema_cross_comp)):
    if pd.notnull(ema_price_comp):
        component_info["ema_price"] = {
            "raw": float(ema_price_comp),
            "weight": criteria.w_ema_cross,  # Same weight
            "contribution": float(criteria.w_ema_cross * ema_price_comp)
        }
    if pd.notnull(ema_cross_comp):
        component_info["ema_cross"] = {
            "raw": float(ema_cross_comp),
            "weight": criteria.w_ema_cross,  # Same weight
            "contribution": float(criteria.w_ema_cross * ema_cross_comp)
        }
```

### Example Calculation

**Scenario:**
- Price: $100, EMA-20: $95, EMA-50: $90
- User sets `w_ema_cross` = 2.0

**EMA PRICE:**
- Raw: 0.0526 (price 5.26% above EMA-20)
- Weight: 2.0
- Contribution: 0.0526 × 2.0 = 0.1052

**EMA CROSS:**
- Raw: 0.0556 (EMA-20 is 5.56% above EMA-50)
- Weight: 2.0
- Contribution: 0.0556 × 2.0 = 0.1112

**Total EMA Contribution to Score:**
- EMA PRICE contribution: 0.1052
- EMA CROSS contribution: 0.1112
- **Total: 0.2164**

## Why Two Components?

1. **EMA PRICE**: Measures current price position vs short-term trend
   - Shows if price is "overshooting" or "undershooting" the short EMA
   - Indicates immediate momentum

2. **EMA CROSS**: Measures trend direction (short vs long EMA relationship)
   - Shows if the overall trend is bullish or bearish
   - Indicates trend strength and direction

**Both together** give a complete picture of both short-term momentum and overall trend strength.

## Visual Example

```
Price: $100 (current)
EMA-20: $95 (short-term average)
EMA-50: $90 (long-term average)

ema_price_comp = (100-95)/95 = +0.0526 (price above short EMA = bullish)
ema_cross_comp = (95-90)/90 = +0.0556 (short EMA above long EMA = uptrend)

If w_ema_cross = 2.0:
  - ema_price contribution = 0.1052
  - ema_cross contribution = 0.1112
  - Total EMA contribution = 0.2164
```

This shows the stock is in a strong uptrend (short EMA > long EMA) AND the price is above the short-term average, creating a bullish signal.

