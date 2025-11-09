# 実現可能な機能拡張提案書（既存データのみ使用）

**作成日**: 2025-10-26
**前提条件**: 求職者データ937名のみ使用（求人データ・成約履歴なし）

---

## 🎯 データ制約の明確化

### 利用可能データ
- ✅ 求職者937名（年齢、性別、居住地）
- ✅ 希望勤務地3,726件（都道府県、市区町村）
- ✅ 資格情報（217項目）
- ✅ 希望入職時期（5段階）
- ✅ 座標データ1,902件（geocache.json）

### 利用不可データ
- ❌ 求人情報（給与、勤務条件、募集要項）
- ❌ 成約履歴（マッチング結果、採用実績）
- ❌ 過去の時系列データ（月次推移）
- ❌ 競合他社データ
- ❌ 採用コスト・ROI情報

---

## 🚀 実装可能な機能拡張（優先度順）

---

## 【🔴 高優先度】既存データで即座に価値提供

---

### 1. ⭐ **人材供給密度マップ（ヒートマップ強化版）**

#### 概要
地域ごとの「求職者密度」「資格保有率」「年齢構成」を重ね合わせた多層ヒートマップ。

#### ビジネス価値
- 🎯 **採用担当者**: 「どこに求人を出すべきか」の判断根拠
- 📊 **営業**: 「この地域は人材が豊富です」という提案材料
- 💡 **経営**: エリア戦略・出店計画の意思決定支援

#### 実装方法
```python
def create_supply_density_map():
    """人材供給密度の可視化"""
    # 地域ごとの求職者数
    density = df.groupby('市区町村').size()

    # 資格保有率
    qualified_rate = df.groupby('市区町村')['資格数'].apply(
        lambda x: (x > 0).sum() / len(x)
    )

    # 平均年齢
    avg_age = df.groupby('市区町村')['年齢'].mean()

    # 希望入職時期（緊急度）
    urgency = df.groupby('市区町村')['希望入職時期'].apply(
        lambda x: (x.isin(['今すぐに', '1ヶ月以内'])).sum() / len(x)
    )

    return pd.DataFrame({
        '求職者密度': density,
        '資格保有率': qualified_rate,
        '平均年齢': avg_age,
        '緊急度': urgency,
        '総合スコア': (density * 0.4 + qualified_rate * 0.3 +
                       urgency * 0.3)
    })
```

#### 出力CSV例
```csv
市区町村,求職者密度,資格保有率,平均年齢,緊急度,総合スコア,ランク
栃木県宇都宮市,374,0.82,47.3,0.15,8.5,S
栃木県小山市,169,0.75,45.8,0.22,7.2,A
栃木県足利市,133,0.68,52.1,0.10,5.8,B
```

#### GAS連携
- 🗺️ 既存ヒートマップに総合スコアレイヤー追加
- 📊 ランク別色分け（S=濃緑、A=緑、B=黄、C=オレンジ、D=赤）
- 🔍 クリックで詳細内訳表示

---

### 2. ⭐ **資格別人材分布分析**

#### 概要
「介護福祉士」「看護師」など特定資格保有者がどこに集中しているかを可視化。

#### ビジネス価値
- 🎯 **資格限定求人**: 「看護師募集」の際にどこに広告を出すべきか
- 📊 **需給ギャップ分析**: 資格保有者が少ない＝希少価値高い
- 💡 **採用戦略**: 資格取得支援制度の設計根拠

#### 実装方法
```python
def analyze_qualification_distribution():
    """資格別人材分布分析"""
    # 資格カテゴリごとの地域分布
    results = []

    for category, qualifications in QUALIFICATIONS.items():
        # この資格カテゴリを持つ求職者
        mask = df['資格情報'].apply(
            lambda x: any(q in str(x) for q in qualifications)
        )
        qualified_df = df[mask]

        # 地域別カウント
        distribution = qualified_df.groupby('市区町村').size()

        # 全求職者に対する割合
        total_by_region = df.groupby('市区町村').size()
        penetration = distribution / total_by_region

        results.append({
            '資格カテゴリ': category,
            '総保有者数': len(qualified_df),
            '分布トップ3': distribution.nlargest(3).to_dict(),
            '希少地域': penetration.nsmallest(3).to_dict()
        })

    return pd.DataFrame(results)
```

#### 出力CSV例
```csv
資格カテゴリ,総保有者数,分布1位,分布2位,分布3位,希少地域1,希少地域2
介護福祉専門職,245,宇都宮市(89),小山市(42),足利市(31),石垣市,延岡市
看護系,112,宇都宮市(35),小山市(18),佐野市(12),函館市,旭川市
リハビリ系,68,宇都宮市(22),小山市(10),栃木市(8),鹿児島市,那覇市
```

#### GAS連携
- 🎨 資格カテゴリ選択ドロップダウン
- 🗺️ 選択資格の分布マップ表示
- 📊 資格保有率の棒グラフ

---

### 3. ⭐ **年齢層別・性別クロス分析**

#### 概要
「若年女性」「中高年男性」など、セグメント別の地域偏在を分析。

#### ビジネス価値
- 🎯 **ターゲット採用**: 「20代女性が欲しい」→該当者が多い地域を特定
- 📊 **ダイバーシティ**: 男女比・年齢構成のバランス把握
- 💡 **採用メッセージ**: セグメント別の訴求ポイント設計

#### 実装方法
```python
def cross_analysis_age_gender():
    """年齢層×性別クロス分析"""
    # セグメント定義
    df['年齢層'] = pd.cut(df['年齢'],
                          bins=[0, 30, 45, 60, 100],
                          labels=['若年層', '中年層', '準高齢層', '高齢層'])

    # 地域×年齢層×性別の3次元集計
    cross = df.groupby(['市区町村', '年齢層', '性別']).size().unstack(fill_value=0)

    # 各地域の特徴抽出
    dominant_segment = cross.idxmax(axis=1)
    diversity_score = cross.apply(lambda x: 1 - (x**2).sum() / x.sum()**2, axis=1)

    return pd.DataFrame({
        '支配的セグメント': dominant_segment,
        'ダイバーシティスコア': diversity_score,
        '若年女性比率': cross.get(('若年層', '女性'), 0) / cross.sum(axis=1),
        '中年男性比率': cross.get(('中年層', '男性'), 0) / cross.sum(axis=1)
    })
```

#### 出力CSV例
```csv
市区町村,支配的セグメント,若年女性,中年女性,若年男性,中年男性,多様性スコア
宇都宮市,中年女性,85,142,42,105,0.72
小山市,若年女性,48,68,22,31,0.68
```

#### GAS連携
- 📊 セグメント構成の積み上げ棒グラフ
- 🎯 セグメント選択フィルター
- 🗺️ セグメント優勢地域のマップ表示

---

### 4. ⭐ **移動許容度スコアリング**

#### 概要
希望勤務地の「広がり具合」から、求職者の移動許容度を定量化。

#### ビジネス価値
- 🎯 **採用効率化**: 移動許容度が高い人材を優先的にマッチング
- 📊 **求人配置**: 「この施設は遠方人材もOK」vs「地元限定」
- 💡 **待遇設計**: 遠方採用なら住宅手当・交通費支給

#### 実装方法
```python
def calculate_mobility_score():
    """移動許容度スコア算出"""
    applicant_mobility = []

    for applicant_id in df['申請者ID'].unique():
        locations = df[df['申請者ID']==applicant_id]['希望勤務地']

        # 希望地の広がり（標準偏差）
        coords = [geocache.get(loc) for loc in locations]
        if len(coords) > 1:
            lat_std = np.std([c['lat'] for c in coords])
            lng_std = np.std([c['lng'] for c in coords])
            spread = np.sqrt(lat_std**2 + lng_std**2)
        else:
            spread = 0

        # 最大移動距離
        if len(coords) > 1:
            distances = cdist(coords, coords, metric='euclidean')
            max_distance = distances.max()
        else:
            max_distance = 0

        # 移動許容度スコア（0-100）
        score = min(100, spread * 10 + max_distance * 0.5)

        if score >= 70: level = 'A: 広域移動OK'
        elif score >= 40: level = 'B: 中距離OK'
        elif score >= 10: level = 'C: 近距離のみ'
        else: level = 'D: 地元限定'

        applicant_mobility.append({
            '申請者ID': applicant_id,
            '希望地数': len(locations),
            '最大移動距離km': max_distance,
            '移動許容度スコア': score,
            '移動許容度': level
        })

    return pd.DataFrame(applicant_mobility)
```

#### 出力CSV例
```csv
申請者ID,希望地数,最大移動距離km,移動スコア,移動許容度,居住地
ID_1,1,0,5,D:地元限定,宇都宮市
ID_2,3,45,38,B:中距離OK,小山市
ID_3,12,420,85,A:広域移動OK,浜松市
```

#### GAS連携
- 🎯 移動許容度フィルター（A/B/C/D選択）
- 📊 許容度分布の円グラフ
- 🗺️ 求職者の希望地範囲を円で表示

---

### 5. ⭐ **ペルソナ詳細プロファイル生成**

#### 概要
既存5ペルソナを詳細化。行動パターン・特徴を深掘り。

#### ビジネス価値
- 🎯 **採用メッセージ最適化**: ペルソナ別の訴求ポイント
- 📊 **求人設計**: ペルソナに合わせた条件設定
- 💡 **営業ツール**: 提案資料の説得力強化

#### 実装方法
```python
def generate_detailed_persona_profile():
    """ペルソナ詳細プロファイル生成"""
    for segment_id in df['segment_id'].unique():
        segment_df = df[df['segment_id'] == segment_id]

        profile = {
            'セグメント名': segment_df['segment_name'].iloc[0],
            '人数': len(segment_df),
            '平均年齢': segment_df['年齢'].mean(),
            '性別比': segment_df['性別'].value_counts(normalize=True),
            '資格保有率': (segment_df['資格数'] > 0).mean(),
            '平均資格数': segment_df['資格数'].mean(),
            '希望地数': segment_df.groupby('申請者ID')['希望勤務地'].count().mean(),
            '移動距離': segment_df['最大移動距離'].mean(),
            '緊急度': (segment_df['希望入職時期'].isin(['今すぐに', '1ヶ月以内'])).mean(),
            '主要居住地TOP5': segment_df['居住地_市区町村'].value_counts().head(5),
            '主要資格TOP5': extract_top_qualifications(segment_df),
            '行動特性': classify_behavior_pattern(segment_df)
        }

        yield profile
```

#### 出力CSV例
```csv
セグメント,人数,平均年齢,女性比率,資格保有率,希望地数,移動距離,緊急度,主要居住地,特徴
若年層地域志向型,149,26.0,74%,45%,2.1,18km,22%,宇都宮(35),柔軟性高・資格取得意欲
中年層地元密着型,254,45.3,70%,78%,1.9,8km,10%,小山(28),安定志向・経験豊富
```

#### GAS連携
- 📊 ペルソナ選択UI
- 🎨 レーダーチャートで特性可視化
- 📄 ペルソナカード（印刷用）生成

---

## 【🟡 中優先度】深掘り分析・洞察抽出

---

### 6. 📊 **資格取得パターン分析**

#### 概要
「介護福祉士を持つ人は初任者研修も持つ」など、資格の組み合わせパターンを発見。

#### 実装方法
- 相関分析・アソシエーションルール（Apriori）
- 資格取得の典型的な経路を可視化

---

### 7. 🔍 **異常値検知（データ品質チェック）**

#### 概要
「年齢15歳で資格10個」「希望地50箇所」など、不自然なデータを自動検出。

#### 実装方法
- Isolation Forestで外れ値検出
- 統計的閾値（平均±3σ）で異常判定

---

### 8. 📍 **地域クラスタリング（似た特性の地域グルーピング）**

#### 概要
「宇都宮と浜松は求職者構成が似ている」など、地域間の類似性を発見。

#### 実装方法
- K-meansで地域をクラスタリング
- 年齢構成・資格保有率・移動距離などの特徴量使用

---

### 9. 🌊 **希望勤務地の重複度分析**

#### 概要
「複数の求職者が同じ地域を希望している」競合度の高いエリアを特定。

#### 実装方法
- HHI指数（ハーフィンダール指数）で市場集中度算出
- 競合度ランキング生成

---

### 10. 📈 **ペルソナ間の距離分析**

#### 概要
「若年層地域志向型」と「中年層地元密着型」の特性差を定量化。

#### 実装方法
- ユークリッド距離・マハラノビス距離で類似度計算
- デンドログラム（樹形図）で階層構造可視化

---

## 【🟢 低優先度】発展的分析・実験的機能

---

### 11. 🎨 **3Dバブルマップ**

#### 概要
X軸=緯度、Y軸=経度、Z軸=求職者数の3次元可視化。

---

### 12. 🔮 **仮想シミュレーション**

#### 概要
「もし宇都宮に新施設を出すと、何人が応募可能か」のWhat-if分析。

---

## 📊 実装優先順位マトリクス（データ制約版）

| 機能 | ビジネス価値 | 実装難易度 | 優先度 | 推定工数 |
|------|-------------|-----------|-------|---------|
| 1. 人材供給密度マップ | ★★★★★ | ★☆☆ | 🔴 高 | 1日 |
| 2. 資格別人材分布 | ★★★★★ | ★★☆ | 🔴 高 | 1-2日 |
| 3. 年齢層×性別クロス分析 | ★★★★☆ | ★☆☆ | 🔴 高 | 1日 |
| 4. 移動許容度スコア | ★★★★☆ | ★★☆ | 🔴 高 | 1-2日 |
| 5. ペルソナ詳細プロファイル | ★★★★☆ | ★★☆ | 🔴 高 | 1-2日 |
| 6. 資格取得パターン | ★★★☆☆ | ★★☆ | 🟡 中 | 1-2日 |
| 7. 異常値検知 | ★★☆☆☆ | ★☆☆ | 🟡 中 | 1日 |
| 8. 地域クラスタリング | ★★★☆☆ | ★★★☆ | 🟡 中 | 2日 |
| 9. 希望地重複度分析 | ★★★☆☆ | ★☆☆ | 🟡 中 | 1日 |
| 10. ペルソナ間距離分析 | ★★☆☆☆ | ★★☆ | 🟡 中 | 1日 |

---

## 🎯 推奨実装ロードマップ

### Phase 7-A（即時実装）: 供給分析強化
- **Week 1**: 人材供給密度マップ + 資格別人材分布
- **期待効果**: 「どこに求人を出すべきか」の判断精度向上

### Phase 7-B（短期）: セグメント深掘り
- **Week 2**: 年齢層×性別クロス分析 + 移動許容度スコア
- **期待効果**: ターゲット採用の効率化

### Phase 7-C（中期）: ペルソナ活用
- **Week 3**: ペルソナ詳細プロファイル + 資格取得パターン
- **期待効果**: 採用メッセージ・求人設計の最適化

---

## 💡 すぐに試せるクイックWin

### 最小実装版: 人材供給密度スコア（15分で実装可能）

```python
def quick_supply_density_score(location):
    """シンプル版人材供給密度スコア"""
    # その地域の求職者数
    count = len(df[df['市区町村'] == location])

    # 資格保有率
    qualified = df[df['市区町村'] == location]['資格数'] > 0
    qual_rate = qualified.mean() if len(qualified) > 0 else 0

    # 緊急度（すぐ就職したい人の割合）
    urgent = df[df['市区町村'] == location]['希望入職時期'].isin(['今すぐに', '1ヶ月以内'])
    urgent_rate = urgent.mean() if len(urgent) > 0 else 0

    # 総合スコア
    score = count * 0.5 + qual_rate * 30 + urgent_rate * 20

    if score >= 50: return f'S: 採用しやすい ({count}名)'
    elif score >= 30: return f'A: 標準的 ({count}名)'
    elif score >= 10: return f'B: やや困難 ({count}名)'
    else: return f'C: 困難 ({count}名)'

# 全地域のスコア算出
scores = {loc: quick_supply_density_score(loc)
          for loc in df['市区町村'].unique()}
```

---

## 📝 次のステップ

どの機能を実装しますか？

1. **クイックWin**: 15分で人材供給密度スコア
2. **Phase 7-A**: 供給分析強化（1週間）
3. **カスタム**: 特定機能のみピックアップ

---

**作成者**: Claude Code (SuperClaude Framework)
**バージョン**: 2.0（データ制約対応版）
**最終更新**: 2025-10-26
