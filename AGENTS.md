# 项目：场内金融工具

## 环境

```bash
conda activate fund-analysis
```

Python 3.10，依赖：akshare、pandas、matplotlib

## 文件清单

| 文件 | 说明 |
|------|------|
| fund_premium_analyzer.py | 场内基金溢价率分析 |
| us_index.py | 美股指数历史行情（纳指/标普等） |
| us_index_compare.py | 基金 vs 指数归一化对比 |
| fund_cache/ | API 响应缓存（所有脚本共用） |
| AGENTS.md | 本文件 |

## 数据源

- 场内基金市场价 → 新浪财经 `fund_etf_hist_sina`
- 场内基金净值 → 东方财富 `fund_open_fund_info_em`
- 美股指数 → 新浪财经 `index_us_stock_sina`（代码：.NDX/.INX/.IXIC/.DJI）

## 缓存

- `{symbol}_name.txt`：永久，一经缓存不再请求
- `{symbol}_market.csv`：最新日期 ≥ 今天-1 天则命中
- `{symbol}_nav.csv`：3 天内创建过则命中
- `{symbol}_index.csv`：最新日期 ≥ 今天-1 天则命中
- 缓存目录：`fund_cache/`

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
python fund_alert.py                                 # 需设置 FUND_SYMBOLS 和 BARK_KEY 环境变量
python fund_alert.py --dry-run                       # 仅打印，不推送
```

## GitHub Actions 定时任务

每天早上 9:30（北京时间，周一至周五）自动执行 `fund_alert.py`，检查各基金最新溢价率并推送 Bark 日报，每条基金附带买入区间建议。

| 配置项 | 位置 | 说明 |
|--------|------|------|
| `FUND_SYMBOLS` | GitHub > Settings > Variables > Actions | 监控的基金列表，逗号分隔，如 `513870,513100,513500` |
| `BARK_KEY` | GitHub > Settings > Secrets > Actions | Bark 推送 Key |

执行后自动将 `fund_cache/` 中的缓存数据 commit 回仓库，避免重复拉取。

## Agent 注意事项

- 代码中**不要添加重试机制**
- **不要修改缓存逻辑**
- 图表用 `plt.show()` 弹窗，不存文件
- 系统代理可能开启，不写代理处理代码
- QDII 净值有 T+2 延迟，用 T-1 shift 对齐
- 缓存数据时保存全部列，不裁剪子集
- 修改前先读本文件
- 图表横坐标用 `AutoDateLocator` + `AutoDateFormatter`，不写死 `MonthLocator`
