import os
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Tushare API验证所有A股ETF代码和名称
确保100%准确性
"""

import tushare as ts
import pandas as pd
from datetime import datetime

# Tushare API Token
TS_TOKEN = os.environ.get('TUSHARE_TOKEN', '')

# 当前系统中所有A股ETF代码和名称
CURRENT_ETFS = {
    # 基准指数
    '510300': '沪深300',
    '510050': '上证50',
    '159915': '创业板指',
    '588000': '科创50',
    '510500': '中证500',

    # 科技/半导体
    '512480': '半导体',
    '512760': '半导体芯片',
    '588200': '芯片',
    '159995': '芯片ETF',
    '515000': '5G',
    '515980': '人工智能',
    '159819': 'AI应用',

    # 医药/医疗
    '512010': '医药卫生',
    '159938': '医疗器械',
    '159929': '医药',
    '512290': '生物医药',
    '512880': '保险',
    '515230': '证券保险',

    # 军工
    '512660': '军工',
    '512680': '军工ETF',
    '512690': '国防',

    # 周期/资源
    '512400': '有色金属',
    '515220': '煤炭',
    '516920': '钢铁',
    '516780': '化工',  # 已知错误：应该是稀土
    '159857': '石油',

    # 新能源
    '516160': '新能源',
    '516790': '光伏',  # 已知错误：应该是医疗ETF
    '159863': '风电',  # 已知错误：应该是光伏
    '159767': '储能',
    '515030': '新能源汽车',
    '159745': '电池',

    # 基建/汽车
    '516970': '基建',
    '516110': '汽车',
    '165520': '建材',

    # 消费
    '159928': '消费',
    '512930': '传媒',
    '159855': '消费电子',

    # 策略
    '512100': '中证1000',
    '515080': '红利ETF',
    '512890': '红利低波',
}

def verify_etfs_with_tushare():
    """使用Tushare API验证所有ETF"""

    print("=" * 80)
    print("A股ETF代码和名称全面核查")
    print("=" * 80)
    print(f"核查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据源: Tushare API (专业金融数据库)")
    print("=" * 80)
    print()

    # 初始化Tushare API
    ts.set_token(TS_TOKEN)
    pro = ts.pro_api()

    results = []
    errors = []
    corrections = []

    print("【开始逐个验证ETF】\n")

    for code, current_name in sorted(CURRENT_ETFS.items()):
        try:
            # 确定市场后缀
            if code.startswith('51') or code.startswith('56'):
                ts_code = f'{code}.SH'  # 上海市场
            elif code.startswith('15') or code.startswith('16'):
                ts_code = f'{code}.SZ'  # 深圳市场
            else:
                ts_code = code

            # 查询基金基本信息
            df = pro.fund_basic(ts_code=ts_code)

            if df is not None and len(df) > 0:
                official_name = df.iloc[0]['name']
                fund_type = df.iloc[0]['fund_type']
                list_date = df.iloc[0]['list_date']
                status = df.iloc[0]['status']

                # 对比当前名称和官方名称
                is_match = current_name.strip() == official_name.strip()

                result = {
                    '代码': code,
                    '当前名称': current_name,
                    '官方名称': official_name,
                    '状态': status,
                    '上市日期': list_date,
                    '是否匹配': '✅ 匹配' if is_match else '❌ 不匹配'
                }

                results.append(result)

                # 打印验证结果
                match_symbol = '✅' if is_match else '❌'
                print(f"{match_symbol} {code} | {current_name:15s} | {official_name}")

                if not is_match:
                    correction = {
                        '代码': code,
                        '错误名称': current_name,
                        '正确名称': official_name
                    }
                    corrections.append(correction)
                    print(f"   ⚠️  发现错误！当前名称'{current_name}'应该是'{official_name}'")

            else:
                # 没有查询到结果
                error = {
                    '代码': code,
                    '当前名称': current_name,
                    '问题': '未在Tushare中找到'
                }
                errors.append(error)
                print(f"❌ {code} | {current_name:15s} | 未找到")

        except Exception as e:
            error = {
                '代码': code,
                '当前名称': current_name,
                '问题': f'查询失败: {str(e)}'
            }
            errors.append(error)
            print(f"❌ {code} | {current_name:15s} | 查询失败: {str(e)}")

        print()

    # 生成报告
    print("=" * 80)
    print("【核查结果汇总】")
    print("=" * 80)
    print()

    # 1. 统计信息
    total = len(CURRENT_ETFS)
    matched = len([r for r in results if r['是否匹配'] == '✅ 匹配'])
    unmatched = len(corrections)
    error_count = len(errors)

    print(f"总计ETF: {total}个")
    print(f"✅ 名称正确: {matched}个")
    print(f"❌ 名称错误: {unmatched}个")
    print(f"⚠️  查询失败: {error_count}个")
    print()

    # 2. 错误详情
    if corrections:
        print("=" * 80)
        print("【发现的错误 - 需要修正】")
        print("=" * 80)
        print()

        corrections_df = pd.DataFrame(corrections)
        print(corrections_df.to_string(index=False))
        print()

        # 生成修正代码
        print("=" * 80)
        print("【修正代码】")
        print("=" * 80)
        print()
        print("将以下代码添加到 monitor_v3.py 的 self.cn_etfs 字典中：")
        print()

        for corr in corrections:
            code = corr['代码']
            correct_name = corr['正确名称']
            print(f"'{code}': ('{correct_name}', 'sector'),  # 修正")

    # 3. 保存完整报告
    results_df = pd.DataFrame(results)
    report_file = '/Users/cast/AI内容/AI对话整理内容/金融和交易/08-监控系统工具/09-监控报告/tushare_verification_report.csv'
    results_df.to_csv(report_file, index=False, encoding='utf-8-sig')

    print()
    print("=" * 80)
    print("核查完成！")
    print("=" * 80)
    print(f"完整报告已保存到: {report_file}")
    print()

    # 4. 最终结论
    if unmatched > 0 or error_count > 0:
        print("⚠️  警告：发现错误，需要立即修正！")
        print(f"   - 需要修正的ETF: {unmatched}个")
        print(f"   - 查询失败的ETF: {error_count}个")
        print()
        print("📋 下一步：")
        print("   1. 根据上述修正代码更新 monitor_v3.py")
        print("   2. 重新运行验证，确保100%正确")
        print("   3. 只有在验证100%通过后才运行监控系统")
    else:
        print("✅ 恭喜！所有ETF验证通过，名称100%准确！")
        print()
        print("📋 下一步：")
        print("   可以安全地运行监控系统了")

    print("=" * 80)

if __name__ == '__main__':
    verify_etfs_with_tushare()
