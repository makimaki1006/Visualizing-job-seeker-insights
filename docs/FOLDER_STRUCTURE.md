# フォルダ構成ガイド（Regional Dashboard 関連）

```
project-root/
├── apps_script_bundle/              # GAS への貼り付け用バンドル
│   ├── README.md
│   ├── regional_dashboard.gs
│   ├── regional_dashboard_with_map.html
│   ├── all_scripts_bundle.gs
│   ├── all_html_bundle.html
│   ├── production_scripts_bundle.gs   # gas_files_production/scripts/ の結合結果
│   ├── production_html_bundle.html    # gas_files_production/html/ の結合結果
│   └── phases/                        # フェーズ単位のバンドル
│       ├── phase1_core.gs
│       ├── phase2_phase3_viz.gs
│       ├── phase6_flow.gs
│       ├── phase7_import.gs
│       ├── phase7_visualization.gs
│       ├── phase8_career.gs
│       ├── phase10_urgency.gs
│       ├── persona_tools.gs
│       └── integration_core.gs
│
├── dist/                            # 自動生成ファイル（ビルド結果）
│   ├── regional_dashboard.gs
│   ├── regional_dashboard.html
│   ├── regional_dashboard_with_map.html
│   ├── all_scripts_bundle.gs
│   ├── all_html_bundle.html
│   ├── production_scripts_bundle.gs
│   └── production_html_bundle.html
│
├── gas_files/                       # 開発用ソース
│   ├── scripts/
│   │   ├── RegionStateService.gs
│   │   ├── RegionDashboard.gs
│   │   ├── MapVisualization.gs
│   │   └── ...
│   └── html/
│       ├── RegionalDashboard.html
│       ├── MapComplete.html
│       └── ...
│
├── gas_files_production/            # 運用用ソース（今回の正規取り込み先）
│   ├── scripts/
│   │   ├── DataValidationEnhanced.gs
│   │   ├── MapVisualization.gs
│   │   ├── Phase7SupplyDensityViz.gs
│   │   └── ...（全19本）
│   └── html/
│       ├── BubbleMap.html
│       ├── HeatMap.html
│       ├── RegionalDashboard.html
│       └── ...
│
├── tools/
│   └── build_regional_dashboard_bundle.js  # バンドル生成スクリプト（バックアップ: .bak）
│
├── docs/
│   ├── REGIONAL_DASHBOARD_HANDOVER.md
│   ├── REGIONAL_DASHBOARD_TEST_CHECKLIST.md
│   └── FOLDER_STRUCTURE.md（このファイル）
│
└── README.md
```

## 運用の流れ

1. `node tools/build_regional_dashboard_bundle.js` を実行すると `dist/` と `apps_script_bundle/` が更新されます。
2. GAS へ貼り付けるときは用途に合わせて以下を利用してください。
   - 全機能まとめて → `apps_script_bundle/production_scripts_bundle.gs` + `production_html_bundle.html`
   - Regional Dashboard 追加分のみ → `apps_script_bundle/regional_dashboard.gs` + `regional_dashboard_with_map.html`
   - 特定フェーズだけ → `apps_script_bundle/phases/*.gs`
3. 個別の `.gs` / `.html` を編集した場合は `gas_files/` または `gas_files_production/` を更新し、再度ビルドスクリプトを実行して反映します。
