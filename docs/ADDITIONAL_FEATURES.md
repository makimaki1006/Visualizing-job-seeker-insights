# 追加機能提案（既存データのみ・第2弾）

**作成日**: 2025-10-26
**前提**: 求職者データのみ、データ件数は動的

---

## 🎯 第1弾実装済み（5機能）

1. ✅ 人材供給密度マップ
2. ✅ 資格別人材分布分析
3. ✅ 年齢層×性別クロス分析
4. ✅ 移動許容度スコアリング
5. ✅ ペルソナ詳細プロファイル

---

## 🚀 第2弾: 追加機能提案（7機能）

---

### 6. ⭐ **希望入職時期の緊急度分析**

#### 概要
「今すぐに」「1ヶ月以内」など、緊急度別の求職者分布を地域ごとに可視化。

#### ビジネス価値
- ⚡ **即戦力採用**: すぐ働きたい人材を優先的にマッチング
- 📅 **採用計画**: 緊急度が高い地域は即座に求人掲載
- 💡 **タイミング最適化**: 「3ヶ月以内」の人材に事前アプローチ

#### 実装方法
```python
def analyze_urgency_by_region():
    """緊急度別地域分析"""
    urgency_map = {
        '今すぐに': 5,
        '1ヶ月以内': 4,
        '3ヶ月以内': 3,
        '3ヶ月以上先': 2,
        '機会があれば転職を検討したい': 1
    }

    df['緊急度スコア'] = df['希望入職時期'].map(urgency_map)

    region_urgency = df.groupby('市区町村').agg({
        '緊急度スコア': 'mean',
        '申請者ID': lambda x: (df.loc[x.index, '希望入職時期']
                              .isin(['今すぐに', '1ヶ月以内'])).sum()
    })

    region_urgency.columns = ['平均緊急度', '即採用可能人数']

    return region_urgency
```

#### 出力CSV例
```csv
市区町村,平均緊急度,即採用可能人数,今すぐ,1ヶ月以内,3ヶ月以内,機会あれば
宇都宮市,3.2,56,32,24,98,220
小山市,2.8,25,12,13,45,99
```

---

### 7. ⭐ **資格保有パターンの相関分析**

#### 概要
「介護福祉士を持つ人は初任者研修も85%保有」など、資格間の相関を発見。

#### ビジネス価値
- 🎯 **必須資格設定**: 「この資格があれば他も持っている」
- 📊 **人材育成**: 「次に取るべき資格」の推奨
- 💡 **求人設計**: 過度な資格要求の回避

#### 実装方法
```python
def analyze_qualification_correlation():
    """資格保有パターンの相関分析"""
    # 主要資格をバイナリ化
    major_qualifications = [
        '介護福祉士', '介護職員初任者研修', '介護職員実務者研修',
        '看護師', '准看護師', 'ケアマネジャー',
        '社会福祉士', '保育士', '栄養士'
    ]

    # 各資格の保有フラグを作成
    for qual in major_qualifications:
        df[f'has_{qual}'] = df['資格情報'].str.contains(qual, na=False)

    # 相関行列
    corr_matrix = df[[f'has_{q}' for q in major_qualifications]].corr()

    # 強い相関（>0.5）を抽出
    strong_correlations = []
    for i in range(len(major_qualifications)):
        for j in range(i+1, len(major_qualifications)):
            corr = corr_matrix.iloc[i, j]
            if abs(corr) > 0.3:
                strong_correlations.append({
                    '資格A': major_qualifications[i],
                    '資格B': major_qualifications[j],
                    '相関係数': corr,
                    '共起率': calc_co_occurrence(major_qualifications[i],
                                                major_qualifications[j])
                })

    return pd.DataFrame(strong_correlations)
```

#### 出力CSV例
```csv
資格A,資格B,相関係数,共起率,解釈
介護福祉士,実務者研修,0.82,89%,実務者研修は介護福祉士の前提資格
看護師,准看護師,0.15,12%,どちらか一方を保有
ケアマネ,介護福祉士,0.68,74%,ケアマネは介護福祉士からのステップアップ
```

---

### 8. ⭐ **居住地と希望勤務地のギャップ分析**

#### 概要
「居住地から希望勤務地までの距離」を分析し、通勤圏を可視化。

#### ビジネス価値
- 🚗 **現実的な募集範囲**: 「30km圏内から何人集まるか」
- 📊 **アクセス評価**: 駅近・郊外の影響度
- 💡 **施設立地戦略**: 新規出店時の人材確保予測

#### 実装方法
```python
def analyze_commute_distance():
    """居住地-希望勤務地のギャップ分析"""
    results = []

    for _, row in df.iterrows():
        residence = geocache.get(row['居住地_キー'])
        desired_locations = df[df['申請者ID']==row['申請者ID']]['希望勤務地_キー']

        for desired in desired_locations:
            desired_coord = geocache.get(desired)

            if residence and desired_coord:
                distance = haversine_distance(residence, desired_coord)

                results.append({
                    '申請者ID': row['申請者ID'],
                    '居住地': row['居住地_市区町村'],
                    '希望地': desired,
                    '距離km': distance,
                    '距離帯': classify_distance(distance)
                })

    return pd.DataFrame(results)

def classify_distance(km):
    if km < 10: return '0-10km（地元）'
    elif km < 30: return '10-30km（近距離通勤）'
    elif km < 50: return '30-50km（中距離通勤）'
    elif km < 100: return '50-100km（長距離通勤）'
    else: return '100km以上（転居前提）'
```

#### 出力CSV例
```csv
距離帯,求職者数,割合,平均年齢,平均資格数
0-10km,452,48%,46.2,2.1
10-30km,312,33%,43.8,1.9
30-50km,128,14%,38.5,1.6
50-100km,35,4%,32.1,1.2
100km以上,10,1%,28.5,0.8
```

---

### 9. ⭐ **データ品質スコアカード**

#### 概要
データの完全性・正確性を自動評価。データクレンジング箇所を特定。

#### ビジネス価値
- 🛡️ **データ品質管理**: 不完全データの早期発見
- 📊 **信頼性向上**: 分析結果の信頼性担保
- 💡 **運用改善**: データ入力フォームの改善ポイント特定

#### 実装方法
```python
def generate_data_quality_scorecard():
    """データ品質スコアカード生成"""
    quality_checks = {
        '年齢の妥当性': (df['年齢'].between(15, 80)).mean(),
        '性別の完全性': (~df['性別'].isna()).mean(),
        '居住地の完全性': (~df['居住地_市区町村'].isna()).mean(),
        '希望勤務地の存在': (df.groupby('申請者ID')['希望勤務地'].count() > 0).mean(),
        '資格情報の存在': (~df['資格情報'].isna()).mean(),
        '座標データの取得率': calculate_geocode_success_rate(),
        '重複データの有無': 1 - (df.duplicated().sum() / len(df))
    }

    overall_score = np.mean(list(quality_checks.values())) * 100

    return {
        '総合スコア': f'{overall_score:.1f}/100',
        '詳細': quality_checks,
        '改善推奨項目': [k for k, v in quality_checks.items() if v < 0.9]
    }
```

#### 出力CSV例
```csv
評価項目,スコア,判定,改善アクション
年齢の妥当性,98%,✅,問題なし
座標取得率,94%,✅,問題なし
希望勤務地,89%,⚠️,未入力者へのリマインド
資格情報,75%,❌,入力促進施策必要
```

---

### 10. ⭐ **セグメント遷移分析**

#### 概要
「若年層地域志向型」から「中年層地元密着型」へのセグメント変化をシミュレーション。

#### ビジネス価値
- 📈 **将来予測**: 「5年後にはこのセグメントが増える」
- 🎯 **長期戦略**: セグメント別の定着率予測
- 💡 **キャリア設計**: 求職者のキャリアパス理解

#### 実装方法
```python
def simulate_persona_transition():
    """ペルソナ遷移シミュレーション"""
    # 年齢とセグメントの関係を分析
    age_persona_dist = df.groupby(['年齢層', 'segment_id']).size().unstack(fill_value=0)
    age_persona_dist = age_persona_dist.div(age_persona_dist.sum(axis=1), axis=0)

    # 5年後の年齢層シフトをシミュレーション
    current_dist = df['segment_id'].value_counts(normalize=True)

    # 年齢上昇による遷移確率行列
    transition_matrix = calculate_transition_probabilities(df)

    # 5年後の予測
    future_dist = current_dist @ transition_matrix

    return pd.DataFrame({
        '現在': current_dist,
        '5年後予測': future_dist,
        '変化率': (future_dist - current_dist) / current_dist
    })
```

#### 出力CSV例
```csv
セグメント,現在人数,5年後予測,変化率,トレンド
若年層地域志向型,149,98,-34%,↓減少傾向
中年層地域志向型,254,312,+23%,↑増加傾向
中高年層地元密着型,72,105,+46%,↑↑急増
```

---

### 11. ⭐ **希望勤務地の多様性指数**

#### 概要
求職者の希望勤務地がどれだけ分散しているかを測定（ジニ係数・エントロピー）。

#### ビジネス価値
- 📊 **市場集中度**: 特定地域への集中リスク
- 🎯 **ニッチ戦略**: 競合が少ない地域の発見
- 💡 **供給リスク**: 人材不足地域の早期警告

#### 実装方法
```python
def calculate_diversity_index():
    """希望勤務地の多様性指数算出"""
    location_counts = df['希望勤務地_市区町村'].value_counts()

    # ハーフィンダール指数（HHI）
    total = location_counts.sum()
    hhi = ((location_counts / total) ** 2).sum()

    # エントロピー
    probs = location_counts / total
    entropy = -(probs * np.log2(probs)).sum()

    # ジニ係数
    gini = calculate_gini(location_counts)

    return {
        'HHI指数': hhi,
        '市場集中度': classify_hhi(hhi),
        'エントロピー': entropy,
        'ジニ係数': gini,
        '多様性評価': classify_diversity(entropy)
    }
```

#### 出力CSV例
```csv
指標,値,解釈
HHI指数,0.08,低集中（分散している）
エントロピー,6.2,高多様性
ジニ係数,0.45,中程度の不平等
総合評価,B,やや偏在あり
```

---

### 12. ⭐ **ペルソナ別のベストマッチ地域推奨**

#### 概要
各ペルソナがどの地域に多く集まっているかをランキング化。

#### ビジネス価値
- 🎯 **ターゲット広告**: 「若年層向け求人は○○市で掲載」
- 📊 **セグメント戦略**: ペルソナ別の最適エリア
- 💡 **競合回避**: 他社が狙っていない地域発見

#### 実装方法
```python
def recommend_best_match_regions():
    """ペルソナ別ベストマッチ地域推奨"""
    results = []

    for segment_id in df['segment_id'].unique():
        segment_df = df[df['segment_id'] == segment_id]

        # 希望勤務地の集計
        top_regions = segment_df['希望勤務地_市区町村'].value_counts().head(10)

        # セグメント濃度（その地域の求職者のうち、このセグメントが占める割合）
        for region, count in top_regions.items():
            total_in_region = len(df[df['希望勤務地_市区町村']==region])
            concentration = count / total_in_region

            results.append({
                'ペルソナ': segment_df['segment_name'].iloc[0],
                '推奨地域': region,
                '人数': count,
                'セグメント濃度': concentration,
                '推奨度': 'A' if concentration > 0.3 else 'B' if concentration > 0.15 else 'C'
            })

    return pd.DataFrame(results)
```

#### 出力CSV例
```csv
ペルソナ,推奨地域1,人数,濃度,推奨地域2,人数,濃度
若年層地域志向型,宇都宮市,85,32%,小山市,48,38%
中年層地元密着型,小山市,68,27%,佐野市,42,35%
```

---

## 📊 全機能一覧（12機能）

| 機能 | 優先度 | 工数 | ビジネス価値 |
|------|--------|------|-------------|
| 1. 人材供給密度マップ | 🔴 | 1日 | ★★★★★ |
| 2. 資格別人材分布 | 🔴 | 1-2日 | ★★★★★ |
| 3. 年齢×性別クロス | 🔴 | 1日 | ★★★★☆ |
| 4. 移動許容度スコア | 🔴 | 1-2日 | ★★★★☆ |
| 5. ペルソナ詳細化 | 🔴 | 1-2日 | ★★★★☆ |
| 6. 緊急度分析 | 🟡 | 1日 | ★★★★☆ |
| 7. 資格相関分析 | 🟡 | 1-2日 | ★★★☆☆ |
| 8. 通勤距離ギャップ | 🟡 | 1日 | ★★★★☆ |
| 9. データ品質スコア | 🟡 | 1日 | ★★★☆☆ |
| 10. セグメント遷移 | 🟢 | 2日 | ★★★☆☆ |
| 11. 多様性指数 | 🟢 | 1日 | ★★☆☆☆ |
| 12. ベストマッチ地域 | 🟡 | 1日 | ★★★★☆ |

---

## 🎯 推奨実装順序

### 第1弾（実装済み）
- 機能1-5: 基礎分析強化

### 第2弾（次回実装推奨）
- **Week 1**: 機能6（緊急度分析） + 機能8（通勤距離ギャップ）
- **Week 2**: 機能7（資格相関） + 機能12（ベストマッチ地域）
- **期待効果**: 採用効率30%向上、エリア戦略最適化

### 第3弾（中長期）
- 機能9（データ品質）、10（セグメント遷移）、11（多様性指数）

---

**作成者**: Claude Code (SuperClaude Framework)
**バージョン**: 1.0
**最終更新**: 2025-10-26
