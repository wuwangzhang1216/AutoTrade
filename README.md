# AI Multi-Agent Trading Platform

一个基于AI多代理的自动化交易平台，采用微服务架构，具备实时市场数据处理、智能决策制定和自动交易执行功能。

## 🌟 特性

- **多AI代理竞争**: 6个不同的AI模型（GPT-5、Claude、Gemini、Grok、DeepSeek、Qwen）同时进行交易竞争
- **实时市场数据**: 从Binance获取实时加密货币市场数据
- **智能决策引擎**: 基于技术指标和AI分析生成交易信号
- **自动交易执行**: 模拟交易执行，包含手续费和滑点
- **可视化面板**: React前端展示实时交易表现和排行榜
- **性能追踪**: 实时追踪每个AI代理的表现和收益

## 📊 架构

### 统一服务架构（推荐 - 成本更低）

**新的统一服务将三个微服务合并为一个应用，节省约56%的部署成本！**

```
Unified Service (Port 8080)
├── Market Data Service
├── Decision Engine
└── Trading Service
```

**成本对比**:
- 旧架构（3个服务）: ~$75/月
- 新架构（统一服务）: ~$33/月
- **节省**: ~$42/月 (56%)

### 传统微服务架构（可选）

```
Market Data Service (Port 8001) → Decision Engine (Port 8002) → Trading Service (Port 8003)
```

## 🚀 快速开始

### 选项1: 统一服务部署（推荐）

#### 本地Docker测试

```bash
# 1. 克隆仓库
git clone <your-repo-url>
cd AutoTrade

# 2. 配置环境变量
cp unified_service/.env.example .env
# 编辑.env文件，填写OPENROUTER_API_KEY

# 3. 启动统一服务
docker-compose -f docker-compose.unified.yml up

# 4. 访问
# API: http://localhost:8080
# 健康检查: http://localhost:8080/api/health
```

#### Heroku部署

**自动部署（推荐）**:
```bash
# 1. 登录Heroku
heroku login

# 2. 运行部署脚本
chmod +x deploy-unified.sh
./deploy-unified.sh autotrade-unified
```

**手动部署**:
```bash
# 1. 创建应用
heroku create autotrade-unified

# 2. 添加数据库和Redis
heroku addons:create heroku-postgresql:essential-0 -a autotrade-unified
heroku addons:create heroku-redis:mini -a autotrade-unified

# 3. 设置环境变量
heroku config:set \
  OPENROUTER_API_KEY="your_key_here" \
  DATA_COLLECTION_INTERVAL="5" \
  SYMBOLS="BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,DOGEUSDT,XRPUSDT" \
  INITIAL_BALANCE="10000.0" \
  MAX_POSITION_SIZE="0.3" \
  RISK_PER_TRADE="0.02" \
  DECISION_INTERVAL="60" \
  COMMISSION_RATE="0.001" \
  SLIPPAGE_RATE="0.0005" \
  -a autotrade-unified

# 4. 部署
git push heroku main

# 5. 启动
heroku ps:scale web=1 -a autotrade-unified

# 6. 查看日志
heroku logs --tail -a autotrade-unified
```

### 选项2: 传统微服务架构

```bash
# 1. 克隆仓库
git clone <your-repo-url>
cd AutoTrade

# 2. 配置环境变量
cp .env.example .env
# 编辑.env文件

# 3. 启动所有服务
docker-compose up -d

# 4. 验证服务
docker-compose ps
```

## 📁 项目结构

```
AutoTrade/
├── unified_service/              # 统一服务（推荐）
│   ├── app/
│   │   ├── main.py              # 合并的主应用
│   │   └── config.py            # 统一配置
│   ├── requirements.txt          # 依赖
│   ├── Dockerfile               # Docker配置
│   └── README.md                # 详细文档
├── market_data_service/          # 市场数据微服务
│   ├── app/
│   │   ├── main.py
│   │   ├── collectors/          # 数据采集器
│   │   ├── storage/             # 存储层
│   │   └── processors/          # 数据处理
│   └── requirements.txt
├── decision_engine/              # 决策引擎微服务
│   ├── app/
│   │   ├── main.py
│   │   ├── agents/              # AI代理
│   │   ├── database.py          # 数据库层
│   │   └── executor.py          # 决策执行器
│   └── requirements.txt
├── trading_service/              # 交易服务微服务
│   ├── app/
│   │   ├── main.py
│   │   ├── execution/           # 交易执行
│   │   ├── risk/                # 风险管理
│   │   └── portfolio_manager.py # 投资组合管理
│   └── requirements.txt
├── gui/                          # React前端面板
│   ├── App.tsx
│   ├── components/
│   └── services/
├── docker-compose.yml            # 传统微服务编排
├── docker-compose.unified.yml    # 统一服务编排
├── Procfile                      # Heroku配置
├── deploy-unified.sh             # 部署脚本
└── init-db.sql                  # 数据库初始化
```

## 🛠️ 技术栈

### 后端
- **Python 3.11+** with FastAPI
- **PostgreSQL** (TimescaleDB) - 时序数据库
- **Redis** - 缓存和实时数据
- **SQLAlchemy** - ORM
- **asyncio/aiohttp** - 异步编程

### AI/ML
- **OpenRouter API** - 访问多个AI模型
- **pandas/numpy** - 数据分析
- **ta (Technical Analysis)** - 技术指标计算

### 前端
- **React + TypeScript**
- **Tailwind CSS**
- **Recharts** - 图表可视化
- **WebSocket** - 实时数据更新

### DevOps
- **Docker & Docker Compose**
- **Heroku** - 云部署
- **GitHub Actions** - CI/CD（可选）

## 📡 API端点

### 市场数据
- `GET /api/market/latest` - 获取最新市场快照
- `GET /api/market/{symbol}` - 获取特定交易对数据
- `GET /api/market/history/{symbol}` - 获取历史数据
- `GET /api/market/symbols` - 列出监控的交易对
- `WS /ws/market` - WebSocket实时数据推送

### AI代理
- `GET /api/agents` - 列出所有AI代理
- `GET /api/agents/leaderboard` - 获取排行榜
- `GET /api/agents/{agent_id}/account` - 获取代理账户状态
- `GET /api/agents/{agent_id}/decisions` - 获取决策历史
- `GET /api/agents/{agent_id}/positions` - 获取持仓

### 交易
- `GET /api/portfolio` - 获取投资组合
- `GET /api/positions` - 获取持仓列表
- `GET /api/positions/all` - 获取所有代理的持仓
- `GET /api/trades/all` - 获取所有交易记录
- `GET /api/performance/history` - 获取性能历史

### 健康检查
- `GET /` - 服务信息
- `GET /api/health` - 健康状态检查

## ⚙️ 配置

### 环境变量

创建 `.env` 文件并配置以下变量：

```bash
# 数据库配置
DATABASE_URL=postgresql://user:pass@host:5432/db
TIMESCALE_HOST=localhost
TIMESCALE_PORT=5432
TIMESCALE_DB=trading_platform
TIMESCALE_USER=admin
TIMESCALE_PASSWORD=password

# Redis配置
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 市场数据设置
DATA_COLLECTION_INTERVAL=5                           # 数据采集间隔（秒）
SYMBOLS=BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,DOGEUSDT,XRPUSDT

# AI决策引擎设置
OPENROUTER_API_KEY=your_api_key_here                # OpenRouter API密钥
INITIAL_BALANCE=10000.0                              # 初始余额
MAX_POSITION_SIZE=0.3                                # 最大仓位（30%）
RISK_PER_TRADE=0.02                                  # 每笔交易风险（2%）
DECISION_INTERVAL=60                                 # 决策间隔（秒）

# 交易设置
COMMISSION_RATE=0.001                                # 手续费率（0.1%）
SLIPPAGE_RATE=0.0005                                 # 滑点率（0.05%）

# 服务器设置
PORT=8080                                            # 端口号
```

### AI代理配置

平台支持6个AI模型进行交易竞争：

| 代理ID | 模型名称 | 提供商 |
|--------|----------|--------|
| gpt5 | GPT-4o | OpenAI |
| claude | Claude 3.5 Sonnet | Anthropic |
| gemini | Gemini 2.0 Flash | Google |
| grok | Grok 2 | xAI |
| deepseek | DeepSeek Chat | DeepSeek |
| qwen | Qwen 2.5 72B | Alibaba |

每个代理：
- 初始资金：$10,000
- 独立决策和交易
- 实时排名竞争

## 🖥️ GUI配置

### 开发环境
在 `gui/.env` 中：
```bash
VITE_UNIFIED_SERVICE_URL=http://localhost:8080
```

### 生产环境
在 `gui/.env.production` 中：
```bash
VITE_UNIFIED_SERVICE_URL=https://your-app.herokuapp.com
```

构建GUI：
```bash
cd gui
npm install
npm run build
```

## 📊 监控和调试

### 本地开发

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f unified_service

# 连接到数据库
docker-compose exec postgres psql -U admin -d trading_platform

# 连接到Redis
docker-compose exec redis redis-cli

# 检查服务状态
docker-compose ps
```

### Heroku生产环境

```bash
# 查看实时日志
heroku logs --tail -a autotrade-unified

# 检查dyno状态
heroku ps -a autotrade-unified

# 重启服务
heroku restart -a autotrade-unified

# 查看配置
heroku config -a autotrade-unified

# 连接到数据库
heroku pg:psql -a autotrade-unified

# 打开应用
heroku open -a autotrade-unified
```

## 🔍 故障排除

### 服务无法启动

1. **检查Docker是否运行**:
   ```bash
   docker info
   ```

2. **检查端口占用**:
   ```bash
   lsof -i :8080  # 统一服务
   lsof -i :5432  # PostgreSQL
   lsof -i :6379  # Redis
   ```

3. **查看日志**:
   ```bash
   docker-compose logs
   ```

### 数据库连接问题

1. **验证PostgreSQL运行中**:
   ```bash
   docker-compose ps postgres
   ```

2. **检查凭据**:
   确保 `.env` 中的凭据与 `docker-compose.yml` 匹配

3. **重置数据库**:
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

### AI决策失败

1. **验证API密钥**:
   ```bash
   echo $OPENROUTER_API_KEY
   ```

2. **检查API配额**:
   访问 [OpenRouter Dashboard](https://openrouter.ai/)

3. **查看决策日志**:
   ```bash
   heroku logs --tail -a autotrade-unified | grep "Decision"
   ```

### 内存不足

1. **升级dyno类型** (Heroku):
   ```bash
   heroku ps:resize web=standard-2x -a autotrade-unified
   ```

2. **调整采集频率**:
   增加 `DATA_COLLECTION_INTERVAL` 和 `DECISION_INTERVAL`

3. **优化数据库**:
   ```bash
   heroku pg:upgrade essential-0 -a autotrade-unified
   ```

## 🚀 从旧架构迁移

如果您已经部署了三个独立的微服务，可以平滑迁移到统一服务：

1. **部署统一服务**（不影响现有服务）
2. **测试所有功能**确保正常工作
3. **更新GUI配置**指向新服务
4. **验证一段时间**确认稳定
5. **删除旧服务**节省成本：
   ```bash
   heroku apps:destroy autotrade-market-data
   heroku apps:destroy autotrade-decision-engine
   heroku apps:destroy autotrade-trading-service
   ```

## 📈 性能优化

### Heroku部署建议

| 资源 | 推荐配置 | 月费用 |
|------|----------|--------|
| Dyno | Standard-1x | $25 |
| PostgreSQL | Essential-0 | $5 |
| Redis | Mini | $3 |
| **总计** | | **$33** |

### 优化建议

1. **数据采集**:
   - 测试环境: 10-30秒
   - 生产环境: 5-10秒

2. **决策间隔**:
   - 保守策略: 120-300秒
   - 激进策略: 60-120秒

3. **数据库**:
   - 定期清理旧数据
   - 添加适当索引
   - 考虑升级到Standard-0

4. **Redis**:
   - 设置合理的TTL
   - 避免存储大对象
   - 监控内存使用

## 🔒 安全考虑

- ✅ 生产环境更改默认密码
- ✅ 使用环境变量存储敏感信息
- ✅ 启用HTTPS（Heroku自动提供）
- ✅ 限制数据库访问
- ✅ 定期更新依赖
- ✅ 实施API速率限制
- ✅ 添加身份验证（生产必需）

## 🧪 测试

```bash
# 运行单元测试（待实现）
docker-compose run --rm unified_service python -m pytest

# 运行集成测试（待实现）
docker-compose run --rm unified_service python -m pytest tests/integration

# API健康检查
curl http://localhost:8080/api/health
```

## 📝 开发指南

### 添加新的AI代理

1. 在 `decision_engine/app/agents/` 创建新代理类
2. 继承 `BaseAgent` 并实现 `make_decision()` 方法
3. 在 `main.py` 中注册新代理
4. 更新 `AI_AGENTS` 列表

### 添加新的技术指标

1. 在 `market_data_service/app/processors/indicators.py` 添加计算函数
2. 在 `IndicatorCalculator.calculate_all()` 中调用
3. 更新 `MarketData` 模型

### 自定义交易策略

在 `decision_engine/app/agents/base_agent.py` 中修改 `make_decision()` 逻辑。

## 🗺️ 路线图

- [x] 多AI代理竞争系统
- [x] 实时市场数据采集
- [x] 技术指标计算
- [x] 交易执行和组合管理
- [x] 可视化前端面板
- [x] 统一服务架构
- [ ] 回测框架
- [ ] 更多交易所支持
- [ ] 高级风险管理
- [ ] 机器学习预测模型
- [ ] 实时告警系统
- [ ] 多资产支持

## 📄 许可证

本项目仅供教育和研究目的使用。

## ⚠️ 免责声明

本交易平台仅供教育目的。交易涉及风险，您永远不应该用无法承受损失的资金进行交易。过去的表现不能保证未来的结果。在进行交易之前，请务必进行自己的研究并考虑咨询财务顾问。

## 🤝 贡献

欢迎提交问题和拉取请求！

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开拉取请求

## 💬 支持

遇到问题？
- 📖 查看详细文档: `unified_service/README.md`
- 🔍 检查故障排除部分
- 📊 查看API文档
- 🐛 提交Issue到GitHub

## 🎉 致谢

感谢所有为本项目做出贡献的开发者和AI模型提供商。

---

**开始交易竞赛，看看哪个AI能赚得最多！** 🚀💰
