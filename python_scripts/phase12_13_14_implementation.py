"""
Phase 12, 13, 14の実装コード

run_complete_v2_perfect.pyに追加するコード
"""

def export_phase12(self, output_dir='data/output_v2/phase12'):
    """Phase 12: 需給ギャップ分析のエクスポート"""
    print("\n[PHASE12] Phase 12: 需給ギャップ分析")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. データ生成
    supply_demand_gap = self._generate_supply_demand_gap()

    # 2. 品質ゲートチェック
    save_data, quality_score = self._check_quality_gate(supply_demand_gap, 12, "需給ギャップ分析", mode='descriptive')

    if not save_data:
        print(f"  [SKIP] Phase 12をスキップしました")
        return

    # 3. CSV保存
    supply_demand_gap.to_csv(output_path / 'SupplyDemandGap.csv', index=False, encoding='utf-8-sig')
    print(f"  [OK] SupplyDemandGap.csv: {len(supply_demand_gap)}件")

    # 4. 品質レポート保存
    self._save_quality_report(supply_demand_gap, 12, output_path, mode='descriptive')

    report = self.validator_descriptive.generate_quality_report(supply_demand_gap)
    self.validator_descriptive.export_quality_report_csv(report, str(output_path / 'P12_QualityReport.csv'))
    print(f"  [OK] P12_QualityReport.csv")

    print(f"  [OK] Phase 12完了（品質スコア: {quality_score:.1f}/100）")
    print(f"  [DIR] 出力先: {output_path}")


def export_phase13(self, output_dir='data/output_v2/phase13'):
    """Phase 13: 希少性スコアのエクスポート"""
    print("\n[PHASE13] Phase 13: 希少性スコア")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. データ生成
    rarity_score = self._generate_rarity_score()

    # 2. 品質ゲートチェック
    save_data, quality_score = self._check_quality_gate(rarity_score, 13, "希少性スコア", mode='descriptive')

    if not save_data:
        print(f"  [SKIP] Phase 13をスキップしました")
        return

    # 3. CSV保存
    rarity_score.to_csv(output_path / 'RarityScore.csv', index=False, encoding='utf-8-sig')
    print(f"  [OK] RarityScore.csv: {len(rarity_score)}件")

    # 4. 品質レポート保存
    self._save_quality_report(rarity_score, 13, output_path, mode='descriptive')

    report = self.validator_descriptive.generate_quality_report(rarity_score)
    self.validator_descriptive.export_quality_report_csv(report, str(output_path / 'P13_QualityReport.csv'))
    print(f"  [OK] P13_QualityReport.csv")

    print(f"  [OK] Phase 13完了（品質スコア: {quality_score:.1f}/100）")
    print(f"  [DIR] 出力先: {output_path}")


def export_phase14(self, output_dir='data/output_v2/phase14'):
    """Phase 14: 競合分析のエクスポート"""
    print("\n[PHASE14] Phase 14: 競合分析")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. データ生成
    competition_profile = self._generate_competition_profile()

    # 2. 品質ゲートチェック
    save_data, quality_score = self._check_quality_gate(competition_profile, 14, "競合分析", mode='descriptive')

    if not save_data:
        print(f"  [SKIP] Phase 14をスキップしました")
        return

    # 3. CSV保存
    competition_profile.to_csv(output_path / 'CompetitionProfile.csv', index=False, encoding='utf-8-sig')
    print(f"  [OK] CompetitionProfile.csv: {len(competition_profile)}件")

    # 4. 品質レポート保存
    self._save_quality_report(competition_profile, 14, output_path, mode='descriptive')

    report = self.validator_descriptive.generate_quality_report(competition_profile)
    self.validator_descriptive.export_quality_report_csv(report, str(output_path / 'P14_QualityReport.csv'))
    print(f"  [OK] P14_QualityReport.csv")

    print(f"  [OK] Phase 14完了（品質スコア: {quality_score:.1f}/100）")
    print(f"  [DIR] 出力先: {output_path}")


# ===========================================
# Phase 12, 13, 14 ヘルパーメソッド
# ===========================================

def _generate_supply_demand_gap(self):
    """需給ギャップ分析データを生成（MAP統合対応）"""

    # 各市町村への需要（希望者数）
    demand_list = []
    for idx, row in self.processed_data.iterrows():
        for area in row['desired_areas']:
            demand_list.append({
                'prefecture': area['prefecture'],
                'municipality': area['municipality'] if area['municipality'] else '',
                'location': area['full']
            })

    demand_df = pd.DataFrame(demand_list)
    demand = demand_df.groupby('location').size().reset_index(name='demand_count')

    # 各市町村からの供給（居住者数）
    # 修正: location フォーマットを demand と同じ形式（都道府県+市町村）に統一
    supply_list = []
    for idx, row in self.processed_data.iterrows():
        if row['residence_pref'] and row['residence_muni']:
            location = f"{row['residence_pref']}{row['residence_muni']}"
            supply_list.append({'location': location})

    if supply_list:
        supply_df = pd.DataFrame(supply_list)
        supply = supply_df.groupby('location').size().reset_index(name='supply_count')
    else:
        supply = pd.DataFrame(columns=['location', 'supply_count'])

    # 需給マッチング
    gap = pd.merge(demand, supply, on='location', how='outer').fillna(0)
    gap['demand_supply_ratio'] = gap['demand_count'] / (gap['supply_count'] + 1)
    gap['gap'] = gap['demand_count'] - gap['supply_count']

    # 都道府県・市町村に分割
    gap[['prefecture', 'municipality']] = gap['location'].str.extract(r'^([\u4e00-\u9fff]{2,3}[都道府県])(.*)$')
    gap['municipality'] = gap['municipality'].fillna('')

    # 座標を追加（MAP統合用）
    gap['latitude'] = None
    gap['longitude'] = None

    for idx, row in gap.iterrows():
        location_key = row['location']
        if location_key in self.municipality_coords:
            lat, lon = self.municipality_coords[location_key]
            gap.at[idx, 'latitude'] = lat
            gap.at[idx, 'longitude'] = lon
        elif location_key in self.geocache:
            cache_data = self.geocache[location_key]
            gap.at[idx, 'latitude'] = cache_data.get('latitude')
            gap.at[idx, 'longitude'] = cache_data.get('longitude')

    # カラム順序を整理（MAP統合に適した形式）
    gap = gap[['prefecture', 'municipality', 'location', 'demand_count', 'supply_count',
               'demand_supply_ratio', 'gap', 'latitude', 'longitude']]

    return gap.sort_values('demand_supply_ratio', ascending=False)


def _generate_rarity_score(self):
    """希少性スコアを生成（MAP統合対応）"""

    # 希望勤務地を展開
    desired_list = []
    for idx, row in self.processed_data.iterrows():
        for area in row['desired_areas']:
            desired_list.append({
                'location': area['full'],
                'prefecture': area['prefecture'],
                'municipality': area['municipality'] if area['municipality'] else '',
                'age_bucket': row['age_bucket'],
                'gender': row['gender'],
                'has_national_license': row['has_national_license']
            })

    desired_df = pd.DataFrame(desired_list)

    # 市町村 × 年齢層 × 性別 × 国家資格でグループ化
    rarity = desired_df.groupby(['location', 'prefecture', 'municipality',
                                   'age_bucket', 'gender', 'has_national_license']).size().reset_index(name='count')

    # 希少性スコア = 1 / count
    rarity['rarity_score'] = 1 / rarity['count']

    # ランク付け
    def get_rarity_rank(score):
        if score >= 1.0:
            return 'S: 超希少（1人のみ）'
        elif score >= 0.5:
            return 'A: 非常に希少（2人）'
        elif score >= 0.2:
            return 'B: 希少（3-5人）'
        elif score >= 0.05:
            return 'C: やや希少（6-20人）'
        else:
            return 'D: 一般的（20人超）'

    rarity['rarity_rank'] = rarity['rarity_score'].apply(get_rarity_rank)

    # 座標を追加（MAP統合用）
    rarity['latitude'] = None
    rarity['longitude'] = None

    for idx, row in rarity.iterrows():
        location_key = row['location']
        if location_key in self.municipality_coords:
            lat, lon = self.municipality_coords[location_key]
            rarity.at[idx, 'latitude'] = lat
            rarity.at[idx, 'longitude'] = lon
        elif location_key in self.geocache:
            cache_data = self.geocache[location_key]
            rarity.at[idx, 'latitude'] = cache_data.get('latitude')
            rarity.at[idx, 'longitude'] = cache_data.get('longitude')

    # カラム順序を整理
    rarity = rarity[['prefecture', 'municipality', 'location', 'age_bucket', 'gender',
                     'has_national_license', 'count', 'rarity_score', 'rarity_rank',
                     'latitude', 'longitude']]

    return rarity.sort_values('rarity_score', ascending=False)


def _generate_competition_profile(self):
    """競合分析データを生成（MAP統合対応）"""

    # 希望勤務地を展開
    desired_list = []
    for idx, row in self.processed_data.iterrows():
        for area in row['desired_areas']:
            desired_list.append({
                'location': area['full'],
                'prefecture': area['prefecture'],
                'municipality': area['municipality'] if area['municipality'] else '',
                'age_bucket': row['age_bucket'],
                'gender': row['gender'],
                'has_national_license': row['has_national_license'],
                'employment_status': row['employment_status'],
                'qualification_count': row['qualification_count']
            })

    desired_df = pd.DataFrame(desired_list)

    # 市町村ごとに集計
    results = []

    for location in desired_df['location'].unique():
        muni_data = desired_df[desired_df['location'] == location]

        if len(muni_data) == 0:
            continue

        # 基本統計
        total_count = len(muni_data)

        # 年齢層分布（最も多い年齢層）
        age_dist = muni_data['age_bucket'].value_counts()
        top_age = age_dist.index[0] if len(age_dist) > 0 else None
        top_age_count = age_dist.iloc[0] if len(age_dist) > 0 else 0
        top_age_ratio = top_age_count / total_count if total_count > 0 else 0

        # 性別分布
        gender_dist = muni_data['gender'].value_counts()
        female_count = gender_dist.get('女性', 0)
        male_count = gender_dist.get('男性', 0)
        female_ratio = female_count / total_count if total_count > 0 else 0

        # 国家資格保有率
        national_license_rate = muni_data['has_national_license'].mean()

        # 就業状態分布（最も多い状態）
        emp_dist = muni_data['employment_status'].value_counts()
        top_employment = emp_dist.index[0] if len(emp_dist) > 0 else None
        top_employment_count = emp_dist.iloc[0] if len(emp_dist) > 0 else 0
        top_employment_ratio = top_employment_count / total_count if total_count > 0 else 0

        # 平均資格数
        avg_qualification = muni_data['qualification_count'].mean()

        # 都道府県・市町村
        prefecture = muni_data['prefecture'].iloc[0] if len(muni_data) > 0 else ''
        municipality = muni_data['municipality'].iloc[0] if len(muni_data) > 0 else ''

        results.append({
            'prefecture': prefecture,
            'municipality': municipality,
            'location': location,
            'total_applicants': total_count,
            'top_age_group': top_age,
            'top_age_ratio': top_age_ratio,
            'female_ratio': female_ratio,
            'male_ratio': 1 - female_ratio,
            'national_license_rate': national_license_rate,
            'top_employment_status': top_employment,
            'top_employment_ratio': top_employment_ratio,
            'avg_qualification_count': avg_qualification
        })

    competition_df = pd.DataFrame(results)

    # 座標を追加（MAP統合用）
    competition_df['latitude'] = None
    competition_df['longitude'] = None

    for idx, row in competition_df.iterrows():
        location_key = row['location']
        if location_key in self.municipality_coords:
            lat, lon = self.municipality_coords[location_key]
            competition_df.at[idx, 'latitude'] = lat
            competition_df.at[idx, 'longitude'] = lon
        elif location_key in self.geocache:
            cache_data = self.geocache[location_key]
            competition_df.at[idx, 'latitude'] = cache_data.get('latitude')
            competition_df.at[idx, 'longitude'] = cache_data.get('longitude')

    # カラム順序を整理
    competition_df = competition_df[['prefecture', 'municipality', 'location', 'total_applicants',
                                     'top_age_group', 'top_age_ratio', 'female_ratio', 'male_ratio',
                                     'national_license_rate', 'top_employment_status', 'top_employment_ratio',
                                     'avg_qualification_count', 'latitude', 'longitude']]

    return competition_df.sort_values('total_applicants', ascending=False)
