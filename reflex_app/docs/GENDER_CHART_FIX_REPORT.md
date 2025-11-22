# 性別グラフ修正レポート（2025年11月21日）

## 問題の概要

ユーザーから以下の2つの問題が報告されました：

1. **性別構成グラフが地域内訳を表示**していた（「前橋市、高崎市...」という市区町村別リスト）
2. **色盲対応の色使いができていない**

## 根本原因

### 問題1: 性別グラフの地域内訳表示

**ファイル**: `mapcomplete_dashboard/mapcomplete_dashboard.py`
**メソッド**: `overview_gender_data` (line 872-917)

**原因**:
- メソッド内に**2つのロジック**が存在していた：
  1. **Lines 889-904**: 市区町村ごとの `outflow` データをTop10表示（誤ったロジック）
  2. **Lines 906-915**: 男性・女性の合計を表示（正しいロジック）
- 最初のロジックが先に実行され、`outflow` カラムが存在する場合に市区町村別の内訳を返していた

**表示されていたデータ**:
```
- 前橋市: 1,773人
- 高崎市: 1,665人
- 伊勢崎市: 1,098人
... (Top 10市区町村)
```

**期待されるデータ**:
```
- 男性: 2,742人
- 女性: 6,670人
```

### 問題2: 色盲非対応パレット

**ファイル**: `mapcomplete_dashboard/mapcomplete_dashboard.py`
**メソッド**: `competition_gender_data` (line 2970-2997)

**原因**:
- `COLOR_PALETTE[5]` を女性用に使用していた
- `COLOR_PALETTE[5]` = '#D55E00' (朱色) は色盲対応だが、統一性がなかった
- コメントに「ピンク」と書かれていたが、実際には朱色が適用されていた

## 修正内容

### 修正1: `overview_gender_data` の市区町村groupbyロジック削除

**変更前** (lines 888-917):
```python
# 自治体で集約（重複カテゴリ解消）
if 'municipality' in filtered.columns and 'outflow' in filtered.columns:
    try:
        grouped = (
            filtered.groupby('municipality')['outflow']
            .sum()
            .reset_index()
            .sort_values('outflow', ascending=False)
            .head(10)
        )
        result = [
            {"name": str(r['municipality']), "value": int(r['outflow']) if pd.notna(r['outflow']) else 0}
            for _, r in grouped.iterrows()
        ]
        return result
    except Exception:
        pass

# SUMMARYからmale_count, female_countを取得
summary_rows = filtered[filtered['row_type'] == 'SUMMARY']
if not summary_rows.empty and 'male_count' in summary_rows.columns and 'female_count' in summary_rows.columns:
    male = int(summary_rows['male_count'].sum())
    female = int(summary_rows['female_count'].sum())
    return [
        {"name": "男性", "value": male, "fill": COLOR_PALETTE[0]},
        {"name": "女性", "value": female, "fill": COLOR_PALETTE[1]}
    ]
```

**変更後** (lines 889-901):
```python
# SUMMARYからmale_count, female_countを集計
summary_rows = filtered[filtered['row_type'] == 'SUMMARY']
if not summary_rows.empty and 'male_count' in summary_rows.columns and 'female_count' in summary_rows.columns:
    male = int(summary_rows['male_count'].sum())
    female = int(summary_rows['female_count'].sum())

    # 色盲対応パレット使用
    return [
        {"name": "男性", "value": male, "fill": COLOR_PALETTE[0]},  # 青
        {"name": "女性", "value": female, "fill": COLOR_PALETTE[1]}  # オレンジ
    ]

return []
```

### 修正2: `competition_gender_data` の色盲対応パレット統一

**変更前** (lines 2993-2997):
```python
# GAS COLOR配列を使用（性別2つ）
return [
    {"name": "女性", "value": int(female_count), "fill": COLOR_PALETTE[5]},  # ピンク
    {"name": "男性", "value": int(male_count), "fill": COLOR_PALETTE[0]}   # 青
]
```

**変更後** (lines 2993-2997):
```python
# 色盲対応パレット使用（overview_gender_dataと統一）
return [
    {"name": "男性", "value": int(male_count), "fill": COLOR_PALETTE[0]},   # 青
    {"name": "女性", "value": int(female_count), "fill": COLOR_PALETTE[1]}  # オレンジ
]
```

## 色盲対応パレット（Wong's Palette）

既に使用されていたパレット（line 51）:

```python
COLOR_PALETTE = [
    '#0072B2',  # 0: 青（男性）
    '#E69F00',  # 1: オレンジ（女性）
    '#CC79A7',  # 2: ピンク
    '#009E73',  # 3: 緑
    '#F0E442',  # 4: 黄
    '#D55E00',  # 5: 朱色
    '#56B4E9'   # 6: 水色
]
```

このパレットは**Wong's Color Blind Safe Palette**に基づいており、以下の色覚異常に対応：
- **Deuteranopia（緑色盲）**: 最も一般的（男性の約5%）
- **Protanopia（赤色盲）**: 男性の約1%
- **Tritanopia（青色盲）**: 非常に稀

## 検証結果

### テストスクリプト実行結果

**ファイル**: `test_gender_fix.py`

```
=== 性別グラフ修正検証 ===

選択都道府県: 群馬県
SUMMARYデータ件数: 36

=== 修正後の出力（期待値） ===
データポイント数: 2
  - 男性: 2,742人 (色: #0072B2)
  - 女性: 6,670人 (色: #E69F00)

✅ 結果: シンプルな男女2項目のみ表示
   - 市区町村別内訳は表示されない
   - 色盲対応パレット使用（青・オレンジ）
```

### Reflexサーバー自動リロード確認

```
WARNING: WatchFiles detected changes in 'mapcomplete_dashboard\mapcomplete_dashboard.py'. Reloading...
App running at: http://localhost:3000/
Backend running at: http://0.0.0.0:8000
```

修正が正常に反映されました。

## 影響範囲

### 修正されたグラフ

1. **概要パネル: 性別構成ドーナツチャート**
   - メソッド: `overview_gender_data`
   - コンポーネント: `overview_gender_chart` (line 3899)
   - 修正内容: 市区町村別内訳 → 男女2項目のみ

2. **競合パネル: 性別分布ドーナツチャート**
   - メソッド: `competition_gender_data`
   - コンポーネント: `competition_gender_chart` (line 4871)
   - 修正内容: 色統一（朱色 → オレンジ）、順序統一（女性→男性 → 男性→女性）

### 変更されていないグラフ

- その他の全グラフは既に `COLOR_PALETTE` を使用しており、色盲対応済み

## 今後の推奨事項

1. **全グラフの色盲対応監査**
   - すべてのグラフで `COLOR_PALETTE` の使用を確認
   - ハードコードされた色（例: '#ec4899'）がないか確認

2. **E2Eテストの追加**
   - 性別グラフのデータ構造を検証するテスト
   - 色盲対応パレットの使用を検証するテスト

3. **ドキュメント化**
   - 色盲対応ガイドラインの作成
   - グラフごとの色使いルールの明文化

## 参考資料

- **Wong's Color Blind Safe Palette**: https://www.nature.com/articles/nmeth.1618
- **WCAG 2.1 色のコントラスト**: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html
- **Color Blindness Simulator**: https://www.color-blindness.com/coblis-color-blindness-simulator/
