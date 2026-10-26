# 板块轮动监控系统使用指南

**功能**: 自动监控美股和A股板块ETF的相对强度排名
**语言**: Python 3.x
**数据源**: Yahoo Finance (免费)

---

## 快速开始

### 1. 安装依赖

```bash
pip install yfinance pandas
```

或者使用requirements.txt：

```bash
pip install -r requirements.txt
```

### 2. 运行监控

```bash
python sector_rotation_monitor.py
```

### 3. 查看报告

脚本会自动生成Markdown格式的报告，保存在同一目录下：

```
sector_rotation_report_20260216.md
```

报告包含：
- ✅ 美股Top 3板块（关注重点）
- ⚠️ 美股Bottom 3板块（谨慎规避）
- ✅ A股Top 5板块（关注重点）
- ⚠️ A股Bottom 5板块（谨慎规避）
- 📊 完整排名表
- 💡 使用建议

---

## 系统架构

### 监控的标的

**美股11个板块ETF：**
- XLK（科技）
- XLF（金融）
- XLE（能源）
- XLV（医疗）
- XLY（非必需消费）
- XLP（必需消费）
- XLI（工业）
- XLC（通信服务）
- XLRE（房地产）
- XLB（材料）
- XLU（公用事业）

**A股17个行业ETF：**
- 芯片/半导体（512480、512760）
- 医药（512010、159938）
- 消费（512930、159928）
- 金融（512800、515230）
- 新能源（516160、516790）
- 军工（512660、512680）
- 有色（512400）
- 煤炭（515220）
- 电力（516880）
- 基建（516970）
- 汽车（516110）

### 计算方法

1. **获取价格数据**: 获取最近3个月的数据
2. **计算收益率**: 计算4周和12周的收益率
3. **计算相对强度**: 相对于基准指数（美股用SPY，A股用沪深300）
4. **综合得分**: 4周和12周相对强度的平均值
5. **排名**: 按综合得分从高到低排序

---

## 定时任务设置

### 每周日自动运行

**macOS/Linux:**

使用crontab：

```bash
crontab -e
```

添加以下行（每周日晚上8点运行）：

```
0 20 * * 0 cd /path/to/金融和交易 && python sector_rotation_monitor.py
```

**Windows:**

使用任务计划程序：
1. 打开"任务计划程序"
2. 创建基本任务
3. 设置触发器：每周日
4. 设置操作：运行Python脚本

---

## 自定义配置

### 修改监控标的

编辑 `sector_rotation_monitor.py` 文件：

```python
# 修改A股行业ETF
self.cn_sectors = {
    '512480.SS': '芯片',
    '512760.SS': '半导体',
    # 添加或删除代码...
}
```

### 修改排名周期

默认使用4周和12周，可以修改：

```python
# 计算不同周期的收益率
for week in [2, 4, 8, 12]:  # 添加2周和8周
    # ...
```

### 修改基准指数

美股默认用SPY，A股默认用沪深300，可以修改：

```python
# 美股用QQQ作为基准
us_returns = self.calculate_relative_strength(us_returns, 'QQQ', '纳斯达克100')

# A股用创业板指作为基准
cn_returns = self.calculate_relative_strength(cn_returns, '159915.SZ', '创业板指')
```

---

## 输出示例

```
板块轮动监控报告
生成时间: 2026年02月16日

---

美股板块轮动排名

📊 Top 3 - 关注重点

1. 科技 (XLK)
- 当前价格: $145.23
- 4周涨幅: +8.5%
- 12周涨幅: +15.3%
- 相对强度(4周): +5.2%
- 相对强度(12周): +7.8%
- 综合得分: +6.50

2. 能源 (XLE)
- 当前价格: $87.45
...

⚠️ Bottom 3 - 谨慎规避

11. 公用事业 (XLU)
- 当前价格: $67.89
- 4周涨幅: -2.3%
- 12周涨幅: -5.1%
- 相对强度(4周): -5.9%
- 相对强度(12周): -7.6%
- 综合得分: -6.75
...
```

---

## 常见问题

### Q1: 数据获取失败

**原因**: 网络问题或Yahoo Finance服务不稳定

**解决**:
- 检查网络连接
- 稍后重试
- 使用VPN（如果在中国大陆）

### Q2: A股数据不准确

**原因**: Yahoo Finance的A股数据可能有延迟

**解决**:
- 交叉验证其他数据源
- 关注趋势而非绝对值
- 结合国内数据源（如东方财富）

### Q3: 如何解读相对强度

**正数**: 板块跑赢基准指数（强势）
**负数**: 板块跑输基准指数（弱势）
**数值越大**: 相对强度越高

**示例**:
- 科技板块相对强度 +5.2% = 跑赢标普500 5.2个百分点
- 公用事业相对强度 -3.1% = 跑输标普500 3.1个百分点

### Q4: 多久运行一次

**推荐**: 每周一次（周日晚上或周一早上）

**原因**:
- 板块轮动是中期趋势，不需要每日监控
- 周末有时间回顾和分析
- 为新的一周做准备

---

## 高级功能扩展

### 导出为Excel

在代码中添加：

```python
# 保存到Excel
us_rankings.to_excel('us_sectors.xlsx')
cn_rankings.to_excel('cn_sectors.xlsx')
```

### 发送邮件通知

```python
import smtplib
from email.mime.text import MIMEText

def send_email(report):
    msg = MIMEText(report)
    msg['Subject'] = '板块轮动周报'
    msg['From'] = 'your@email.com'
    msg['To'] = 'recipient@email.com'

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('your@email.com', 'password')
        server.send_message(msg)
```

### 集成到交易系统

```python
# 获取Top 3板块代码
top_sectors = us_rankings.head(3)['code'].tolist()

# 在这些板块中筛选个股
for sector_code in top_sectors:
    stocks = get_stocks_in_sector(sector_code)
    # ... 进一步筛选
```

---

## 免责声明

本工具仅用于教育和研究目的，不构成投资建议。投资有风险，请谨慎决策。

---

## 更新日志

**2026-02-16**
- 初始版本
- 支持美股11个板块ETF
- 支持A股17个行业ETF
- 自动生成Markdown报告
- 计算相对强度排名

---

**文档结束**
