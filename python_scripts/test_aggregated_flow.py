#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AggregatedFlowEdges生成テスト

既存のMunicipalityFlowEdges.csvを読み込み、
_generate_aggregated_flow_edges()ロジックをテストします。
"""

import pandas as pd
from pathlib import Path

def test_generate_aggregated_flow_edges():
    """AggregatedFlowEdges生成テスト"""

    # 入力ファイル
    input_file = Path("data/output_v2/phase6/MunicipalityFlowEdges.csv")
    output_file = Path("data/output_v2/phase6/AggregatedFlowEdges.csv")

    if not input_file.exists():
        print(f"[ERROR] ファイルが見つかりません: {input_file}")
        return False

    print(f"[INFO] 入力ファイル: {input_file}")

    # CSVを読み込み
    flow_edges = pd.read_csv(input_file, encoding='utf-8-sig')
    print(f"[OK] 読み込み成功: {len(flow_edges)}行")

    # カラムを確認
    print(f"\n[INFO] カラム一覧: {list(flow_edges.columns)}")

    # _generate_aggregated_flow_edges()ロジックを実行
    print("\n[PROCESSING] Origin→Destinationの組み合わせで集約中...")

    if flow_edges.empty:
        print("[WARNING] データが空です")
        return False

    # groupby対象カラムの欠損値を確認
    groupby_cols = ['origin', 'destination', 'origin_pref', 'origin_muni', 'destination_pref', 'destination_muni']
    has_null = flow_edges[groupby_cols].isnull().any(axis=1)
    null_rows_count = has_null.sum()

    if null_rows_count > 0:
        print(f"[INFO] groupby対象カラムに欠損値を含む行: {null_rows_count}件（除外されます）")

    # 欠損値を除外
    flow_edges_clean = flow_edges.dropna(subset=groupby_cols)
    print(f"[INFO] 欠損値除外後の行数: {len(flow_edges_clean)}行")

    # Origin→Destinationの組み合わせで集約
    agg = flow_edges_clean.groupby([
        'origin', 'destination',
        'origin_pref', 'origin_muni',
        'destination_pref', 'destination_muni'
    ]).agg({
        'applicant_id': 'count',  # フロー数
        'age': 'mean',            # 平均年齢
        'gender': lambda x: x.mode()[0] if len(x.mode()) > 0 else '不明'  # 最頻性別
    }).reset_index()

    # カラム名を変更
    agg.rename(columns={
        'applicant_id': 'flow_count',
        'age': 'avg_age',
        'gender': 'gender_mode'
    }, inplace=True)

    # flow_count降順でソート
    agg = agg.sort_values('flow_count', ascending=False)

    print(f"[OK] 集約完了: {len(agg)}行（{len(flow_edges_clean)}行 -> {len(agg)}行）")
    print(f"[INFO] 削減率: {(1 - len(agg) / len(flow_edges_clean)) * 100:.1f}%")

    # サンプルデータを表示
    print("\n[INFO] TOP 5 フロー:")
    print(agg.head(5).to_string(index=False))

    # データ整合性チェック
    print("\n[TEST] データ整合性チェック:")
    total_original = len(flow_edges_clean)
    total_aggregated = agg['flow_count'].sum()

    print(f"  元データ総行数（欠損値除外後）: {total_original}")
    print(f"  集約データ総flow_count: {total_aggregated}")

    if total_original == total_aggregated:
        print("  [OK] 総フロー数が一致しています")
    else:
        print(f"  [ERROR] 総フロー数が一致しません（差分: {abs(total_original - total_aggregated)}）")
        return False

    # 特定のフローの集約が正しいかチェック
    sample = agg.iloc[0]
    sample_edges = flow_edges_clean[
        (flow_edges_clean['origin'] == sample['origin']) &
        (flow_edges_clean['destination'] == sample['destination'])
    ]

    print(f"\n[TEST] サンプルフローの検証:")
    print(f"  Origin: {sample['origin']}")
    print(f"  Destination: {sample['destination']}")
    print(f"  集約flow_count: {sample['flow_count']}")
    print(f"  元データ行数: {len(sample_edges)}")
    print(f"  集約avg_age: {sample['avg_age']:.2f}")
    print(f"  元データ平均年齢: {sample_edges['age'].mean():.2f}")

    if len(sample_edges) == sample['flow_count']:
        print("  [OK] flow_countが一致しています")
    else:
        print("  [ERROR] flow_countが一致しません")
        return False

    if abs(sample_edges['age'].mean() - sample['avg_age']) < 0.01:
        print("  [OK] avg_ageが一致しています")
    else:
        print("  [ERROR] avg_ageが一致しません")
        return False

    # CSVに保存
    print(f"\n[SAVE] 保存中: {output_file}")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    agg.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"[OK] 保存完了: {output_file}")

    # ファイルサイズを表示
    file_size = output_file.stat().st_size
    print(f"[INFO] ファイルサイズ: {file_size:,} bytes ({file_size / 1024:.1f} KB)")

    return True

if __name__ == '__main__':
    print("=" * 60)
    print("AggregatedFlowEdges生成テスト")
    print("=" * 60)
    print()

    success = test_generate_aggregated_flow_edges()

    print()
    print("=" * 60)
    if success:
        print("[SUCCESS] テスト成功！")
    else:
        print("[FAILED] テスト失敗")
    print("=" * 60)
