#!/usr/bin/env python3
"""
板块与主题轮动监控系统 v2.0
监控美股和A股的板块ETF以及细分主题的相对强度排名
新增功能：主题监控、动态维护、趋势识别
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class EnhancedRotationMonitor:
    """增强版轮动监控类 - 板块 + 主题"""

    def __init__(self):
        # ==================== 美股基准指数 ====================
        self.us_benchmarks = {
            'SPY': '标普500',
            'QQQ': '纳斯达克100'
        }

        # ==================== 美股11个板块ETF ====================
        self.us_sectors = {
            'XLK': '科技',
            'XLF': '金融',
            'XLE': '能源',
            'XLV': '医疗',
            'XLY': '非必需消费',
            'XLP': '必需消费',
            'XLI': '工业',
            'XLC': '通信服务',
            'XLRE': '房地产',
            'XLB': '材料',
            'XLU': '公用事业'
        }

        # ==================== 美股主题ETF（新增）====================
        self.us_themes = {
            # 科技细分
            'SMH': '半导体',
            'SOXX': '半导体SOXX',
            'IGV': '软件',
            'FYC': '云计算',
            'CIBR': '网络安全',
            'XT': '通信设备',
            'FDL': '电信',

            # 金融细分
            'KRE': '地区银行',
            'KBE': '银行',
            'XLF': '金融',
            'IAK': '保险',
            'REM': '房贷REIT',

            # 房地产
            'XHB': '住宅建筑商',
            'HOMZ': '家居建筑',
            'REZ': '住宅REIT',

            # 大宗商品
            'GDX': '金矿',
            'SLV': '白银',
            'GLD': '黄金',
            'USO': '原油',
            'DBC': '大宗商品',
            'JJM': '工业金属',
            'REMX': '稀土',

            # 能源
            'XLE': '能源',
            'XOP': '油气勘探',
            'ICLN': '清洁能源',
            'PBW': '环保',
            'TAN': '太阳能',
            'FAN': '风电',

            # 科技主题
            'BOTZ': '机器人AI',
            'ARKK': '创新',
            'ARKG': '基因革命',
            'ARKF': '金融科技',

            # 国防
            'ITA': '航空航天',
            'XAR': '国防',
            'PPA': '航空航天国防',

            # 交通
            'IYT': '运输',
            'JETS': '航空',
            'DRIV': '自动驾驶',

            # 其他
            'BJK': '博彩',
            'PEJ': '娱乐',
            'PBS': '体育',
        }

        # ==================== A股基准指数 ====================
        self.cn_benchmarks = {
            '510300.SS': '沪深300',
            '510050.SS': '上证50',
            '159915.SZ': '创业板指',
            '588000.SS': '科创50'
        }

        # ==================== A股主要行业ETF ====================
        self.cn_sectors = {
            '512480.SS': '芯片',
            '512760.SS': '半导体',
            '512010.SS': '医药',
            '159938.SZ': '医药ETF',
            '512930.SS': '消费',
            '159928.SZ': '消费ETF',
            '512800.SS': '金融',
            '515230.SS': '金融ETF',
            '516160.SS': '新能源',
            '516790.SS': '新能源ETF',
            '512660.SS': '军工',
            '512680.SS': '军工ETF',
            '512400.SS': '有色',
            '515220.SS': '煤炭',
            '516880.SS': '电力',
            '516970.SS': '基建',
            '516110.SS': '汽车'
        }

        # ==================== A股主题ETF（新增）====================
        self.cn_themes = {
            # AI产业链
            '515000.SS': 'AI算力',
            '159819.SZ': 'AI应用',

            # 半导体细分
            '562960.SS': '半导体设备',
            '588200.SS': '芯片ETF',

            # 新能源细分
            '516790.SS': '光伏',
            '159863.SZ': '风电',
            '159767.SZ': '储能',
            '516390.SZ': '新能源车',

            # 军工细分
            '512660.SS': '军工',
            '512680.SS': '军工ETF',
            '512690.SS': '国防',

            # 科技主题
            '159631.SZ': '网络安全',
            '515220.SS': '云计算',
            '159783.SZ': '双创50',

            # 周期
            '518880.SS': '黄金',
            '512400.SS': '有色',
            '515220.SS': '煤炭',
            '516920.SS': '钢铁',

            # 消费细分
            '512930.SS': '白酒',
            '159928.SZ': '食品饮料',
            '159938.SZ': '家电',

            # 医药细分
            '512010.SS': '创新药',
            '159938.SZ': '医疗器械',
            '512980.SS': '中药',

            # 金融细分
            '512800.SS': '银行',
            '512000.SS': '券商',
            '512880.SS': '保险',

            # 其他主题
            '516970.SS': '中特估',
            '515050.SZ': '5G通信',
            '515000.SZ': '数字经济',
        }

    def get_price_data(self, symbols, period='3mo'):
        """获取价格数据"""
        print(f"正在获取 {len(symbols)} 个标的的数据...")

        data = {}
        for code, name in symbols.items():
            try:
                ticker = yf.Ticker(code)
                hist = ticker.history(period=period)

                if not hist.empty and 'Close' in hist.columns:
                    data[code] = {
                        'name': name,
                        'current_price': hist['Close'].iloc[-1],
                        'prices': hist['Close'],
                        'volume': hist['Volume'].iloc[-1] if 'Volume' in hist.columns else 0
                    }
                    print(f"  ✓ {code} ({name}): {hist['Close'].iloc[-1]:.2f}")
                else:
                    print(f"  ✗ {code} ({name}): 无数据")

            except Exception as e:
                print(f"  ✗ {code} ({name}): 错误 - {str(e)}")

        return data

    def calculate_returns(self, price_data, weeks=[4, 12]):
        """计算收益率"""
        results = []

        for code, data in price_data.items():
            prices = data['prices']
            current_price = data['current_price']
            name = data['name']
            volume = data.get('volume', 0)

            result = {
                'code': code,
                'name': name,
                'current_price': current_price,
                'volume': volume
            }

            # 计算不同周期的收益率
            for week in weeks:
                days_ago = week * 5
                if len(prices) > days_ago:
                    past_price = prices.iloc[-days_ago]
                    returns = (current_price - past_price) / past_price * 100
                    result[f'{week}w_return'] = returns
                else:
                    result[f'{week}w_return'] = None

            results.append(result)

        df = pd.DataFrame(results)
        return df

    def calculate_relative_strength(self, sector_returns, benchmark_code, benchmark_name):
        """计算相对强度"""
        benchmark_row = sector_returns[sector_returns['code'] == benchmark_code]

        if benchmark_row.empty:
            return sector_returns

        for week in [4, 12]:
            benchmark_return = benchmark_row[f'{week}w_return'].values[0]
            if benchmark_return is not None:
                sector_returns[f'{week}w_relative_{benchmark_code}'] = (
                    sector_returns[f'{week}w_return'] - benchmark_return
                )
            else:
                sector_returns[f'{week}w_relative_{benchmark_code}'] = None

        return sector_returns

    def rank_sectors(self, df, benchmark_code, weeks=[4, 12]):
        """对板块进行排名"""
        sectors_df = df[df['code'] != benchmark_code].copy()

        for week in weeks:
            col = f'{week}w_relative_{benchmark_code}'
            if col in sectors_df.columns:
                sectors_df[col] = pd.to_numeric(sectors_df[col], errors='coerce')

        # 计算综合得分
        score_cols = [f'{w}w_relative_{benchmark_code}' for w in weeks]
        available_score_cols = [c for c in score_cols if c in sectors_df.columns]

        if available_score_cols:
            sectors_df['score'] = sectors_df[available_score_cols].mean(axis=1)
        else:
            sectors_df['score'] = 0

        # 排名
        sectors_df['rank'] = sectors_df['score'].rank(ascending=False)
        sectors_df = sectors_df.sort_values('rank')

        return sectors_df

    def identify_trends(self, rankings):
        """识别趋势（升级/降级）"""
        rankings['trend'] = 'neutral'

        # 强势信号：得分>5且4周相对强度为正
        strong_mask = (rankings['score'] > 5) & (rankings['4w_return'] > 0)
        rankings.loc[strong_mask, 'trend'] = 'strong_up'

        # 升级信号：4周相对强度改善，12周相对强度也为正
        upgrade_mask = (rankings['4w_return'] > 0) & (rankings['12w_return'] > 0) & (rankings['score'] > 0)
        rankings.loc[upgrade_mask, 'trend'] = 'upgrading'

        # 降级信号：4周和12周相对强度都为负
        downgrade_mask = (rankings['4w_return'] < 0) & (rankings['12w_return'] < 0)
        rankings.loc[downgrade_mask, 'trend'] = 'downgrading'

        # 弱势信号：得分<-5且4周相对强度为负
        weak_mask = (rankings['score'] < -5) & (rankings['4w_return'] < 0)
        rankings.loc[weak_mask, 'trend'] = 'weak_down'

        return rankings

    def generate_enhanced_report(self, us_sector_rankings, us_theme_rankings,
                                  cn_sector_rankings, cn_theme_rankings):
        """生成增强版报告"""
        report_date = datetime.now().strftime('%Y年%m月%d日')
        report = f"# 板块与主题轮动监控报告 v2.0\n\n"
        report += f"**生成时间**: {report_date}\n\n"
        report += f"**数据来源**: Yahoo Finance\n\n"
        report += "---\n\n"

        # ==================== 美股板块轮动 ====================
        if us_sector_rankings is not None and not us_sector_rankings.empty:
            report += "## 美股板块轮动排名\n\n"
            report += "### 📊 Top 3 - 关注重点\n\n"

            top3 = us_sector_rankings.head(3)
            for idx, row in top3.iterrows():
                emoji = '🔥' if row.get('trend') == 'strong_up' else '📈' if row.get('trend') in ['upgrading', 'strong_up'] else '➡️'
                report += f"**{emoji} {row['rank']:.0f}. {row['name']} (${row['code'][:2]})**\n\n"
                report += f"- 当前价格: ${row['current_price']:.2f}\n"
                report += f"- 4周涨幅: {row['4w_return']:+.2f}%\n"
                report += f"- 12周涨幅: {row['12w_return']:+.2f}%\n"
                report += f"- 相对强度(4周): {row['4w_relative_SPY']:+.2f}%\n"
                report += f"- 综合得分: {row['score']:+.2f}\n"
                trend_desc = {
                    'strong_up': '强势上涨',
                    'upgrading': '正在升级',
                    'neutral': '中性',
                    'downgrading': '正在降级',
                    'weak_down': '弱势下跌'
                }
                report += f"- 趋势: {trend_desc.get(row.get('trend', 'neutral'), '中性')}\n\n"

            report += "### ⚠️ Bottom 3 - 谨慎规避\n\n"

            bottom3 = us_sector_rankings.tail(3)[::-1]
            for idx, row in bottom3.iterrows():
                emoji = '💔' if row.get('trend') == 'weak_down' else '📉' if row.get('trend') in ['downgrading', 'weak_down'] else '➡️'
                report += f"**{emoji} {row['rank']:.0f}. {row['name']} (${row['code'][:2]})**\n\n"
                report += f"- 当前价格: ${row['current_price']:.2f}\n"
                report += f"- 4周涨幅: {row['4w_return']:+.2f}%\n"
                report += f"- 综合得分: {row['score']:+.2f}\n\n"

        # ==================== 美股主题监控 ====================
        if us_theme_rankings is not None and not us_theme_rankings.empty:
            report += "---\n\n"
            report += "## 美股主题监控\n\n"
            report += "### 🔥 强势主题（Top 10）\n\n"

            top10 = us_theme_rankings.head(10)
            report += "| 排名 | 主题 | 代码 | 当前价 | 4周涨幅 | 12周涨幅 | 得分 | 趋势 |\n"
            report += "|------|------|------|--------|---------|----------|------|------|\n"

            for idx, row in top10.iterrows():
                trend_emoji = {
                    'strong_up': '🔥',
                    'upgrading': '📈',
                    'neutral': '➡️',
                    'downgrading': '📉',
                    'weak_down': '💔'
                }
                emoji = trend_emoji.get(row.get('trend', 'neutral'), '➡️')
                report += f"| {row['rank']:.0f} | {row['name']} | ${row['code'][:4]} | ${row['current_price']:.2f} | {row['4w_return']:+.2f}% | {row['12w_return']:+.2f}% | {row['score']:+.2f} | {emoji} |\n"

            report += "\n### 💡 主题建议\n\n"
            strong_up = us_theme_rankings[us_theme_rankings['trend'] == 'strong_up']
            if not strong_up.empty:
                report += "**✅ 强势上涨（重点关注）**:\n"
                for idx, row in strong_up.head(5).iterrows():
                    report += f"- {row['name']} (${row['code'][:4]}): 得分 {row['score']:+.2f}\n"
                report += "\n"

            upgrading = us_theme_rankings[us_theme_rankings['trend'] == 'upgrading']
            if not upgrading.empty:
                report += "**📈 正在升级（开始关注）**:\n"
                for idx, row in upgrading.head(5).iterrows():
                    report += f"- {row['name']} (${row['code'][:4]}): 得分 {row['score']:+.2f}\n"
                report += "\n"

            downgrading = us_theme_rankings[us_theme_rankings['trend'] == 'downgrading']
            if not downgrading.empty:
                report += "**📉 正在降级（考虑离场）**:\n"
                for idx, row in downgrading.head(5).iterrows():
                    report += f"- {row['name']} (${row['code'][:4]}): 得分 {row['score']:+.2f}\n"
                report += "\n"

        # ==================== A股板块轮动 ====================
        if cn_sector_rankings is not None and not cn_sector_rankings.empty:
            report += "---\n\n"
            report += "## A股板块轮动排名\n\n"
            report += "### 📊 Top 5 - 关注重点\n\n"

            top5 = cn_sector_rankings.head(5)
            for idx, row in top5.iterrows():
                emoji = '🔥' if row.get('trend') == 'strong_up' else '📈' if row.get('trend') in ['upgrading', 'strong_up'] else '➡️'
                report += f"**{emoji} {row['rank']:.0f}. {row['name']} ({row['code'][:6]})**\n\n"
                report += f"- 当前价格: ¥{row['current_price']:.2f}\n"
                report += f"- 4周涨幅: {row['4w_return']:+.2f}%\n"
                report += f"- 12周涨幅: {row['12w_return']:+.2f}%\n"
                report += f"- 综合得分: {row['score']:+.2f}\n"
                report += f"- 趋势: {'强势上涨' if row.get('trend') == 'strong_up' else '正在升级' if row.get('trend') == 'upgrading' else '中性'}\n\n"

            report += "### ⚠️ Bottom 5 - 谨慎规避\n\n"

            bottom5 = cn_sector_rankings.tail(5)[::-1]
            for idx, row in bottom5.iterrows():
                emoji = '💔' if row.get('trend') == 'weak_down' else '📉' if row.get('trend') in ['downgrading', 'weak_down'] else '➡️'
                report += f"**{emoji} {row['rank']:.0f}. {row['name']} ({row['code'][:6]})**\n\n"
                report += f"- 当前价格: ¥{row['current_price']:.2f}\n"
                report += f"- 4周涨幅: {row['4w_return']:+.2f}%\n"
                report += f"- 综合得分: {row['score']:+.2f}\n\n"

        # ==================== A股主题监控 ====================
        if cn_theme_rankings is not None and not cn_theme_rankings.empty:
            report += "---\n\n"
            report += "## A股主题监控\n\n"
            report += "### 🔥 强势主题（Top 10）\n\n"

            top10 = cn_theme_rankings.head(10)
            report += "| 排名 | 主题 | 代码 | 当前价 | 4周涨幅 | 12周涨幅 | 得分 | 趋势 |\n"
            report += "|------|------|------|--------|---------|----------|------|------|\n"

            for idx, row in top10.iterrows():
                trend_emoji = {
                    'strong_up': '🔥',
                    'upgrading': '📈',
                    'neutral': '➡️',
                    'downgrading': '📉',
                    'weak_down': '💔'
                }
                emoji = trend_emoji.get(row.get('trend', 'neutral'), '➡️')
                report += f"| {row['rank']:.0f} | {row['name']} | {row['code'][:6]} | ¥{row['current_price']:.2f} | {row['4w_return']:+.2f}% | {row['12w_return']:+.2f}% | {row['score']:+.2f} | {emoji} |\n"

        # ==================== 使用建议 ====================
        report += "\n---\n\n"
        report += "## 💡 使用建议\n\n"

        report += "### 美股策略\n"
        report += "- ✅ 在Top 3板块中寻找个股机会\n"
        report += "- 🔍 关注强势上涨的主题（🔥标记）\n"
        report += "- 📈 寻找正在升级的主题（📈标记）的早期机会\n"
        report += "- ❌ 规避正在降级和弱势下跌的主题\n\n"

        report += "### A股策略\n"
        report += "- ✅ 在Top 5板块中寻找个股机会\n"
        report += "- 🔍 结合政策导向和技术面\n"
        report += "- 📈 关注正在升级的主题\n"
        report += "- ⚠️ 注意涨跌停和T+1限制\n\n"

        report += "### 主题维护建议\n"
        report += "- 每周回顾主题清单，添加新兴主题\n"
        report += "- 移除失去动能的主题（得分<-5且趋势为💔）\n"
        report += "- 在强势板块中寻找细分主题机会\n"
        report += "- 关注成交量放大的主题突破\n\n"

        report += "---\n\n"
        report += "**注**: 本报告基于历史价格数据生成，不构成投资建议。投资有风险，请谨慎决策。\n"

        return report

    def run_monitor(self, save_report=True, include_themes=True):
        """运行完整监控流程"""
        print("=" * 60)
        print("板块与主题轮动监控系统 v2.0")
        print("=" * 60)
        print()

        # ==================== 美股板块 ====================
        print("【1/4】美股板块数据...")
        all_us_sector_data = {**self.us_benchmarks, **self.us_sectors}
        us_sector_returns = self.calculate_returns(self.get_price_data(all_us_sector_data))
        us_sector_returns = self.calculate_relative_strength(us_sector_returns, 'SPY', '标普500')
        us_sector_rankings = self.identify_trends(self.rank_sectors(us_sector_returns, 'SPY'))

        # ==================== 美股主题 ====================
        us_theme_rankings = None
        if include_themes:
            print("\n【2/4】美股主题数据...")
            all_us_theme_data = {**self.us_benchmarks, **self.us_themes}
            us_theme_returns = self.calculate_returns(self.get_price_data(all_us_theme_data))
            us_theme_returns = self.calculate_relative_strength(us_theme_returns, 'SPY', '标普500')
            us_theme_rankings = self.identify_trends(self.rank_sectors(us_theme_returns, 'SPY'))

        # ==================== A股板块 ====================
        print("\n【3/4】A股板块数据...")
        all_cn_sector_data = {**self.cn_benchmarks, **self.cn_sectors}
        cn_sector_returns = self.calculate_returns(self.get_price_data(all_cn_sector_data))
        cn_sector_returns = self.calculate_relative_strength(cn_sector_returns, '510300.SS', '沪深300')
        cn_sector_rankings = self.identify_trends(self.rank_sectors(cn_sector_returns, '510300.SS'))

        # ==================== A股主题 ====================
        cn_theme_rankings = None
        if include_themes:
            print("\n【4/4】A股主题数据...")
            all_cn_theme_data = {**self.cn_benchmarks, **self.cn_themes}
            cn_theme_returns = self.calculate_returns(self.get_price_data(all_cn_theme_data))
            cn_theme_returns = self.calculate_relative_strength(cn_theme_returns, '510300.SS', '沪深300')
            cn_theme_rankings = self.identify_trends(self.rank_sectors(cn_theme_returns, '510300.SS'))

        # 生成报告
        print("\n生成报告...")
        report = self.generate_enhanced_report(
            us_sector_rankings, us_theme_rankings,
            cn_sector_rankings, cn_theme_rankings
        )

        # 保存报告
        if save_report:
            filename = f"enhanced_rotation_report_{datetime.now().strftime('%Y%m%d')}.md"
            filepath = f"/Users/cast/AI内容/AI对话整理内容/金融和交易/{filename}"

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)

            print(f"\n✓ 报告已保存到: {filepath}")

        return us_sector_rankings, us_theme_rankings, cn_sector_rankings, cn_theme_rankings, report


def main():
    """主函数"""
    monitor = EnhancedRotationMonitor()

    try:
        us_sector, us_theme, cn_sector, cn_theme, report = monitor.run_monitor(
            save_report=True,
            include_themes=True
        )

        print("\n" + "=" * 60)
        print("报告预览:")
        print("=" * 60)
        print(report[:1500] + "...\n")

        print("✓ 监控完成！")
        print(f"✓ 美股板块: {len(us_sector)} 个")
        print(f"✓ 美股主题: {len(us_theme)} 个" if us_theme is not None else "")
        print(f"✓ A股板块: {len(cn_sector)} 个")
        print(f"✓ A股主题: {len(cn_theme)} 个" if cn_theme is not None else "")

    except Exception as e:
        print(f"\n✗ 错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
