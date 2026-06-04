# 项目：场内金融工具

## 环境

```bash
conda activate fund-analysis
```

Python 3.10，依赖：akshare、pandas、matplotlib、numpy

## 文件清单

| 文件 | 说明 |
|------|------|
| fund_premium_analyzer.py | 场内基金溢价率分析 |
| us_index.py | 美股指数历史行情（纳指/标普等） |
| us_index_compare.py | 基金 vs 指数归一化对比 |
| fund_alert.py | 溢价率监控告警（邮件推送） |
| fund_cache/ | API 响应缓存（所有脚本共用） |
| AGENTS.md | 本文件 |

## 数据源

- 场内基金市场价 → 新浪财经 `fund_etf_hist_sina`
- 场内基金净值 → 东方财富 `fund_open_fund_info_em`
- 美股指数 → 新浪财经 `index_us_stock_sina`（代码：.NDX/.INX/.IXIC/.DJI）

## 缓存

- `fund_etf_spot_em.csv`：全市场 ETF 行情，永久，首次请求后不再调用 API
- `fund_lof_spot_em.csv`：全市场 LOF 行情，永久，首次请求后不再调用 API
- `{symbol}_market.csv`：最新日期 ≥ 今天-1 天则命中
- `{symbol}_nav.csv`：3 天内创建过则命中
- `{symbol}_index.csv`：最新日期 ≥ 今天-1 天则命中
- 缓存目录：`fund_cache/`（首次运行由脚本自动创建）

## 调用方式

```bash
# 场内基金溢价率分析
python fund_premium_analyzer.py                    # 默认 513870 近 1 年
python fund_premium_analyzer.py 513500 180
python fund_premium_analyzer.py 513870 365 --chart

# 美股指数行情
python us_index.py                                   # 默认 .NDX 近 180 天
python us_index.py .INX 365
python us_index.py .NDX 30 --chart

# 基金 vs 指数归一化对比
python us_index_compare.py                           # 默认 513100 vs .NDX 近 365 天
python us_index_compare.py 180                       # 默认 513100 近 180 天
python us_index_compare.py 365 513100 513500         # 两个基金
python us_index_compare.py 180 513500 --no-chart     # 仅打印表格

# 溢价率监控告警（配合 GitHub Actions 定时执行）
python fund_alert.py                                 # 需设置 SMTP 等环境变量
python fund_alert.py --dry-run                       # 仅打印，不推送
```

## GitHub Actions 定时任务

每天早上 9:30（北京时间，周一至周五）自动执行 `fund_alert.py`，检查各基金最新溢价率并推送邮件日报（含溢价率趋势图），每条基金附带买入区间建议。

| 配置项 | 位置 | 说明 |
|--------|------|------|
| `FUND_SYMBOLS` | GitHub > Settings > Variables > Actions | 监控的基金列表，逗号分隔，如 `513870,513100,513500` |
| `SMTP_HOST` | GitHub > Settings > Secrets > Actions | SMTP 服务器，如 `smtp.qq.com` |
| `SMTP_PORT` | GitHub > Settings > Secrets > Actions | SMTP 端口，如 `465` |
| `SMTP_USER` | GitHub > Settings > Secrets > Actions | 发件邮箱地址 |
| `SMTP_PASS` | GitHub > Settings > Secrets > Actions | SMTP 授权码（QQ 邮箱需生成授权码） |
| `MAIL_TO` | GitHub > Settings > Secrets > Actions | 收件邮箱，多个用逗号分隔 |

执行后自动将 `fund_cache/` 中的缓存数据 commit 回仓库，避免重复拉取。

## Agent 注意事项

- 代码中**不要添加重试机制**
- `create_premium_figure()` 用 `Agg` 后台渲染（不弹窗）；`show_chart()` 仍用 `plt.show()` 弹窗
- 邮件发送用 `smtplib` 内嵌 base64 图表，不依赖外部库
- 系统代理可能开启，不写代理处理代码
- QDII 净值有 T+2 延迟，用 T-1 shift 对齐
- 缓存数据时保存全部列，不裁剪子集
- 秘密从环境变量读取，不硬编码
- 修改前先读本文件
- 图表横坐标用 `AutoDateLocator` + `AutoDateFormatter`，不写死 `MonthLocator`
