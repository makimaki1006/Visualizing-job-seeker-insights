"""
データ分析用定数定義
マジックストリングを防止し、データ正規化を支援
"""

from typing import Optional, List


class EmploymentStatus:
    """
    就業状態の定数定義

    使用例:
        from constants import EmploymentStatus

        # 定数の使用
        if row['employment_status'] == EmploymentStatus.EMPLOYED:
            count += 1

        # 正規化
        normalized = EmploymentStatus.normalize('在職中')
        # → '就業中'
    """

    # 標準形式
    EMPLOYED = '就業中'       # 就業中
    UNEMPLOYED = '離職中'     # 離職中
    ENROLLED = '在学中'       # 在学中

    # すべての状態のリスト
    ALL = [EMPLOYED, UNEMPLOYED, ENROLLED]

    @classmethod
    def normalize(cls, status: str) -> Optional[str]:
        """
        就業状態を正規化

        Args:
            status: 元の就業状態文字列

        Returns:
            正規化された就業状態（EMPLOYED, UNEMPLOYED, ENROLLED のいずれか）
            認識できない場合は None

        Examples:
            >>> EmploymentStatus.normalize('在職中')
            '就業中'
            >>> EmploymentStatus.normalize('退職済み')
            '離職中'
            >>> EmploymentStatus.normalize('学生')
            '在学中'
        """
        # NaN、None、空文字列をチェック
        if not status or not isinstance(status, str):
            return None

        status_clean = status.strip()

        # 就業中のバリエーション
        if status_clean in ['就業中', '在職中', '就業中（正社員）', '就業中（契約社員）',
                           '就業中（派遣社員）', '就業中（パート）', '就業中（アルバイト）']:
            return cls.EMPLOYED

        # 離職中のバリエーション
        if status_clean in ['離職中', '退職済み', '無職', '求職中', '転職活動中']:
            return cls.UNEMPLOYED

        # 在学中のバリエーション
        if status_clean in ['在学中', '学生', '大学生', '専門学校生']:
            return cls.ENROLLED

        return None

    @classmethod
    def is_valid(cls, status: str) -> bool:
        """
        就業状態が有効かチェック

        Args:
            status: チェックする就業状態文字列

        Returns:
            有効な場合True、無効な場合False
        """
        return cls.normalize(status) is not None


class EducationLevel:
    """
    学歴レベルの定数定義

    使用例:
        from constants import EducationLevel

        # 定数の使用
        if education == EducationLevel.UNIVERSITY:
            count += 1

        # 正規化
        normalized = EducationLevel.normalize('大学卒')
        # → '大学'
    """

    # 標準形式
    UNIVERSITY = '大学'           # 大学
    GRADUATE_SCHOOL = '大学院'    # 大学院
    JUNIOR_COLLEGE = '短期大学'   # 短期大学
    VOCATIONAL = '専門学校'       # 専門学校
    HIGH_SCHOOL = '高等学校'      # 高等学校
    JUNIOR_HIGH = '中学校'        # 中学校
    OTHER = 'その他'              # その他

    # すべての学歴レベルのリスト
    ALL = [UNIVERSITY, GRADUATE_SCHOOL, JUNIOR_COLLEGE, VOCATIONAL,
           HIGH_SCHOOL, JUNIOR_HIGH, OTHER]

    @classmethod
    def normalize(cls, education: str) -> Optional[str]:
        """
        学歴レベルを正規化

        Args:
            education: 元の学歴文字列

        Returns:
            正規化された学歴レベル
            認識できない場合は None

        Examples:
            >>> EducationLevel.normalize('大学卒')
            '大学'
            >>> EducationLevel.normalize('専門')
            '専門学校'
        """
        # NaN、None、空文字列をチェック
        if not education or not isinstance(education, str):
            return None

        education_clean = education.strip()

        # 大学院
        if any(keyword in education_clean for keyword in ['大学院', '修士', '博士']):
            return cls.GRADUATE_SCHOOL

        # 大学（大学院より後にチェック）
        if any(keyword in education_clean for keyword in ['大学', '大卒', '学士']):
            return cls.UNIVERSITY

        # 短期大学
        if any(keyword in education_clean for keyword in ['短期大学', '短大', '短大卒']):
            return cls.JUNIOR_COLLEGE

        # 専門学校
        if any(keyword in education_clean for keyword in ['専門学校', '専門', '専修学校']):
            return cls.VOCATIONAL

        # 高等学校
        if any(keyword in education_clean for keyword in ['高等学校', '高校', '高卒']):
            return cls.HIGH_SCHOOL

        # 中学校
        if any(keyword in education_clean for keyword in ['中学校', '中学', '中卒']):
            return cls.JUNIOR_HIGH

        return cls.OTHER

    @classmethod
    def is_valid(cls, education: str) -> bool:
        """
        学歴レベルが有効かチェック

        Args:
            education: チェックする学歴文字列

        Returns:
            有効な場合True、無効な場合False
        """
        return cls.normalize(education) is not None


class AgeGroup:
    """
    年齢層の定数定義

    使用例:
        from constants import AgeGroup

        # 年齢から年齢層を取得
        age_group = AgeGroup.from_age(25)
        # → '20代'
    """

    # 標準形式
    TEENS = '10代'
    TWENTIES = '20代'
    THIRTIES = '30代'
    FORTIES = '40代'
    FIFTIES = '50代'
    SIXTIES_PLUS = '60代以上'

    # すべての年齢層のリスト
    ALL = [TEENS, TWENTIES, THIRTIES, FORTIES, FIFTIES, SIXTIES_PLUS]

    @classmethod
    def from_age(cls, age: int) -> Optional[str]:
        """
        年齢から年齢層を取得

        Args:
            age: 年齢

        Returns:
            年齢層文字列
            範囲外の場合は None

        Examples:
            >>> AgeGroup.from_age(25)
            '20代'
            >>> AgeGroup.from_age(65)
            '60代以上'
        """
        if age is None or age < 0:
            return None

        if age < 20:
            return cls.TEENS
        elif age < 30:
            return cls.TWENTIES
        elif age < 40:
            return cls.THIRTIES
        elif age < 50:
            return cls.FORTIES
        elif age < 60:
            return cls.FIFTIES
        else:
            return cls.SIXTIES_PLUS


class Gender:
    """
    性別の定数定義

    使用例:
        from constants import Gender

        # 定数の使用
        if gender == Gender.MALE:
            count += 1
    """

    # 標準形式
    MALE = '男性'
    FEMALE = '女性'
    OTHER = 'その他'

    # すべての性別のリスト
    ALL = [MALE, FEMALE, OTHER]

    @classmethod
    def normalize(cls, gender: str) -> Optional[str]:
        """
        性別を正規化

        Args:
            gender: 元の性別文字列

        Returns:
            正規化された性別
            認識できない場合は None

        Examples:
            >>> Gender.normalize('男')
            '男性'
            >>> Gender.normalize('女')
            '女性'
        """
        # NaN、None、空文字列をチェック
        if not gender or not isinstance(gender, str):
            return None

        gender_clean = gender.strip()

        if gender_clean in ['男性', '男', 'M', 'Male', 'male']:
            return cls.MALE

        if gender_clean in ['女性', '女', 'F', 'Female', 'female']:
            return cls.FEMALE

        return cls.OTHER

    @classmethod
    def is_valid(cls, gender: str) -> bool:
        """
        性別が有効かチェック

        Args:
            gender: チェックする性別文字列

        Returns:
            有効な場合True、無効な場合False
        """
        return cls.normalize(gender) in cls.ALL
