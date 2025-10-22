import type { CryptoData, ModelData, ChartPoint, ModelPositions } from './types';
import {
  BtcIcon,
  EthIcon,
  SolIcon,
  BnbIcon,
  DogeIcon,
  XrpIcon,
  GptIcon,
  ClaudeIcon,
  GeminiIcon,
  GrokIcon,
  DeepseekIcon,
  QwenIcon
} from './components/Icons';

// NOTE: All hardcoded data removed - GUI now uses REAL data from backend APIs
// Crypto ticker data is fetched via useMarketData hook from /api/market/{symbol}
export const CRYPTO_TICKER_DATA: CryptoData[] = [];

// Model metadata (icons and colors) - values are fetched from API
export const MODELS_DATA: ModelData[] = [
  { id: 'gpt5', name: 'GPT 5', value: 10000, color: '#10B981', icon: GptIcon },
  { id: 'claude', name: 'CLAUDE SONNET 4.5', value: 10000, color: '#F59E0B', icon: ClaudeIcon },
  { id: 'gemini', name: 'GEMINI 2.5 PRO', value: 10000, color: '#6366F1', icon: GeminiIcon },
  { id: 'grok', name: 'GROK 4', value: 10000, color: '#D1D5DB', icon: GrokIcon },
  { id: 'deepseek', name: 'DEEPSEEK CHAT V3.1', value: 10000, color: '#60A5FA', icon: DeepseekIcon },
  { id: 'qwen', name: 'QWEN3 MAX', value: 10000, color: '#A855F7', icon: QwenIcon },
  { id: 'btcHold', name: 'BTC BUY&HOLD', value: 10000, color: '#9CA3AF', icon: BtcIcon },
];

// Chart data - replaced with real API data
// Keeping one data point for initial render, will be replaced by real data
export const CHART_DATA: ChartPoint[] = [
    { date: "Now", gpt5: 10000, claude: 10000, gemini: 10000, grok: 10000, deepseek: 10000, qwen: 10000, btcHold: 10000},
];

// Positions data - replaced with real API data from /api/positions/all
export const POSITIONS_DATA: ModelPositions[] = [];
