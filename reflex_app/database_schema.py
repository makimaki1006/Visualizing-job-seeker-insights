"""
SQLiteデータベーススキーマ定義

無料で使えるSQLiteを使用したデータベーススキーマ。
CSV形式からデータベースへの移行を実現。
"""

# データベース設計
DATABASE_SCHEMA = {
    # ===========================
    # Phase 1: 基礎集計データ
    # ===========================
    "applicants": {
        "description": "申請者基本情報",
        "columns": [
            ("applicant_id", "INTEGER PRIMARY KEY"),
            ("age", "INTEGER"),
            ("gender", "TEXT"),
            ("age_group", "TEXT"),
            ("residence_prefecture", "TEXT"),
            ("residence_municipality", "TEXT"),
            ("desired_area_count", "INTEGER"),
            ("qualification_count", "INTEGER"),
            ("has_national_license", "BOOLEAN"),
            ("qualifications", "TEXT"),
            ("desired_workstyle", "TEXT"),
            ("desired_start", "TEXT"),
            ("desired_job", "TEXT"),
            ("career", "TEXT"),
            ("employment_status", "TEXT"),
            ("status", "TEXT"),
            ("member_id", "INTEGER"),
        ],
        "indexes": [
            "CREATE INDEX idx_residence ON applicants(residence_prefecture, residence_municipality)",
            "CREATE INDEX idx_age_group ON applicants(age_group)",
            "CREATE INDEX idx_gender ON applicants(gender)",
            "CREATE INDEX idx_has_national_license ON applicants(has_national_license)",
        ],
    },
    "desired_work": {
        "description": "希望勤務地詳細",
        "columns": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("applicant_id", "INTEGER"),
            ("desired_prefecture", "TEXT"),
            ("desired_municipality", "TEXT"),
            ("desired_job", "TEXT"),
            ("FOREIGN KEY (applicant_id)", "REFERENCES applicants(applicant_id)"),
        ],
        "indexes": [
            "CREATE INDEX idx_desired_location ON desired_work(desired_prefecture, desired_municipality)",
        ],
    },
    "agg_desired": {
        "description": "希望勤務地集計",
        "columns": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("prefecture", "TEXT"),
            ("municipality", "TEXT"),
            ("count", "INTEGER"),
        ],
        "indexes": [
            "CREATE INDEX idx_location ON agg_desired(prefecture, municipality)",
        ],
    },
    "map_metrics": {
        "description": "地図表示用メトリクス（座標付き）",
        "columns": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("prefecture", "TEXT"),
            ("municipality", "TEXT"),
            ("count", "INTEGER"),
            ("latitude", "REAL"),
            ("longitude", "REAL"),
        ],
        "indexes": [
            "CREATE INDEX idx_map_location ON map_metrics(prefecture, municipality)",
        ],
    },
    # ===========================
    # Phase 2: 統計分析データ
    # ===========================
    "chi_square_tests": {
        "description": "カイ二乗検定結果",
        "columns": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("test_name", "TEXT"),
            ("chi2_statistic", "REAL"),
            ("p_value", "REAL"),
            ("degrees_of_freedom", "INTEGER"),
            ("is_significant", "BOOLEAN"),
        ],
    },
    "anova_tests": {
        "description": "ANOVA検定結果",
        "columns": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("test_name", "TEXT"),
            ("f_statistic", "REAL"),
            ("p_value", "REAL"),
            ("is_significant", "BOOLEAN"),
        ],
    },
    # ===========================
    # Phase 3: ペルソナ分析データ
    # ===========================
    "persona_summary": {
        "description": "ペルソナサマリー",
        "columns": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("persona_name", "TEXT UNIQUE"),
            ("age_group", "TEXT"),
            ("gender", "TEXT"),
            ("has_national_license", "BOOLEAN"),
            ("count", "INTEGER"),
            ("avg_desired_areas", "REAL"),
            ("avg_qualifications", "REAL"),
            ("employment_rate", "REAL"),
        ],
        "indexes": [
            "CREATE INDEX idx_persona_name ON persona_summary(persona_name)",
        ],
    },
    "persona_details": {
        "description": "ペルソナ詳細",
        "columns": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("persona_name", "TEXT"),
            ("applicant_id", "INTEGER"),
            ("age", "INTEGER"),
            ("gender", "TEXT"),
            ("has_national_license", "BOOLEAN"),
            ("residence_prefecture", "TEXT"),
            ("residence_municipality", "TEXT"),
            ("FOREIGN KEY (applicant_id)", "REFERENCES applicants(applicant_id)"),
        ],
        "indexes": [
            "CREATE INDEX idx_persona_detail ON persona_details(persona_name)",
        ],
    },
    "persona_summary_by_municipality": {
        "description": "市区町村別ペルソナサマリー",
        "columns": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("prefecture", "TEXT"),
            ("municipality", "TEXT"),
            ("persona_name", "TEXT"),
            ("count", "INTEGER"),
            ("avg_desired_areas", "REAL"),
            ("avg_qualifications", "REAL"),
            ("employment_rate", "REAL"),
        ],
        "indexes": [
            "CREATE INDEX idx_muni_persona ON persona_summary_by_municipality(prefecture, municipality, persona_name)",
        ],
    },
    # ===========================
    # Phase 6: フロー分析データ
    # ===========================
    "municipality_flow_edges": {
        "description": "自治体間フローエッジ",
        "columns": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("from_prefecture", "TEXT"),
            ("from_municipality", "TEXT"),
            ("to_prefecture", "TEXT"),
            ("to_municipality", "TEXT"),
            ("flow_count", "INTEGER"),
        ],
        "indexes": [
            "CREATE INDEX idx_flow_from ON municipality_flow_edges(from_prefecture, from_municipality)",
            "CREATE INDEX idx_flow_to ON municipality_flow_edges(to_prefecture, to_municipality)",
        ],
    },
    "municipality_flow_nodes": {
        "description": "自治体間フローノード",
        "columns": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("prefecture", "TEXT"),
            ("municipality", "TEXT"),
            ("inflow", "INTEGER"),
            ("outflow", "INTEGER"),
            ("net_flow", "INTEGER"),
        ],
        "indexes": [
            "CREATE INDEX idx_node_location ON municipality_flow_nodes(prefecture, municipality)",
        ],
    },
    "proximity_analysis": {
        "description": "移動パターン分析",
        "columns": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("residence_prefecture", "TEXT"),
            ("residence_municipality", "TEXT"),
            ("desired_prefecture", "TEXT"),
            ("desired_municipality", "TEXT"),
            ("count", "INTEGER"),
            ("is_same_municipality", "BOOLEAN"),
            ("is_same_prefecture", "BOOLEAN"),
        ],
        "indexes": [
            "CREATE INDEX idx_proximity ON proximity_analysis(residence_prefecture, residence_municipality)",
        ],
    },
    # ===========================
    # Phase 7: 高度分析データ
    # ===========================
    "supply_density_map": {
        "description": "人材供給密度マップ",
        "columns": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("location", "TEXT UNIQUE"),
            ("supply_count", "INTEGER"),
            ("avg_age", "REAL"),
            ("national_license_count", "INTEGER"),
            ("avg_qualifications", "REAL"),
        ],
        "indexes": [
            "CREATE INDEX idx_supply_location ON supply_density_map(location)",
        ],
    },
    "qualification_distribution": {
        "description": "資格別人材分布",
        "columns": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("qualification", "TEXT"),
            ("prefecture", "TEXT"),
            ("municipality", "TEXT"),
            ("count", "INTEGER"),
        ],
        "indexes": [
            "CREATE INDEX idx_qual_dist ON qualification_distribution(qualification, prefecture, municipality)",
        ],
    },
    "age_gender_cross_analysis": {
        "description": "年齢層×性別クロス分析",
        "columns": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("age_group", "TEXT"),
            ("gender", "TEXT"),
            ("count", "INTEGER"),
            ("avg_qualifications", "REAL"),
            ("employment_rate", "REAL"),
        ],
        "indexes": [
            "CREATE INDEX idx_age_gender ON age_gender_cross_analysis(age_group, gender)",
        ],
    },
    "mobility_score": {
        "description": "移動許容度スコアリング",
        "columns": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("applicant_id", "INTEGER"),
            ("mobility_score", "REAL"),
            ("desired_area_count", "INTEGER"),
            ("FOREIGN KEY (applicant_id)", "REFERENCES applicants(applicant_id)"),
        ],
        "indexes": [
            "CREATE INDEX idx_mobility ON mobility_score(applicant_id)",
        ],
    },
    "detailed_persona_profile": {
        "description": "ペルソナ詳細プロファイル",
        "columns": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("persona_name", "TEXT"),
            ("age_group", "TEXT"),
            ("gender", "TEXT"),
            ("has_national_license", "BOOLEAN"),
            ("avg_qualifications", "REAL"),
            ("avg_desired_areas", "REAL"),
            ("employment_rate", "REAL"),
            ("count", "INTEGER"),
        ],
        "indexes": [
            "CREATE INDEX idx_detailed_persona ON detailed_persona_profile(persona_name)",
        ],
    },
    # ===========================
    # Phase 8: キャリア・学歴分析
    # ===========================
    "career_distribution": {
        "description": "キャリア分布",
        "columns": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("career", "TEXT"),
            ("count", "INTEGER"),
        ],
    },
    "career_age_cross": {
        "description": "キャリア×年齢クロス分析",
        "columns": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("career", "TEXT"),
            ("age_group", "TEXT"),
            ("count", "INTEGER"),
        ],
        "indexes": [
            "CREATE INDEX idx_career_age ON career_age_cross(career, age_group)",
        ],
    },
    "graduation_year_distribution": {
        "description": "卒業年分布",
        "columns": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("graduation_year", "INTEGER"),
            ("count", "INTEGER"),
        ],
    },
    # ===========================
    # Phase 10: 転職意欲・緊急度分析
    # ===========================
    "urgency_distribution": {
        "description": "転職緊急度分布",
        "columns": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("urgency_level", "TEXT"),
            ("count", "INTEGER"),
        ],
    },
    "urgency_age_cross": {
        "description": "緊急度×年齢クロス分析",
        "columns": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("urgency_level", "TEXT"),
            ("age_group", "TEXT"),
            ("count", "INTEGER"),
        ],
        "indexes": [
            "CREATE INDEX idx_urgency_age ON urgency_age_cross(urgency_level, age_group)",
        ],
    },
    "urgency_employment_cross": {
        "description": "緊急度×就業状態クロス分析",
        "columns": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("urgency_level", "TEXT"),
            ("employment_status", "TEXT"),
            ("count", "INTEGER"),
        ],
        "indexes": [
            "CREATE INDEX idx_urgency_employment ON urgency_employment_cross(urgency_level, employment_status)",
        ],
    },
}


def get_create_table_sql(table_name: str) -> str:
    """
    テーブル作成SQL文を生成

    Args:
        table_name: テーブル名

    Returns:
        CREATE TABLE SQL文
    """
    if table_name not in DATABASE_SCHEMA:
        raise ValueError(f"Unknown table: {table_name}")

    schema = DATABASE_SCHEMA[table_name]
    columns = schema["columns"]

    columns_sql = ",\n    ".join([f"{col[0]} {col[1]}" for col in columns])

    sql = f"""CREATE TABLE IF NOT EXISTS {table_name} (
    {columns_sql}
);"""

    return sql


def get_all_create_table_sqls() -> list:
    """
    全テーブルのCREATE TABLE SQL文を生成

    Returns:
        CREATE TABLE SQL文のリスト
    """
    sqls = []
    for table_name in DATABASE_SCHEMA.keys():
        sqls.append(get_create_table_sql(table_name))

        # インデックス作成SQL
        if "indexes" in DATABASE_SCHEMA[table_name]:
            sqls.extend(DATABASE_SCHEMA[table_name]["indexes"])

    return sqls
