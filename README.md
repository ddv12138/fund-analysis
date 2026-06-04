# 场内金融工具

场内基金溢价率分析、美股指数历史行情、基金 vs 指数归一化对比，以及每日溢价率邮件日报。

## 功能

| 脚本 | 功能 |
|------|------|
| `fund_premium_analyzer.py` | 场内基金溢价率分析，支持图表展示 |
| `us_index.py` | 美股指数（纳指/标普/道指）历史行情 |
| `us_index_compare.py` | 基金 vs 指数归一化对比，多基金同框 |
| `fund_alert.py` | 溢价率监控，每日邮件日报（含趋势图） |

## 快速开始

```bash
conda activate fund-analysis
# 或使用 pip
pip install akshare pandas matplotlib numpy
```

## 脚本用法

### 溢价率分析

```bash
python fund_premium_analyzer.py                    # 默认 513870 近 1 年
python fund_premium_analyzer.py 513500 180         # 指定基金和时间
python fund_premium_analyzer.py 513870 365 --chart # 趋势图
```

### 美股指数

```bash
python us_index.py                                 # 默认 .NDX 近 180 天
python us_index.py .INX 365                        # 标普 500
python us_index.py .NDX 30 --chart                 # 近 30 天图表
```

### 基金 vs 指数对比

```bash
python us_index_compare.py                         # 默认 513100 vs .NDX
python us_index_compare.py 180                     # 近 180 天
python us_index_compare.py 365 513100 513500       # 两个基金对比
python us_index_compare.py 180 513500 --no-chart   # 仅表格
```

### 溢价率邮件日报（配合 GitHub Actions）

```bash
python fund_alert.py --dry-run                     # 仅打印，不发送
python fund_alert.py                               # 需配置环境变量
```

## GitHub Actions 定时日报

每天早上 9:30（北京时间，周一至周五）自动执行 `fund_alert.py`，检查各基金溢价率并推送邮件日报（含溢价率趋势图）。

### 配置 Secrets

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `SMTP_HOST` | SMTP 服务器 | `smtp.qq.com` |
| `SMTP_PORT` | SMTP 端口 | `465` |
| `SMTP_USER` | 发件邮箱 | `123456@qq.com` |
| `SMTP_PASS` | SMTP 授权码（QQ 邮箱需生成授权码） | `xxxxxxxxxx` |
| `MAIL_TO` | 收件邮箱（多个用逗号分隔） | `user1@qq.com,user2@qq.com` |

### 配置 Variables

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `FUND_SYMBOLS` | 监控基金列表（逗号分隔） | `513870,513100,513500` |

## 买入区间说明

买入区间基于近 365 天历史溢价率数据的均值与标准差计算：

| 条件 | 判定 | 建议 |
|------|------|------|
| 溢价率 < 均值-σ | ✅ 低估区间 | 适合买入 |
| 均值-σ ~ min(均值+σ, 均值×1.5) | ✅ 适合买入 | 正常持有 |
| 溢价率 > min(均值+σ, 均值×1.5) | ❌ 溢价偏高 | 观望，避免买入 |

## 缓存机制

所有 API 响应缓存在 `fund_cache/` 目录：

| 缓存文件 | 说明 | 有效期 |
|---------|------|--------|
| `fund_etf_spot_em.csv` | 全市场 ETF 行情 | 永久 |
| `fund_lof_spot_em.csv` | 全市场 LOF 行情 | 永久 |
| `{symbol}_market.csv` | 基金历史市场价 | 最新日期 ≥ T-1 |
| `{symbol}_nav.csv` | 基金历史净值 | 3 天内 |
| `{symbol}_index.csv` | 美股指数行情 | 最新日期 ≥ T-1 |

GitHub Actions 执行后会 commit 缓存回仓库，避免重复拉取 API。

## 安全说明

- 所有敏感信息（SMTP 密码、邮箱等）通过环境变量或 GitHub Secrets 配置
- 代码中不硬编码任何密钥
- 缓存数据仅包含公开行情信息
