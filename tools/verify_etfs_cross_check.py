import os
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合验证A股ETF代码和名称
使用Tushare + AKShare + 实时价格数据交叉验证
"""

import tushare as ts
import akshare as ak
import pandas as pd
from datetime import datetime
import time

# Tushare API Token
TS_TOKEN = os.environ.get('TUSHARE_TOKEN', '')

# 需要验证的ETF代码列表
ETF_CODES = [
    # 用户指出的错误代码（优先验证）
    ('516780', '化工'),  # 应该是稀土
    ('159863', '风电'),  # 应该是光伏
    ('516790', '光伏'),  # 应该是医疗ETF

    # 宽基指数
    ('510300', '沪深300'),
    ('510050', '上证50'),
    ('159915', '创业板指'),
    ('588000', '科创50'),
    ('510500', '中证500'),

    # 科技/半导体
    ('512480', '半导体'),
    ('512760', '半导体芯片'),
    ('588200', '芯片'),
    ('159995', '芯片ETF'),
    ('515000', '5G'),
    ('515980', '人工智能'),
    ('159819', 'AI应用'),

    # 医药/医疗
    ('512010', '医药卫生'),
    ('159938', '医疗器械'),
    ('159929', '医药'),
    ('512290', '生物医药'),
    ('512880', '保险'),
    ('515230', '证券保险'),

    # 军工
    ('512660', '军工'),
    ('512680', '军工ETF'),
    ('512690', '国防'),

    # 周期/资源
    ('512400', '有色金属'),
    ('515220', '煤炭'),
    ('516920', '钢铁'),
    ('159857', '石油'),
    ('165520', '建材'),

    # 新能源
    ('516160', '新能源'),
    ('159767', '储能'),
    ('515030', '新能源汽车'),
    ('159745', '电池'),

    # 基建/汽车
    ('516970', '基建'),
    ('516110', '汽车'),

    # 消费
    ('159928', '消费'),
    ('512930', '传媒'),
    ('159855', '消费电子'),

    # 策略
    ('512100', '中证1000'),
    ('515080', '红利ETF'),
    ('512890', '红利低波'),
]

def get_akshare_fund_name(code):
    """使用AKShare获取基金名称"""
    try:
        # 尝试使用 fund_etf_fund_daily_em 获取ETF信息
        df = ak.fund_etf_fund_daily_em(symbol=code)
        if df is not None and len(df) > 0:
            # 返回第一行的名称
            return df.iloc[0]['名称'].strip()
    except Exception as e:
        pass

    try:
        # 尝试使用 fund_etf_category_sina
        df = ak.fund_etf_category_sina(symbol=code)
        if df is not None and len(df) > 0:
            return df.iloc[0]['名称'].strip()
    except Exception as e:
        pass

    return None

def get_tushare_fund_name(pro, code):
    """使用Tushare获取基金名称"""
    try:
        # 确定市场后缀
        if code.startswith('51') or code.startswith('56'):
            ts_code = f'{code}.SH'
        elif code.startswith('15') or code.startswith('16'):
            ts_code = f'{code}.SZ'
        else:
            ts_code = code

        df = pro.fund_basic(ts_code=ts_code)
        if df is not None and len(df) > 0:
            return df.iloc[0]['name'].strip()
    except Exception as e:
        pass

    return None

def verify_with_real_time_price(code):
    """使用实时价格验证ETF代码是否有效"""
    try:
        # 尝试获取实时数据
        df = ak.fund_etf_fund_daily_em(symbol=code)
        if df is not None and len(df) > 0:
            latest_price = df.iloc[0]['最新价']
            return True, latest_price
    except Exception as e:
        pass

    return False, None

def cross_verify_etfs():
    """交叉验证所有ETF"""

    print("=" * 100)
    print("A股ETF代码和名称交叉验证")
    print("=" * 100)
    print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据源: Tushare API + AKShare + 实时价格")
    print("=" * 100)
    print()

    # 初始化Tushare
    ts.set_token(TS_TOKEN)
    pro = ts.pro_api()

    results = []
    serious_errors = []

    print("【开始交叉验证】\n")

    for code, current_name in ETF_CODES:
        print(f"正在验证: {code} ({current_name})")

        # 获取Tushare名称
        ts_name = get_tushare_fund_name(pro, code)

        # 获取AKShare名称
        ak_name = get_akshare_fund_name(code)

        # 验证代码有效性
        is_valid, price = verify_with_real_time_price(code)

        # 判断是否匹配
        ts_match = ts_name == current_name if ts_name else False
        ak_match = ak_name == current_name if ak_name else False

        # 打印结果
        print(f"  Tushare: {ts_name if ts_name else '未获取'} {'✅' if ts_match else '❌'}")
        print(f"  AKShare: {ak_name if ak_name else '未获取'} {'✅' if ak_match else '❌'}")
        print(f"  实时价格: {'¥' + str(price) if price else '未获取'} {'✅' if is_valid else '❌'}")

        # 检查是否有严重不一致
        if ts_name and ak_name and ts_name != ak_name:
            print(f"  ⚠️  警告: Tushare和AKShare名称不一致！")

        # 判断是否需要修正
        needs_fix = False
        correct_name = current_name

        # 如果Tushare和AKShare都返回了相同的名称，且与当前名称不同
        if ts_name and ak_name and ts_name == ak_name and ts_name != current_name:
            needs_fix = True
            correct_name = ts_name
            print(f"  🔴 需要修正: '{current_name}' -> '{correct_name}'")

            # 检查是否是用户指出的错误
            if code in ['516780', '159863', '516790']:
                serious_errors.append({
                    '代码': code,
                    '错误名称': current_name,
                    '正确名称': correct_name,
                    '优先级': '🔴 严重（用户已指出）'
                })
            else:
                serious_errors.append({
                    '代码': code,
                    '错误名称': current_name,
                    '正确名称': correct_name,
                    '优先级': '⚠️  需核实'
                })

        # 保存结果
        result = {
            '代码': code,
            '当前名称': current_name,
            'Tushare名称': ts_name if ts_name else '未获取',
            'AKShare名称': ak_name if ak_name else '未获取',
            '实时价格': f"¥{price}" if price else '未获取',
            '代码有效': '✅' if is_valid else '❌',
            '需要修正': '是' if needs_fix else '否'
        }
        results.append(result)

        print()
        time.sleep(0.5)  # 避免API频率限制

    # 生成报告
    print("=" * 100)
    print("【验证结果汇总】")
    print("=" * 100)
    print()

    results_df = pd.DataFrame(results)

    # 统计
    total = len(results)
    valid_codes = len([r for r in results if r['代码有效'] == '✅'])
    needs_fix_count = len([r for r in results if r['需要修正'] == '是'])

    print(f"总计ETF: {total}个")
    print(f"✅ 代码有效: {valid_codes}个")
    print(f"❌ 需要修正: {needs_fix_count}个")
    print()

    # 显示需要修正的ETF
    if serious_errors:
        print("=" * 100)
        print("【需要修正的ETF】")
        print("=" * 100)
        print()

        errors_df = pd.DataFrame(serious_errors)
        print(errors_df.to_string(index=False))
        print()

        # 生成修正建议
        print("=" * 100)
        print("【修正建议代码】")
        print("=" * 100)
        print()

        for err in serious_errors:
            code = err['代码']
            correct_name = err['正确名称']
            priority = err['优先级']
            print(f"# {priority}")
            print(f"'{code}': ('{correct_name}', 'sector'),  # 修正: 原'{err['错误名称']}'")
            print()

    # 保存详细报告
    report_file = '/Users/cast/AI内容/AI对话整理内容/金融和交易/08-监控系统工具/09-监控报告/cross_verification_report.csv'
    results_df.to_csv(report_file, index=False, encoding='utf-8-sig')

    print("=" * 100)
    print("交叉验证完成！")
    print("=" * 100)
    print(f"详细报告已保存到: {report_file}")

if __name__ == '__main__':
    cross_verify_etfs()
