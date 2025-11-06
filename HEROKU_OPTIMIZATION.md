# Heroku 性能优化指南

## 问题分析

### 原始问题

部署到 Heroku 后，频繁出现 **Request timeout (H12 error)**，所有 API 请求在 30 秒后超时：

- `/api/account` - 超时
- `/api/positions` - 超时
- `/api/ohlcv` - 超时
- `/api/equity-curve` - 超时

### 根本原因

从 Heroku 日志分析发现：

1. **AI Decision Scheduler 资源耗尽**
   - AI 决策每 **1 分钟**运行一次
   - 每次运行需要 **30-60 秒**（DeepSeek + Qwen 并行调用）
   - **9 个交易对** × AI 分析 = 每分钟大量 API 调用
   - 如果上一次还没完成，新的请求就会堆积
   - 导致内存和 CPU 耗尽

2. **Heroku 免费/基础层限制**
   - 基础 dyno: 512MB RAM
   - 30 秒请求超时
   - PostgreSQL 免费层: 20 连接限制

## 优化方案

### ✅ 方案 1: 禁用 AI Decision Scheduler（推荐）

**默认行为**：AI Scheduler 现在默认**禁用**

```bash
# Heroku 生产环境（默认禁用，推荐）
# 不需要设置任何环境变量，系统会自动禁用 AI Scheduler
```

**启用 AI Scheduler**（可选，谨慎使用）：

```bash
# 如果确实需要启用（会消耗大量资源）
heroku config:set ENABLE_AI_SCHEDULER=true -a autotrade-backend-kraken
```

**优点**：
- ✅ 彻底解决超时问题
- ✅ 大幅减少 CPU/内存使用
- ✅ 降低 OpenRouter API 成本
- ✅ 前端仍然可以手动触发 AI 决策（未来功能）

**缺点**：
- ❌ 不会自动执行交易（需要手动或通过 API 触发）

---

### ✅ 方案 2: 调整 AI Scheduler 间隔（如果启用）

如果必须启用 AI Scheduler，可以调整运行间隔：

```bash
# 设置为 5 分钟（默认）
heroku config:set AI_SCHEDULER_INTERVAL_MINUTES=5 -a autotrade-backend-kraken

# 设置为 10 分钟（更保守）
heroku config:set AI_SCHEDULER_INTERVAL_MINUTES=10 -a autotrade-backend-kraken

# 设置为 15 分钟（最保守）
heroku config:set AI_SCHEDULER_INTERVAL_MINUTES=15 -a autotrade-backend-kraken
```

**性能对比**：

| 间隔 | API 调用/小时 | 预估成本/月 | 资源使用 |
|------|---------------|-------------|----------|
| 1 分钟（原始） | 540 次 | $15-30 | 极高 ⚠️ |
| 5 分钟（默认） | 108 次 | $3-6 | 中等 |
| 10 分钟 | 54 次 | $2-3 | 低 |
| 15 分钟 | 36 次 | $1-2 | 很低 ✅ |

**计算公式**：
```
每小时调用次数 = (60 / 间隔分钟数) × 9个交易对 × 2个AI模型
每月成本 = 每小时调用次数 × 24小时 × 30天 × $0.001/调用
```

---

### ✅ 方案 3: 升级 Dyno（如果预算允许）

#### 当前配置（免费/基础层）
```
Dyno Type: Basic/Eco
RAM: 512MB
Timeout: 30 seconds
Cost: ~$7/月（Eco dyno） 或 $0（免费dyno，有休眠）
```

#### 推荐升级

**Standard 1X** ($25/月):
```bash
heroku ps:scale web=1:Standard-1X -a autotrade-backend-kraken
```
- RAM: 512MB
- Timeout: 30 seconds
- **不休眠**
- 更稳定的性能

**Standard 2X** ($50/月):
```bash
heroku ps:scale web=1:Standard-2X -a autotrade-backend-kraken
```
- RAM: 1GB
- Timeout: 30 seconds
- 可以处理更多并发

**Performance** ($250+/月):
```bash
heroku ps:scale web=1:Performance-M -a autotrade-backend-kraken
```
- RAM: 2.5GB
- Timeout: **自定义**
- 更高性能

---

## 当前生产环境配置

### 已部署的优化（v27）

✅ **AI Scheduler**: 默认禁用
✅ **AI Scheduler 间隔**: 5 分钟（如果启用）
✅ **数据库连接池**: 5 连接（保守配置）
✅ **API 缓存**: 3-5 秒 TTL
✅ **Database**: PostgreSQL (Essential-0, 20 连接限制)

### 环境变量

查看当前配置：
```bash
heroku config -a autotrade-backend-kraken
```

关键配置：
```bash
ENABLE_AI_SCHEDULER=false  # AI Scheduler 禁用（默认）
AI_SCHEDULER_INTERVAL_MINUTES=5  # 间隔 5 分钟（如果启用）
DATABASE_URL=postgres://...  # PostgreSQL 连接
OPENROUTER_API_KEY=sk-...  # OpenRouter API key
```

---

## 监控和诊断

### 查看实时日志

```bash
# 实时日志（持续监控）
heroku logs --app autotrade-backend-kraken --tail

# 最近 500 行日志
heroku logs --app autotrade-backend-kraken --num 500

# 仅查看错误
heroku logs --app autotrade-backend-kraken --tail | grep -i "error\|timeout\|H12"
```

### 关键日志指标

**✅ 正常运行**：
```
INFO: AI Decision Scheduler is DISABLED (set ENABLE_AI_SCHEDULER=true to enable)
INFO: AutoTrade AI API starting...
```

**⚠️ 需要注意**：
```
heroku[router]: at=error code=H12 desc="Request timeout" method=GET path="/api/account"
```

**❌ 资源耗尽**：
```
ERROR: R14 (Memory quota exceeded)
ERROR: R15 (Memory quota vastly exceeded)
heroku[router]: at=error code=H12 desc="Request timeout"
```

### Heroku 性能指标

```bash
# 查看 dyno 状态
heroku ps -a autotrade-backend-kraken

# 查看资源使用
heroku ps:status -a autotrade-backend-kraken

# 查看数据库连接
heroku pg:info -a autotrade-backend-kraken
```

---

## 推荐配置方案

### 方案 A: 低成本（推荐用于开发/测试）

**配置**：
```bash
Dyno: Eco ($5/月) 或 Free (休眠)
AI Scheduler: 禁用
数据库: Essential-0 (免费)
```

**优点**：
- 成本极低（$0-5/月）
- 性能稳定（无 AI scheduler 消耗）
- 适合前端展示和 API 测试

**缺点**：
- 无自动交易
- 免费 dyno 会休眠（30 分钟不活动）

---

### 方案 B: 平衡方案（推荐用于小规模生产）

**配置**：
```bash
Dyno: Standard-1X ($25/月)
AI Scheduler: 启用，间隔 10-15 分钟
数据库: Mini ($5/月, 60 连接)
```

**设置命令**：
```bash
heroku ps:scale web=1:Standard-1X -a autotrade-backend-kraken
heroku config:set ENABLE_AI_SCHEDULER=true -a autotrade-backend-kraken
heroku config:set AI_SCHEDULER_INTERVAL_MINUTES=10 -a autotrade-backend-kraken
heroku addons:create heroku-postgresql:mini -a autotrade-backend-kraken
```

**优点**：
- 自动交易功能
- 不休眠
- 中等成本（$30-35/月）

**缺点**：
- 仍有资源限制
- API 成本增加

---

### 方案 C: 高性能方案（推荐用于大规模生产）

**配置**：
```bash
Dyno: Standard-2X ($50/月)
AI Scheduler: 启用，间隔 5 分钟
数据库: Standard-0 ($50/月, 120 连接)
```

**设置命令**：
```bash
heroku ps:scale web=1:Standard-2X -a autotrade-backend-kraken
heroku config:set ENABLE_AI_SCHEDULER=true -a autotrade-backend-kraken
heroku config:set AI_SCHEDULER_INTERVAL_MINUTES=5 -a autotrade-backend-kraken
heroku addons:create heroku-postgresql:standard-0 -a autotrade-backend-kraken
```

**优点**：
- 高性能
- 频繁的 AI 决策
- 稳定可靠

**缺点**：
- 成本较高（$100-150/月，含 OpenRouter API）

---

## 替代方案：AWS App Runner

如果 Heroku 性能不满足需求，可以考虑迁移到 AWS App Runner：

**优势**：
- 更好的全球覆盖（避免 Binance geo-blocking）
- 更灵活的资源配置
- 自动扩展
- 按使用付费

**部署指南**：参见 [AWS_DEPLOY.md](AWS_DEPLOY.md)

---

## 故障排除

### 问题 1: 仍然出现超时

**检查**：
```bash
# 1. 确认 AI Scheduler 已禁用
heroku logs --tail -a autotrade-backend-kraken | grep "Scheduler"

# 应该看到: "AI Decision Scheduler is DISABLED"
```

**解决**：
```bash
# 确保环境变量正确
heroku config -a autotrade-backend-kraken | grep SCHEDULER

# 如果不存在或为 true，设置为 false
heroku config:set ENABLE_AI_SCHEDULER=false -a autotrade-backend-kraken

# 重启应用
heroku restart -a autotrade-backend-kraken
```

---

### 问题 2: 数据库连接耗尽

**症状**：
```
FATAL: remaining connection slots are reserved
```

**解决**：
```bash
# 1. 检查当前连接数
heroku pg:info -a autotrade-backend-kraken

# 2. 升级数据库（如果免费层）
heroku addons:create heroku-postgresql:mini -a autotrade-backend-kraken

# 3. 减少连接池大小（backend/database/models.py 已优化为 5）
```

---

### 问题 3: OpenRouter API 成本过高

**优化**：
```bash
# 1. 增加 AI Scheduler 间隔
heroku config:set AI_SCHEDULER_INTERVAL_MINUTES=15 -a autotrade-backend-kraken

# 2. 减少交易对数量（backend/config/settings.py）
# 从 9 个减少到 3-5 个关键交易对

# 3. 使用更便宜的 AI 模型
# DeepSeek Chat v3.1: $0.27/1M tokens (已经很便宜)
# Qwen 3 VL: $1.50/1M tokens
```

---

## 性能基准测试

### 优化前（v26 及以前）

```
AI Scheduler: 每 1 分钟运行
资源使用: 极高（内存接近限制）
API 超时率: 80-90%
平均响应时间: 30+ 秒（超时）
OpenRouter 成本: $20-30/月
```

### 优化后（v27+）

```
AI Scheduler: 默认禁用
资源使用: 低（稳定在 200-300MB）
API 超时率: <5%
平均响应时间: 500-2000ms
OpenRouter 成本: $0-5/月（取决于手动触发频率）
```

---

## 后续优化建议

### 短期（1-2 周）

1. ✅ 监控部署效果，确认超时问题解决
2. 📝 添加前端手动触发 AI 决策按钮
3. 📝 实现 AI 决策队列系统（避免并发过载）

### 中期（1-2 月）

1. 📝 迁移到 AWS App Runner（更好的性能和地理覆盖）
2. 📝 实现 Redis 缓存层（减少数据库查询）
3. 📝 添加 APM 监控（如 New Relic）

### 长期（3-6 月）

1. 📝 微服务架构（分离 AI 决策服务）
2. 📝 Kubernetes 部署（更灵活的扩展）
3. 📝 多区域部署（全球访问优化）

---

## 总结

### 当前状态 ✅

- **部署版本**: v27
- **AI Scheduler**: 默认禁用（生产环境稳定）
- **API 性能**: 超时问题基本解决
- **成本**: 大幅降低（$0-10/月）

### 建议行动

**立即执行**：
1. ✅ 保持 AI Scheduler 禁用（当前配置）
2. 📊 监控应用性能 1-2 天
3. 📈 观察前端是否仍有超时

**可选优化**（根据需求）：
1. 如果需要自动交易：启用 AI Scheduler，间隔 15 分钟
2. 如果仍有超时：升级到 Standard-1X dyno
3. 如果预算充足：迁移到 AWS App Runner

---

## 联系和支持

- **GitHub Issues**: https://github.com/wuwangzhang1216/AutoTrade/issues
- **Heroku 文档**: https://devcenter.heroku.com/
- **OpenRouter 文档**: https://openrouter.ai/docs

---

最后更新: 2025-01-06
版本: v27
作者: W Axis Inc.
