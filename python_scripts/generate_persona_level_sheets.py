"""
都道府県別ペルソナレベル統合シート生成スクリプト

Phase3_PersonaSummaryByMunicipality（市区町村×ペルソナセグメント）をベースに、
全Phaseデータを統合した都道府県別CSVを生成します。

用途: ペルソナ難易度分析（年齢×性別×資格での絞り込み）
"""

import pandas as pd
from pathlib import Path


class PersonaLevelSheetGenerator:
    """ペルソナレベル統合シート生成クラス"""

    def __init__(self, output_base_dir='data/output_v2'):
        self.output_base_dir = Path(output_base_dir)
        self.persona_sheets_dir = self.output_base_dir / 'persona_level_sheets'
        self.persona_sheets_dir.mkdir(exist_ok=True)

        # 各PhaseのデータをDataFrameとして保持
        self.phase_data = {}

    def load_all_phases(self):
        """全PhaseのCSVデータを読み込む"""
        print("\n[LOAD] 全Phaseデータ読み込み開始...")

        # Phase 3: ペルソナサマリー（ベースデータ）
        self._load_phase('phase3', [
            'Phase3_PersonaSummaryByMunicipality.csv'
        ])

        # Phase 13: 希少性スコア（ペルソナレベル）
        self._load_phase('phase13', [
            'Phase13_RarityScore.csv'
        ])

        # Phase 6: フロー分析（市区町村レベル）
        self._load_phase('phase6', [
            'Phase6_MunicipalityFlowNodes.csv'
        ])

        # Phase 7: 供給密度（市区町村レベル）
        self._load_phase('phase7', [
            'Phase7_SupplyDensityMap.csv'
        ])

        # Phase 10: 緊急度分析（市区町村レベル）
        self._load_phase('phase10', [
            'Phase10_UrgencyByMunicipality.csv'
        ])

        # Phase 14: 競合分析（市区町村レベル）
        self._load_phase('phase14', [
            'Phase14_CompetitionProfile.csv'
        ])

        # Phase 12: 需給ギャップ（都道府県レベル）
        self._load_phase('phase12', [
            'Phase12_SupplyDemandGap.csv'
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
                    key = csv_file.replace('.csv', '').replace('Phase3_', '').replace('Phase6_', '').replace('Phase7_', '').replace('Phase10_', '').replace('Phase12_', '').replace('Phase13_', '').replace('Phase14_', '')
                    self.phase_data[phase_name][key] = df
                    print(f"  [OK] {phase_name}/{csv_file}: {len(df)}行")
                except Exception as e:
                    print(f"  [WARN] {phase_name}/{csv_file}: 読み込みエラー - {e}")
            else:
                print(f"  [SKIP] {phase_name}/{csv_file}: ファイルなし")

    def generate_prefecture_sheets(self):
        """都道府県別ペルソナレベル統合シート生成"""
        print("\n[GENERATE] 都道府県別ペルソナレベル統合シート生成開始...")

        # Phase13_RarityScoreから正しい都道府県リストを取得
        rarity_score = self.phase_data.get('phase13', {}).get('RarityScore')
        if rarity_score is None or rarity_score.empty or 'prefecture' not in rarity_score.columns:
            print("  [ERROR] Phase13_RarityScoreまたはprefecture列が見つかりません")
            return

        # 都道府県リスト取得（Phase13から）
        prefectures = rarity_score['prefecture'].dropna().unique()
        print(f"  [INFO] 都道府県数: {len(prefectures)}件")

        # Phase3にprefecture列を追加（Phase13からマッピング）
        persona_summary = self.phase_data.get('phase3', {}).get('PersonaSummaryByMunicipality')
        if persona_summary is None or persona_summary.empty:
            print("  [ERROR] PersonaSummaryByMunicipalityが見つかりません")
            return

        # Phase13のlocation→prefecture マッピングを作成
        # Phase13の'location'列を'municipality'にリネームしてマッピング
        # Phase3は完全な住所（都道府県+市区町村）を使用
        prefecture_map = rarity_score[['location', 'prefecture']].drop_duplicates()
        prefecture_map = prefecture_map.rename(columns={'location': 'municipality'})

        # デバッグ: マッピング前のサンプル確認
        print(f"  [DEBUG] Phase3 municipality サンプル: {persona_summary['municipality'].head(3).tolist()}")
        print(f"  [DEBUG] Phase13 location(→municipality) サンプル: {prefecture_map['municipality'].head(3).tolist()}")

        persona_summary = persona_summary.merge(prefecture_map, on='municipality', how='left')

        # デバッグ: マッピング後の確認
        null_count = persona_summary['prefecture'].isna().sum()
        print(f"  [DEBUG] マッピング後のprefecture欠損数: {null_count}/{len(persona_summary)}")
        if null_count > 0:
            print(f"  [WARN] マッピングに失敗した municipality: {persona_summary[persona_summary['prefecture'].isna()]['municipality'].head(5).tolist()}")

        self.phase_data['phase3']['PersonaSummaryByMunicipality'] = persona_summary

        # 都道府県別に統合CSV生成
        for prefecture in prefectures:
            self._generate_single_prefecture_sheet(prefecture)

        print(f"\n  [OK] 都道府県別ペルソナレベル統合シート生成完了: {self.persona_sheets_dir}")

    def _generate_single_prefecture_sheet(self, prefecture):
        """単一都道府県のペルソナレベル統合シート生成"""
        print(f"\n  [GENERATE] {prefecture} のペルソナレベル統合シート生成中...")

        # ベース: Phase3_PersonaSummaryByMunicipality（既にprefecture列を追加済み）
        persona_summary = self.phase_data.get('phase3', {}).get('PersonaSummaryByMunicipality')
        if persona_summary is None or persona_summary.empty:
            print(f"    [SKIP] {prefecture}: PersonaSummaryByMunicipalityなし")
            return

        # 該当都道府県のデータのみ抽出
        base_df = persona_summary[persona_summary['prefecture'] == prefecture].copy()

        if base_df.empty:
            print(f"    [SKIP] {prefecture}: データなし")
            return

        print(f"    - PersonaSummaryByMunicipality: {len(base_df)}行（ベース）")

        # Phase 13: RarityScore（ペルソナレベル - 完全マージ）
        rarity_score = self.phase_data.get('phase13', {}).get('RarityScore')
        if rarity_score is not None and not rarity_score.empty:
            # 都道府県で絞り込み
            if 'prefecture' in rarity_score.columns:
                rarity_filtered = rarity_score[rarity_score['prefecture'] == prefecture].copy()
                if not rarity_filtered.empty:
                    # Phase13のlocation列をmunicipalityにリネーム（完全な住所形式で一致させる）
                    # 元のmunicipality列（短縮形）は削除
                    rarity_filtered = rarity_filtered.drop(columns=['municipality'], errors='ignore')
                    rarity_filtered = rarity_filtered.rename(columns={
                        'location': 'municipality',
                        'age_bucket': 'age_group'
                    })

                    # カラム名プレフィックス追加
                    rarity_cols = {col: f'phase13_{col}' for col in rarity_filtered.columns
                                   if col not in ['municipality', 'age_group', 'gender', 'has_national_license', 'prefecture']}
                    rarity_filtered = rarity_filtered.rename(columns=rarity_cols)

                    # マージ
                    base_df = base_df.merge(
                        rarity_filtered,
                        on=['municipality', 'age_group', 'gender', 'has_national_license'],
                        how='left'
                    )
                    print(f"    - Phase13_RarityScore: 結合完了")

        # Phase 7: SupplyDensityMap（市区町村レベル - ブロードキャスト）
        supply_density = self.phase_data.get('phase7', {}).get('SupplyDensityMap')
        if supply_density is not None and not supply_density.empty:
            # location列をmunicipalityにリネーム
            supply_renamed = supply_density.rename(columns={'location': 'municipality'})
            # カラム名プレフィックス追加
            supply_cols = {col: f'phase7_{col}' for col in supply_renamed.columns if col not in ['municipality']}
            supply_renamed = supply_renamed.rename(columns=supply_cols)
            # マージ
            base_df = base_df.merge(supply_renamed, on='municipality', how='left')
            print(f"    - Phase7_SupplyDensityMap: 結合完了")

        # Phase 6: MunicipalityFlowNodes（市区町村レベル - ブロードキャスト）
        flow_nodes = self.phase_data.get('phase6', {}).get('MunicipalityFlowNodes')
        if flow_nodes is not None and not flow_nodes.empty:
            # 元のmunicipality列（短縮形）を削除
            flow_nodes = flow_nodes.drop(columns=['municipality'], errors='ignore')
            # location列をmunicipalityにリネーム（完全な住所形式で一致させる）
            flow_nodes = flow_nodes.rename(columns={'location': 'municipality'})
            # カラム名プレフィックス追加
            flow_cols = {col: f'phase6_{col}' for col in flow_nodes.columns if col not in ['municipality', 'prefecture']}
            flow_renamed = flow_nodes.rename(columns=flow_cols)
            # マージ
            base_df = base_df.merge(flow_renamed[['municipality'] + [c for c in flow_renamed.columns if c.startswith('phase6_')]], on='municipality', how='left')
            print(f"    - Phase6_MunicipalityFlowNodes: 結合完了")

        # Phase 10: UrgencyByMunicipality（市区町村レベル - ブロードキャスト）
        urgency_muni = self.phase_data.get('phase10', {}).get('UrgencyByMunicipality')
        if urgency_muni is not None and not urgency_muni.empty and 'location' in urgency_muni.columns:
            urgency_renamed = urgency_muni.rename(columns={'location': 'municipality'})
            urgency_cols = {col: f'phase10_{col}' for col in urgency_renamed.columns if col not in ['municipality']}
            urgency_renamed = urgency_renamed.rename(columns=urgency_cols)
            base_df = base_df.merge(urgency_renamed, on='municipality', how='left')
            print(f"    - Phase10_UrgencyByMunicipality: 結合完了")

        # Phase 14: CompetitionProfile（市区町村レベル - ブロードキャスト）
        competition = self.phase_data.get('phase14', {}).get('CompetitionProfile')
        if competition is not None and not competition.empty:
            # 元のmunicipality列（短縮形）を削除
            competition = competition.drop(columns=['municipality'], errors='ignore')
            # location列をmunicipalityにリネーム（完全な住所形式で一致させる）
            competition = competition.rename(columns={'location': 'municipality'})
            # カラム名プレフィックス追加
            comp_cols = {col: f'phase14_{col}' for col in competition.columns if col not in ['municipality', 'prefecture']}
            competition_renamed = competition.rename(columns=comp_cols)
            # マージ
            base_df = base_df.merge(competition_renamed, on='municipality', how='left')
            print(f"    - Phase14_CompetitionProfile: 結合完了")

        # Phase 12: SupplyDemandGap（都道府県レベル - 全行に同じ値をブロードキャスト）
        supply_demand = self.phase_data.get('phase12', {}).get('SupplyDemandGap')
        if supply_demand is not None and not supply_demand.empty and 'prefecture' in supply_demand.columns:
            pref_data = supply_demand[supply_demand['prefecture'] == prefecture].copy()
            if not pref_data.empty:
                # 都道府県レベルのデータを全行に追加
                for col in pref_data.columns:
                    if col not in ['prefecture', 'municipality', 'location', 'latitude', 'longitude']:
                        base_df[f'phase12_{col}'] = pref_data[col].iloc[0]
                print(f"    - Phase12_SupplyDemandGap（都道府県レベル）: 結合完了")

        # prefecture列の重複を整理（prefecture_x, prefecture_y, prefecture → prefecture）
        if 'prefecture' not in base_df.columns:
            if 'prefecture_x' in base_df.columns:
                base_df['prefecture'] = base_df['prefecture_x']
            elif 'prefecture_y' in base_df.columns:
                base_df['prefecture'] = base_df['prefecture_y']

        # 重複したprefecture列を削除
        cols_to_drop = [col for col in ['prefecture_x', 'prefecture_y'] if col in base_df.columns and col != 'prefecture']
        if cols_to_drop:
            base_df = base_df.drop(columns=cols_to_drop)

        # CSV出力
        safe_prefecture = prefecture.replace('/', '_').replace('\\', '_')
        output_file = self.persona_sheets_dir / f'PersonaLevel_{safe_prefecture}.csv'
        base_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"    [OK] 出力完了: {output_file} ({len(base_df)}行 × {len(base_df.columns)}列)")


def main():
    """メイン処理"""
    print(f"\n{'='*60}")
    print(f"  都道府県別ペルソナレベル統合シート生成")
    print(f"{'='*60}")

    generator = PersonaLevelSheetGenerator()
    generator.load_all_phases()
    generator.generate_prefecture_sheets()

    print(f"\n{'='*60}")
    print(f"  [OK] 処理完了")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
