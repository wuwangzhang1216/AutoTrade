
import type { SVGProps } from 'react';
import React from 'react';
// Official AI Model Icons from @lobehub/icons
import { OpenAI, Claude, Gemini, Grok, DeepSeek, Qwen } from '@lobehub/icons';

// Official Cryptocurrency Icons from cryptocurrency-icons package
import BtcSvg from 'cryptocurrency-icons/svg/color/btc.svg';
import EthSvg from 'cryptocurrency-icons/svg/color/eth.svg';
import SolSvg from 'cryptocurrency-icons/svg/color/sol.svg';
import BnbSvg from 'cryptocurrency-icons/svg/color/bnb.svg';
import DogeSvg from 'cryptocurrency-icons/svg/color/doge.svg';
import XrpSvg from 'cryptocurrency-icons/svg/color/xrp.svg';

export const BtcIcon = (props: { className?: string; style?: React.CSSProperties; size?: number }) => {
  const { size = 24, ...rest } = props;
  return <img src={BtcSvg} alt="Bitcoin" width={size} height={size} {...rest} />;
};

export const EthIcon = (props: { className?: string; style?: React.CSSProperties; size?: number }) => {
  const { size = 24, ...rest } = props;
  return <img src={EthSvg} alt="Ethereum" width={size} height={size} {...rest} />;
};

export const SolIcon = (props: { className?: string; style?: React.CSSProperties; size?: number }) => {
  const { size = 24, ...rest } = props;
  return <img src={SolSvg} alt="Solana" width={size} height={size} {...rest} />;
};

export const BnbIcon = (props: { className?: string; style?: React.CSSProperties; size?: number }) => {
  const { size = 24, ...rest } = props;
  return <img src={BnbSvg} alt="BNB" width={size} height={size} {...rest} />;
};

export const DogeIcon = (props: { className?: string; style?: React.CSSProperties; size?: number }) => {
  const { size = 24, ...rest } = props;
  return <img src={DogeSvg} alt="Dogecoin" width={size} height={size} {...rest} />;
};

export const XrpIcon = (props: { className?: string; style?: React.CSSProperties; size?: number }) => {
  const { size = 24, ...rest } = props;
  return <img src={XrpSvg} alt="Ripple" width={size} height={size} {...rest} />;
};

// Official AI Model Icons using @lobehub/icons
export const GptIcon = (props: { className?: string; style?: React.CSSProperties; [key: string]: any }) => (
  <OpenAI {...props} />
);

export const ClaudeIcon = (props: { className?: string; style?: React.CSSProperties; [key: string]: any }) => (
  <Claude {...props} />
);

export const GeminiIcon = (props: { className?: string; style?: React.CSSProperties; [key: string]: any }) => (
  <Gemini {...props} />
);

export const GrokIcon = (props: { className?: string; style?: React.CSSProperties; [key: string]: any }) => (
  <Grok {...props} />
);

export const DeepseekIcon = (props: { className?: string; style?: React.CSSProperties; [key: string]: any }) => (
  <DeepSeek {...props} />
);

export const QwenIcon = (props: { className?: string; style?: React.CSSProperties; [key: string]: any }) => (
  <Qwen {...props} />
);
