# MapComplete統合ダッシュボード - Dash実装版

**フレームワーク**: Dash (Plotly)
**作成日**: 2025年11月13日
**目的**: GAS統合ダッシュボードの完全再現（Reflex版と並列開発）

---

## 実装内容

### ✅ 目標機能（10タブ）

| Phase | 機能 | row_type | タブ | 実装状況 |
|-------|------|---------|------|---------|
| **Phase 1** | 基礎集計 | SUMMARY | 📊 サマリー | ⬜ 未実装 |
| **Phase 2** | 年齢×性別 | AGE_GENDER | 👥 年齢×性別 | ⬜ 未実装 |
| **Phase 3** | ペルソナ分析 | PERSONA_MUNI | 🎯 ペルソナ | ⬜ 未実装 |
| **Phase 6** | フロー分析 | FLOW | 🌊 フロー分析 | ⬜ 未実装 |
| **Phase 6** | 需給ギャップ | GAP | 📈 需給ギャップ | ⬜ 未実装 |
| **Phase 6** | 希少人材 | RARITY | 💎 希少人材 | ⬜ 未実装 |
| **Phase 6** | 競争プロファイル | COMPETITION | 🏆 競争プロファイル | ⬜ 未実装 |
| **Phase 8** | キャリア×年齢 | CAREER_CROSS | 💼 キャリア×年齢 | ⬜ 未実装 |
| **Phase 10** | 緊急度×年齢 | URGENCY_AGE | ⏰ 緊急度×年齢 | ⬜ 未実装 |
| **Phase 10** | 緊急度×就業 | URGENCY_EMPLOYMENT | 💼 緊急度×就業 | ⬜ 未実装 |

---

## セットアップ

### 1. 依存関係インストール

```bash
cd dash_app
pip install -r requirements.txt
```

### 2. CSVファイル配置

```bash
# 以下のパスにCSVを配置（または相対パスで読み込み）
../python_scripts/data/output_v2/mapcomplete_complete_sheets/MapComplete_Complete_All_FIXED.csv
```

### 3. アプリ起動

```bash
python app.py
```

ブラウザで http://127.0.0.1:8050 を開く

---

## 開発計画

### Day 1: 基礎実装（8時間）
- [x] プロジェクト初期化
- [ ] CSVロード機能
- [ ] レイアウト基本構造
- [ ] サイドバー（地域選択）
- [ ] タブ1-3実装（サマリー、年齢×性別、ペルソナ）

### Day 2: 完全実装（8時間）
- [ ] タブ4-7実装（フロー、ギャップ、希少人材、競争）
- [ ] タブ8-10実装（キャリア、緊急度×2）
- [ ] スタイリング調整
- [ ] パフォーマンステスト

---

## 技術スタック

- **Dash**: 2.14.0以上
- **Dash Bootstrap Components**: レスポンシブレイアウト
- **Plotly**: インタラクティブグラフ
- **pandas**: データ処理

---

## ディレクトリ構成

```
dash_app/
├── app.py                 # メインアプリケーション
├── components/            # UIコンポーネント
│   ├── sidebar.py        # サイドバー（地域選択）
│   └── tabs/             # 各タブの実装
│       ├── tab_summary.py
│       ├── tab_age_gender.py
│       └── ...
├── data_loader.py        # CSVロード・フィルタリング
├── assets/               # CSS/画像
│   └── custom.css
├── requirements.txt
└── README.md
```

---

## Reflex版との比較

| 項目 | Dash | Reflex |
|------|------|--------|
| **開発期間** | 2日間 | 3日間 |
| **学習コスト** | 低（Reactライク） | 中（新技術） |
| **コード量** | 多い（~500行） | 少ない（~350行） |
| **カスタマイズ性** | 高（CSS/JS完全制御） | 中（Chakra UI制約） |
| **パフォーマンス** | 高速（実績あり） | 未知（要検証） |
| **コミュニティ** | 成熟 | 成長中 |

---

**次のステップ**: `app.py`のMVP実装
