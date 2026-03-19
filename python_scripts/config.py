"""
設定ファイル
プロジェクト全体で共通の設定を管理
"""

import os
from pathlib import Path
from typing import Dict, List

# ========================================
# 年齢層定義
# ========================================

# 年齢層区分（5区分）
AGE_BINS_5 = [0, 29, 39, 49, 59, 100]
AGE_LABELS_5 = ['20代以下', '30代', '40代', '50代', '60代以上']

# 年齢層区分（4区分）- Phase 7用（廃止予定）
AGE_BINS_4 = [0, 30, 45, 60, 100]
AGE_LABELS_4 = ['若年層', '中年層', '準高齢層', '高齢層']

# デフォルトの年齢層定義（5区分を標準とする）
DEFAULT_AGE_BINS = AGE_BINS_5
DEFAULT_AGE_LABELS = AGE_LABELS_5

# ========================================
# データ品質検証の閾値
# ========================================

# サンプルサイズの基準（推論的考察用）
MIN_SAMPLE_TOTAL = 100  # 全体最小件数
MIN_SAMPLE_GROUP = 30   # グループ最小件数
MIN_SAMPLE_CROSS = 5    # クロス集計セル最小件数

# 欠損率の基準
MAX_MISSING_RATE = 0.7  # 70%以上欠損は警告

# ========================================
# 外れ値処理
# ========================================

# 希望勤務地数の上限
MAX_DESIRED_LOCATIONS = 50

# ========================================
# ファイルパス設定
# ========================================

# プロジェクトルートディレクトリ
PROJECT_ROOT = Path(__file__).parent.parent

# 出力ディレクトリ
OUTPUT_DIR = PROJECT_ROOT / "data" / "output_v2"

# geocacheファイルパス
GEOCACHE_FILE = OUTPUT_DIR / "geocache.json"

# 旧バージョンとの互換のために参照するgeocache候補
GEOCACHE_FALLBACK_FILES = [
    PROJECT_ROOT / "data" / "output" / "geocache.json",
    PROJECT_ROOT / "archive" / "output_v1" / "geocache.json",
]

# ジオコーディングAPI設定（国土地理院アドレスマッチングサービス）
GSI_API_URL = "https://msearch.gsi.go.jp/address-search/AddressSearch"
GSI_API_MAX_RETRIES = 3
GSI_API_TIMEOUT = 10  # 秒
GSI_API_REQUEST_INTERVAL = 0.3  # 秒
ENABLE_GSI_GEOCODING = os.environ.get("DISABLE_GSI_GEOCODING", "").lower() not in {"1", "true", "yes"}

# ========================================
# クラスタリング設定
# ========================================

# デフォルトのクラスタ数（Phase 3: ペルソナ分析）
DEFAULT_N_CLUSTERS = 5

# クラスタリング用特徴量
CLUSTERING_FEATURES = [
    'age',              # 年齢
    'gender_encoded',   # 性別（エンコード済み）
    'age_group_encoded',  # 年齢層（エンコード済み）
    'desired_location_count',  # 希望勤務地数
    'urgency_score',    # 緊急度スコア
    # 'education_level_encoded'  # 学歴レベル（オプション）
]

# 特徴量のスケーリングを行うか
USE_FEATURE_SCALING = True

# ========================================
# エンコーディング設定
# ========================================

# CSV読み込み時のエンコーディング候補（優先順位順）
ENCODING_CANDIDATES = [
    'utf-8-sig',
    'utf-8',
    'shift-jis',
    'cp932',
    'euc-jp'
]

# ========================================
# 欠損値処理ポリシー
# ========================================

# 欠損値の扱い（カラムごと）
MISSING_VALUE_POLICY: Dict[str, any] = {
    'age': None,               # NaNのまま
    'gender': None,            # NaNのまま
    'desired_area': [],        # 空リスト
    'qualifications': None,    # NaNのまま
    'urgency_score': 0,        # 0（未記載）
    'employment_status': None, # NaNのまま
    'education_level': 'なし',  # 「なし」
    'graduation_year': None    # NaNのまま
}

# ========================================
# 出力ファイル検証設定
# ========================================

# 期待される出力ファイル数（品質レポート・Matrix除く）
# ファイル名はPhase{N}_プレフィックス付き（実際の出力と一致）
EXPECTED_OUTPUT_FILES: Dict[str, List[str]] = {
    'phase1': [
        'Phase1_Applicants.csv', 'Phase1_DesiredWork.csv',
        'Phase1_AggDesired.csv', 'Phase1_MapMetrics.csv',
        'Phase1_QualificationMaster.csv', 'Phase1_PrefectureMaster.csv',
        'Phase1_EmploymentStatusMaster.csv',
        'Phase1_PersonaByMunicipality_WithResidence.csv',
        'Phase1_QualificationDistributionByMunicipality.csv',
    ],
    'phase2': ['Phase2_ChiSquareTests.csv', 'Phase2_ANOVATests.csv'],
    'phase3': [
        'Phase3_PersonaSummary.csv', 'Phase3_PersonaDetails.csv',
        'Phase3_PersonaSummaryByMunicipality.csv',
    ],
    'phase6': [
        'Phase6_MunicipalityFlowEdges.csv', 'Phase6_MunicipalityFlowNodes.csv',
        'Phase6_ProximityAnalysis.csv', 'Phase6_AggregatedFlowEdges.csv',
    ],
    'phase7': [
        'Phase7_SupplyDensityMap.csv', 'Phase7_QualificationDistribution.csv',
        'Phase7_AgeGenderCrossAnalysis.csv', 'Phase7_AgeGenderCrossAnalysis_Residence.csv',
        'Phase7_MobilityScore.csv', 'Phase7_DetailedPersonaProfile.csv',
    ],
    'phase8': [
        'Phase8_CareerDistribution.csv', 'Phase8_CareerAgeCross.csv',
        'Phase8_GraduationYearDistribution.csv',
    ],
    'phase10': [
        'Phase10_UrgencyDistribution.csv',
        'Phase10_UrgencyByMunicipality.csv',
        'Phase10_UrgencyAgeCross.csv',
        'Phase10_UrgencyAgeCross_ByMunicipality.csv',
        'Phase10_UrgencyEmploymentCross.csv',
        'Phase10_UrgencyEmploymentCross_ByMunicipality.csv',
        'Phase10_UrgencyGenderCross.csv',
        'Phase10_UrgencyGenderCross_ByMunicipality.csv',
        'Phase10_UrgencyStartCategoryCross.csv',
        'Phase10_UrgencyStartCategoryCross_ByMunicipality.csv',
    ],
    'phase12': ['Phase12_SupplyDemandGap.csv'],
    'phase13': ['Phase13_RarityScore.csv'],
    'phase14': ['Phase14_CompetitionProfile.csv'],
}

# ========================================
# バックアップ設定
# ========================================

# 既存ファイルのバックアップを作成するか
CREATE_BACKUP = True

# バックアップファイル名の形式（タイムスタンプ付き）
BACKUP_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

# ========================================
# ログ設定
# ========================================

# 詳細ログを出力するか
VERBOSE = True

# 警告を表示するか
SHOW_WARNINGS = True
