# アーカイブ済みファイル

役割を終えた、または上位スクリプトに統合されたファイルをアーカイブしています。
必要に応じて復元可能です。

## アーカイブ日: 2026-03-18

---

## python_deprecated/

### process_job_type.py
- **元の機能**: 職種別データ処理パイプライン（V2分析→MapComplete生成→Tursoインポート）
- **経緯**: 2026-02-20に作成。run_complete_v2_perfect.pyとgenerate_mapcomplete_complete_sheets.pyの処理をラッパーとしてまとめたもの。git未コミットのまま放置されていた
- **廃止理由**: run_complete_v2_perfect.pyにスタンドアロンスクリプト統合（2026-03-18）で不要に。create_ready_csv.pyが後継
- **JOB_TYPE_PREFIX_MAPが5職種のみ定義** — 全職種に対応していなかった

### run_v2_all_jobtypes.py
- **元の機能**: 全職種のV2処理を順次実行し、各職種のMapComplete CSVを生成
- **経緯**: 看護師・保育士・生活相談員の3職種のみJOB_TYPESにハードコード。他職種は未対応
- **廃止理由**: run_complete_v2_perfect.pyが1職種ずつ処理する設計に統一。全職種一括実行の需要がなくなった
- **旧copy_mapcomplete_for_jobtypeのデータ混在バグ修正の記録が残っている**（コメントに経緯記載）

---

## nicegui_check_scripts/

NiceGUIダッシュボード開発期（2025-12〜2026-01）に作成されたデバッグ・検証用スクリプト群。
NiceGUIからRust Dashboardへの移行（2026-02〜03）に伴い不要になった。

### check_amakusa.py / check_amakusa_detail.py / check_amakusa_workstyle.py
- **用途**: 天草市のデータを個別検証（都道府県フィルタ・ワークスタイル表示のデバッグ）
- **経緯**: NiceGUI版ダッシュボードで天草市のデータ表示に問題が発生し、原因調査のために作成

### check_db_all_duplicates.py / check_db_duplicates.py / check_dup.py
- **用途**: Turso DB内の重複データ検出
- **経緯**: 2026-01-04〜05のDB重複事故（$70超過請求）の調査・修復に使用
- **後継**: turso_sync.pyのvalidateコマンドに統合済み

### check_db_all_jobtypes.py / check_job_type.py
- **用途**: Turso DB内の全職種データ件数確認
- **後継**: check_turso_jobtypes.py（2026-03-18作成、nicegui_app/に残存）

### check_db_correct_keys.py
- **用途**: Turso DB内の一意キー定義の整合性チェック
- **後継**: turso_sync.pyのvalidateコマンドに統合済み

### check_db_workstyle_all.py / check_workstyle.py
- **用途**: 雇用形態データの分布確認（正職員/パート/バイト）
- **経緯**: WORKSTYLE_DISTRIBUTION row_typeのデバッグに使用
