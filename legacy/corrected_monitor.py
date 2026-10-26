#!/usr/bin/env python3
"""
板块与主题轮动监控系统 v2.1 - 修正版
修正了A股ETF代码错误，只使用确认正确的ETF
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class CorrectedRotationMonitor:
    """修正版轮动监控类"""

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

        # ==================== 美股主题ETF（已核实）====================
        self.us_themes = {
            # 科技细分
            'SMH': '半导体',
            'SOXX': '半导体SOXX',

            # 金融细分
            'KRE': '地区银行',
            'KBE': '银行',
            'XHB': '住宅建筑商',

            # 大宗商品
            'GDX': '金矿',
            'SLV': '白银',
            'GLD': '黄金',

            # 能源
            'XOP': '油气勘探',

            # 科技主题
            'BOTZ': '机器人AI',

            # 国防
            'ITA': '航空航天',
            'XAR': '国防',

            # 交通
            'IYT': '运输',
            'JETS': '航空',
        }

        # ==================== A股基准指数 ====================
        self.cn_benchmarks = {
            '510300.SS': '沪深300',
            '510050.SS': '上证50',
            '159915.SZ': '创业板指',
            '588000.SS': '科创50'
        }

        # ==================== A股主要行业ETF（已核实）====================
        self.cn_sectors = {
            # 科技/半导体
            '512480.SS': '半导体',  # 国联安半导体ETF
            '512760.SS': '半导体芯片',  # 国泰半导体ETF

            # 医药/医疗
            '512010.SS': '医药卫生',  # 易方达沪深300医药ETF
            '159938.SZ': '医疗器械',  # 华宝中证医疗ETF

            # 金融
            '512800.SS': '银行',  # 华宝中证银行ETF
            '512000.SS': '证券',  # 国泰证券ETF

            # 军工
            '512660.SS': '军工',  # 国泰军工ETF
            '512680.SS': '军工ETF',  # 广发军工ETF

            # 周期/资源
            '512400.SS': '有色金属',  # 华宝有色ETF
            '515220.SS': '煤炭',  # 国泰煤炭ETF

            # 新能源
            '516160.SS': '新能源',  # 易方达新能源ETF

            # 其他
            '516970.SS': '基建',  # 广发基建ETF
            '516110.SS': '汽车',  # 国泰汽车ETF
        }

        # ==================== A股主题ETF（已核实）====================
        self.cn_themes = {
            # 待核实后再添加，暂时留空
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

        score_cols = [f'{w}w_relative_{benchmark_code}' for w in weeks]
        available_score_cols = [c for c in score_cols if c in sectors_df.columns]

        if available_score_cols:
            sectors_df['score'] = sectors_df[available_score_cols].mean(axis=1)
        else:
            sectors_df['score'] = 0

        sectors_df['rank'] = sectors_df['score'].rank(ascending=False)
        sectors_df = sectors_df.sort_values('rank')

        return sectors_df

    def identify_trends(self, rankings):
        """识别趋势"""
        rankings['trend'] = 'neutral'

        strong_mask = (rankings['score'] > 5) & (rankings['4w_return'] > 0)
        rankings.loc[strong_mask, 'trend'] = 'strong_up'

        upgrade_mask = (rankings['4w_return'] > 0) & (rankings['12w_return'] > 0) & (rankings['score'] > 0)
        rankings.loc[upgrade_mask, 'trend'] = 'upgrading'

        downgrade_mask = (rankings['4w_return'] < 0) & (rankings['12w_return'] < 0)
        rankings.loc[downgrade_mask, 'trend'] = 'downgrading'

        weak_mask = (rankings['score'] < -5) & (rankings['4w_return'] < 0)
        rankings.loc[weak_mask, 'trend'] = 'weak_down'

        return rankings

    def generate_report(self, us_sector_rankings, us_theme_rankings, cn_sector_rankings):
        """生成报告"""
        report_date = datetime.now().strftime('%Y年%m月%d日')
        report = f"# 板块轮动监控报告 v2.1（修正版）\n\n"
        report += f"**生成时间**: {report_date}\n\n"
        report += f"**数据来源**: Yahoo Finance\n\n"
        report += f"**修正说明**: 已移除所有标记不确定的A股ETF，只使用核实确认的ETF\n\n"
        report += "---\n\n"

        # 美股板块
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
                report += f"- 综合得分: {row['score']:+.2f}\n\n"

        # 美股主题
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

        # A股板块
        if cn_sector_rankings is not None and not cn_sector_rankings.empty:
            report += "\n---\n\n"
            report += "## A股板块轮动排名\n\n"
            report += "### 📊 Top 5 - 关注重点\n\n"

            top5 = cn_sector_rankings.head(5)
            for idx, row in top5.iterrows():
                emoji = '🔥' if row.get('trend') == 'strong_up' else '📈' if row.get('trend') in ['upgrading', 'strong_up'] else '➡️'
                report += f"**{emoji} {row['rank']:.0f}. {row['name']} ({row['code'][:6]})**\n\n"
                report += f"- 当前价格: ¥{row['current_price']:.2f}\n"
                report += f"- 4周涨幅: {row['4w_return']:+.2f}%\n"
                report += f"- 12周涨幅: {row['12w_return']:+.2f}%\n"
                report += f"- 综合得分: {row['score']:+.2f}\n\n"

            report += "### 📋 完整排名\n\n"
            report += "| 排名 | 板块 | 代码 | 当前价 | 4周涨幅 | 12周涨幅 | 得分 | 趋势 |\n"
            report += "|------|------|------|--------|---------|----------|------|------|\n"

            for idx, row in cn_sector_rankings.iterrows():
                trend_emoji = {
                    'strong_up': '🔥',
                    'upgrading': '📈',
                    'neutral': '➡️',
                    'downgrading': '📉',
                    'weak_down': '💔'
                }
                emoji = trend_emoji.get(row.get('trend', 'neutral'), '➡️')
                report += f"| {row['rank']:.0f} | {row['name']} | {row['code'][:6]} | ¥{row['current_price']:.2f} | {row['4w_return']:+.2f}% | {row['12w_return']:+.2f}% | {row['score']:+.2f} | {emoji} |\n"

        report += "\n---\n\n"
        report += "## 💡 使用说明\n\n"
        report += "### ⚠️ 重要说明\n"
        report += "- 本版本已移除所有标记不确定的A股ETF\n"
        report += "- 只使用经过核实确认的ETF\n"
        report += "- 后续会逐步添加更多经过验证的ETF\n\n"
        report += "### 美股策略\n"
        report += "- ✅ 在Top 3板块中寻找个股机会\n"
        report += "- 🔍 关注强势上涨的主题\n"
        report += "- ❌ 规避正在降级和弱势下跌的主题\n\n"
        report += "### A股策略\n"
        report += "- ✅ 在Top 5板块中寻找个股机会\n"
        report += "- 🔍 结合政策导向和技术面\n"
        report += "- ⚠️ 注意涨跌停和T+1限制\n\n"

        report += "---\n\n"
        report += "**注**: 本报告基于历史价格数据生成，不构成投资建议。投资有风险，请谨慎决策。\n"

        return report

    def run_monitor(self, save_report=True):
        """运行监控"""
        print("=" * 60)
        print("板块轮动监控系统 v2.1（修正版）")
        print("=" * 60)
        print()

        # 美股板块
        print("【1/3】美股板块数据...")
        all_us_sector_data = {**self.us_benchmarks, **self.us_sectors}
        us_sector_returns = self.calculate_returns(self.get_price_data(all_us_sector_data))
        us_sector_returns = self.calculate_relative_strength(us_sector_returns, 'SPY', '标普500')
        us_sector_rankings = self.identify_trends(self.rank_sectors(us_sector_returns, 'SPY'))

        # 美股主题
        print("\n【2/3】美股主题数据...")
        all_us_theme_data = {**self.us_benchmarks, **self.us_themes}
        us_theme_returns = self.calculate_returns(self.get_price_data(all_us_theme_data))
        us_theme_returns = self.calculate_relative_strength(us_theme_returns, 'SPY', '标普500')
        us_theme_rankings = self.identify_trends(self.rank_sectors(us_theme_returns, 'SPY'))

        # A股板块
        print("\n【3/3】A股板块数据...")
        all_cn_sector_data = {**self.cn_benchmarks, **self.cn_sectors}
        cn_sector_returns = self.calculate_returns(self.get_price_data(all_cn_sector_data))
        cn_sector_returns = self.calculate_relative_strength(cn_sector_returns, '510300.SS', '沪深300')
        cn_sector_rankings = self.identify_trends(self.rank_sectors(cn_sector_returns, '510300.SS'))

        # 生成报告
        print("\n生成报告...")
        report = self.generate_report(
            us_sector_rankings,
            us_theme_rankings,
            cn_sector_rankings
        )

        # 保存报告
        if save_report:
            filename = f"corrected_rotation_report_{datetime.now().strftime('%Y%m%d')}.md"
            filepath = f"/Users/cast/AI内容/AI对话整理内容/金融和交易/09-监控报告/{filename}"

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)

            print(f"\n✓ 报告已保存到: {filepath}")

        return us_sector_rankings, us_theme_rankings, cn_sector_rankings, report


def main():
    """主函数"""
    monitor = CorrectedRotationMonitor()

    try:
        us_sector, us_theme, cn_sector, report = monitor.run_monitor(
            save_report=True
        )

        print("\n" + "=" * 60)
        print("✓ 修正版监控完成！")
        print("=" * 60)
        print(f"✓ 美股板块: {len(us_sector)} 个")
        print(f"✓ 美股主题: {len(us_theme)} 个")
        print(f"✓ A股板块: {len(cn_sector)} 个")
        print("\n⚠️ 注意:")
        print("- 已移除所有标记不确定的A股ETF")
        print("- 只使用核实确认的ETF")
        print("- 后续会逐步添加更多验证过的ETF")

    except Exception as e:
        print(f"\n✗ 错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
