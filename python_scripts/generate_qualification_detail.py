# -*- coding: utf-8 -*-
"""QUALIFICATION_DETAIL生成スクリプト

資格×年齢×性別×就業状況のクロス集計を生成します。
"""
import pandas as pd
import sys
import io
from pathlib import Path

# Windows環境での絵文字出力対応
try:
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
except (ValueError, AttributeError):
    # stdout already configured or not available
    pass

# 国家資格リスト（validate_source_data.pyから）
NATIONAL_LICENSES = [
    '介護福祉士', '看護師', '准看護師', '理学療法士', '作業療法士',
    '言語聴覚士', '社会福祉士', '精神保健福祉士', '管理栄養士', '栄養士',
    '保健師', '助産師', '薬剤師', '歯科衛生士', '歯科技工士',
    '臨床検査技師', '診療放射線技師', '臨床工学技士', '義肢装具士',
    'あん摩マッサージ指圧師', 'はり師', 'きゅう師', '柔道整復師',
    '視能訓練士', '救急救命士'
]


def is_national_license(qualification_name):
    """国家資格判定"""
    for nl in NATIONAL_LICENSES:
        if nl in qualification_name:
            return True
    return False


def generate_qualification_detail():
    """QUALIFICATION_DETAILデータ生成"""
    print("\n" + "=" * 60)
    print("QUALIFICATION_DETAIL生成開始")
    print("=" * 60)

    # Phase1 Applicants読み込み
    applicants_path = Path('data/output_v2/phase1/Phase1_Applicants.csv')
    print(f"\n[LOAD] {applicants_path}")

    df = pd.read_csv(applicants_path, encoding='utf-8-sig')
    print(f"  [OK] {len(df)}行読み込み")

    # qualificationsがNaNでない行のみ抽出
    df_with_quals = df[df['qualifications'].notna()].copy()
    print(f"  [INFO] 資格データあり: {len(df_with_quals)}行")

    # 資格を展開
    qualification_rows = []

    for idx, row in df_with_quals.iterrows():
        quals_str = str(row['qualifications'])

        # カンマ区切りで分割
        qualifications = [q.strip() for q in quals_str.split(',') if q.strip()]

        for qual in qualifications:
            # 「取得予定」を除外
            if '取得予定' in qual:
                continue

            qualification_rows.append({
                'prefecture': row['residence_prefecture'],
                'municipality': row['residence_municipality'],
                'qualification_name': qual,
                'is_national_license': is_national_license(qual),
                'age_group': row['age_group'],
                'gender': row['gender'],
                'employment_status': row['employment_status']
            })

    print(f"  [INFO] 資格展開: {len(qualification_rows)}件")

    # DataFrameに変換
    df_quals = pd.DataFrame(qualification_rows)

    # グループ化してカウント
    grouped = df_quals.groupby([
        'prefecture', 'municipality', 'qualification_name',
        'is_national_license', 'age_group', 'gender', 'employment_status'
    ]).size().reset_index(name='count')

    print(f"  [INFO] グループ化後: {len(grouped)}行")

    # row_type追加
    grouped['row_type'] = 'QUALIFICATION_DETAIL'

    # カラム順序調整
    result = grouped[[
        'row_type', 'prefecture', 'municipality', 'qualification_name',
        'is_national_license', 'age_group', 'gender', 'employment_status', 'count'
    ]]

    # 保存
    output_dir = Path('data/output_v2/qualification_detail')
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / 'QualificationDetail.csv'
    result.to_csv(output_file, index=False, encoding='utf-8-sig')

    print(f"\n[SAVE] {output_file}")
    print(f"  [OK] {len(result)}行保存")

    # 統計情報
    print("\n" + "=" * 60)
    print("統計情報")
    print("=" * 60)
    print(f"総行数: {len(result)}")
    print(f"ユニーク資格数: {result['qualification_name'].nunique()}")
    print(f"国家資格比率: {result[result['is_national_license']]['count'].sum() / result['count'].sum() * 100:.1f}%")

    print("\n資格TOP10:")
    top_quals = result.groupby('qualification_name')['count'].sum().sort_values(ascending=False).head(10)
    for i, (qual, count) in enumerate(top_quals.items(), 1):
        is_national = is_national_license(qual)
        mark = "🏅" if is_national else "  "
        print(f"  {i:2d}. {mark} {qual:50s}: {count:,}件")

    print("\n" + "=" * 60)
    print("✅ QUALIFICATION_DETAIL生成完了")
    print("=" * 60)

    return result


if __name__ == '__main__':
    result = generate_qualification_detail()
