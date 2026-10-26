# sector-monitor — 板块与主题轮动监控系统 v3

美股 ETF + A股 ETF 双市场板块轮动监控:批量采集 → 动量排名/趋势识别 → 历史对比 → 图表与增强版周报,一台 Mac 定时全自动运行。

## 功能

- **美股板块**: 40+ 只行业/主题 ETF(yfinance),5 只一批分批下载
  - 防 429 限流: 批间重试(90s 退避)+ **连续 2 批全限流熔断**(IP 被标记后果断放弃,降级为仅 A股报告,不硬刚刷新封锁窗口)
  - 全部失败时**优雅降级**: 美股段标"本次缺失",A股段照常产出
- **A股板块**: 58 只 ETF(Tushare 专业数据源)
- **排名与趋势**: 20/60 日收益 → 相对基准强度 → 综合得分 → 趋势分档(strong_up / upgrading / neutral / downgrading / weak_down)
- **历史对比**: 与上周排名对比,升降位标注
- **可视化与报告**: 3 张图表 + `enhanced_report_v3_日期.md` 完整报告

## 快速开始

```bash
pip install -r requirements.txt

# Tushare token(https://tushare.pro 注册获取)
export TUSHARE_TOKEN=你的token

python3 monitor_v3.py
```

输出在 `09-监控报告/`(报告 + charts/ + rankings_history.csv)。

## 定时运行(macOS launchd)

每周日 20:17 自动运行,示例 plist 见 `com.local.sector-monitor.example.plist`:

```bash
cp com.local.sector-monitor.example.plist ~/Library/LaunchAgents/com.local.sector-monitor.plist
launchctl load ~/Library/LaunchAgents/com.local.sector-monitor.plist
```

## 目录

| 路径 | 说明 |
|---|---|
| `monitor_v3.py` | 主程序(v3.1) |
| `tools/` | ETF 清单核验脚本(Tushare 交叉验证) |
| `legacy/` | v1/v2 旧版,存档 |
| `docs/` | ETF 清单、数据源调研、升级报告等文档 |

## 环境变量

| 变量 | 用途 |
|---|---|
| `TUSHARE_TOKEN` | Tushare Pro 接口 token(必需,A股数据) |

## 已知行为

- yfinance 对同 IP 高频请求限流严格且封锁窗口较长(实测 60+ 分钟),故采用"分批+熔断+降级"而非无限重试
- macOS 睡眠会压掉晚间定时窗口,醒后 launchd 补跑一次;进程挂起僵死由调用方看门狗兜底
