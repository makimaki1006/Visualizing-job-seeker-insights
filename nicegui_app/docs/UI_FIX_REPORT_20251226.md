# UI修正レポート (2025-12-26)

## 概要

本レポートは、NiceGUIダッシュボードにおける以下2つのUI問題の修正について記録します。

1. **チェックボックスレイアウト問題** - 資格チェックボックスのラベルが右端に押し出される
2. **求人地図表示問題** - iframeがセキュリティエラーで表示されない

---

## 1. チェックボックスレイアウト修正

### 問題の状況

「人材属性」タブ → 「人材組み合わせ分析」セクションにおいて、資格チェックボックスのレイアウトに問題がありました。

**症状**:
- チェックボックスが左端に配置
- ラベル（資格名）が右端に押し出される
- チェックボックスとラベルの間に大きな空白

### 原因分析

年代・性別のチェックボックスは `ui.checkbox(text, ...)` でテキストを直接渡していたのに対し、資格チェックボックスは `ui.row()` 内で `ui.checkbox()` と `ui.label()` を別々に配置していました。

```python
# 問題のあったコード（修正前）
with ui.row().classes("items-center gap-1"):
    ui.checkbox(on_change=lambda e, q=qual_name: ...)
    ui.label(label_text).style(...)
```

この方法では、flexboxのレイアウトにより要素間に意図しない空白が生じていました。

### 解決策

年代・性別チェックボックスと同じパターンに統一しました。

```python
# 修正後のコード (main.py:1430-1434)
label_text = f"{qual_name} ({qual_count:,}人)"
ui.checkbox(label_text, on_change=lambda e, q=qual_name: (
    rarity_state["qualifications"].append(q) if e.value else
    rarity_state["qualifications"].remove(q) if q in rarity_state["qualifications"] else None
)).classes("text-sm").style(f"color: {TEXT_COLOR};")
```

### DOM構造の比較

**修正前**:
```yaml
- generic:  # ui.row()
  - checkbox:
    - img
  - generic: 介護福祉士 (18人)  # 別要素
```

**修正後**:
```yaml
- checkbox "介護福祉士 (18人)":  # テキストがcheckbox内に含まれる
  - img
  - generic: 介護福祉士 (18人)
```

---

## 2. 求人地図表示修正

### 問題の状況

「求人地図」タブでGoogle Apps Script (GAS) のWebアプリをiframeで埋め込んでいましたが、表示されませんでした。

**エラーメッセージ**:
```
Refused to display 'https://script.google.com/' in a frame
because it set 'X-Frame-Options' to 'sameorigin'.
```

### 原因分析

GoogleはセキュリティのためGAS WebアプリのiframeへのURL埋め込みを禁止しています（X-Frame-Options: SAMEORIGIN）。これはGoogleのセキュリティポリシーであり、回避できません。

### 解決策

iframeを廃止し、新しいタブで開くボタン方式に変更しました。

**修正後のUI構成** (main.py:2153-2200):

1. **タイトル**: 「求人地図（GAS連携）」
2. **説明カード**: セキュリティ制限の説明
3. **操作エリア**:
   - 職種選択ドロップダウン（介護職など）
   - 「🗺️ 求人地図を開く」ボタン
4. **機能一覧カード**: 求人地図の機能説明

```python
# 修正後のコード概要
with ui.card().classes("p-4 mb-4"):
    ui.label("⚠️ Googleのセキュリティ制限により、求人地図は新しいタブで開きます")
    ui.label("下のボタンをクリックすると、求人地図が新しいタブで表示されます。")

with ui.row().classes("items-center gap-4 mb-4"):
    ui.select(options=list(gas_urls.keys()), value=current_job, label="職種", ...)
    ui.button("🗺️ 求人地図を開く",
        on_click=lambda: ui.run_javascript(f'window.open("{gas_urls[current_job]}", "_blank")')
    ).classes("bg-blue-600 text-white px-6 py-2").props("unelevated")
```

### GAS URLの管理

```python
gas_urls = {
    "介護職": "https://script.google.com/macros/s/AKfycby.../exec",
}
```

将来的に他の職種を追加する場合は、このdictに追加するだけで対応できます。

---

## 変更ファイル

| ファイル | 変更内容 |
|----------|----------|
| `main.py` | チェックボックスパターン変更、求人地図タブ全面改修 |
| `db_helper.py` | 関連するデータ取得機能の調整 |

## コミット情報

- **コミットハッシュ**: `8db8598`
- **コミットメッセージ**: Fix checkbox layout and job map display
- **ブランチ**: main
- **日時**: 2025-12-26

## デプロイ

- **プラットフォーム**: Render
- **自動デプロイ**: GitHub main ブランチへのプッシュで自動開始
- **URL**: https://nicegui-mapcomplete-dashboard.onrender.com

---

## 検証結果

### チェックボックスレイアウト

| 項目 | 修正前 | 修正後 |
|------|--------|--------|
| 年代チェックボックス | ✅ 正常 | ✅ 正常 |
| 性別チェックボックス | ✅ 正常 | ✅ 正常 |
| 資格チェックボックス | ❌ ラベル離れ | ✅ 正常 |

### 求人地図タブ

| 項目 | 修正前 | 修正後 |
|------|--------|--------|
| 表示方式 | iframe | 新しいタブ |
| 表示状態 | ❌ エラー | ✅ 正常 |
| ユーザー体験 | 不可 | ボタンクリックで地図表示 |

---

## スクリーンショット

修正後のスクリーンショットは以下に保存されています:

- `.playwright-mcp/checkbox_layout_fixed.png` - チェックボックスレイアウト
- `.playwright-mcp/jobmap_tab_fixed.png` - 求人地図タブ

---

## 今後の改善案

1. **求人地図の職種拡充**: 現在は介護職のみ。他職種のGAS URLを追加可能
2. **埋め込み表示の代替案**: GASの代わりにLeaflet/Mapboxを使用したネイティブ地図実装

---

## 関連ドキュメント

- `DROPDOWN_FIX_REPORT_20251224.md` - ドロップダウン修正レポート
- `SYSTEM_OVERVIEW_20251225.md` - システム概要
- `REFLEX_TO_NICEGUI_MAPPING.md` - Reflex→NiceGUI移行マッピング
