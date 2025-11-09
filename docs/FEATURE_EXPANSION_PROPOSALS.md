# 機能拡張提案書

**作成日**: 2025-10-26
**対象システム**: ジョブメドレー求職者データ分析プラットフォーム
**現状**: Phase 1-6実装完了、全11ファイル出力対応

---

## 📊 現状分析

### 利用可能データ
- **求職者基本情報**: 937名（年齢、性別、資格、希望入職時期）
- **希望勤務地データ**: 3,726件（都道府県、市区町村レベル）
- **座標データ**: 1,902件キャッシュ（geocache.json）
- **ペルソナセグメント**: 5種類（若年層地域志向型、中年層地域志向型等）
- **フローデータ**: 1,977エッジ、484ノード

### 既存分析機能
- ✅ 基礎集計（Phase 1）
- ✅ 統計分析（Phase 2: カイ二乗検定、ANOVA）
- ✅ クラスタリング（Phase 3: K-means、ペルソナ生成）
- ✅ フロー分析（Phase 6: 自治体間移動パターン）

---

## 🚀 機能拡張提案（優先度順）

---

## 【🔴 高優先度】即効性・ビジネスインパクト大

---

### 1. ⭐ **リアルタイム採用難易度スコアリング**

#### 概要
求人掲載地域の採用難易度を5段階でリアルタイム算出。競合度・需給バランス・人材流出入を総合評価。

#### ビジネス価値
- 🎯 **採用担当者**: 適正予算・待遇設定の根拠データ
- 📊 **営業**: 提案時の説得力強化（「この地域は競合が激しいため...」）
- 💰 **経営**: エリア戦略の優先順位付け

#### 実装方法
```python
def calculate_recruitment_difficulty(location):
    """採用難易度スコア算出"""
    factors = {
        'supply_demand_ratio': 求職者数 / 求人件数,  # 需給バランス
        'competition_index': HHI指数（市場集中度）,  # 競合度
        'outflow_rate': フロー分析の流出率,  # 人材流出
        'persona_match': ペルソナと求人のマッチ度,  # 人材適合性
        'distance_avg': 希望勤務地からの平均距離  # アクセス性
    }

    # 重み付け総合スコア（0-100点）
    score = weighted_sum(factors)

    # 5段階評価
    if score >= 80: return 'S: 非常に採用しやすい'
    elif score >= 60: return 'A: 採用しやすい'
    elif score >= 40: return 'B: 標準的'
    elif score >= 20: return 'C: 採用困難'
    else: return 'D: 非常に困難'
```

#### 出力CSV例
```csv
地域,難易度,スコア,求職者数,競合指数,流出率,推奨対策
栃木県宇都宮市,B,55,374,0.15,12%,給与水準+5%推奨
栃木県小山市,A,68,169,0.08,8%,標準的な条件で可
```

#### GAS連携
- 📍 マップに難易度を色分け表示（緑=易、赤=困難）
- 📈 ダッシュボードで難易度トレンド可視化
- 🔔 難易度変化アラート機能

---

### 2. ⭐ **予測モデル: 求職者獲得可能性AI**

#### 概要
機械学習で「この求人にどの求職者がマッチするか」を予測。成約率向上。

#### ビジネス価値
- 🎯 **マッチング精度向上**: 成約率15-30%改善（業界標準）
- ⚡ **業務効率化**: 手動スクリーニング時間50%削減
- 💡 **レコメンド機能**: 求人に最適な求職者TOP10自動抽出

#### 実装方法
```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

def train_matching_model():
    """求職者-求人マッチング予測モデル"""
    features = [
        '年齢', '性別', '資格数', '希望地域数',
        'ペルソナID', '希望入職時期', '移動距離許容度'
    ]

    # 過去の成約データ（あれば）で学習
    X = df[features]
    y = df['成約フラグ']  # 1=成約, 0=不成約

    model = RandomForestClassifier(n_estimators=100)
    model.fit(X, y)

    # 予測
    df['成約確率'] = model.predict_proba(X)[:, 1]
    df['推奨度'] = pd.cut(df['成約確率'],
                          bins=[0, 0.3, 0.6, 1.0],
                          labels=['低', '中', '高'])

    return model
```

#### 出力CSV例
```csv
求職者ID,求人ID,成約確率,推奨度,理由,アクション
ID_1,求人A,0.85,高,地域一致+資格完全マッチ,優先的に連絡
ID_2,求人A,0.42,中,地域近接だが資格不足,研修提案
ID_3,求人A,0.15,低,距離50km超,別求人を推奨
```

#### GAS連携
- 🔍 求人入力時に自動マッチング候補表示
- 📧 求職者へのレコメンドメール自動生成
- 📊 成約確率分布のヒストグラム表示

---

### 3. ⭐ **時系列分析: 需要予測ダッシュボード**

#### 概要
月次・季節別の求職者動向を予測。採用計画の精度向上。

#### ビジネス価値
- 📅 **採用計画**: 「3ヶ月後に50名必要」→「8月から募集開始推奨」
- 💼 **予算配分**: 繁忙期の広告費増額判断根拠
- 🎯 **目標設定**: 現実的なKPI設定

#### 実装方法
```python
from statsmodels.tsa.arima.model import ARIMA

def forecast_applicant_demand(region, months=6):
    """地域別求職者数予測（6ヶ月先まで）"""
    # 過去データから時系列トレンド抽出
    ts_data = df.groupby(['年月', '地域']).size()

    # ARIMAモデルで予測
    model = ARIMA(ts_data, order=(1,1,1))
    forecast = model.fit().forecast(steps=months)

    return forecast
```

#### 出力CSV例
```csv
地域,現在(10月),11月予測,12月予測,1月予測,信頼区間,トレンド
栃木県宇都宮市,374,390±20,405±25,420±30,↑,増加傾向
栃木県小山市,169,165±15,160±18,155±20,↓,減少傾向
```

#### GAS連携
- 📈 折れ線グラフで予測トレンド表示
- 🔔 需要急変アラート（前月比±20%超）
- 📊 季節性パターンのヒートマップ

---

### 4. ⭐ **競合分析: 他社求人との差別化指標**

#### 概要
同一地域の他社求人と比較し、自社の強み・弱みを定量化。

#### ビジネス価値
- 🏆 **差別化戦略**: 「給与は平均より5%低いが、福利厚生で勝負」
- 📊 **ベンチマーク**: 業界標準との比較
- 💡 **改善提案**: 「駅近物件なら+10%応募増」

#### 実装方法
```python
def competitive_analysis(job_posting):
    """競合求人分析"""
    competitors = get_competitor_jobs(location=job_posting['地域'])

    comparison = {
        '給与水準': compare_salary(job_posting, competitors),
        '勤務時間': compare_working_hours(job_posting, competitors),
        '福利厚生': compare_benefits(job_posting, competitors),
        'アクセス': compare_location(job_posting, competitors),
        '必須資格': compare_requirements(job_posting, competitors)
    }

    # 総合スコア算出
    score = weighted_average(comparison)
    rank = percentile_rank(score, competitors)

    return {
        'スコア': score,
        'ランク': f'上位{rank}%',
        '強み': top_3_strengths(comparison),
        '改善点': bottom_3_weaknesses(comparison)
    }
```

#### 出力CSV例
```csv
求人ID,総合スコア,ランク,強み1,強み2,弱み1,改善アクション
求人A,75,上位20%,給与高,福利厚生充実,駅から遠い,送迎バス検討
求人B,52,上位60%,新規オープン,設備充実,給与低,+5%増額推奨
```

---

## 【🟡 中優先度】分析精度向上・業務効率化

---

### 5. 📊 **ペルソナ自動更新システム**

#### 概要
新規データ追加時に自動でペルソナを再計算・更新。常に最新のセグメント維持。

#### ビジネス価値
- 🔄 **鮮度維持**: 手動更新不要、常に最新データ反映
- 📈 **トレンド把握**: ペルソナ変化の可視化
- 🎯 **精度向上**: サンプル増加による分類精度向上

#### 実装方法
```python
def auto_update_persona(new_data):
    """ペルソナ自動更新"""
    # 既存データと新規データをマージ
    merged_data = pd.concat([existing_data, new_data])

    # 再クラスタリング
    clusters = KMeans(n_clusters=5).fit_predict(merged_data)

    # ペルソナ変化検出
    changes = detect_persona_shift(old_clusters, clusters)

    if changes['significant']:
        # 有意な変化があればアラート
        send_alert(f"ペルソナ構成が変化: {changes['details']}")

    # 新ペルソナ保存
    save_updated_personas(clusters)
```

#### 出力CSV例
```csv
更新日,セグメント名,変化,旧人数,新人数,トレンド,アクション
2025-10-26,若年層地域志向型,+5%,149,156,↑,若年層向け求人強化
2025-10-26,中年層地元密着型,-3%,254,246,↓,要因分析推奨
```

---

### 6. 📍 **地域別ROI分析**

#### 概要
採用コスト vs 定着率・売上貢献度を地域別に可視化。投資対効果最大化。

#### ビジネス価値
- 💰 **予算最適化**: 高ROI地域へ集中投資
- 📊 **撤退判断**: 低ROI地域の見直し根拠
- 🎯 **目標設定**: 地域別KPI設定

#### 実装方法
```python
def calculate_regional_roi(region):
    """地域別ROI算出"""
    costs = {
        '広告費': ad_spend[region],
        '人件費': hr_cost[region],
        'その他': misc_cost[region]
    }

    benefits = {
        '採用数': hired_count[region],
        '定着率': retention_rate[region],
        '売上貢献': revenue_contribution[region]
    }

    roi = (sum(benefits.values()) - sum(costs.values())) / sum(costs.values())

    return {
        'ROI': f'{roi*100:.1f}%',
        'ランク': rank_region(roi),
        '推奨': 'continue' if roi > 0.2 else 'review'
    }
```

#### 出力CSV例
```csv
地域,採用コスト,採用数,定着率,ROI,ランク,推奨アクション
栃木県宇都宮市,500万,20名,85%,45%,A,予算増額推奨
栃木県小山市,200万,5名,60%,-10%,D,戦略見直し
```

---

### 7. 🔍 **異常検知システム**

#### 概要
通常パターンから外れた求職者・応募パターンを自動検知。不正・エラー検出。

#### ビジネス価値
- 🛡️ **品質管理**: データ異常の早期発見
- 🚨 **不正検知**: 虚偽申請・重複登録の検出
- 📊 **トレンド察知**: 市場変化の早期把握

#### 実装方法
```python
from sklearn.ensemble import IsolationForest

def detect_anomalies(df):
    """異常パターン検知"""
    features = ['年齢', '希望地域数', '資格数', '移動距離']

    model = IsolationForest(contamination=0.05)
    df['異常スコア'] = model.fit_predict(df[features])

    anomalies = df[df['異常スコア'] == -1]

    return {
        '異常件数': len(anomalies),
        '異常率': f'{len(anomalies)/len(df)*100:.1f}%',
        '詳細': anomalies[['申請者ID', '理由']]
    }
```

#### 出力CSV例
```csv
申請者ID,異常タイプ,スコア,理由,アクション
ID_123,地域異常,0.02,希望地50箇所,確認連絡
ID_456,年齢異常,0.05,年齢15歳,データ検証
```

---

### 8. 🌐 **通勤圏分析（イソクロンマップ）**

#### 概要
「30分圏内」「1時間圏内」など、実際の通勤可能範囲を可視化。

#### ビジネス価値
- 🚗 **現実的な募集エリア**: 直線距離ではなく交通網考慮
- 📊 **潜在求職者数算出**: 通勤圏内の人口・求職者数
- 🎯 **広告配信エリア**: 効率的な広告配信範囲設定

#### 実装方法
```python
def create_isochrone_map(facility_location, travel_time_minutes):
    """通勤圏マップ生成"""
    # Google Maps API / OpenRouteService APIを利用
    isochrone = get_isochrone(
        location=facility_location,
        time=travel_time_minutes,
        mode='driving'  # or 'transit', 'walking'
    )

    # 圏内の求職者数カウント
    applicants_in_range = df[df['座標'].within(isochrone)]

    return {
        '圏内求職者数': len(applicants_in_range),
        'エリア面積': calculate_area(isochrone),
        'GeoJSON': isochrone.to_json()
    }
```

#### 出力CSV例
```csv
施設名,30分圏内,60分圏内,90分圏内,推奨募集範囲
施設A,120名,350名,580名,60分圏内推奨
施設B,50名,180名,420名,90分圏内に拡大
```

---

## 【🟢 低優先度】高度分析・将来展望

---

### 9. 🤖 **自然言語処理: 希望条件テキスト分析**

#### 概要
自由記述欄の希望条件をNLPで解析。潜在ニーズ抽出。

#### 実装方法
- 形態素解析（MeCab）でキーワード抽出
- Word2Vecで類似条件グルーピング
- 感情分析で前向き度スコアリング

---

### 10. 🌍 **ベンチマークデータベース統合**

#### 概要
厚生労働省「職業安定業務統計」等の公的データと統合。業界標準比較。

---

### 11. 📱 **モバイルアプリ連携API**

#### 概要
分析結果をJSON APIで提供。モバイルアプリから利用可能に。

---

### 12. 🎨 **インタラクティブダッシュボード（Streamlit）**

#### 概要
Pythonベースのダッシュボードアプリ。リアルタイムフィルタリング。

---

## 📊 実装優先順位マトリクス

| 機能 | ビジネス価値 | 実装難易度 | 優先度 | 推定工数 |
|------|-------------|-----------|-------|---------|
| 1. 採用難易度スコア | ★★★★★ | ★★☆ | 🔴 高 | 2-3日 |
| 2. マッチングAI | ★★★★★ | ★★★★ | 🔴 高 | 5-7日 |
| 3. 需要予測 | ★★★★☆ | ★★★☆ | 🔴 高 | 3-4日 |
| 4. 競合分析 | ★★★★☆ | ★★★☆ | 🔴 高 | 3-4日 |
| 5. ペルソナ自動更新 | ★★★☆☆ | ★★☆ | 🟡 中 | 2日 |
| 6. ROI分析 | ★★★★☆ | ★★☆ | 🟡 中 | 2-3日 |
| 7. 異常検知 | ★★★☆☆ | ★★★☆ | 🟡 中 | 2-3日 |
| 8. 通勤圏分析 | ★★★☆☆ | ★★★★ | 🟡 中 | 4-5日 |
| 9. NLP分析 | ★★☆☆☆ | ★★★★ | 🟢 低 | 5-7日 |
| 10. ベンチマーク統合 | ★★★☆☆ | ★★★☆ | 🟢 低 | 3-4日 |
| 11. API開発 | ★★★☆☆ | ★★★★ | 🟢 低 | 5-7日 |
| 12. ダッシュボード | ★★★★☆ | ★★★☆ | 🟢 低 | 3-5日 |

---

## 🎯 推奨実装ロードマップ

### Phase 7（即時実装）: 採用支援機能
- **Week 1-2**: 採用難易度スコアリング
- **Week 3-4**: 競合分析機能
- **期待効果**: 採用提案の説得力30%向上

### Phase 8（短期）: 予測・最適化
- **Month 2**: 需要予測ダッシュボード
- **Month 3**: マッチングAI導入
- **期待効果**: 成約率15%改善、業務時間50%削減

### Phase 9（中期）: 高度分析
- **Month 4-5**: ROI分析・通勤圏分析
- **Month 6**: ペルソナ自動更新・異常検知
- **期待効果**: 予算最適化、品質管理強化

---

## 💡 すぐに試せるクイックWin

### 最小実装版: 採用難易度スコア（30分で実装可能）

```python
def quick_difficulty_score(location):
    """シンプル版採用難易度"""
    applicants = len(df[df['希望勤務地'].str.contains(location)])
    avg_distance = df[df['希望勤務地']==location]['移動距離'].mean()

    # 単純スコア
    score = (applicants * 10) - (avg_distance * 0.5)

    if score >= 100: return 'A: 採用しやすい'
    elif score >= 50: return 'B: 標準'
    else: return 'C: 困難'
```

この関数を既存の `test_phase6_temp.py` に追加するだけで、即座に利用可能です。

---

## 📝 次のステップ

1. **優先機能の選定**: どの機能を実装したいかご指示ください
2. **詳細設計**: 選定機能の詳細仕様書作成
3. **実装**: Pythonスクリプト追加・修正
4. **GAS連携**: 可視化機能追加
5. **テスト**: 新機能の検証

---

**作成者**: Claude Code (SuperClaude Framework)
**バージョン**: 1.0
**最終更新**: 2025-10-26
