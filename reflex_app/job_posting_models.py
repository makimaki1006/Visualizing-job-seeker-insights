"""求人データモデル定義

GAS SourceDataシートの構造に基づく求人データのデータクラス定義
全30カラムに対応
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class JobPosting:
    """求人データモデル

    GAS SourceDataシートの全カラムに対応
    緯度・経度を使用した地図表示、フィルタリング、統計分析が可能
    """

    # 基本情報 (0-3)
    facility_name: str              # 0: 法人・施設名
    service_type: str               # 1: 診療科目・サービス形態
    access: str                     # 2: アクセス
    address_reliability: int        # 3: 住所信頼度 (0-100)

    # 給与情報 (4-10)
    employment_type: str            # 4: 給与_雇用形態 (正職員、契約職員、パート・アルバイト)
    salary_category: str            # 5: 給与_区分 (月給、時給)
    salary_range: str               # 6: 給与_範囲 (表示用文字列)
    salary_lower: Optional[int]     # 7: 給与_下限 (数値)
    salary_upper: Optional[int]     # 8: 給与_上限 (数値)
    salary_note: str                # 9: 給与の備考
    expected_annual_income: str     # 10: 想定年収

    # 待遇・勤務条件 (11-15)
    benefits: str                   # 11: 待遇
    training: str                   # 12: 教育体制・研修
    work_hours: str                 # 13: 勤務時間
    holidays: str                   # 14: 休日
    long_holidays: str              # 15: 長期休暇・特別休暇

    # 応募・仕事内容 (16-19)
    requirements: str               # 16: 応募要件
    bottom_text: str                # 17: bottom_text
    job_description: str            # 18: 仕事内容
    job_category: str               # 19: 募集職種カテゴリ

    # 空白カラム (20-25)
    # GASでは使用されていないが、将来の拡張用に予約

    # 位置情報 (26-29)
    longitude: float                # 26: fX (経度)
    latitude: float                 # 27: fY (緯度)
    confidence: int                 # 28: iConf (ジオコーディング信頼度)
    level: int                      # 29: iLvl (住所レベル)

    def to_dict(self) -> dict:
        """辞書形式に変換（JSON出力用）"""
        return {
            'facility_name': self.facility_name,
            'service_type': self.service_type,
            'access': self.access,
            'address_reliability': self.address_reliability,
            'employment_type': self.employment_type,
            'salary_category': self.salary_category,
            'salary_range': self.salary_range,
            'salary_lower': self.salary_lower,
            'salary_upper': self.salary_upper,
            'salary_note': self.salary_note,
            'expected_annual_income': self.expected_annual_income,
            'benefits': self.benefits,
            'training': self.training,
            'work_hours': self.work_hours,
            'holidays': self.holidays,
            'long_holidays': self.long_holidays,
            'requirements': self.requirements,
            'bottom_text': self.bottom_text,
            'job_description': self.job_description,
            'job_category': self.job_category,
            'longitude': self.longitude,
            'latitude': self.latitude,
            'confidence': self.confidence,
            'level': self.level,
        }

    @classmethod
    def from_csv_row(cls, row: list) -> 'JobPosting':
        """CSVの行データからインスタンスを生成

        Args:
            row: CSVの1行（30カラム）

        Returns:
            JobPostingインスタンス
        """
        return cls(
            facility_name=str(row[0]) if len(row) > 0 else "",
            service_type=str(row[1]) if len(row) > 1 else "",
            access=str(row[2]) if len(row) > 2 else "",
            address_reliability=int(row[3]) if len(row) > 3 and row[3] else 0,
            employment_type=str(row[4]) if len(row) > 4 else "",
            salary_category=str(row[5]) if len(row) > 5 else "",
            salary_range=str(row[6]) if len(row) > 6 else "",
            salary_lower=int(row[7]) if len(row) > 7 and row[7] else None,
            salary_upper=int(row[8]) if len(row) > 8 and row[8] else None,
            salary_note=str(row[9]) if len(row) > 9 else "",
            expected_annual_income=str(row[10]) if len(row) > 10 else "",
            benefits=str(row[11]) if len(row) > 11 else "",
            training=str(row[12]) if len(row) > 12 else "",
            work_hours=str(row[13]) if len(row) > 13 else "",
            holidays=str(row[14]) if len(row) > 14 else "",
            long_holidays=str(row[15]) if len(row) > 15 else "",
            requirements=str(row[16]) if len(row) > 16 else "",
            bottom_text=str(row[17]) if len(row) > 17 else "",
            job_description=str(row[18]) if len(row) > 18 else "",
            job_category=str(row[19]) if len(row) > 19 else "",
            longitude=float(row[26]) if len(row) > 26 and row[26] else 0.0,
            latitude=float(row[27]) if len(row) > 27 and row[27] else 0.0,
            confidence=int(row[28]) if len(row) > 28 and row[28] else 0,
            level=int(row[29]) if len(row) > 29 and row[29] else 0,
        )

    def get_marker_info_html(self) -> str:
        """マーカークリック時の詳細情報HTML生成

        GAS Map.htmlのgetFilteredMarkers()の形式に準拠

        Returns:
            HTML形式の詳細情報文字列
        """
        info_parts = [
            f"法人・施設名: {self.facility_name}",
            f"診療科目・サービス形態: {self.service_type}",
            f"アクセス: {self.access}",
            f"住所信頼度: {self.address_reliability}",
            f"給与_雇用形態: {self.employment_type}",
            f"給与_区分: {self.salary_category}",
            f"給与_範囲: {self.salary_range}",
            f"給与_下限: {self.salary_lower}",
            f"給与_上限: {self.salary_upper}",
            f"待遇: {self.benefits[:100]}..." if len(self.benefits) > 100 else f"待遇: {self.benefits}",
            f"勤務時間: {self.work_hours}",
            f"休日: {self.holidays}",
            f"応募要件: {self.requirements[:100]}..." if len(self.requirements) > 100 else f"応募要件: {self.requirements}",
        ]
        return "<br/>".join(info_parts)


# カラム定義（CSVヘッダー用）
CSV_COLUMNS = [
    "法人・施設名",
    "診療科目・サービス形態",
    "アクセス",
    "住所信頼度",
    "給与_雇用形態",
    "給与_区分",
    "給与_範囲",
    "給与_下限",
    "給与_上限",
    "給与の備考",
    "想定年収",
    "待遇",
    "教育体制・研修",
    "勤務時間",
    "休日",
    "長期休暇・特別休暇",
    "応募要件",
    "bottom_text",
    "仕事内容",
    "募集職種カテゴリ",
    "", "", "", "", "", "",  # 空白カラム (20-25)
    "fX",  # 経度
    "fY",  # 緯度
    "iConf",
    "iLvl",
]
