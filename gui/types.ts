// FIX: Import React to make the JSX namespace available and resolve "Cannot find namespace 'JSX'" errors.
// The unused ReactNode import was also removed.
import React from 'react';
import type { SVGProps } from 'react';

export interface CryptoData {
  name: string;
  price: number;
  // FIX: Changed JSX.Element to React.ReactElement to resolve `Cannot find namespace 'JSX'` error on line 9.
  icon: (props: SVGProps<SVGSVGElement>) => React.ReactElement;
}

export interface ModelData {
  id: string;
  name: string;
  value: number;
  color: string;
  // FIX: Changed JSX.Element to React.ReactElement to resolve `Cannot find namespace 'JSX'` error on line 17.
  // Updated to include size prop for @lobehub/icons compatibility
  icon: (props: { className?: string; style?: React.CSSProperties; size?: number; [key: string]: any }) => React.ReactElement;
}

export interface ChartPoint {
  date: string;
  [key: string]: number | string;
}

export interface Position {
  side: 'LONG' | 'SHORT';
  coin: string;
  // FIX: Changed JSX.Element to React.ReactElement to resolve `Cannot find namespace 'JSX'` error on line 28.
  coinIcon: (props: SVGProps<SVGSVGElement>) => React.ReactElement;
  notional: number;
  unrealPL: number;
}

export interface ModelPositions {
  modelId: string;
  totalUnrealizedPL: number;
  availableCash: number;
  positions: Position[];
}