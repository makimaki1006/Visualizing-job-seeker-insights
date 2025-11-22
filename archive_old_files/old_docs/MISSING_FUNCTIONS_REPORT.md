# 存在しない関数レポート

## MenuIntegration.gsで呼ばれているが定義が存在しない関数

| 関数名 | メニュー表示名 | 状態 |
|--------|--------------|------|
| `showMapBubble` | 🗺️ 地図表示（バブル） | ❌ 存在しない |
| `showMapHeatmap` | 📍 地図表示（ヒートマップ） | ❌ 存在しない |
| `showChiSquareTests` | 🔬 カイ二乗検定結果 | ❌ 存在しない |
| `showANOVATests` | 📊 ANOVA検定結果 | ❌ 存在しない |
| `showPersonaSummary` | 👥 ペルソナサマリー | ❌ 存在しない |
| `showPersonaDetails` | 📋 ペルソナ詳細 | ❌ 存在しない |
| `showFlowAnalysis` | 🔀 自治体間フロー分析 | ❌ 存在しない |
| `showProximityAnalysis` | 🏘️ 移動パターン分析 | ❌ 存在しない |
| `showFlowProximityDashboard` | 🎯 フロー・移動統合ビュー | ❌ 存在しない |
| `checkMapData` | 🔍 データ確認 | ❌ 存在しない |
| `showStatsSummary` | 📊 統計サマリー | ❌ 存在しない |
| `clearAllData` | 🧹 全データクリア | ❌ 存在しない |
| `showDebugLog` | 🐛 デバッグログ | ❌ 存在しない |
| `analyzeDesiredColumns` | 🔧 カラム分析 | ❌ 存在しない |

## 既存の関数で代替可能なもの

| 存在しない関数 | 既存の代替関数 | 備考 |
|--------------|--------------|------|
| `showMapBubble` | `showPersonaMapVisualization` | ペルソナマップが最も近い |
| `showMapHeatmap` | なし | 実装が必要 |
| `showFlowAnalysis` | `showMunicipalityFlowNetworkVisualization` | 既に実装済み |
| `showProximityAnalysis` | なし | Phase 6機能、実装必要 |
| `showFlowProximityDashboard` | なし | 統合ダッシュボード、実装必要 |
| `showChiSquareTests` | なし | Phase 2機能、実装必要 |
| `showANOVATests` | なし | Phase 2機能、実装必要 |
| `showPersonaSummary` | なし | Phase 3機能、実装必要 |
| `showPersonaDetails` | なし | Phase 3機能、実装必要 |

## 推奨対応

### 即座に対応（MenuIntegration.gsを修正）

1. **存在しない関数を削除または既存関数に置き換え**
2. **MinimalMenuIntegration.gsで置き換え**（既存関数のみ使用）

### 長期対応（機能実装）

Phase 2, 3, 6の可視化機能を実装する必要があります。
