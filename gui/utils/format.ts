/**
 * Utility functions for safe number formatting that handle null/undefined values
 */

/**
 * Safely format a number as currency
 * Returns "N/A" if value is null/undefined/NaN
 */
export function formatCurrency(
  value: number | null | undefined,
  options?: {
    minimumFractionDigits?: number;
    maximumFractionDigits?: number;
    fallback?: string;
  }
): string {
  const { minimumFractionDigits = 0, maximumFractionDigits = 0, fallback = 'N/A' } = options || {};

  if (value === null || value === undefined || isNaN(value)) {
    return fallback;
  }

  return `$${value.toLocaleString('en-US', { minimumFractionDigits, maximumFractionDigits })}`;
}

/**
 * Safely format a number as a percentage
 * Returns "N/A" if value is null/undefined/NaN
 */
export function formatPercent(
  value: number | null | undefined,
  options?: {
    decimals?: number;
    showSign?: boolean;
    fallback?: string;
  }
): string {
  const { decimals = 2, showSign = true, fallback = 'N/A' } = options || {};

  if (value === null || value === undefined || isNaN(value)) {
    return fallback;
  }

  const sign = showSign && value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(decimals)}%`;
}

/**
 * Safely format a number with decimal places
 * Returns "N/A" if value is null/undefined/NaN
 */
export function formatNumber(
  value: number | null | undefined,
  options?: {
    decimals?: number;
    fallback?: string;
  }
): string {
  const { decimals = 0, fallback = 'N/A' } = options || {};

  if (value === null || value === undefined || isNaN(value)) {
    return fallback;
  }

  return decimals > 0 ? value.toFixed(decimals) : value.toLocaleString('en-US');
}

/**
 * Safely format a price value
 * Returns "N/A" if value is null/undefined/NaN
 * Automatically adjusts decimal places based on price magnitude
 */
export function formatPrice(
  value: number | null | undefined,
  options?: {
    fallback?: string;
  }
): string {
  const { fallback = 'N/A' } = options || {};

  if (value === null || value === undefined || isNaN(value)) {
    return fallback;
  }

  const decimals = value < 1 ? 4 : 2;
  return `$${value.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}`;
}
