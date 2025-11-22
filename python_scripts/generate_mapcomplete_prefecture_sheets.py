"""
都道府県別MapComplete統合シート生成スクリプト

全Phaseのデータを都道府県別にまとめた統合CSVを生成します。
これにより、GAS側は1シートのみ読み込めば全データを取得できます。
"""

import pandas as pd
import json
from pathlib import Path
from collections import defaultdict


class MapCompletePrefectureSheetGenerator:
    """都道府県別MapComplete統合シート生成クラス"""

    def __init__(self, output_base_dir='data/output_v2'):
        self.output_base_dir = Path(output_base_dir)
        self.mapcomplete_dir = self.output_base_dir / 'mapcomplete_sheets'
        self.mapcomplete_dir.mkdir(exist_ok=True)

        # 各PhaseのデータをDataFrameとして保持
        self.phase_data = {}

    def load_all_phases(self):
        """全PhaseのCSVデータを読み込む"""
        print("\n[LOAD] 全Phaseデータ読み込み開始...")

        # Phase 1
        self._load_phase('phase1', [
            'Phase1_MapMetrics.csv',
            'Phase1_Applicants.csv',
            'Phase1_DesiredWork.csv'
        ])

        # Phase 3
        self._load_phase('phase3', [
            'Phase3_PersonaSummary.csv',
            'Phase3_PersonaDetails.csv',
            'Phase3_PersonaSummaryByMunicipality.csv'
        ])

        # Phase 6
        self._load_phase('phase6', [
            'Phase6_MunicipalityFlowEdges.csv',
            'Phase6_MunicipalityFlowNodes.csv',
            'Phase6_ProximityAnalysis.csv'
        ])

        # Phase 7
        self._load_phase('phase7', [
            'Phase7_SupplyDensityMap.csv',
            'Phase7_AgeGenderCrossAnalysis.csv',
            'Phase7_DetailedPersonaProfile.csv',
            'Phase7_MobilityScore.csv'
        ])

        # Phase 8
        self._load_phase('phase8', [
            'Phase8_GraduationYearDistribution.csv',
            'Phase8_CareerDistribution.csv',
            'Phase8_CareerAgeCross_Matrix.csv'
        ])

        # Phase 10
        self._load_phase('phase10', [
            'Phase10_UrgencyDistribution.csv',
            'Phase10_UrgencyAgeCross.csv',
            'Phase10_UrgencyAgeCross_Matrix.csv',
            'Phase10_UrgencyEmploymentCross.csv',
            'Phase10_UrgencyEmploymentCross_Matrix.csv',
            'Phase10_UrgencyByMunicipality.csv'
        ])

        # Phase 12-14（Phase 12-14統合ダッシュボード用）
        self._load_phase('phase12', [
            'Phase12_SupplyDemandGap.csv'
        ])
        self._load_phase('phase13', [
            'Phase13_RarityScore.csv'
        ])
        self._load_phase('phase14', [
            'Phase14_CompetitionProfile.csv'
        ])

        print("  [OK] 全Phaseデータ読み込み完了\n")

    def _load_phase(self, phase_name, csv_files):
        """個別Phaseのデータ読み込み"""
        phase_dir = self.output_base_dir / phase_name
        self.phase_data[phase_name] = {}

        for csv_file in csv_files:
            file_path = phase_dir / csv_file
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path, encoding='utf-8-sig')
                    key = csv_file.replace('.csv', '').replace('Phase1_', '').replace('Phase3_', '').replace('Phase6_', '').replace('Phase7_', '').replace('Phase8_', '').replace('Phase10_', '').replace('Phase12_', '').replace('Phase13_', '').replace('Phase14_', '')
                    self.phase_data[phase_name][key] = df
                    print(f"  [OK] {phase_name}/{csv_file}: {len(df)}行")
                except Exception as e:
                    print(f"  [WARN] {phase_name}/{csv_file}: 読み込みエラー - {e}")
            else:
                print(f"  [SKIP] {phase_name}/{csv_file}: ファイルなし")

    def generate_prefecture_sheets(self):
        """都道府県別統合シート生成"""
        print("\n[GENERATE] 都道府県別統合シート生成開始...")

        # Phase1のMapMetricsから都道府県リストを取得
        map_metrics = self.phase_data.get('phase1', {}).get('MapMetrics')
        if map_metrics is None or map_metrics.empty:
            print("  [ERROR] MapMetricsが見つかりません")
            return

        # 都道府県列名の候補
        pref_cols = ['prefecture', 'residence_pref', '都道府県', '居住都道府県']
        pref_col = None
        for col in pref_cols:
            if col in map_metrics.columns:
                pref_col = col
                break

        if pref_col is None:
            print(f"  [ERROR] 都道府県列が見つかりません。利用可能な列: {list(map_metrics.columns)}")
            return

        # 都道府県リスト取得
        prefectures = map_metrics[pref_col].dropna().unique()
        print(f"  [INFO] 都道府県数: {len(prefectures)}件")

        # 都道府県別に統合CSV生成
        for prefecture in prefectures:
            self._generate_single_prefecture_sheet(prefecture, pref_col)

        print(f"\n  [OK] 都道府県別統合シート生成完了: {self.mapcomplete_dir}")

    def _generate_single_prefecture_sheet(self, prefecture, pref_col):
        """単一都道府県の統合シート生成"""
        print(f"\n  [GENERATE] {prefecture} の統合シート生成中...")

        # Phase1_MapMetricsから該当都道府県のデータを抽出（ベース）
        map_metrics = self.phase_data.get('phase1', {}).get('MapMetrics')
        if map_metrics is None or map_metrics.empty:
            print(f"    [SKIP] {prefecture}: MapMetricsなし")
            return

        if pref_col not in map_metrics.columns:
            print(f"    [ERROR] {prefecture}: {pref_col}列なし")
            return

        # 該当都道府県のデータのみ抽出
        base_df = map_metrics[map_metrics[pref_col] == prefecture].copy()

        if base_df.empty:
            print(f"    [SKIP] {prefecture}: データなし")
            return

        print(f"    - MapMetrics: {len(base_df)}行（ベース）")

        # 結合キー: location_key
        if 'location_key' not in base_df.columns:
            print(f"    [ERROR] {prefecture}: location_key列なし")
            return

        # Phase7_SupplyDensityMapを結合
        supply_density = self.phase_data.get('phase7', {}).get('SupplyDensityMap')
        if supply_density is not None and not supply_density.empty and 'location' in supply_density.columns:
            # location列をlocation_keyにリネーム
            supply_density_renamed = supply_density.rename(columns={'location': 'location_key'})
            # カラム名の重複を避けるため、プレフィックス追加
            supply_cols = {col: f'phase7_{col}' for col in supply_density_renamed.columns if col not in ['location_key']}
            supply_density_renamed = supply_density_renamed.rename(columns=supply_cols)
            # left join
            base_df = base_df.merge(supply_density_renamed, on='location_key', how='left')
            print(f"    - Phase7_SupplyDensityMap: 結合完了")

        # Phase3_PersonaSummaryByMunicipalityを結合（市区町村ごとの代表ペルソナのみ）
        persona_by_muni = self.phase_data.get('phase3', {}).get('PersonaSummaryByMunicipality')
        if persona_by_muni is not None and not persona_by_muni.empty and 'municipality' in persona_by_muni.columns:
            # 市区町村ごとに最も多いペルソナを抽出
            top_persona = persona_by_muni.loc[persona_by_muni.groupby('municipality')['count'].idxmax()].copy()
            # municipality列をlocation_keyにリネーム
            top_persona = top_persona.rename(columns={'municipality': 'location_key'})
            # カラム名の重複を避けるため、プレフィックス追加
            persona_cols = {col: f'phase3_top_{col}' for col in top_persona.columns if col not in ['location_key']}
            top_persona = top_persona.rename(columns=persona_cols)
            # left join
            base_df = base_df.merge(top_persona, on='location_key', how='left')
            print(f"    - Phase3_PersonaSummaryByMunicipality（代表ペルソナ）: 結合完了")

        # Phase 6: Flow分析データを結合（市区町村レベル）
        # Phase6_MunicipalityFlowNodes（市区町村間フローノード）
        flow_nodes = self.phase_data.get('phase6', {}).get('MunicipalityFlowNodes')
        if flow_nodes is not None and not flow_nodes.empty:
            # 都道府県で絞り込み
            if 'prefecture' in flow_nodes.columns and 'municipality' in flow_nodes.columns:
                flow_filtered = flow_nodes[flow_nodes['prefecture'] == prefecture].copy()
                if not flow_filtered.empty:
                    # municipalityをlocation_keyにリネーム
                    flow_renamed = flow_filtered.rename(columns={'municipality': 'location_key'})
                    # カラム名の重複を避けるため、プレフィックス追加
                    flow_cols = {col: f'phase6_{col}' for col in flow_renamed.columns if col not in ['location_key', 'prefecture', 'location']}
                    flow_renamed = flow_renamed.rename(columns=flow_cols)
                    # left join
                    base_df = base_df.merge(flow_renamed[['location_key'] + [c for c in flow_renamed.columns if c.startswith('phase6_')]], on='location_key', how='left')
                    print(f"    - Phase6_MunicipalityFlowNodes: 結合完了")

        # Phase 8: 学歴分析データ（全国レベルのため除外）
        # Phase8_GraduationYearDistributionは都道府県・市区町村の列がないため、
        # 市区町村レベルの統合シートには含めない

        # Phase 10: 緊急度分析データを結合（市区町村レベル）
        # Phase10_UrgencyByMunicipality
        urgency_muni = self.phase_data.get('phase10', {}).get('UrgencyByMunicipality')
        if urgency_muni is not None and not urgency_muni.empty and 'location' in urgency_muni.columns:
            urgency_renamed = urgency_muni.rename(columns={'location': 'location_key'})
            urgency_cols = {col: f'phase10_{col}' for col in urgency_renamed.columns if col not in ['location_key']}
            urgency_renamed = urgency_renamed.rename(columns=urgency_cols)
            base_df = base_df.merge(urgency_renamed, on='location_key', how='left')
            print(f"    - Phase10_UrgencyByMunicipality: 結合完了")

        # Phase 12-14データを結合（Phase 12-14統合ダッシュボード用）
        # Phase 13: RarityScore（市区町村レベル）
        rarity_score = self.phase_data.get('phase13', {}).get('RarityScore')
        if rarity_score is not None and not rarity_score.empty:
            # 市区町村ごとに最高希少性スコアを抽出
            if 'municipality' in rarity_score.columns and 'rarity_score' in rarity_score.columns:
                top_rarity = rarity_score.loc[rarity_score.groupby('municipality')['rarity_score'].idxmax()].copy()
                top_rarity = top_rarity.rename(columns={'municipality': 'location_key'})
                rarity_cols = {col: f'phase13_{col}' for col in top_rarity.columns if col not in ['location_key', 'prefecture']}
                top_rarity = top_rarity.rename(columns=rarity_cols)
                base_df = base_df.merge(top_rarity[['location_key'] + [c for c in top_rarity.columns if c.startswith('phase13_')]], on='location_key', how='left')
                print(f"    - Phase13_RarityScore: 結合完了")

        # Phase 14: CompetitionProfile（市区町村レベル）
        competition = self.phase_data.get('phase14', {}).get('CompetitionProfile')
        if competition is not None and not competition.empty and 'municipality' in competition.columns:
            competition_renamed = competition.rename(columns={'municipality': 'location_key'})
            comp_cols = {col: f'phase14_{col}' for col in competition_renamed.columns if col not in ['location_key', 'prefecture']}
            competition_renamed = competition_renamed.rename(columns=comp_cols)
            base_df = base_df.merge(competition_renamed, on='location_key', how='left')
            print(f"    - Phase14_CompetitionProfile: 結合完了")

        # Phase 12: SupplyDemandGap（都道府県レベル）- 全市区町村に同じ値をブロードキャスト
        supply_demand = self.phase_data.get('phase12', {}).get('SupplyDemandGap')
        if supply_demand is not None and not supply_demand.empty and pref_col in supply_demand.columns:
            pref_data = supply_demand[supply_demand[pref_col] == prefecture].copy()
            if not pref_data.empty:
                # 都道府県レベルのデータを全行に追加
                for col in pref_data.columns:
                    if col not in [pref_col, 'municipality', 'location', 'latitude', 'longitude']:
                        base_df[f'phase12_{col}'] = pref_data[col].iloc[0]
                print(f"    - Phase12_SupplyDemandGap（都道府県レベル）: 結合完了")

        # CSV出力
        safe_prefecture = prefecture.replace('/', '_').replace('\\', '_')
        output_file = self.mapcomplete_dir / f'MapComplete_{safe_prefecture}.csv'
        base_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"    [OK] 出力完了: {output_file} ({len(base_df)}行 × {len(base_df.columns)}列)")


def main():
    """メイン処理"""
    print(f"\n{'='*60}")
    print(f"  都道府県別MapComplete統合シート生成")
    print(f"{'='*60}")

    generator = MapCompletePrefectureSheetGenerator()
    generator.load_all_phases()
    generator.generate_prefecture_sheets()

    print(f"\n{'='*60}")
    print(f"  [OK] 処理完了")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
