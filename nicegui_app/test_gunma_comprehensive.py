# -*- coding: utf-8 -*-
"""
群馬県30パターン包括テスト
5職種 × 6市区町村 = 30パターン
各パターンで以下を検証:
1. 基本統計（応募者数、平均年齢、資格保有数）
2. フローデータ（流入、流出、純流入）
3. 地元志向率・性別比率
4. 競合データ
5. 距離統計
6. 移動タイプ分布
"""

import os
import sys
import json
from datetime import datetime

# db_helperをインポート
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db_helper as db

# テスト対象
JOB_TYPES = ['介護職', '看護師', '保育士', '栄養士', '生活相談員']
MUNICIPALITIES = ['前橋市', '高崎市', '太田市', '桐生市', '沼田市', '富岡市']
PREFECTURE = '群馬県'

def test_pattern(job_type: str, municipality: str) -> dict:
    """1パターンのテストを実行"""
    result = {
        'job_type': job_type,
        'prefecture': PREFECTURE,
        'municipality': municipality,
        'timestamp': datetime.now().isoformat(),
        'tests': {},
        'errors': [],
        'warnings': []
    }

    # 職種を設定
    db.set_current_job_type(job_type)
    current_jt = db.get_current_job_type()
    if current_jt != job_type:
        result['errors'].append(f'職種設定失敗: 期待={job_type}, 実際={current_jt}')
        return result

    # 1. 基本統計テスト
    try:
        stats = db.get_municipality_stats(PREFECTURE, municipality)
        result['tests']['basic_stats'] = {
            'applicant_count': stats.get('applicant_count', 0),
            'avg_age': stats.get('avg_age', 0),
            'avg_qualifications': stats.get('avg_qualifications', 0),
            'male_count': stats.get('male_count', 0),
            'female_count': stats.get('female_count', 0),
        }
        # 検証: 応募者数が0より大きいか
        if stats.get('applicant_count', 0) == 0:
            result['warnings'].append('basic_stats: applicant_count=0')
    except Exception as e:
        result['errors'].append(f'basic_stats error: {str(e)}')

    # 2. フローデータテスト
    try:
        flow = db.get_talent_flow(prefecture=PREFECTURE, municipality=municipality)
        result['tests']['flow'] = {
            'inflow': flow.get('inflow', 0),
            'outflow': flow.get('outflow', 0),
            'net_flow': flow.get('net_flow', 0),
            'applicant_count': flow.get('applicant_count', 0),
        }
        # 検証: 流入・流出が整合性あるか
        if flow.get('inflow', 0) < 0 or flow.get('outflow', 0) < 0:
            result['errors'].append('flow: negative value exists')
    except Exception as e:
        result['errors'].append(f'flow error: {str(e)}')

    # 3. 競合データテスト
    try:
        competition = db.get_competition_overview(prefecture=PREFECTURE, municipality=municipality)
        if isinstance(competition, dict):
            result['tests']['competition'] = {
                'data_exists': True,
                'type': 'dict',
                'keys': list(competition.keys())[:5]
            }
        elif isinstance(competition, list):
            result['tests']['competition'] = {
                'data_exists': len(competition) > 0,
                'type': 'list',
                'count': len(competition)
            }
        else:
            result['tests']['competition'] = {
                'data_exists': False,
                'type': str(type(competition))
            }
    except Exception as e:
        result['errors'].append(f'competition error: {str(e)}')

    # 4. 距離統計テスト
    try:
        distance = db.get_distance_stats(prefecture=PREFECTURE, municipality=municipality)
        result['tests']['distance'] = {
            'mean': distance.get('mean', '-'),
            'median': distance.get('median', '-'),
            'min': distance.get('min', '-'),
            'max': distance.get('max', '-'),
        }
    except Exception as e:
        result['errors'].append(f'distance error: {str(e)}')

    # 5. 移動タイプ分布テスト
    try:
        mobility = db.get_mobility_type_distribution(prefecture=PREFECTURE, municipality=municipality)
        result['tests']['mobility'] = {
            'data_exists': len(mobility) > 0,
            'types': [m.get('mobility_type') for m in mobility] if mobility else []
        }
    except Exception as e:
        result['errors'].append(f'mobility error: {str(e)}')

    # 6. ペルソナデータテスト
    try:
        persona = db.get_persona_employment_breakdown(prefecture=PREFECTURE, municipality=municipality)
        result['tests']['persona'] = {
            'data_exists': len(persona) > 0,
            'count': len(persona)
        }
    except Exception as e:
        result['errors'].append(f'persona error: {str(e)}')

    # 7. 希少性分析テスト
    try:
        rarity = db.get_rarity_analysis(prefecture=PREFECTURE, municipality=municipality)
        result['tests']['rarity'] = {
            'data_exists': len(rarity) > 0,
            'count': len(rarity)
        }
    except Exception as e:
        result['errors'].append(f'rarity error: {str(e)}')

    return result


def compare_job_types(municipality: str) -> dict:
    """同一市区町村で職種間のデータが異なることを検証"""
    flows = {}
    for jt in JOB_TYPES:
        db.set_current_job_type(jt)
        flow = db.get_talent_flow(prefecture=PREFECTURE, municipality=municipality)
        flows[jt] = {
            'inflow': flow.get('inflow', 0),
            'outflow': flow.get('outflow', 0),
            'applicant_count': flow.get('applicant_count', 0),
        }

    # 全職種で同じ値になっていないかチェック
    inflows = [f['inflow'] for f in flows.values()]
    if len(set(inflows)) == 1 and inflows[0] != 0:
        return {
            'municipality': municipality,
            'status': 'SUSPICIOUS',
            'message': f'全職種で流入が同じ値: {inflows[0]}',
            'data': flows
        }

    return {
        'municipality': municipality,
        'status': 'OK',
        'message': '職種間でデータが正しく異なる',
        'data': flows
    }


def run_all_tests():
    """30パターン全テスト実行"""
    print("=" * 80)
    print("群馬県 30パターン包括テスト")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    all_results = []
    error_count = 0
    warning_count = 0

    # 30パターンテスト
    pattern_num = 0
    for municipality in MUNICIPALITIES:
        for job_type in JOB_TYPES:
            pattern_num += 1
            print(f"\n[{pattern_num:02d}/30] {job_type} × {municipality}", end=" ... ")

            result = test_pattern(job_type, municipality)
            all_results.append(result)

            if result['errors']:
                print(f"[ERROR] {len(result['errors'])}件")
                error_count += len(result['errors'])
                for err in result['errors']:
                    print(f"    -> {err}")
            elif result['warnings']:
                print(f"[WARN] {len(result['warnings'])}件")
                warning_count += len(result['warnings'])
            else:
                # データサマリー表示
                flow = result['tests'].get('flow', {})
                stats = result['tests'].get('basic_stats', {})
                print(f"[OK] applicant={stats.get('applicant_count', '-')}, "
                      f"inflow={flow.get('inflow', '-')}, "
                      f"outflow={flow.get('outflow', '-')}")

    # 職種間比較テスト
    print("\n" + "=" * 80)
    print("職種間データ比較テスト")
    print("=" * 80)

    comparison_results = []
    for municipality in MUNICIPALITIES:
        print(f"\n{municipality}:", end=" ")
        comp = compare_job_types(municipality)
        comparison_results.append(comp)

        if comp['status'] == 'SUSPICIOUS':
            print(f"[WARN] {comp['message']}")
            warning_count += 1
        else:
            # 各職種の流入値を表示
            data = comp['data']
            vals = [f"{jt}={data[jt]['inflow']}" for jt in JOB_TYPES]
            print(f"[OK] {', '.join(vals)}")

    # サマリー
    print("\n" + "=" * 80)
    print("テストサマリー")
    print("=" * 80)
    print(f"テストパターン数: 30")
    print(f"エラー数: {error_count}")
    print(f"警告数: {warning_count}")
    print(f"成功率: {(30 - error_count) / 30 * 100:.1f}%")

    # 詳細結果をJSON出力
    output = {
        'summary': {
            'total_patterns': 30,
            'errors': error_count,
            'warnings': warning_count,
            'success_rate': (30 - error_count) / 30 * 100
        },
        'pattern_results': all_results,
        'comparison_results': comparison_results
    }

    output_path = os.path.join(os.path.dirname(__file__), 'test_gunma_results.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n詳細結果: {output_path}")

    return output


if __name__ == '__main__':
    run_all_tests()
