# 当前 AI 智能体配置详解

> 生成时间：2025-11-07
> 位置：`backend/ai/`

---

## 📋 目录

1. [AI 模型配置](#1-ai-模型配置)
2. [System Prompt (系统提示词)](#2-system-prompt-系统提示词)
3. [User Prompt (用户提示词结构)](#3-user-prompt-用户提示词结构)
4. [决策输出格式](#4-决策输出格式)
5. [投票和执行机制](#5-投票和执行机制)
6. [当前问题分析](#6-当前问题分析)

---

## 1. AI 模型配置

### 使用的模型

```python
# 配置位置: backend/config/settings.py

# 主模型（Model 1）
AI_MODEL_PRIMARY = "deepseek/deepseek-chat-v3.1"
# 特点：成本低、速度快、通用对话模型

# 次模型（Model 2）
AI_MODEL_SECONDARY = "qwen/qwen3-vl-235b-a22b-instruct"
# 特点：多模态、支持视觉理解（但本系统未使用视觉功能）
```

### API 配置

```python
# 配置位置: backend/config/settings.py

# 温度（创造性）
TEMPERATURE = 0.7
# 0.0 = 完全确定性，2.0 = 高度随机
# 0.7 = 中等，允许一些创造性但保持相对稳定

# 最大Token数
MAX_TOKENS = 1000
# 限制AI响应长度，控制成本

# API 超时设置
API_REQUEST_TIMEOUT = 60  # 秒
# 单个API请求的最大等待时间

DECISION_TIMEOUT = 90  # 秒
# 双模型决策的总超时时间（需要 > API_REQUEST_TIMEOUT）

# 最低置信度阈值
MIN_CONFIDENCE = 0.6  # 60%
# 只有置信度 ≥ 60% 的决策才会被执行

# 投票策略
VOTING_STRATEGY = "majority"
# 选项: "majority" | "unanimous" | "weighted"
```

---

## 2. System Prompt (系统提示词)

### 完整内容

```
You are an expert cryptocurrency trading AI assistant for a quantitative trading system.

Your role is to analyze market data (both technical and fundamental) and provide clear
trading recommendations.

You must respond with a valid JSON object in this exact format:
{
  "decision": "BUY" | "SELL" | "HOLD",
  "confidence": 0.0 to 1.0,
  "reasoning": "Your detailed explanation"
}
```

### 关键指引

#### 1. 决策类型
```
- decision: Must be exactly one of: "BUY", "SELL", or "HOLD"
```

#### 2. 持仓管理机制（核心逻辑）

```
POSITION CLOSING MECHANISM (CRITICAL):
----------------------------------------

IF YOU HAVE A LONG POSITION:
  - BUY → Add to long position (stack/average up)
  - SELL → CLOSE the long position (take profit or cut loss)
  - HOLD → Keep the long position open

IF YOU HAVE A SHORT POSITION:
  - BUY → CLOSE the short position (take profit or cut loss)
  - SELL → Add to short position (stack/average down)
  - HOLD → Keep the short position open

IF YOU HAVE NO POSITION:
  - BUY → Open new long position (expect price to rise)
  - SELL → Open new short position (expect price to fall)
  - HOLD → Stay out of market, wait for better opportunity
```

#### 3. 何时平仓（建议性，非强制）

```
WHEN TO CLOSE POSITIONS:
- Close losing positions: If P&L is significantly negative (e.g., -5% or worse)
- Take profit: If P&L meets target (e.g., +10% or better)
- Market reversal: If technical signals suggest trend has reversed
- Risk management: If approaching liquidation price or stop loss levels
```

⚠️ **问题**: 这些只是"建议"，AI可以忽略

#### 4. 置信度标准

```
confidence: Your confidence level as a decimal number (0.0 to 1.0)
  - 0.8-1.0: Strong signal, high confidence
  - 0.6-0.8: Moderate signal, good confidence
  - 0.4-0.6: Weak signal, low confidence
  - Below 0.4: Very uncertain, recommend HOLD
```

#### 5. 推理要素

```
reasoning: Explain your decision based on:
  1. Position management (if you have an open position, should you close it?)
  2. Technical indicators (trend, momentum, overbought/oversold)
  3. Fundamental factors (sentiment, news, social activity)
  4. Risk considerations and P&L targets
  5. Market context and timing
```

#### 6. 输出要求

```
IMPORTANT: Return ONLY valid JSON, no additional text before or after the JSON object.
Be concise but thorough in your reasoning. Focus on actionable insights.
```

---

## 3. User Prompt (用户提示词结构)

AI 接收的完整输入包含以下部分：

### 3.1 交易上下文（Trading Context）

```
═══════════════════════════════════════════════════════════════════
                        TRADING CONTEXT
═══════════════════════════════════════════════════════════════════

CURRENT TIME & MARKET SESSION:
- Date & Time: 2025-11-07 15:30:00 UTC
- Day of Week: Thursday
- Trading Session: US/European Active Hours (High Liquidity)

ACCOUNT STATUS:
- Total Equity: $10,500.00
- Available Capital: $6,000.00 (57.1% free)
- Total P&L: $500.00 (+5.00%)
- Open Positions: 2/5 slots used
```

**判断逻辑**:
- 交易时段：UTC 13:00-21:00 = 高流动性，0:00-8:00 = 亚洲时段，其他 = 非高峰
- 资金利用率：如果 < 30% 会提醒"资金有限，谨慎开仓"

### 3.2 持仓状态（Position Status）

```
POSITION STATUS FOR THIS SYMBOL:
OPEN LONG position
  - Entry Price: $50,000.00
  - Current P&L: $1,500.00 (+10.00%)
  - Margin Used: $1,500.00
  - Duration: 120 minutes
  - Liquidation Price: $47,250.00
  ⚠️  SIGNIFICANT PROFIT - Consider taking profit
```

**自动警告**:
- PnL > +10% → 提醒止盈
- PnL < -5% → 提醒风险管理

### 3.3 历史决策（Historical Context）

```
HISTORICAL CONTEXT:
Last Decision: BUY at $49,000.00 (2 hours ago) - ✓ EXECUTED
  - Average Confidence: 0.72
```

### 3.4 交易表现（Trading Performance）

```
TRADING PERFORMANCE RECORD:
- Total Completed Trades: 12
- Win Rate: 58.3% (7W / 5L)
  ~ MODERATE PERFORMANCE - Profitable but room for improvement
```

**自动评估**:
- 胜率 ≥ 70% → "表现强劲"
- 胜率 50-70% → "中等表现"
- 胜率 30-50% → "表现不佳，建议保守"
- 胜率 < 30% → "严重问题，非常谨慎"

### 3.5 技术分析（Technical Analysis）

```
TECHNICAL ANALYSIS for BTC/USDT:
- Current Price: $50,500.00
- Technical Recommendation: BUY
- Bullish Signals: 70.0%
- Key Signals:
  - Moving Average: BULLISH (Golden Cross)
  - MACD: BULLISH (Above signal line)
  - RSI: NEUTRAL (RSI=55, not overbought/oversold)
  - Bollinger Bands: NEUTRAL (Mid-band)
  - Trend Strength: STRONG (ADX=32)
- Support: $49,000.00 (3.0% below)
- Resistance: $52,000.00 (2.97% above)
```

### 3.6 基本面分析（Fundamental Analysis）

```
FUNDAMENTAL ANALYSIS:
- Fundamental Score: 65.0/100
- Fundamental Recommendation: BUY
- Fear & Greed Index: 55/100 (Neutral)
  Market shows balanced sentiment
- News Sentiment: Positive (Score: 0.6)
  Recent News: 15 articles
- Social Metrics:
  - Galaxy Score: 75
  - Social Volume: High
  - Sentiment: Bullish

MARKET CONTEXT:
- BTC Dominance: 45.2%
- Market Cap Change 24h: +2.30%
```

### 3.7 决策要素指导（Decision Factors）

```
IMPORTANT DECISION FACTORS:

1. POSITION MANAGEMENT (HIGHEST PRIORITY):

   IF YOU HAVE AN OPEN POSITION FOR THIS SYMBOL:
   - Check the current P&L percentage and absolute value
   - Evaluate if conditions have changed since entry
   - Decide whether to CLOSE the position or HOLD it:

   TO CLOSE A LOSING POSITION (Cut Loss):
     • If LONG and losing → recommend SELL (this closes the long)
     • If SHORT and losing → recommend BUY (this closes the short)
     • Consider closing if: P&L < -5%, trend reversed, or risk too high

   TO CLOSE A WINNING POSITION (Take Profit):
     • If LONG and profitable → recommend SELL (this closes the long)
     • If SHORT and profitable → recommend BUY (this closes the short)
     • Consider closing if: P&L > +10%, overbought/oversold, or reversal signals

   TO HOLD THE POSITION:
     • Recommend HOLD if position is still valid and target not reached
     • Only hold if trend continues and risk is manageable

2. NEW POSITION ENTRY (if no current position):
   - Only recommend BUY/SELL if you see a strong opportunity
   - Check available capital before recommending new positions
   - With limited capital, be highly selective

3. PERFORMANCE AWARENESS:
   - If win rate is low (<50%), be more conservative and focus on closing losers
   - If performing well (>70%), maintain current strategy
   - Learn from past decisions for this symbol

4. MARKET TIMING:
   - High liquidity sessions are better for entries/exits
   - Avoid major position changes during off-peak hours

5. RISK MANAGEMENT:
   - Never let losses grow beyond -10% without closing
   - Always have a clear profit target and stop loss in mind
   - Preserve capital for future opportunities

REMEMBER: Your primary job when you have an open position is to ACTIVELY MANAGE it.
Don't just HOLD losing positions hoping they recover - close them if conditions have worsened.
Don't be afraid to SELL (close LONG) or BUY (close SHORT) to protect profits or cut losses.
```

---

## 4. 决策输出格式

### 4.1 标准 JSON 格式

```json
{
  "decision": "BUY",
  "confidence": 0.75,
  "reasoning": "Strong bullish momentum with golden cross and positive fundamentals. RSI not overbought. Good entry opportunity."
}
```

### 4.2 增强的 JSON Schema（强制验证）

系统使用严格的 JSON Schema 确保输出格式：

```json
{
  "type": "object",
  "properties": {
    "decision": {
      "type": "string",
      "enum": ["BUY", "SELL", "HOLD"]
    },
    "confidence": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "description": "MUST be decimal 0.0-1.0, NOT percentage"
    },
    "reasoning": {
      "type": "string",
      "minLength": 50,
      "maxLength": 500
    }
  },
  "required": ["decision", "confidence", "reasoning"],
  "additionalProperties": false
}
```

### 4.3 置信度归一化

AI 可能返回不同格式的置信度，系统会自动归一化：

```python
# 智能检测和转换
if 0.0 <= value <= 1.0:
    # 已经是正确格式 (e.g., 0.75)
    confidence = value

elif 1.0 < value <= 10.0:
    # 1-10 评分制 (e.g., 7.5)
    confidence = value / 10.0  # → 0.75

elif 10.0 < value <= 100.0:
    # 百分比制 (e.g., 75)
    confidence = value / 100.0  # → 0.75

else:
    # 异常值，强制限制并警告
    confidence = clamp(value / 100.0, 0.0, 1.0)
```

---

## 5. 投票和执行机制

### 5.1 双模型并行

```python
# 两个模型同时运行（ThreadPoolExecutor）
Model 1 (DeepSeek)  ─┐
                      ├─→ 并行执行 (最多90秒)
Model 2 (Qwen3)     ─┘

# 每个模型返回：
{
  "decision": "BUY",
  "confidence": 0.75,
  "reasoning": "..."
}
```

### 5.2 Majority 投票（当前默认）

```python
if model_1.decision == model_2.decision:
    # 两模型一致
    final_decision = model_1.decision
    avg_confidence = (conf_1 + conf_2) / 2

    # 质量检查
    if final_decision != "HOLD" and avg_confidence < 0.6:
        # 即使一致，置信度不足 → 降级为 HOLD
        return "HOLD"

    return final_decision

else:
    # 两模型分歧
    if |conf_1 - conf_2| >= 0.2:  # 20% 差距
        # 置信度差距大 → 采用高置信度方
        if conf_1 > conf_2 and conf_1 >= 0.6:
            return model_1.decision
        elif conf_2 > conf_1 and conf_2 >= 0.6:
            return model_2.decision
        else:
            return "HOLD"  # 虽有差距但都不足60%
    else:
        # 置信度接近且分歧 → 保守 HOLD
        return "HOLD"
```

### 5.3 Unanimous 投票（一致性）

```python
if model_1.decision == model_2.decision:
    avg_confidence = (conf_1 + conf_2) / 2

    if decision != "HOLD" and avg_confidence < 0.6:
        return "HOLD"

    return decision
else:
    # 不一致直接 HOLD
    return "HOLD"
```

### 5.4 Weighted 投票（加权）

```python
# 默认权重都是 0.5
weight_1 = 0.5
weight_2 = 0.5

score_1 = conf_1 * weight_1
score_2 = conf_2 * weight_2

if model_1.decision == model_2.decision:
    # 逻辑同 unanimous
    ...
else:
    # 加权分数决定
    if |score_1 - score_2| >= 0.15:  # 15% 差距
        winner = 高分方
        if winner.confidence >= 0.6:
            return winner.decision
        else:
            return "HOLD"
    else:
        # 分数接近 → HOLD
        return "HOLD"
```

### 5.5 执行过滤（最后关卡）

即使投票通过，还要检查是否真的执行：

```python
def should_execute_decision(final_decision, model_1, model_2):
    if final_decision == "HOLD":
        return False

    # 双模型可用
    if both_models_available:
        # 检查支持该决策的模型中的最高置信度
        max_confidence = max(支持决策的模型置信度)
        return max_confidence >= 0.6

    # 单模型可用（另一个失败）
    else:
        # 降低阈值 5%
        adjusted_threshold = 0.55
        return confidence >= adjusted_threshold
```

---

## 6. 当前问题分析

### 6.1 System Prompt 的问题

#### ❌ 问题 1: 建议性而非强制性

```
当前:
"Close losing positions: If P&L is significantly negative (e.g., -5% or worse)"
"Take profit: If P&L meets target (e.g., +10% or better)"

问题:
- 使用 "Consider closing" / "If P&L meets target"
- 这是建议，AI可以忽略
- 没有强制止损机制

改进方向:
- 添加硬性规则："P&L < -8% → 必须推荐 SELL/BUY 平仓"
- 分离"建议"和"强制"规则
```

#### ❌ 问题 2: 缺乏市场状态识别

```
当前:
- AI 需要自己从技术指标判断市场状态
- 没有明确的"趋势市场" vs "震荡市场"概念
- 可能在不同状态使用同一策略

改进方向:
- 先识别市场状态（trending/ranging/volatile）
- 根据状态使用不同策略
```

#### ❌ 问题 3: 缺乏事件响应指南

```
当前:
- 只有常规分析，没有突发事件处理
- 暴跌/暴涨时与平时一样处理

改进方向:
- 添加事件检测和响应规则
- 如："检测到5分钟内下跌3% → 立即评估是恐慌还是基本面"
```

#### ❌ 问题 4: 仓位管理指导不足

```
当前:
- 只告诉 AI "BUY = 开多/加仓"
- 没有仓位大小的指导

改进方向:
- 输出中要求 AI 推荐仓位大小
- "position_size_recommendation": "3%" | "5%" | "8%"
```

### 6.2 模型选择的问题

#### ❌ 问题: 使用通用 LLM 而非金融专用模型

```
当前:
- DeepSeek Chat v3.1: 通用对话模型
- Qwen3 VL 235B: 多模态模型（但未使用视觉）

问题:
- 这些模型是为对话/文本生成设计的
- 没有针对金融时间序列优化
- 没有针对交易决策微调

更好的选择:
- FinBERT (金融情绪分析)
- 自训练的 LSTM/Transformer (价格预测)
- 或者根本不用 LLM，用传统量化模型
```

### 6.3 温度设置的问题

#### ⚠️ 问题: Temperature = 0.7（中等随机性）

```
当前:
TEMPERATURE = 0.7

问题:
- 同样输入可能产生不同输出
- 不利于回测（无法复现）
- 交易决策需要一致性

建议:
- 降低到 0.1-0.3（更确定性）
- 或直接用 temperature = 0（完全确定性）
```

### 6.4 缺失的配置

#### ❌ 缺少止损止盈的明确输出

```
当前输出:
{
  "decision": "BUY",
  "confidence": 0.75,
  "reasoning": "..."
}

建议增强:
{
  "decision": "BUY",
  "confidence": 0.75,
  "reasoning": "...",
  "risk_management": {
    "stop_loss_price": 49000,
    "take_profit_targets": [51000, 53000, 55000],
    "position_size_recommendation": "5%",
    "max_holding_time": "4h"
  }
}
```

#### ❌ 缺少市场状态输出

```
建议增加:
{
  "decision": "BUY",
  "confidence": 0.75,
  "market_state": "trending_up",  # 新增
  "reasoning": "..."
}

market_state 选项:
- "trending_up": 上升趋势
- "trending_down": 下降趋势
- "ranging": 震荡
- "volatile": 高波动
- "consolidating": 盘整
```

---

## 7. 改进优先级建议

### 🔴 高优先级（立即）

1. **降低温度**
   ```python
   TEMPERATURE = 0.7  # → 改为 0.2
   ```

2. **增强止损止盈输出**
   ```python
   # 修改 JSON Schema，要求输出 risk_management
   ```

3. **添加市场状态识别**
   ```python
   # 在 System Prompt 中添加市场状态判断规则
   ```

### 🟡 中优先级（本周）

4. **优化 System Prompt**
   - 添加事件响应规则
   - 明确强制性要求（止损）
   - 增加仓位大小指导

5. **改进投票策略**
   - 当前 majority 太宽松
   - 考虑改为 unanimous（更保守）
   - 或添加技术指标作为第三票

### 🟢 低优先级（后续）

6. **模型替换探索**
   - 考虑使用金融专用模型
   - 或完全用传统量化策略

7. **回测能力**
   - 记录所有 AI 输入输出
   - 使用 temperature = 0 确保可复现

---

## 8. 完整配置清单

```python
# === AI 模型 ===
AI_MODEL_PRIMARY = "deepseek/deepseek-chat-v3.1"
AI_MODEL_SECONDARY = "qwen/qwen3-vl-235b-a22b-instruct"

# === API 参数 ===
TEMPERATURE = 0.7                    # 建议改为 0.2
MAX_TOKENS = 1000                    # ✓ 合理
API_REQUEST_TIMEOUT = 60             # ✓ 合理
DECISION_TIMEOUT = 90                # ✓ 合理

# === 决策阈值 ===
MIN_CONFIDENCE = 0.6                 # ✓ 合理（60%）
VOTING_STRATEGY = "majority"         # 建议改为 "unanimous"

# === 模型权重（如使用 weighted）===
MODEL_WEIGHTS = {
    "deepseek/deepseek-chat-v3.1": 0.5,
    "qwen/qwen3-vl-235b-a22b-instruct": 0.5
}

# === 投票机制参数 ===
CONFIDENCE_DIFF_THRESHOLD = 0.2      # 20% 差距才考虑单方
SCORE_DIFF_THRESHOLD = 0.15          # 加权分差 15%

# === 输出格式 ===
JSON_SCHEMA = {
    "decision": str (BUY/SELL/HOLD),
    "confidence": float (0.0-1.0),
    "reasoning": str (50-500 chars)
}
```

---

## 总结

### ✅ 当前做得好的地方

1. **双模型验证** - 降低单一模型错误
2. **结构化输出** - 强制 JSON Schema
3. **置信度过滤** - 低置信度不执行
4. **上下文丰富** - 提供账户、持仓、历史信息
5. **重试机制** - 网络失败自动重试

### ❌ 需要改进的地方

1. **模型选择** - LLM 不适合量化交易
2. **温度设置** - 0.7 太随机，不利于回测
3. **Prompt 设计** - 建议性而非强制性
4. **缺少市场状态** - 所有情况用同一策略
5. **缺少事件响应** - 无法处理突发行情
6. **风控输出不足** - 没有止损止盈价格
7. **仓位管理弱** - 没有仓位大小建议

### 🎯 建议的下一步

1. **立即**: 降低温度到 0.2，改投票策略为 unanimous
2. **本周**: 增强输出格式（风控信息），优化 Prompt（市场状态）
3. **下周**: 实施事件驱动机制
4. **长期**: 考虑用传统量化策略替代 LLM

---

**配置文件位置：**
- System Prompt: `backend/ai/prompt_templates.py`
- 模型配置: `backend/config/settings.py`
- API 客户端: `backend/ai/openrouter_client.py`
- 决策引擎: `backend/ai/decision_engine.py`
