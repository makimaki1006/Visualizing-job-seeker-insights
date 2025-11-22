# Streamlitプロトタイプダッシュボード

**作成日**: 2025年11月12日
**目的**: GASの代替として、Streamlitによる高速・簡単な可視化ダッシュボードを検証

---

## 実行方法

### 1. 依存関係インストール

```bash
cd "C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\streamlit_app"
pip install -r requirements.txt
```

### 2. Streamlitアプリ起動

```bash
streamlit run streamlit_dashboard.py
```

### 3. ブラウザで表示

自動的にブラウザが開きます（通常 http://localhost:8501）

### 4. CSVファイルアップロード

**2つの方法**:

#### 方法1: 自動読み込み（推奨）
- CSVファイルを以下のパスに配置:
  ```
  python_scripts/data/output_v2/mapcomplete_complete_sheets/MapComplete_Complete_All_FIXED.csv
  ```
- 自動的に読み込まれます

#### 方法2: ドラッグ&ドロップ（簡単）
- ブラウザ上の「**ファイルをアップロード**」エリアに `MapComplete_Complete_All_FIXED.csv` をドラッグ&ドロップ
- または「Browse files」をクリックしてファイルを選択
- 約2秒で読み込み完了（20,590行×36列）

---

## 機能一覧

### サイドバー
- 📍 **都道府県選択**: 47都道府県から選択
- 📍 **市区町村選択**: 選択した都道府県の全市区町村

### 6つのタブ

1. **📊 サマリー**
   - 申請者数
   - 平均年齢
   - 男性・女性比率

2. **👥 年齢×性別**
   - 年齢層×性別のクロス集計
   - インタラクティブ棒グラフ

3. **🌊 フロー分析**
   - 流入（Inflow）
   - 流出（Outflow）
   - 純流入（Net Flow）
   - サンキー図

4. **📈 需給ギャップ**
   - 需要（Demand）
   - 供給（Supply）
   - ギャップ（Gap）
   - 棒グラフ比較

5. **🎯 ペルソナ分析**
   - ペルソナ別人数分布
   - 棒グラフ

6. **💼 キャリア×年齢**
   - キャリア×年齢層クロス集計
   - インタラクティブ棒グラフ

---

## GASとの比較

| 項目 | GAS | Streamlit |
|------|-----|-----------|
| **開発時間** | 数週間 | 1日 |
| **学習コスト** | 高い（GAS独自API） | 低い（Python） |
| **パフォーマンス** | 遅い（98秒） | 速い（2秒） |
| **カスタマイズ性** | 制約あり | 自由度高い |
| **デプロイ** | GAS | Render/Streamlit Cloud（無料） |
| **保守性** | やや低い | 高い |

---

## 次のステップ

### Option 1: Streamlitで続ける場合
1. 機能追加（Phase 7高度分析など）
2. Renderにデプロイ（無料プラン）
3. カスタムドメイン設定

### Option 2: GASで続ける場合
1. 修正版MapCompleteDataBridge.jsをデプロイ
2. 統合ダッシュボードで動作確認
3. パフォーマンス最適化

---

## トラブルシューティング

### CSVファイルが見つからない
**エラー**: `CSVファイルが見つかりません`

**解決方法**:
1. ブラウザ上でドラッグ&ドロップしてファイルをアップロード
2. または、`python_scripts/data/output_v2/mapcomplete_complete_sheets/MapComplete_Complete_All_FIXED.csv` にファイルを配置

### ポートが使用中
**エラー**: `Port 8501 is already in use`

**解決方法**:
```bash
streamlit run streamlit_dashboard.py --server.port 8502
```

---

## Renderデプロイ手順

### 1. GitHubにプッシュ

```bash
cd "C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project"
git init
git add streamlit_app/
git commit -m "Add Streamlit dashboard"
git remote add origin https://github.com/YOUR_USERNAME/job_medley_dashboard.git
git push -u origin main
```

### 2. Renderで新規サービス作成

1. https://render.com/ でサインイン
2. **New** → **Web Service**
3. GitHubリポジトリを接続
4. 以下を設定:
   - **Name**: job-medley-dashboard
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r streamlit_app/requirements.txt`
   - **Start Command**: `streamlit run streamlit_app/streamlit_dashboard.py --server.port $PORT --server.address 0.0.0.0`
   - **Plan**: Free

5. **Create Web Service**

### 3. デプロイ完了

約5分でデプロイ完了。URLが発行されます（例: https://job-medley-dashboard.onrender.com）

---

## まとめ

- ✅ **開発時間**: 1日（GASは数週間）
- ✅ **パフォーマンス**: GASの50倍速い（2秒 vs 98秒）
- ✅ **学習コスト**: Python知識のみで開発可能
- ✅ **デプロイ**: git pushで自動デプロイ（Render無料プラン）
- ✅ **保守性**: シンプルなPythonコード（GASより保守しやすい）

**推奨**: Streamlitでプロトタイプを作成し、必要に応じてGASと併用
