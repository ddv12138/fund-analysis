# 项目：场内金融工具

## 环境

```bash
conda activate fund-analysis
```

Python 3.10，依赖：akshare、pandas、matplotlib、numpy

## 文件清单

| 文件/目录 | 说明 |
|-----------|------|
| `src/fund_analysis/` | 核心包 |
| `src/fund_analysis/config.py` | 缓存路径、matplotlib 配置、常量 |
| `src/fund_analysis/data/` | 数据获取层（基金/指数/US股票/VIX API + 缓存） |
| `src/fund_analysis/data/fund.py` | 基金市场价/净值获取（新浪+东财） |
| `src/fund_analysis/data/index.py` | 美股指数获取（新浪） |
| `src/fund_analysis/data/us_stock.py` | 美股 ETF/个股获取（新浪），VIX 获取（FRED VIXCLS） |
| `src/fund_analysis/analysis/` | 业务分析层 |
| `src/fund_analysis/analysis/premium.py` | 溢价率计算 |
| `src/fund_analysis/analysis/drawdown.py` | 回撤计算、买入区间、VIX 状态评估 |
| `src/fund_analysis/analysis/rating.py` | 基金评级算法（排名评分、溢价偏离评分） |
| `src/fund_analysis/plotting/` | 图表层（样式/交互、溢价率图、回撤图） |
| `src/fund_analysis/plotting/style.py` | HoverTool 悬浮交互组件 |
| `src/fund_analysis/plotting/drawdown_chart.py` | 回撤图 + VIX 子图（双轴+色区） |
| `src/fund_analysis/utils/` | 工具模块（邮件发送） |
| `scripts/` | CLI 入口（所有脚本从 `scripts/` 运行） |
| `fund_cache/` | API 响应缓存（所有脚本共用） |
| `AGENTS.md` | 本文件 |

## 数据源

- 场内基金市场价 → 新浪财经 `fund_etf_hist_sina`
- 场内基金净值 → 东方财富 `fund_open_fund_info_em`
- 美股指数 → 新浪财经 `index_us_stock_sina`（代码：.NDX/.INX/.IXIC/.DJI）
- 美股 ETF/个股 → 新浪财经 `stock_us_daily`（代码：QQQM/SPY/VOO 等）
- VIX → FRED API `VIXCLS`（需环境变量 `FRED_API_KEY`）

## 缓存

- `fund_etf_spot_em.csv`：全市场 ETF 行情，永久，首次请求后不再调用 API
- `fund_lof_spot_em.csv`：全市场 LOF 行情，永久，首次请求后不再调用 API
- `{symbol}_market.csv`：最新日期 ≥ 今天-1 天则命中
- `{symbol}_nav.csv`：最新日期 ≥ 今天-3 天则命中（QDII T+2）
- `{symbol}_index.csv`：最新日期 ≥ 今天-1 天则命中
- `{symbol}_us_stock.csv`：最新日期 ≥ 今天-1 天则命中
- `VIX_us_stock.csv`：最新日期 ≥ 今天-3 天则命中（FRED 数据滞后 1-2 天）；过期后增量拉取缺失天数
- `fund_{symbol}_overview.csv`：7 天内创建过则命中
- 缓存目录：`fund_cache/`（首次运行由脚本自动创建）

## 调用方式

```bash
# 场内基金溢价率分析
python scripts/fund_premium_analyzer.py                    # 默认 513870 近 1 年
python scripts/fund_premium_analyzer.py 513500 180
python scripts/fund_premium_analyzer.py 513870 365 --chart

# 美股指数行情
python scripts/us_index.py                                   # 默认 .NDX 近 180 天
python scripts/us_index.py .INX 365
python scripts/us_index.py .NDX 30 --chart

# 美股 ETF/指数回撤分析
python scripts/us_etf_analyzer.py                           # 默认 QQQM 近 180 天
python scripts/us_etf_analyzer.py .NDX 365                  # 纳指 100 近 1 年（自动识别指数）
python scripts/us_etf_analyzer.py QQQM 180 --chart          # 含回撤/收盘/VIX 图表
python scripts/us_etf_analyzer.py .INX 90 --chart           # 标普 500 含图表

# 基金 vs 指数归一化对比
python scripts/us_index_compare.py                           # 默认 513100 vs .NDX 近 365 天
python scripts/us_index_compare.py 180                       # 默认 513100 近 180 天
python scripts/us_index_compare.py 365 513100 513500         # 两个基金
python scripts/us_index_compare.py 180 513500 --no-chart     # 仅打印表格

# 基金评级（多维度排名评分）
python scripts/fund_rating.py                                # 默认 FUND_SYMBOLS
python scripts/fund_rating.py --symbols 513870,513100        # 指定基金

# 溢价率监控告警（配合 GitHub Actions 定时执行）
python scripts/fund_alert.py                                 # 需设置 SMTP 等环境变量
python scripts/fund_alert.py --dry-run                       # 仅打印，不推送
```

## GitHub Actions 定时任务

每天早上 08:30（北京时间，周一至周五）自动执行 `scripts/fund_alert.py`，检查各基金最新溢价率并推送邮件日报（含溢价率趋势图），每条基金附带买入区间建议。

| 配置项 | 位置 | 说明 |
|--------|------|------|
| `FUND_SYMBOLS` | GitHub > Settings > Variables > Actions | 监控的基金列表，逗号分隔，如 `513870,513100,513500` |
| `SMTP_HOST` | GitHub > Settings > Secrets > Actions | SMTP 服务器，如 `smtp.qq.com` |
| `SMTP_PORT` | GitHub > Settings > Secrets > Actions | SMTP 端口，如 `465` |
| `SMTP_USER` | GitHub > Settings > Secrets > Actions | 发件邮箱地址 |
| `SMTP_PASS` | GitHub > Settings > Secrets > Actions | SMTP 授权码（QQ 邮箱需生成授权码） |
| `MAIL_TO` | GitHub > Settings > Secrets > Actions | 收件邮箱，多个用逗号分隔 |
| `CRON_TRIGGER_TOKEN` | GitHub > Settings > Secrets > Actions | 用于外部 cron 触发 workflow 的 GitHub Token |

执行后自动将 `fund_cache/` 中的缓存数据 commit 回仓库，避免重复拉取。

### 外部定时触发（确保准时执行）

GitHub Actions 内置 `schedule`（cron）为尽力执行，高峰期可能延迟。
通过 cron-job.org 外部定时调用 API 触发 workflow，确保 08:30 准时执行。

**配置步骤：**

1. **创建 GitHub Token**
   → Settings → Developer settings → Personal access tokens → Fine-grained tokens
   - 仓库：仅 `ddv12138/fund-analysis`
   - 权限：`Actions: write`
   - 生成后设为 Actions Secret → 名称 `CRON_TRIGGER_TOKEN`

2. **配置 cron-job.org**
   - 注册 https://cron-job.org（免费）
   - 新建任务，注意时区设置：

     | 配置项 | 值 |
     |--------|-----|
     | URL | `https://api.github.com/repos/ddv12138/fund-analysis/actions/workflows/daily_check.yml/dispatches` |
     | Method | `POST` |
     | Header | `Authorization: Bearer <CRON_TRIGGER_TOKEN>` |
     | Header | `Accept: application/vnd.github+json` |
     | Body | `{"ref":"main"}` |
     | Schedule | `30 08 * * 1-5` |
     | Timezone | **`Asia/Shanghai`**（在任务设置中修改，非默认 UTC） |

     关键：cron-job.org 默认使用 UTC，务必在任务设置中将时区改为 `Asia/Shanghai`，
     cron 表达式 `30 08 * * 1-5` 才是北京时间 08:30。若不改时区，
     需将 cron 改为 `30 0 * * 1-5`（UTC 00:30 = BJT 08:30）。

3. **兜底**
   保留 GitHub 内置 `schedule`（cron: `30 0 * * 1-5`），即使外部服务异常仍会尝试执行。

## Agent 注意事项

- 代码中**不要添加重试机制**
- `create_premium_figure()` 用 `Agg` 后台渲染（不弹窗）；`show_chart()` 仍用 `plt.show()` 弹窗
- 邮件发送用 `mail_utils.py`（`smtplib` 内嵌 base64 图表），不依赖外部库
- 系统代理可能开启，不写代理处理代码
- QDII 净值有 T+2 延迟，用 T-1 shift 对齐
- 缓存数据时保存全部列，不裁剪子集
- 秘密从环境变量读取，不硬编码
- 修改前先读本文件
- 图表横坐标用 `AutoDateLocator` + `AutoDateFormatter`，不写死 `MonthLocator`
- VIX 数据通过 FRED API 获取（`requests` 直调 JSON），增量缓存，不重复拉全量
- `rank_score()` 排名评分支持 `reverse` 参数控制正序/倒序
