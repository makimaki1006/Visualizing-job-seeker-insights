"""求人データ用Stateクラスと地理的フィルタリング機能

GAS Code.jsのgetFilteredMarkers()ロジックをPythonで再現
- 都道府県・市区町村による中心点取得
- Haversine式による距離計算
- 給与条件フィルタリング
- 統計計算（平均、中央値、最頻値）
"""

import reflex as rx
import pandas as pd
import math
from typing import Optional, List, Dict, Any
from job_posting_models import JobPosting


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """2点間の距離（km）をHaversine式で計算

    GAS Code.js Line 99-108の実装をPython化

    Args:
        lat1, lng1: 地点1の緯度・経度
        lat2, lng2: 地点2の緯度・経度

    Returns:
        距離（km）
    """
    R = 6371  # 地球の半径（km）

    def to_radians(deg: float) -> float:
        return deg * math.pi / 180

    dLat = to_radians(lat2 - lat1)
    dLng = to_radians(lng2 - lng1)

    a = (math.sin(dLat / 2) ** 2 +
         math.cos(to_radians(lat1)) * math.cos(to_radians(lat2)) *
         math.sin(dLng / 2) ** 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def compute_stats(values: List[float]) -> Dict[str, float]:
    """統計計算（平均、中央値、最頻値）

    GAS Code.js Line 223-235のcomputeStats()をPython化

    Args:
        values: 数値リスト

    Returns:
        統計値の辞書 {average, median, mode}
    """
    if not values or len(values) == 0:
        return {'average': 0, 'median': 0, 'mode': 0}

    # 平均
    average = sum(values) / len(values)

    # 中央値
    sorted_values = sorted(values)
    mid = len(sorted_values) // 2
    if len(sorted_values) % 2 == 0:
        median = (sorted_values[mid - 1] + sorted_values[mid]) / 2
    else:
        median = sorted_values[mid]

    # 最頻値
    freq = {}
    for v in sorted_values:
        freq[v] = freq.get(v, 0) + 1

    max_freq = 0
    mode = sorted_values[0]
    for v, count in freq.items():
        if count > max_freq:
            max_freq = count
            mode = v

    return {
        'average': round(average, 0),
        'median': round(median, 0),
        'mode': round(mode, 0)
    }


class JobPostingState(rx.State):
    """求人データ用State

    GAS Map.htmlの機能をReflex Stateで再現:
    - CSVデータのロード
    - 地理的フィルタリング（都道府県・市区町村・半径）
    - 給与条件フィルタリング
    - ピン止め機能
    - 統計計算
    """

    # データ
    all_jobs: List[Dict] = []  # 全求人データ（JobPosting.to_dict()形式）
    filtered_jobs: List[Dict] = []  # フィルタ済み求人データ
    pinned_jobs: List[Dict] = []  # ピン止め求人データ
    is_loaded: bool = False

    # フィルタ条件
    prefecture: str = ""
    municipality: str = ""
    radius_km: float = 10.0
    employment_type_filter: str = "全て選択"  # 正職員、契約職員、パート・アルバイト、全て選択
    salary_category_filter: str = "どちらも"  # 月給、時給、どちらも

    # 中心座標（ジオコーディング結果）
    center_lat: float = 35.0
    center_lng: float = 139.0

    # 統計情報
    stats_lower: Dict[str, float] = {}
    stats_upper: Dict[str, float] = {}
    total_count: int = 0
    pinned_count: int = 0

    # プログレス
    progress_percentage: int = 0
    progress_stage: str = "未開始"

    def load_csv(self, file_path: str):
        """CSVファイルから求人データをロード

        Args:
            file_path: CSVファイルパス
        """
        try:
            self.progress_percentage = 10
            self.progress_stage = "CSVファイル読み込み中"

            # CSVファイル読み込み（ヘッダー付き）
            df = pd.read_csv(file_path, encoding='utf-8-sig')

            self.progress_percentage = 30
            self.progress_stage = "データ変換中"

            # DataFrameを辞書リストに変換
            jobs = []
            for _, row in df.iterrows():
                job = JobPosting.from_csv_row(row.tolist())
                jobs.append(job.to_dict())

            self.all_jobs = jobs
            self.filtered_jobs = jobs
            self.total_count = len(jobs)
            self.is_loaded = True

            self.progress_percentage = 100
            self.progress_stage = "完了"

        except Exception as e:
            self.progress_stage = f"エラー: {str(e)}"
            self.progress_percentage = 0

    def geocode_municipality(self, prefecture: str, municipality: str) -> tuple[float, float]:
        """市区町村からジオコーディングで中心座標を取得

        簡易実装: 主要都市の座標をハードコード
        本格実装ではGoogle Maps APIまたはGeopy使用

        Args:
            prefecture: 都道府県名
            municipality: 市区町村名

        Returns:
            (緯度, 経度)のタプル
        """
        # 主要都市の座標（簡易版）
        city_coords = {
            "北海道 札幌市": (43.064, 141.347),
            "東京都 千代田区": (35.694, 139.753),
            "東京都 新宿区": (35.694, 139.703),
            "大阪府 大阪市": (34.694, 135.502),
            "愛知県 名古屋市": (35.181, 136.906),
            "福岡県 福岡市": (33.590, 130.401),
            "京都府 京都市": (35.011, 135.768),
            # 必要に応じて追加
        }

        key = f"{prefecture} {municipality}"
        if key in city_coords:
            return city_coords[key]

        # デフォルト: 東京
        return (35.694, 139.753)

    def filter_jobs(self):
        """求人データをフィルタリング

        GAS Code.js Line 120-172のgetFilteredMarkers()ロジック
        """
        if not self.all_jobs:
            return

        self.progress_percentage = 0
        self.progress_stage = "フィルタ処理開始"

        # Step 1: 中心座標取得
        self.center_lat, self.center_lng = self.geocode_municipality(
            self.prefecture, self.municipality
        )
        self.progress_percentage = 20
        self.progress_stage = "ジオコーディング完了"

        # Step 2: 距離フィルタリング + 給与条件フィルタリング
        filtered = []
        total = len(self.all_jobs)

        for i, job in enumerate(self.all_jobs):
            # 距離計算
            distance = haversine_distance(
                self.center_lat, self.center_lng,
                job['latitude'], job['longitude']
            )

            # 距離フィルタ
            if distance > self.radius_km:
                continue

            # 給与_雇用形態フィルタ
            if (self.employment_type_filter != "全て選択" and
                job['employment_type'] != self.employment_type_filter):
                continue

            # 給与_区分フィルタ
            if (self.salary_category_filter != "どちらも" and
                job['salary_category'] != self.salary_category_filter):
                continue

            filtered.append(job)

            # プログレス更新（10%刻み）
            progress_percent = 20 + int(((i + 1) / total) * 60)
            if progress_percent % 10 == 0:
                self.progress_percentage = progress_percent
                self.progress_stage = "フィルタ処理中"

        self.filtered_jobs = filtered
        self.total_count = len(filtered)

        # Step 3: 統計計算
        self.calculate_stats()

        self.progress_percentage = 100
        self.progress_stage = "完了"

    def calculate_stats(self):
        """フィルタ済み求人データの統計計算

        給与下限・上限の平均、中央値、最頻値を計算
        """
        if not self.filtered_jobs:
            self.stats_lower = {'average': 0, 'median': 0, 'mode': 0}
            self.stats_upper = {'average': 0, 'median': 0, 'mode': 0}
            return

        lower_values = [
            job['salary_lower']
            for job in self.filtered_jobs
            if job['salary_lower'] is not None
        ]

        upper_values = [
            job['salary_upper']
            for job in self.filtered_jobs
            if job['salary_upper'] is not None
        ]

        self.stats_lower = compute_stats(lower_values)
        self.stats_upper = compute_stats(upper_values)

    def calculate_pinned_stats(self):
        """ピン止め求人データの統計計算"""
        if not self.pinned_jobs:
            self.stats_lower = {'average': 0, 'median': 0, 'mode': 0}
            self.stats_upper = {'average': 0, 'median': 0, 'mode': 0}
            self.pinned_count = 0
            return

        lower_values = [
            job['salary_lower']
            for job in self.pinned_jobs
            if job['salary_lower'] is not None
        ]

        upper_values = [
            job['salary_upper']
            for job in self.pinned_jobs
            if job['salary_upper'] is not None
        ]

        self.stats_lower = compute_stats(lower_values)
        self.stats_upper = compute_stats(upper_values)
        self.pinned_count = len(self.pinned_jobs)

    def add_pinned_job(self, job_index: int):
        """求人をピン止めリストに追加

        Args:
            job_index: filtered_jobs内のインデックス
        """
        if 0 <= job_index < len(self.filtered_jobs):
            job = self.filtered_jobs[job_index]
            if job not in self.pinned_jobs:
                self.pinned_jobs.append(job)
                self.calculate_pinned_stats()

    def remove_pinned_job(self, job_index: int):
        """求人をピン止めリストから削除

        Args:
            job_index: pinned_jobs内のインデックス
        """
        if 0 <= job_index < len(self.pinned_jobs):
            self.pinned_jobs.pop(job_index)
            self.calculate_pinned_stats()

    def clear_pinned_jobs(self):
        """全ピン止めをクリア"""
        self.pinned_jobs = []
        self.pinned_count = 0
        self.calculate_stats()  # フィルタ済みデータの統計に戻す
