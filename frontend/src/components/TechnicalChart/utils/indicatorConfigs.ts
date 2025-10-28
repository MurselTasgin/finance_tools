// TechnicalChart/utils/indicatorConfigs.ts
import { IndicatorConfig } from '../types/chart.types';

/**
 * Complete indicator configuration catalog
 *
 * Defines all available indicators with their default parameters and UI configurations
 */
export const INDICATOR_CONFIGS: Record<string, IndicatorConfig> = {
  ema_cross: {
    id: 'ema_cross',
    name: 'EMA Cross',
    description: 'Exponential Moving Average crossover strategy',
    type: 'overlay',
    defaultParameters: {
      short: 12,
      long: 26,
    },
    parameterDefinitions: [
      {
        key: 'short',
        label: 'Short Period',
        type: 'number',
        defaultValue: 12,
        min: 2,
        max: 100,
        step: 1,
        description: 'Fast EMA period',
      },
      {
        key: 'long',
        label: 'Long Period',
        type: 'number',
        defaultValue: 26,
        min: 2,
        max: 200,
        step: 1,
        description: 'Slow EMA period',
      },
    ],
  },

  ema_regime: {
    id: 'ema_regime',
    name: 'EMA Regime',
    description: 'Multi-timeframe EMA regime analysis',
    type: 'overlay',
    defaultParameters: {
      short: 8,
      medium: 21,
      long: 55,
    },
    parameterDefinitions: [
      {
        key: 'short',
        label: 'Short EMA',
        type: 'number',
        defaultValue: 8,
        min: 2,
        max: 50,
        step: 1,
      },
      {
        key: 'medium',
        label: 'Medium EMA',
        type: 'number',
        defaultValue: 21,
        min: 10,
        max: 100,
        step: 1,
      },
      {
        key: 'long',
        label: 'Long EMA',
        type: 'number',
        defaultValue: 55,
        min: 20,
        max: 200,
        step: 1,
      },
    ],
  },

  rsi: {
    id: 'rsi',
    name: 'RSI',
    description: 'Relative Strength Index',
    type: 'subplot',
    defaultParameters: {
      period: 14,
      overbought: 70,
      oversold: 30,
    },
    parameterDefinitions: [
      {
        key: 'period',
        label: 'Period',
        type: 'number',
        defaultValue: 14,
        min: 2,
        max: 50,
        step: 1,
        description: 'RSI calculation period',
      },
      {
        key: 'overbought',
        label: 'Overbought Level',
        type: 'number',
        defaultValue: 70,
        min: 50,
        max: 90,
        step: 5,
      },
      {
        key: 'oversold',
        label: 'Oversold Level',
        type: 'number',
        defaultValue: 30,
        min: 10,
        max: 50,
        step: 5,
      },
    ],
  },

  macd: {
    id: 'macd',
    name: 'MACD',
    description: 'Moving Average Convergence Divergence',
    type: 'subplot',
    defaultParameters: {
      fast: 12,
      slow: 26,
      signal: 9,
    },
    parameterDefinitions: [
      {
        key: 'fast',
        label: 'Fast Period',
        type: 'number',
        defaultValue: 12,
        min: 2,
        max: 50,
        step: 1,
      },
      {
        key: 'slow',
        label: 'Slow Period',
        type: 'number',
        defaultValue: 26,
        min: 10,
        max: 100,
        step: 1,
      },
      {
        key: 'signal',
        label: 'Signal Period',
        type: 'number',
        defaultValue: 9,
        min: 2,
        max: 30,
        step: 1,
      },
    ],
  },

  stochastic: {
    id: 'stochastic',
    name: 'Stochastic',
    description: 'Stochastic Oscillator',
    type: 'subplot',
    defaultParameters: {
      k_period: 14,
      d_period: 3,
      overbought: 80,
      oversold: 20,
    },
    parameterDefinitions: [
      {
        key: 'k_period',
        label: '%K Period',
        type: 'number',
        defaultValue: 14,
        min: 2,
        max: 50,
        step: 1,
      },
      {
        key: 'd_period',
        label: '%D Period',
        type: 'number',
        defaultValue: 3,
        min: 2,
        max: 20,
        step: 1,
      },
      {
        key: 'overbought',
        label: 'Overbought',
        type: 'number',
        defaultValue: 80,
        min: 50,
        max: 100,
        step: 5,
      },
      {
        key: 'oversold',
        label: 'Oversold',
        type: 'number',
        defaultValue: 20,
        min: 0,
        max: 50,
        step: 5,
      },
    ],
  },

  momentum: {
    id: 'momentum',
    name: 'Momentum',
    description: 'Price momentum indicator',
    type: 'subplot',
    defaultParameters: {
      period: 10,
    },
    parameterDefinitions: [
      {
        key: 'period',
        label: 'Period',
        type: 'number',
        defaultValue: 10,
        min: 2,
        max: 50,
        step: 1,
      },
    ],
  },

  volume: {
    id: 'volume',
    name: 'Volume Analysis',
    description: 'Volume-based indicators',
    type: 'subplot',
    defaultParameters: {
      sma_period: 20,
    },
    parameterDefinitions: [
      {
        key: 'sma_period',
        label: 'SMA Period',
        type: 'number',
        defaultValue: 20,
        min: 5,
        max: 100,
        step: 5,
      },
    ],
  },

  atr: {
    id: 'atr',
    name: 'ATR',
    description: 'Average True Range',
    type: 'subplot',
    defaultParameters: {
      period: 14,
    },
    parameterDefinitions: [
      {
        key: 'period',
        label: 'Period',
        type: 'number',
        defaultValue: 14,
        min: 5,
        max: 50,
        step: 1,
      },
    ],
  },

  adx: {
    id: 'adx',
    name: 'ADX',
    description: 'Average Directional Index',
    type: 'subplot',
    defaultParameters: {
      period: 14,
    },
    parameterDefinitions: [
      {
        key: 'period',
        label: 'Period',
        type: 'number',
        defaultValue: 14,
        min: 5,
        max: 50,
        step: 1,
      },
    ],
  },

  sentiment: {
    id: 'sentiment',
    name: 'Sentiment',
    description: 'Market sentiment analysis',
    type: 'subplot',
    defaultParameters: {
      lookback: 20,
    },
    parameterDefinitions: [
      {
        key: 'lookback',
        label: 'Lookback Period',
        type: 'number',
        defaultValue: 20,
        min: 5,
        max: 100,
        step: 5,
      },
    ],
  },
};

/**
 * Get all available indicators
 */
export function getAllIndicators(): IndicatorConfig[] {
  return Object.values(INDICATOR_CONFIGS);
}

/**
 * Get indicator by ID
 */
export function getIndicatorById(id: string): IndicatorConfig | undefined {
  return INDICATOR_CONFIGS[id];
}

/**
 * Get indicators by type
 */
export function getIndicatorsByType(
  type: 'overlay' | 'subplot'
): IndicatorConfig[] {
  return getAllIndicators().filter((ind) => ind.type === type);
}

/**
 * Get overlay indicators
 */
export function getOverlayIndicators(): IndicatorConfig[] {
  return getIndicatorsByType('overlay');
}

/**
 * Get subplot indicators
 */
export function getSubplotIndicators(): IndicatorConfig[] {
  return getIndicatorsByType('subplot');
}

/**
 * Validate indicator parameters against definitions
 */
export function validateIndicatorParameters(
  indicatorId: string,
  parameters: Record<string, any>
): { valid: boolean; errors: string[] } {
  const config = getIndicatorById(indicatorId);
  if (!config) {
    return { valid: false, errors: [`Unknown indicator: ${indicatorId}`] };
  }

  const errors: string[] = [];

  config.parameterDefinitions.forEach((def) => {
    const value = parameters[def.key];

    if (value === undefined || value === null) {
      errors.push(`Missing parameter: ${def.label}`);
      return;
    }

    if (def.type === 'number') {
      const numValue = Number(value);
      if (isNaN(numValue)) {
        errors.push(`${def.label} must be a number`);
      } else {
        if (def.min !== undefined && numValue < def.min) {
          errors.push(`${def.label} must be at least ${def.min}`);
        }
        if (def.max !== undefined && numValue > def.max) {
          errors.push(`${def.label} must be at most ${def.max}`);
        }
      }
    }
  });

  return { valid: errors.length === 0, errors };
}
