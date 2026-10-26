#!/usr/bin/env python3
"""
板块与主题轮动监控系统 v3.1（Tushare版）
新功能：
1. 完整的ETF清单（美股39个 + A股43个）
2. 使用Tushare作为A股数据源（专业金融数据）
3. A股主题监控
4. 历史对比功能
5. 数据可视化（图表）
"""

import yfinance as yf
import tushare as ts
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from datetime import datetime, timedelta
import warnings
import os
import time
warnings.filterwarnings('ignore')


class EnhancedRotationMonitorV3:
    """升级版轮动监控类 v3.0"""

    def __init__(self):
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        # 初始化Tushare API
        self.ts_token = os.environ.get('TUSHARE_TOKEN', '')
        ts.set_token(self.ts_token)
        self.pro = ts.pro_api()

        # ==================== 美股ETF ====================
        self.us_benchmark = 'SPY'  # 标普500作为基准

        self.us_etfs = {
            # 基准指数
            'SPY': '标普500',

            # SPDR Select Sector ETFs (11个)
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
            'XLU': '公用事业',

            # Vanguard Sector ETFs (10个)
            'VGT': '科技Vanguard',
            'VFH': '金融Vanguard',
            'VDE': '能源Vanguard',
            'VHT': '医疗Vanguard',
            'VCR': '非必需消费Vanguard',
            'VDC': '必需消费Vanguard',
            'VIS': '工业Vanguard',
            'VOX': '通信服务Vanguard',
            'VNQ': '房地产Vanguard',
            'VMI': '材料Vanguard',

            # 主题ETF
            'SMH': '半导体',
            'SOXX': '半导体SOXX',
            'GDX': '金矿',
            'GLD': '黄金',
            'SLV': '白银',
            'XOP': '油气勘探',
            'KRE': '地区银行',
            'XHB': '住宅建筑商',
            'KBE': '银行',
            'ITA': '航空航天',
            'XAR': '国防',
            'IYT': '运输',
            'JETS': '航空',
            'BOTZ': '机器人AI',

            # 科技主题
            'CLOU': '云计算',
            'WEBL': '网络安全',
            'FDN': '互联网',
            # 'THNQ': '人工智能',  # 移除：数据获取失败
        }

        # ==================== A股ETF ====================
        # 2026-06-26 重构：剔除Tushare数据失效代码（科创588000/588200），
        # 每个行业最多2个ETF，按申万/中证行业分类补全缺失板块。
        # 所有代码与名称均已通过Tushare fund_basic/fund_daily 核验。
        self.cn_etfs = {
            # ===== 基准指数 =====
            '510300': ('沪深300ETF', 'index'),
            '510050': ('上证50ETF', 'index'),
            '159915': ('创业板ETF', 'index'),
            '510500': ('中证500ETF', 'index'),
            '512100': ('中证1000ETF', 'index'),  # 宽基，归入index便于参考

            # ===== 科技/半导体（核心赛道，最多2×子板块）=====
            '512480': ('半导体ETF', 'sector'),       # 国联安半导体
            '512760': ('芯片ETF', 'sector'),         # 国寿芯片
            '159995': ('芯片ETF鹏华', 'sector'),     # 鹏华芯片
            '515000': ('科技ETF', 'sector'),         # 华宝科技龙头
            '515980': ('人工智能ETF', 'sector'),     # 平安AI
            '159819': ('人工智能ETF易方达', 'sector'),

            # ===== 医药/医疗（2个：综合医药 + 创新药）=====
            '512010': ('医药ETF', 'sector'),         # 易方达医药卫生
            '515120': ('创新药ETF', 'sector'),       # 广发创新药

            # ===== 金融（3个子行业，各最多2个）=====
            '512800': ('银行ETF', 'sector'),         # 华宝银行
            '515020': ('银行ETF华夏', 'sector'),     # 华夏银行
            '512000': ('证券ETF', 'sector'),         # 华宝证券
            '512880': ('证券ETF东财', 'sector'),     # 东方财富证券
            '515630': ('证券保险ETF', 'sector'),     # 鹏华800证券保险

            # ===== 军工/国防（2个）=====
            '512660': ('军工ETF', 'sector'),         # 国泰军工
            '512680': ('军工ETF广发', 'sector'),     # 广发军工

            # ===== 有色/煤炭/钢铁/稀土（资源类）=====
            '512400': ('有色金属ETF', 'sector'),     # 南方有色金属
            '515220': ('煤炭ETF', 'sector'),         # 国泰煤炭
            '515210': ('钢铁ETF', 'sector'),         # 国泰钢铁
            '516780': ('稀土ETF', 'theme'),          # 华泰柏瑞稀土

            # ===== 化工（最多2个）=====
            '516020': ('化工ETF', 'theme'),          # 华宝化工
            '159870': ('化工ETF天弘', 'theme'),      # 天弘化工

            # ===== 油气/石化（最多2个）=====
            '561360': ('石油ETF', 'theme'),          # 南方原油
            '159309': ('油气ETF汇添富', 'theme'),    # 汇添富能源

            # ===== 新能源/光伏/电池/新能源车 =====
            '516160': ('新能源ETF', 'sector'),       # 广发新能源车
            '159857': ('光伏ETF', 'theme'),          # 天弘光伏
            '159767': ('电池ETF', 'theme'),          # 广发电池龙头
            '515030': ('新能源车ETF', 'theme'),      # 华夏新能源车

            # ===== 电力/电网/绿电（最多2个）=====
            '561560': ('电力ETF', 'theme'),          # 华泰柏瑞电力
            '159326': ('电网设备ETF', 'theme'),      # 华夏电网设备

            # ===== 基建/建材/房地产（地产链）=====
            '516950': ('基建ETF', 'sector'),         # 银华中证基建
            '159745': ('建材ETF', 'theme'),          # 国泰建筑材料
            '512200': ('房地产ETF', 'sector'),       # 南方房地产

            # ===== 汽车/机械/机器人（中游制造）=====
            '516110': ('汽车ETF', 'sector'),         # 国泰汽车
            '159272': ('机器人ETF', 'sector'),       # 富国国证机器人产业
            '159213': ('机器人ETF汇添富', 'sector'), # 汇添富中证机器人
            '515970': ('工程机械ETF', 'sector'),     # 华夏中证工程机械
            '159138': ('工程机械ETF易方达', 'sector'), # 易方达中证工程机械

            # ===== 消费（食品饮料/家电/消费/农业）=====
            '515170': ('食品饮料ETF', 'sector'),     # 华夏食品饮料
            '159996': ('家电ETF', 'sector'),         # 国泰家电
            '159928': ('消费ETF', 'sector'),         # 汇添富中证主要消费
            '159825': ('农业ETF', 'sector'),         # 富国农业

            # ===== 交通运输/物流（申万交运）=====
            '516530': ('物流ETF', 'sector'),         # 银华中证现代物流
            '159662': ('交运ETF', 'sector'),         # 南方国证交通运输

            # ===== 社会服务/旅游 =====
            '562510': ('旅游ETF', 'sector'),         # 华夏中证旅游主题
            '159766': ('旅游ETF富国', 'sector'),     # 富国中证旅游主题

            # ===== 传媒/影视 =====
            '159855': ('影视ETF', 'theme'),          # 广发中证传媒
            '512930': ('AI人工智能ETF', 'theme'),    # 华夏AI

            # ===== 通信/环保/软件（细分）=====
            '515880': ('通信ETF', 'sector'),         # 国泰通信设备
            '515230': ('软件ETF', 'sector'),         # 华夏软件
            '512580': ('环保ETF', 'sector'),         # 广发环保

            # ===== 黄金/商品（避险+有色商品）=====
            '518880': ('黄金ETF', 'theme'),          # 华安黄金
            '159934': ('黄金ETF易方达', 'theme'),    # 易方达黄金

            # ===== 策略/风格 =====
            '515080': ('红利ETF', 'strategy'),       # 招商中证红利
            '512890': ('红利低波ETF', 'strategy'),   # 华泰柏瑞红利低波
        }

    def get_yahoo_data(self, symbols, period='3mo'):
        """从Yahoo Finance获取美股数据（小分批下载 + 限流退避）

        2026-10起Yahoo限流收紧:逐只请求(39+次)和39只一次性批量均被拒,
        但小批量(≤6只)请求可正常通过。改为每批5只下载、批间隔休眠30秒;
        单批被限流重试1次;连续2批全被限流则判定IP被标记,立即放弃美股段
        (实测持续重试会刷新封锁窗口,被封60+分钟)。
        """
        symbol_list = list(symbols)
        chunk_size = 5
        chunks = [symbol_list[i:i + chunk_size]
                  for i in range(0, len(symbol_list), chunk_size)]
        print(f"获取Yahoo Finance数据: {len(symbol_list)}个标的,"
              f"分{len(chunks)}批下载(每批{chunk_size}只)...")
        data = {}
        consecutive_limited = 0  # 连续被限流的批数
        for ci, chunk in enumerate(chunks, 1):
            # 连续2批全被限流→IP已被标记,继续重试只会刷新封锁窗口
            # (2026-10-21实测:持续重试被封60+分钟),果断放弃美股段
            if consecutive_limited >= 2:
                rest = sum(len(c) for c in chunks[ci - 1:])
                print(f"  ⛔ 连续{consecutive_limited}批被限流,IP已被Yahoo标记,"
                      f"跳过剩余{rest}只,本次降级为仅A股报告")
                break
            got_chunk = {}
            for attempt in range(2):
                try:
                    batch = yf.download(
                        ' '.join(chunk), period=period, interval='1d',
                        auto_adjust=True, progress=False,
                        group_by='ticker', threads=False,
                    )
                    if batch is not None and not batch.empty:
                        multi = isinstance(batch.columns, pd.MultiIndex)
                        for code in chunk:
                            try:
                                sub = batch[code] if multi else batch
                                if 'Close' not in sub.columns:
                                    continue
                                close = sub['Close'].dropna()
                                if len(close) >= 61:  # 60日收益需61个交易日
                                    got_chunk[code] = close
                            except Exception:
                                pass
                except Exception:
                    pass
                if got_chunk:
                    break
                if attempt < 1:
                    print(f"  ⏳ 第{ci}批被限流,等待90秒后重试(2/2)...")
                    time.sleep(90)
            for code, close in got_chunk.items():
                data[code] = {
                    'name': self.us_etfs[code],
                    'prices': close,
                    'volume': pd.Series(dtype=float),
                }
                print(f"  ✓ {code} ({self.us_etfs[code]}): {close.iloc[-1]:.2f}")
            if len(got_chunk) < len(chunk):
                missing = [c for c in chunk if c not in got_chunk]
                print(f"  ✗ 第{ci}批缺失{len(missing)}只: {', '.join(missing)}")
                consecutive_limited += 1 if not got_chunk else 0
            else:
                consecutive_limited = 0
            if ci < len(chunks):
                time.sleep(30)  # 批间隔休眠,避免触发限流
        print(f"  分批下载完成: {len(data)}/{len(symbol_list)}")
        return data

    def get_tushare_data(self, etf_dict, days=60):
        """从Tushare获取A股数据

        参数:
            etf_dict: ETF字典 {code: (name, type)}
            days: 需要的交易日数量（默认60交易日）

        返回:
            data: 字典，包含价格和成交量数据
        """
        print(f"\n获取Tushare数据: {len(etf_dict)}个标的...")
        data = {}

        # 计算日期范围：获取更多交易日以确保有足够数据
        # 60个交易日 ≈ 85个自然日
        end_date = datetime.now()
        start_date = end_date - timedelta(days=120)  # 获取120天以确保有60个交易日

        start_date_str = start_date.strftime("%Y%m%d")
        end_date_str = end_date.strftime("%Y%m%d")

        print(f"  日期范围: {start_date_str} ~ {end_date_str}")

        failed = []  # 0条数据的代码(疑似配额限制),稍后统一重试
        for code, (name, etf_type) in etf_dict.items():
            try:
                entry = self._fetch_tushare_one(
                    code, name, etf_type, start_date_str, end_date_str, days)
                if entry:
                    data[code] = entry['data']
                    print(f"  ✓ {code} ({name}): {entry['last']:.3f} ({entry['rows']}条·后复权)")
                else:
                    print(f"  ✗ {code} ({name}): 数据不足 (0条)")
                    failed.append(code)
            except Exception as e:
                # 容错处理：即使单个ETF失败，也不影响其他ETF
                error_msg = str(e)
                print(f"  ✗ {code} ({name}): 错误 - {error_msg[:60]}")
            # 配额保护：Tushare按分钟限调用次数,118次无间隔连发会耗尽配额
            # (2026-10-23实测尾部12只全部返回0条),每只间隔0.7秒错峰
            time.sleep(0.7)

        # 配额重试：0条的代码等60秒跨过配额窗口后重试一次
        if failed:
            print(f"\n  ⏳ {len(failed)}只0条(疑似Tushare配额限制),等待60秒后重试...")
            time.sleep(60)
            for code in failed:
                name, etf_type = etf_dict[code]
                try:
                    entry = self._fetch_tushare_one(
                        code, name, etf_type, start_date_str, end_date_str, days)
                    if entry:
                        data[code] = entry['data']
                        print(f"  ✓ {code} ({name}): {entry['last']:.3f} "
                              f"({entry['rows']}条·后复权) [重试成功]")
                    else:
                        print(f"  ✗ {code} ({name}): 重试仍0条,本次放弃")
                except Exception as e:
                    print(f"  ✗ {code} ({name}): 重试错误 - {str(e)[:60]}")
                time.sleep(0.7)

        return data

    def _fetch_tushare_one(self, code, name, etf_type, start_date_str, end_date_str, days):
        """抓取单只ETF后复权数据。返回{'data':…,'rows':…,'last':…}或None

        获取后复权(hfq)历史行情：消除分红/拆分导致的价格跳变。
        注意：pro_bar 的 adj 参数对ETF复权已失效（拆分日仍断崖），
        故采用手动后复权 = fund_daily原始价 × fund_adj复权因子，
        跨拆分/分红日天然连续，涨跌幅计算准确。
        """
        # 确定市场后缀
        if code.startswith('51') or code.startswith('56'):
            ts_code = f'{code}.SH'  # 上海市场
        elif code.startswith('15') or code.startswith('16'):
            ts_code = f'{code}.SZ'  # 深圳市场
        else:
            ts_code = code

        raw = self.pro.fund_daily(
            ts_code=ts_code,
            start_date=start_date_str,
            end_date=end_date_str
        )
        adj = self.pro.fund_adj(
            ts_code=ts_code,
            start_date=start_date_str,
            end_date=end_date_str
        )

        df = None
        if raw is not None and len(raw) > 0:
            raw = raw.sort_values('trade_date').reset_index(drop=True)
            if adj is not None and len(adj) > 0:
                adj = adj.sort_values('trade_date').reset_index(drop=True)
                # 按日期合并复权因子
                df = raw.merge(adj[['trade_date', 'adj_factor']], on='trade_date', how='left')
                df['adj_factor'] = df['adj_factor'].ffill().bfill()
                # 手动后复权：close × 当日累积复权因子
                df['close'] = df['close'] * df['adj_factor']
            else:
                # 无复权因子时退化为不复权
                df = raw

        # 需要 days+1 条：多取一个点供 calculate_returns 做真正的 N 交易日比较
        if df is None or len(df) < days + 1:
            return None

        # 按日期排序,只取最后 days+1 条数据
        df = df.sort_values('trade_date').tail(days + 1)

        # 转换日期格式
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df.index = df['trade_date']

        # 提取需要的列（兼容 fund_daily 列名 vol）
        vol_col = 'vol' if 'vol' in df.columns else 'volume'
        return {
            'data': {
                'name': name,
                'type': etf_type,
                'prices': df['close'],
                'volume': df[vol_col] if vol_col in df.columns else pd.Series(dtype=float)
            },
            'rows': len(df),
            'last': df['close'].iloc[-1],
        }

    def calculate_returns(self, price_data, days=[20, 60]):
        """计算收益率"""
        results = []
        for code, data in price_data.items():
            prices = data['prices']
            name = data['name']

            result = {'code': code, 'name': name}

            for day in days:
                # 需要 day+1 个点才能算出真正的 day 个交易日间隔的涨幅
                # （最新价 + 往前数 day 个间隔 = iloc[-(day+1)]）
                if len(prices) >= day + 1:
                    past_price = prices.iloc[-(day + 1)]
                    current_price = prices.iloc[-1]
                    returns = (current_price - past_price) / past_price * 100
                    result[f'{day}d_return'] = returns
                else:
                    result[f'{day}d_return'] = None

            results.append(result)

        return pd.DataFrame(results)

    def calculate_relative_strength(self, returns_df, benchmark_code):
        """计算相对强度"""
        # 检查数据是否为空
        if returns_df.empty:
            print(f"⚠️ 警告: 没有数据，跳过相对强度计算")
            return returns_df

        # 检查是否有'code'列
        if 'code' not in returns_df.columns:
            print(f"⚠️ 警告: 数据中没有'code'列")
            return returns_df

        benchmark_row = returns_df[returns_df['code'] == benchmark_code]

        if benchmark_row.empty:
            print(f"⚠️ 警告: 基准 {benchmark_code} 不在数据中")
            # 即使没有基准，也使用原始收益率计算score
            available_cols = [c for c in ['20d_return', '60d_return'] if c in returns_df.columns]
            if available_cols:
                returns_df['score'] = returns_df[available_cols].mean(axis=1)
            return returns_df

        for day in [20, 60]:
            return_col = f'{day}d_return'
            relative_col = f'{day}d_relative'

            if return_col not in benchmark_row.columns:
                continue

            benchmark_return = benchmark_row[return_col].values[0]

            if benchmark_return is None:
                print(f"⚠️ 警告: 基准 {benchmark_code} 的 {day}d_return 为 None")
                returns_df[relative_col] = None
            else:
                returns_df[relative_col] = returns_df[return_col] - benchmark_return

        # 计算综合得分
        available_cols = [c for c in ['20d_relative', '60d_relative'] if c in returns_df.columns]
        if available_cols:
            returns_df['score'] = returns_df[available_cols].mean(axis=1)
        else:
            # 如果相对强度计算失败，使用原始收益率
            available_cols = [c for c in ['20d_return', '60d_return'] if c in returns_df.columns]
            if available_cols:
                returns_df['score'] = returns_df[available_cols].mean(axis=1)

        return returns_df

    def rank_and_identify_trend(self, df, exclude_benchmark=None):
        """排名和趋势识别"""
        # 排除基准指数
        if exclude_benchmark and exclude_benchmark in df['code'].values:
            df = df[df['code'] != exclude_benchmark].copy()

        # 移除得分为None的行
        df = df.dropna(subset=['score']).copy()

        df = df.sort_values('score', ascending=False)
        df['rank'] = range(1, len(df) + 1)

        # 趋势识别
        df['trend'] = 'neutral'
        df.loc[(df['score'] > 5) & (df['20d_return'] > 0), 'trend'] = 'strong_up'
        df.loc[(df['score'] > 0) & (df['20d_return'] > 0) & (df['60d_return'] > 0), 'trend'] = 'upgrading'
        df.loc[(df['score'] < 0) & (df['20d_return'] < 0) & (df['60d_return'] < 0), 'trend'] = 'downgrading'
        df.loc[(df['score'] < -5) & (df['20d_return'] < 0), 'trend'] = 'weak_down'

        return df

    def compare_with_history(self, current_rankings, history_file='rankings_history.csv'):
        """历史对比功能"""
        # 确保目录存在
        history_dir = os.path.dirname(history_file)
        if history_dir and not os.path.exists(history_dir):
            os.makedirs(history_dir, exist_ok=True)

        # 读取历史排名
        if os.path.exists(history_file):
            try:
                history_df = pd.read_csv(history_file)
                # 找到上周的数据
                last_week = history_df[history_df['date'] == history_df['date'].max()]
                if not last_week.empty:
                    print("\n📊 历史对比：")
                    for idx, row in current_rankings.head(5).iterrows():
                        code = row['code']
                        last_week_rank = last_week[last_week['code'] == code]['rank'].values
                        if len(last_week_rank) > 0:
                            change = last_week_rank[0] - row['rank']
                            emoji = "⬆️" if change > 0 else "⬇️" if change < 0 else "➡️"
                            print(f"  {row['name']}: {last_week_rank[0]} → {row['rank']} {emoji}")
            except:
                print("\n⚠️ 无法读取历史数据")

        # 保存当前排名
        current_rankings['date'] = datetime.now().strftime('%Y-%m-%d')

        # 追加到历史文件
        if os.path.exists(history_file):
            history_df = pd.read_csv(history_file)
            history_df = pd.concat([history_df, current_rankings[['date', 'code', 'name', 'rank', 'score']]], ignore_index=True)
        else:
            history_df = current_rankings[['date', 'code', 'name', 'rank', 'score']]

        history_df.to_csv(history_file, index=False)
        print(f"✓ 排名历史已保存到 {history_file}")

    def generate_charts(self, us_df, cn_df, output_dir):
        """生成可视化图表"""
        print(f"\n生成图表并保存到 {output_dir}/")

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        date_str = datetime.now().strftime('%Y%m%d')

        # 美股数据缺失时降级（None → 空df，跳过美股图）
        if us_df is None:
            us_df = pd.DataFrame()

        # 美股板块排名图
        if not us_df.empty:
            plt.figure(figsize=(12, 6))
            top10 = us_df.head(10)
            colors = ['red' if x < 0 else 'green' for x in top10['score']]
            plt.barh(range(len(top10)), top10['score'][::-1], color=colors[::-1])
            plt.yticks(range(len(top10)), top10['name'][::-1])
            plt.xlabel('综合得分')
            plt.title(f'美股板块排名（Top 10）- {date_str}')
            plt.grid(axis='x', alpha=0.3)
            plt.tight_layout()
            plt.savefig(f"{output_dir}/us_sectors_ranking_{date_str}.png", dpi=100, bbox_inches='tight')
            plt.close()
            print(f"  ✓ 美股板块排名图")

        # A股板块排名图
        if not cn_df.empty:
            plt.figure(figsize=(12, 8))
            colors = ['red' if x < 0 else 'green' for x in cn_df['score']]
            plt.barh(range(len(cn_df)), cn_df['score'][::-1], color=colors[::-1])
            plt.yticks(range(len(cn_df)), cn_df['name'][::-1])
            plt.xlabel('综合得分')
            plt.title(f'A股板块排名（完整）- {date_str}')
            plt.grid(axis='x', alpha=0.3)
            plt.tight_layout()
            plt.savefig(f"{output_dir}/cn_sectors_ranking_{date_str}.png", dpi=100, bbox_inches='tight')
            plt.close()
            print(f"  ✓ A股板块排名图")

        # 趋势分布饼图
        plt.figure(figsize=(10, 10))
        trend_counts = cn_df['trend'].value_counts()
        trend_labels = {
            'strong_up': '🔥 强势上涨',
            'upgrading': '📈 正在升级',
            'neutral': '➡️ 中性',
            'downgrading': '📉 正在降级',
            'weak_down': '💔 弱势下跌'
        }
        labels = [trend_labels.get(t, t) for t in trend_counts.index]
        plt.pie(trend_counts, labels=labels, autopct='%1.1f%%', startangle=90)
        plt.title(f'A股板块趋势分布 - {date_str}')
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig(f"{output_dir}/cn_trend_pie_{date_str}.png", dpi=100, bbox_inches='tight')
        plt.close()
        print(f"  ✓ A股趋势分布图")

        print(f"\n✓ 所有图表已保存到 {output_dir}/")

    def generate_report(self, us_rankings, cn_rankings):
        """生成监控报告"""
        date_str = datetime.now().strftime('%Y年%m月%d日')

        report = f"""# 板块与主题轮动监控报告 v3.0

**生成时间**: {date_str}
**数据来源**: Yahoo Finance (美股) + Tushare (A股)
**版本**: v3.0 升级版

---

## 🇺🇸 美股板块轮动排名

### 📊 Top 5 - 关注重点

"""

        # 美股Top 5（数据缺失时降级提示）
        if us_rankings is None or us_rankings.empty:
            report += "> ⚠️ **本次美股数据缺失**（Yahoo Finance 限流或网络异常），本报告仅包含A股部分。\n\n---\n\n## 🇨🇳 A股板块轮动排名\n\n### 📊 Top 5 - 关注重点\n\n"
        else:
            for idx, row in us_rankings.head(5).iterrows():
                emoji = {'strong_up': '🔥', 'upgrading': '📈', 'neutral': '➡️', 'downgrading': '📉', 'weak_down': '💔'}
                trend = row.get('trend', 'neutral')
                report += f"**{emoji[trend]} {row['rank']:.0f}. {row['name']}**\n\n"
                report += f"- 综合得分: {row['score']:+.2f}\n"
                report += f"- 20日涨幅: {row['20d_return']:+.2f}%\n" if pd.notna(row['20d_return']) else "- 20日涨幅: N/A\n"
                report += f"- 60日涨幅: {row['60d_return']:+.2f}%\n\n" if pd.notna(row['60d_return']) else "- 60日涨幅: N/A\n\n"

            # 美股完整排名表
            report += "### 📋 美股完整排名\n\n"
            report += "| 排名 | 板块 | 代码 | 20日涨幅 | 60日涨幅 | 得分 | 趋势 |\n"
            report += "|------|------|------|----------|----------|------|------|\n"

            for idx, row in us_rankings.iterrows():
                emoji = {'strong_up': '🔥', 'upgrading': '📈', 'neutral': '➡️', 'downgrading': '📉', 'weak_down': '💔'}
                trend = row.get('trend', 'neutral')
                return_20d = f"{row['20d_return']:+.2f}%" if pd.notna(row['20d_return']) else "N/A"
                return_60d = f"{row['60d_return']:+.2f}%" if pd.notna(row['60d_return']) else "N/A"
                report += f"| {row['rank']:.0f} | {row['name']} | {row['code']} | {return_20d} | {return_60d} | {row['score']:+.2f} | {emoji[trend]} |\n"

            report += "\n---\n\n## 🇨🇳 A股板块轮动排名\n\n### 📊 Top 5 - 关注重点\n\n"

        # A股Top 5（标题已由上方美股分支/降级分支输出）
        for idx, row in cn_rankings.head(5).iterrows():
            emoji = {'strong_up': '🔥', 'upgrading': '📈', 'neutral': '➡️', 'downgrading': '📉', 'weak_down': '💔'}
            trend = row.get('trend', 'neutral')
            report += f"**{emoji[trend]} {row['rank']:.0f}. {row['name']} ({row['code']})**\n\n"
            report += f"- 综合得分: {row['score']:+.2f}\n"
            report += f"- 20日涨幅: {row['20d_return']:+.2f}%\n" if pd.notna(row['20d_return']) else "- 20日涨幅: N/A\n"
            report += f"- 60日涨幅: {row['60d_return']:+.2f}%\n\n" if pd.notna(row['60d_return']) else "- 60日涨幅: N/A\n\n"

        # 完整排名表
        report += "### 📋 A股完整排名\n\n"
        report += "| 排名 | 板块 | 代码 | 20日涨幅 | 60日涨幅 | 得分 | 趋势 |\n"
        report += "|------|------|------|----------|----------|------|------|\n"

        for idx, row in cn_rankings.iterrows():
            emoji = {'strong_up': '🔥', 'upgrading': '📈', 'neutral': '➡️', 'downgrading': '📉', 'weak_down': '💔'}
            trend = row.get('trend', 'neutral')
            return_20d = f"{row['20d_return']:+.2f}%" if pd.notna(row['20d_return']) else "N/A"
            return_60d = f"{row['60d_return']:+.2f}%" if pd.notna(row['60d_return']) else "N/A"
            report += f"| {row['rank']:.0f} | {row['name']} | {row['code']} | {return_20d} | {return_60d} | {row['score']:+.2f} | {emoji[trend]} |\n"

        report += "\n---\n\n## 📊 可视化图表\n\n"
        chart_date = datetime.now().strftime('%Y%m%d')
        if us_rankings is not None and not us_rankings.empty:
            report += f"- 美股板块排名图: us_sectors_ranking_{chart_date}.png\n"
        report += f"- A股板块排名图: cn_sectors_ranking_{chart_date}.png\n"
        report += f"- A股趋势分布图: cn_trend_pie_{chart_date}.png\n"

        report += "\n---\n\n## 💡 使用建议\n\n"
        report += "- ✅ 在Top 5板块中寻找个股机会\n"
        report += "- 🔍 关注趋势为🔥强势上涨或📈正在升级的板块\n"
        report += "- ❌ 规避趋势为📉正在降级或💔弱势下跌的板块\n"
        report += "- 📊 结合图表直观感受板块强弱分布\n\n"

        report += "---\n\n**注**: 本报告基于历史数据生成，不构成投资建议。投资有风险，请谨慎决策。\n"

        return report

    def run_monitor(self, save_to='09-监控报告'):
        """运行完整监控流程"""
        print("=" * 60)
        print("板块与主题轮动监控系统 v3.0")
        print("=" * 60)
        print("\n📊 功能清单:")
        print("  ✓ 美股ETF监控")
        print("  ✓ A股ETF监控（使用Tushare）")
        print("  ✓ 历史对比功能")
        print("  ✓ 数据可视化（图表）")
        print()

        # 获取美股数据（失败时降级：跳过美股，仅生成A股报告，不中断流程）
        print("【1/4】获取美股数据...")
        us_data = self.get_yahoo_data(self.us_etfs.keys())
        us_rankings = None
        if us_data:
            try:
                us_returns = self.calculate_returns(us_data, days=[20, 60])
                us_returns = self.calculate_relative_strength(us_returns, self.us_benchmark)
                us_rankings = self.rank_and_identify_trend(us_returns, exclude_benchmark=self.us_benchmark)
            except Exception as e:
                print(f"⚠️ 美股数据处理失败: {e}")
                us_rankings = None
        if us_rankings is None or us_rankings.empty:
            print("⚠️ 美股数据不可用（可能被Yahoo限流/网络问题），本次降级为仅A股报告")

        # 获取A股数据
        print("\n【2/4】获取A股数据...")
        cn_data = self.get_tushare_data(self.cn_etfs, days=60)
        cn_returns = self.calculate_returns(cn_data, days=[20, 60])
        cn_returns = self.calculate_relative_strength(cn_returns, '510300')
        cn_rankings = self.rank_and_identify_trend(cn_returns, exclude_benchmark='510300')

        if cn_rankings is None or cn_rankings.empty:
            raise RuntimeError("A股数据获取失败（Tushare异常），无法生成报告，请检查网络/API额度")

        # 历史对比
        print("\n【3/4】历史对比...")
        self.compare_with_history(cn_rankings,
                                history_file=f'{save_to}/rankings_history.csv')

        # 生成图表
        print("\n【4/4】生成可视化图表...")
        charts_dir = f'{save_to}/charts'
        self.generate_charts(us_rankings, cn_rankings, charts_dir)

        # 生成报告
        print("\n生成报告...")
        report = self.generate_report(us_rankings, cn_rankings)

        # 保存报告
        filename = f"enhanced_report_v3_{datetime.now().strftime('%Y%m%d')}.md"
        filepath = f"{save_to}/{filename}"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n✓ 报告已保存到: {filepath}")
        print(f"✓ 图表已保存到: {charts_dir}/")
        print(f"✓ 历史数据已保存")

        print("\n" + "=" * 60)
        print("✅ 监控完成！")
        print("=" * 60)

        return us_rankings, cn_rankings, report


def main():
    """主函数"""
    monitor = EnhancedRotationMonitorV3()

    try:
        us_rankings, cn_rankings, report = monitor.run_monitor()

        print("\n📊 数据统计:")
        us_count = len(us_rankings) if us_rankings is not None else 0
        print(f"  美股板块: {us_count} 个" + ("" if us_count else " ⚠️本次缺失"))
        print(f"  A股板块: {len(cn_rankings)} 个")
        print(f"  生成图表: 3张")
        print(f"  报告页数: 完整报告")

    except Exception as e:
        print(f"\n✗ 错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
