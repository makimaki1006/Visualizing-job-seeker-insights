# -*- coding: utf-8 -*-
"""QUALIFICATION_DETAIL生成スクリプト

2種類の資格データを生成:
1. QUALIFICATION_DETAIL: 市区町村×個別資格（全資格表示・保有率付き）
2. QUALIFICATION_PERSONA: 市区町村×個別資格×年齢×性別でペルソナ分析用

用途:
- QUALIFICATION_DETAIL: 「この市区町村でどの資格を何人が持っているか」を全て表示
  （希少資格も含めて全資格を可視化、保有率も計算）
- QUALIFICATION_PERSONA: 「特定資格保持者の年齢×性別セグメント分布」を表示
  （例: 看護師資格を持つ人材が30代女性に何人いるか）
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

# 国家資格リスト（国家資格判定用）
NATIONAL_LICENSES = [
    '介護福祉士', '看護師', '准看護師', '理学療法士', '作業療法士',
    '言語聴覚士', '社会福祉士', '精神保健福祉士', '管理栄養士', '栄養士',
    '保健師', '助産師', '薬剤師', '歯科衛生士', '歯科技工士',
    '臨床検査技師', '診療放射線技師', '臨床工学技士', '義肢装具士',
    'あん摩マッサージ指圧師', 'はり師', 'きゅう師', '柔道整復師',
    '視能訓練士', '救急救命士'
]

def normalize_qualification_string(quals_str):
    """
    資格文字列の前処理（スクレイピングエラーの修正）
    - 「旧ヘルパー1級,基礎研修）」→「旧ヘルパー1級/基礎研修）」に修正
    - 括弧内のカンマをスラッシュに戻す
    """
    import re

    if not quals_str or pd.isna(quals_str):
        return quals_str

    result = str(quals_str)

    # パターン1: 「介護職員実務者研修（旧ヘルパー1級」の後に「,基礎研修）」が続くパターン
    # これは元データでスラッシュがカンマに変換された
    result = re.sub(
        r'介護職員実務者研修（旧ヘルパー1級,基礎研修）',
        '介護職員実務者研修（旧ヘルパー1級/基礎研修）',
        result
    )

    # パターン2: カンマなし連結の場合
    # 「介護職員実務者研修（旧ヘルパー1級」で終わって「基礎研修）」で始まる連結
    # → 「介護職員実務者研修（旧ヘルパー1級/基礎研修）」に修正
    result = re.sub(
        r'介護職員実務者研修（旧ヘルパー1級(?:/基礎研修）)?基礎研修）',
        '介護職員実務者研修（旧ヘルパー1級/基礎研修）',
        result
    )

    # パターン3: 単独で「基礎研修）」が存在する場合（ゴミデータ）は削除
    # カンマ区切りの場合
    result = re.sub(r',\s*基礎研修）\s*,', ',', result)  # 中間
    result = re.sub(r',\s*基礎研修）\s*$', '', result)   # 末尾
    result = re.sub(r'^\s*基礎研修）\s*,', '', result)   # 先頭

    return result


# 既知の資格名パターン（カンマなし連結データの分割用）
# 長い順にソート（部分一致を防ぐため）
KNOWN_QUALIFICATIONS = [
    # 長い名称から順に（部分一致を避けるため）
    '介護職員実務者研修（旧ヘルパー1級/基礎研修）',
    '介護職員初任者研修（旧ヘルパー2級）',
    '介護支援専門員（ケアマネジャー）',
    '主任介護支援専門員',
    '社会福祉主事任用資格',
    '福祉用具専門相談員',
    '医療事務資格（民間）',
    '診療放射線技師',
    'あん摩マッサージ指圧師',
    '精神保健福祉士',
    '臨床検査技師',
    '臨床工学技士',
    '言語聴覚士',
    '理学療法士',
    '作業療法士',
    '視能訓練士',
    '救急救命士',
    '歯科衛生士',
    '歯科技工士',
    '義肢装具士',
    '柔道整復師',
    '管理栄養士',
    '介護福祉士',
    '社会福祉士',
    '自動車運転免許',
    '看護師',
    '准看護師',
    '保健師',
    '助産師',
    '薬剤師',
    '栄養士',
    '調理師',
    'はり師',
    'きゅう師',
]


def split_concatenated_qualifications(quals_str):
    """
    カンマなしで連結された資格文字列を既知の資格名パターンで分割する
    例: '介護福祉士自動車運転免許' -> ['介護福祉士', '自動車運転免許']
    """
    if not quals_str:
        return []

    result = []
    remaining = quals_str

    while remaining:
        found = False
        for qual in KNOWN_QUALIFICATIONS:
            if remaining.startswith(qual):
                result.append(qual)
                remaining = remaining[len(qual):]
                found = True
                break

        if not found:
            # 既知の資格が見つからない場合、'その他'で始まるかチェック
            if remaining.startswith('その他'):
                # 括弧で囲まれた部分を含めて抽出
                import re
                match = re.match(r'その他（[^）]*）', remaining)
                if match:
                    result.append(match.group())
                    remaining = remaining[len(match.group()):]
                else:
                    # 括弧がない場合は残り全体をその他として扱う
                    result.append(remaining)
                    break
            else:
                # 未知のパターンは残り全体を1つの資格として扱う
                if remaining.strip():
                    result.append(remaining.strip())
                break

    return result


def extract_qualifications(quals_str):
    """
    資格文字列を個別資格リストに分割する
    1. まず前処理でスクレイピングエラーを修正
    2. カンマで分割
    3. カンマがない連結資格は既知パターンで分割
    """
    if not quals_str or pd.isna(quals_str):
        return []

    # 前処理: スクレイピングエラーを修正
    normalized_str = normalize_qualification_string(quals_str)
    if not normalized_str:
        return []

    result = []

    # カンマで分割
    for part in str(normalized_str).split(','):
        qual = part.strip()

        # 空文字やゴミデータをスキップ
        if not qual or len(qual) < 2:
            continue

        # 「取得予定」を除外
        if '取得予定' in qual:
            continue

        # カンマなし連結資格を検出して分割
        # 複数の既知資格が連結されているかチェック
        contains_multiple = False
        for known_qual in KNOWN_QUALIFICATIONS:
            if known_qual in qual and qual != known_qual:
                # 既知資格を含むが、完全一致ではない = 連結されている可能性
                contains_multiple = True
                break

        if contains_multiple:
            # 連結資格を分割
            split_quals = split_concatenated_qualifications(qual)
            for sq in split_quals:
                if sq and len(sq) >= 2 and '取得予定' not in sq:
                    result.append(sq)
        else:
            result.append(qual)

    return result


def is_national_license(qualification_name):
    """国家資格判定"""
    for nl in NATIONAL_LICENSES:
        if nl in qualification_name:
            return True
    return False


def generate_qualification_detail():
    """QUALIFICATION_DETAILデータ生成（2種類）"""
    print("\n" + "=" * 60)
    print("QUALIFICATION_DETAIL生成開始")
    print("=" * 60)

    # Phase1 Applicants読み込み
    applicants_path = Path('data/output_v2/phase1/Phase1_Applicants.csv')
    print(f"\n[LOAD] {applicants_path}")

    df = pd.read_csv(applicants_path, encoding='utf-8-sig')
    print(f"  [OK] {len(df)}行読み込み")

    # 市区町村ごとの総人数を計算（保有率の分母）
    municipality_totals = df.groupby(['residence_prefecture', 'residence_municipality']).size().reset_index(name='total_applicants')
    print(f"  [INFO] 市区町村数: {len(municipality_totals)}")

    # qualificationsがNaNでない行のみ抽出
    df_with_quals = df[df['qualifications'].notna()].copy()
    print(f"  [INFO] 資格データあり: {len(df_with_quals)}行")

    # 資格を展開（個別資格ごとに1行）
    # 元データは既にカンマ区切りなので、シンプルにカンマで分割するだけ
    qualification_rows = []

    for idx, row in df_with_quals.iterrows():
        # extract_qualifications()でカンマ分割＋クリーニング
        individual_quals = extract_qualifications(row['qualifications'])

        # 重複を除去（同じ人が同じ資格を複数回持っているケースを排除）
        seen_quals = set()
        for qual in individual_quals:
            if qual in seen_quals:
                continue
            seen_quals.add(qual)

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

    # 出力ディレクトリ
    output_dir = Path('data/output_v2/qualification_detail')
    output_dir.mkdir(parents=True, exist_ok=True)

    # ========================================
    # 1. QUALIFICATION_DETAIL（全資格表示・保有率付き）
    # ========================================
    # グループ化: 市区町村 × 個別資格
    grouped_simple = df_quals.groupby([
        'prefecture', 'municipality', 'qualification_name', 'is_national_license'
    ]).size().reset_index(name='count')

    # 市区町村の総人数をマージして保有率を計算
    grouped_simple = grouped_simple.merge(
        municipality_totals,
        left_on=['prefecture', 'municipality'],
        right_on=['residence_prefecture', 'residence_municipality'],
        how='left'
    )
    grouped_simple['retention_rate'] = (grouped_simple['count'] / grouped_simple['total_applicants'] * 100).round(2)
    grouped_simple['row_type'] = 'QUALIFICATION_DETAIL'

    result_simple = grouped_simple[[
        'row_type', 'prefecture', 'municipality', 'qualification_name',
        'is_national_license', 'count', 'total_applicants', 'retention_rate'
    ]]

    output_file_simple = output_dir / 'QualificationDetail.csv'
    result_simple.to_csv(output_file_simple, index=False, encoding='utf-8-sig')

    print(f"\n[SAVE] {output_file_simple}")
    print(f"  [OK] {len(result_simple)}行保存（全資格・保有率付き）")

    # ========================================
    # 2. QUALIFICATION_PERSONA（詳細版: ペルソナ分析用）
    # ========================================
    # グループ化: 市区町村 × 資格 × 年齢 × 性別
    grouped_persona = df_quals.groupby([
        'prefecture', 'municipality', 'qualification_name', 'is_national_license',
        'age_group', 'gender'
    ]).size().reset_index(name='count')

    grouped_persona['row_type'] = 'QUALIFICATION_PERSONA'

    result_persona = grouped_persona[[
        'row_type', 'prefecture', 'municipality', 'qualification_name',
        'is_national_license', 'age_group', 'gender', 'count'
    ]]

    output_file_persona = output_dir / 'QualificationPersona.csv'
    result_persona.to_csv(output_file_persona, index=False, encoding='utf-8-sig')

    print(f"\n[SAVE] {output_file_persona}")
    print(f"  [OK] {len(result_persona)}行保存（ペルソナ分析用詳細版）")

    # ========================================
    # 統計情報
    # ========================================
    print("\n" + "=" * 60)
    print("統計情報")
    print("=" * 60)
    print(f"QUALIFICATION_DETAIL（全資格・保有率付き）: {len(result_simple)}行")
    print(f"QUALIFICATION_PERSONA（ペルソナ用）: {len(result_persona)}行")
    print(f"ユニーク資格数: {result_simple['qualification_name'].nunique()}")

    national_count = result_simple[result_simple['is_national_license']]['count'].sum()
    total_count = result_simple['count'].sum()
    print(f"国家資格保有者延べ数: {national_count:,} / {total_count:,} ({national_count/total_count*100:.1f}%)")

    print("\n資格TOP10（全体）:")
    top_quals = result_simple.groupby('qualification_name')['count'].sum().sort_values(ascending=False).head(10)
    for i, (qual, count) in enumerate(top_quals.items(), 1):
        is_national = is_national_license(qual)
        mark = "[国]" if is_national else "    "
        print(f"  {i:2d}. {mark} {qual:50s}: {count:,}人")

    # サンプル: 伊勢崎市の資格保有状況
    print("\n伊勢崎市の資格保有状況（サンプル）:")
    isesaki_data = result_simple[result_simple['municipality'].str.contains('伊勢崎', na=False)]
    if len(isesaki_data) > 0:
        print(f"  総応募者数: {isesaki_data['total_applicants'].iloc[0]:,}人")
        print(f"  ユニーク資格数: {isesaki_data['qualification_name'].nunique()}")
        isesaki_top = isesaki_data.sort_values('count', ascending=False).head(10)
        for _, row in isesaki_top.iterrows():
            mark = "[国]" if row['is_national_license'] else "    "
            print(f"    {mark} {row['qualification_name'][:35]:35s}: {int(row['count']):5}人 ({row['retention_rate']:.1f}%)")

        # 希少資格（1-5人）もサンプル表示
        rare_quals = isesaki_data[(isesaki_data['count'] >= 1) & (isesaki_data['count'] <= 5)].sort_values('count')
        if len(rare_quals) > 0:
            print(f"\n  希少資格（1-5人）: {len(rare_quals)}種類")
            for _, row in rare_quals.head(5).iterrows():
                mark = "[国]" if row['is_national_license'] else "    "
                print(f"    {mark} {row['qualification_name'][:35]:35s}: {int(row['count']):5}人 ({row['retention_rate']:.1f}%)")

    # サンプル: 特定資格の年齢×性別分布
    print("\n看護師資格保持者の年齢×性別分布（サンプル）:")
    nurse_data = result_persona[result_persona['qualification_name'] == '看護師']
    if len(nurse_data) > 0:
        nurse_pivot = nurse_data.groupby(['age_group', 'gender'])['count'].sum().unstack(fill_value=0)
        print(nurse_pivot)

    print("\n" + "=" * 60)
    print("[OK] QUALIFICATION_DETAIL生成完了（2種類）")
    print("=" * 60)

    return result_simple, result_persona


if __name__ == '__main__':
    result_simple, result_persona = generate_qualification_detail()
