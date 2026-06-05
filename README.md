# 场内金融工具

场内基金溢价率分析、美股指数/ETF 回撤分析、基金 vs 指数归一化对比，以及每日邮件日报。

## 功能

| 脚本 | 功能 |
|------|------|
| `fund_premium_analyzer.py` | 场内基金溢价率分析，支持图表展示 |
| `us_index.py` | 美股指数（纳指/标普/道指）历史行情 |
| `us_etf_analyzer.py` | 美股 ETF/指数回撤分析，含 VIX 恐慌指数子图 |
| `us_index_compare.py` | 基金 vs 指数归一化对比，多基金同框 |
| `fund_alert.py` | 溢价率监控 + 纳指100回撤分析，每日邮件日报 |

## 快速开始

```bash
pip install akshare pandas matplotlib numpy
pip install -e .
```

需要设置环境变量：

```bash
export FRED_API_KEY=你的fred_api_key  # 获取 VIX 数据
```

## 脚本用法

### 溢价率分析

```bash
python scripts/fund_premium_analyzer.py                    # 默认 513870 近 1 年
python scripts/fund_premium_analyzer.py 513500 180         # 指定基金和时间
python scripts/fund_premium_analyzer.py 513870 365 --chart # 趋势图
```

### 美股指数行情

```bash
python scripts/us_index.py                                 # 默认 .NDX 近 180 天
python scripts/us_index.py .INX 365                        # 标普 500
python scripts/us_index.py .NDX 30 --chart                 # 近 30 天图表
```

### 美股 ETF/指数回撤分析

```bash
python scripts/us_etf_analyzer.py                          # 默认 QQQM 近 180 天
python scripts/us_etf_analyzer.py .NDX 365                 # 纳指 100（自动识别指数）
python scripts/us_etf_analyzer.py QQQM 180 --chart         # 含回撤/收盘/VIX 图表
python scripts/us_etf_analyzer.py .INX 90 --chart          # 标普 500 含图表
```

### 基金 vs 指数对比

```bash
python scripts/us_index_compare.py                         # 默认 513100 vs .NDX
python scripts/us_index_compare.py 180                     # 近 180 天
python scripts/us_index_compare.py 365 513100 513500       # 两个基金对比
python scripts/us_index_compare.py 180 513500 --no-chart   # 仅表格
```

### 邮件日报（配合 GitHub Actions）

```bash
python scripts/fund_alert.py --dry-run                     # 仅打印，不发送
python scripts/fund_alert.py                               # 需配置环境变量
```

## GitHub Actions 定时日报

每天早上 9:30（北京时间，周一至周五）自动执行 `fund_alert.py`，检查各基金溢价率 + 纳指100回撤分析，推送邮件日报（含趋势图表）。

### 配置 Secrets

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `FRED_API_KEY` | FRED API 密钥（获取 VIX 数据） | `xxxxxxxxxxxxxxxxxxx` |
| `SMTP_HOST` | SMTP 服务器 | `smtp.qq.com` |
| `SMTP_PORT` | SMTP 端口 | `465` |
| `SMTP_USER` | 发件邮箱 | `123456@qq.com` |
| `SMTP_PASS` | SMTP 授权码 | `xxxxxxxxxx` |
| `MAIL_TO` | 收件邮箱（多个用逗号分隔） | `user1@qq.com,user2@qq.com` |

### 配置 Variables

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `FUND_SYMBOLS` | 监控基金列表（逗号分隔） | `513870,513100,513500` |

## 买入区间说明

### 溢价率买入区间

基于近 365 天历史溢价率数据的均值与标准差计算：

| 条件 | 判定 | 建议 |
|------|------|------|
| 溢价率 < 均值-σ | ✅ 低估区间 | 适合买入 |
| 均值-σ ~ min(均值+σ, 均值×1.5) | ✅ 适合买入 | 正常持有 |
| 溢价率 > min(均值+σ, 均值×1.5) | ❌ 溢价偏高 | 观望，避免买入 |

### 回撤买入区间

基于从历史最高价（ATH）的下跌幅度：

| 距 ATH | 判定 | 建议 |
|--------|------|------|
| > -5% | 🔵 正常 | 按计划定投 |
| -5% ~ -10% | 🟢 轻度回调 | 可适当加仓 |
| -10% ~ -20% | 🟡 回调区间 | 加大买入 |
| -20% ~ -30% | 🟠 深度低估 | 显著加仓 |
| < -30% | 🔴 历史机会 | 全力买入 |

## 数据源

| 数据 | 来源 |
|------|------|
| 场内基金市场价 | 新浪财经 `fund_etf_hist_sina` |
| 场内基金净值 | 东方财富 `fund_open_fund_info_em` |
| 美股指数 | 新浪财经 `index_us_stock_sina` |
| 美股 ETF/个股 | 新浪财经 `stock_us_daily` |
| VIX 恐慌指数 | FRED API `VIXCLS` |

## 缓存机制

所有 API 响应缓存在 `fund_cache/` 目录：

| 缓存文件 | 有效期 |
|---------|--------|
| `fund_etf_spot_em.csv` | 永久 |
| `fund_lof_spot_em.csv` | 永久 |
| `{symbol}_market.csv` | 最新日期 ≥ T-1 |
| `{symbol}_nav.csv` | 最新日期 ≥ T-3（QDII T+2） |
| `{symbol}_index.csv` | 最新日期 ≥ T-1 |
| `{symbol}_us_stock.csv` | 最新日期 ≥ T-1 |
| `VIX_us_stock.csv` | 最新日期 ≥ T-3（FRED 滞后）；过期后增量拉取缺失天数 |

GitHub Actions 执行后会 commit 缓存回仓库，避免重复拉取 API。

## 安全说明

- 所有敏感信息通过环境变量或 GitHub Secrets 配置
- 代码中不硬编码任何密钥
- 缓存数据仅包含公开行情信息
