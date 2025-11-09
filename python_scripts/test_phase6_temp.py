#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
求職者データ包括分析システム - 完全統合版（拡張分析機能付き）
Job Seeker Comprehensive Analysis System - Complete Edition with Extended Analytics
"""

import pandas as pd
import numpy as np
import json
import re
import os
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# フォントキャッシュのリビルド（必要に応じて）
try:
    import matplotlib.font_manager as fm
    fm._rebuild()
except:
    pass

# 可視化関連
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Circle
import matplotlib.patches as mpatches

# 日本語フォント設定
import platform
system = platform.system()

try:
    import japanize_matplotlib
    print("[OK] japanize_matplotlib を使用")
except ImportError:
    print("japanize_matplotlib がインストールされていません。システムフォントを設定します。")
    
    if system == 'Windows':
        plt.rcParams['font.family'] = ['MS Gothic', 'Yu Gothic', 'Meiryo', 'sans-serif']
    elif system == 'Darwin':  # macOS
        plt.rcParams['font.family'] = ['Hiragino Sans', 'Hiragino Kaku Gothic Pro', 'sans-serif']
    else:  # Linux
        plt.rcParams['font.family'] = ['IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP', 'sans-serif']

# マイナス記号の文字化け対策
plt.rcParams['axes.unicode_minus'] = False

# フォントサイズ設定
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 10
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['figure.dpi'] = 100
plt.style.use('default')

# その他の設定
from matplotlib import rcParams
rcParams['font.size'] = 10
rcParams['figure.dpi'] = 100
plt.style.use('default')

# 分析関連
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import silhouette_score
import networkx as nx
from collections import Counter, defaultdict
from scipy import stats
from scipy.spatial.distance import cdist


# ========================================
# マスターデータ定義（MECEに基づく分類）
# ========================================
class MasterData:
    """求職者分析用マスターデータ"""
    
    # 資格マスター（MECE分類）
    QUALIFICATIONS = {
        '医師・歯科医師': [
            '医師', '歯科医師', '歯科医師（院長/分院長経験あり）'
        ],
        '看護系': [
            '看護師', '准看護師', '保健師', '助産師'
        ],
        '薬剤系': [
            '薬剤師', '登録販売者', 'MR認定資格'
        ],
        'リハビリテーション系': [
            '理学療法士', '作業療法士', '言語聴覚士', '視能訓練士',
            '柔道整復師', '鍼灸師', 'あん摩マッサージ指圧師'
        ],
        '医療技術系': [
            '診療放射線技師', '臨床検査技師', '臨床工学技士',
            '歯科衛生士', '歯科技工士'
        ],
        '介護福祉専門職': [
            '介護支援専門員', 'ケアマネジャー', 'ケアマネ',
            '介護福祉士', '主任介護支援専門員', '主任ケアマネジャー',
            '社会福祉士', '精神保健福祉士'
        ],
        '介護福祉研修・任用': [
            '介護職員実務者研修', '実務者研修', 'ヘルパー1級', '基礎研修',
            '介護職員初任者研修', '初任者研修', 'ヘルパー2級',
            '社会福祉主事任用資格', '社会福祉主事',
            '福祉用具専門相談員', 'サービス管理責任者研修',
            '児童発達支援管理責任者研修', '相談支援従事者研修',
            '主任相談支援専門員'
        ],
        '心理系': [
            '臨床心理士', '公認心理師'
        ],
        '栄養系': [
            '管理栄養士', '栄養士', '栄養教諭', '調理師'
        ],
        '保育・教育系': [
            '保育士', '幼稚園教諭', '小学校教諭', '中学校教諭',
            '高等学校教諭', '養護教諭', '児童指導員任用資格',
            '放課後児童支援員認定資格'
        ],
        '理美容系': [
            '美容師', '理容師'
        ],
        '代替医療・セラピー系': [
            '整体師', 'カイロプラクター', 'リフレクソロジスト', 'アロマセラピスト'
        ],
        '事務系（民間）': [
            '医療事務資格（民間）', '介護事務資格（民間）',
            '調剤事務資格（民間）', '歯科助手資格（民間）',
            'ネイリスト資格（民間）'
        ],
        'その他資格': [
            '自動車運転免許', 'その他'
        ]
    }
    
    # 希望入職時期
    DESIRED_START_TIMING = {
        '1': '今すぐに',
        '2': '1ヶ月以内',
        '3': '3ヶ月以内',
        '4': '3ヶ月以上先',
        '5': '機会があれば転職を検討したい'
    }
    
    # 分析パラメータ
    ANALYSIS_PARAMS = {
        'age_threshold_middle': 45,
        'age_threshold_senior': 60,
        'hhi_high': 0.25,
        'hhi_medium': 0.15,
        'local_preference_threshold': 0.7,
        'high_qualification_count': 3,
        'quality_threshold': 0.8,
        'max_desired_locations': 100,
        'api_delay': 0.2,
        'progress_interval': 50
    }


class AdvancedJobSeekerAnalyzer:
    """求職者データの包括的分析クラス（拡張版）"""
    
    def __init__(self, filepath):
        """初期化"""
        self.filepath = Path(filepath)
        self.df = None
        self.df_processed = None
        self.analysis_results = {}
        self.geocache = {}

        # geocache.jsonのパスを動的に解決
        geocache_candidates = [
            Path('geocache.json'),  # 実行ディレクトリ直下
            Path('data/output/geocache.json'),  # job_medley_project/ から
            Path(__file__).parent.parent / 'data/output/geocache.json',  # スクリプト位置からの相対パス
            Path(r'C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\data\output\geocache.json')  # 絶対パス
        ]

        self.geocache_file = None
        for candidate in geocache_candidates:
            if candidate.exists():
                self.geocache_file = candidate
                break

        # 見つからない場合はデフォルトパス（新規作成用）
        if self.geocache_file is None:
            self.geocache_file = Path('data/output/geocache.json')
            # ディレクトリが存在しない場合は作成
            self.geocache_file.parent.mkdir(parents=True, exist_ok=True)

        self.master = MasterData()
        
        # 都道府県リスト
        self.prefectures = [
            '北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県',
            '茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県',
            '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県', '岐阜県',
            '静岡県', '愛知県', '三重県', '滋賀県', '京都府', '大阪府', '兵庫県',
            '奈良県', '和歌山県', '鳥取県', '島根県', '岡山県', '広島県', '山口県',
            '徳島県', '香川県', '愛媛県', '高知県', '福岡県', '佐賀県', '長崎県',
            '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県'
        ]
        
        # 地方区分
        self.regions = {
            '北海道': ['北海道'],
            '東北': ['青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県'],
            '関東': ['茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県'],
            '中部': ['新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県', '岐阜県', '静岡県', '愛知県'],
            '近畿': ['三重県', '滋賀県', '京都府', '大阪府', '兵庫県', '奈良県', '和歌山県'],
            '中国': ['鳥取県', '島根県', '岡山県', '広島県', '山口県'],
            '四国': ['徳島県', '香川県', '愛媛県', '高知県'],
            '九州': ['福岡県', '佐賀県', '長崎県', '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県']
        }
        
        # 市区町村パターン（政令指定都市の区まで取得）
        # 例: 京都市西京区 → 京都市西京区（全体）
        #     横浜市中区 → 横浜市中区（全体）
        #     京都市 → 京都市（市のみ）
        self.municipality_pattern = re.compile(
            r'(.+?市.+?区|.+?(?:市|区|町|村|郡))(.+?(?:町|村))?'
        )
        
        # 都道府県座標
        self.prefecture_coords = {
            '北海道': {'lat': 43.0642, 'lng': 141.3469},
            '青森県': {'lat': 40.8244, 'lng': 140.7400},
            '岩手県': {'lat': 39.7036, 'lng': 141.1527},
            '宮城県': {'lat': 38.2682, 'lng': 140.8694},
            '秋田県': {'lat': 39.7186, 'lng': 140.1024},
            '山形県': {'lat': 38.2405, 'lng': 140.3634},
            '福島県': {'lat': 37.7503, 'lng': 140.4676},
            '茨城県': {'lat': 36.3418, 'lng': 140.4468},
            '栃木県': {'lat': 36.5657, 'lng': 139.8836},
            '群馬県': {'lat': 36.3907, 'lng': 139.0604},
            '埼玉県': {'lat': 35.8570, 'lng': 139.6489},
            '千葉県': {'lat': 35.6050, 'lng': 140.1233},
            '東京都': {'lat': 35.6762, 'lng': 139.6503},
            '神奈川県': {'lat': 35.4478, 'lng': 139.6425},
            '新潟県': {'lat': 37.9022, 'lng': 139.0235},
            '富山県': {'lat': 36.6953, 'lng': 137.2113},
            '石川県': {'lat': 36.5946, 'lng': 136.6256},
            '福井県': {'lat': 36.0652, 'lng': 136.2216},
            '山梨県': {'lat': 35.6640, 'lng': 138.5684},
            '長野県': {'lat': 36.6513, 'lng': 138.1810},
            '岐阜県': {'lat': 35.3912, 'lng': 136.7223},
            '静岡県': {'lat': 34.9769, 'lng': 138.3831},
            '愛知県': {'lat': 35.1802, 'lng': 136.9066},
            '三重県': {'lat': 34.7303, 'lng': 136.5086},
            '滋賀県': {'lat': 35.0045, 'lng': 135.8685},
            '京都府': {'lat': 35.0116, 'lng': 135.7681},
            '大阪府': {'lat': 34.6862, 'lng': 135.5200},
            '兵庫県': {'lat': 34.6913, 'lng': 135.1830},
            '奈良県': {'lat': 34.6851, 'lng': 135.8327},
            '和歌山県': {'lat': 34.2260, 'lng': 135.1675},
            '鳥取県': {'lat': 35.5039, 'lng': 134.2378},
            '島根県': {'lat': 35.4723, 'lng': 133.0505},
            '岡山県': {'lat': 34.6618, 'lng': 133.9345},
            '広島県': {'lat': 34.3966, 'lng': 132.4596},
            '山口県': {'lat': 34.1860, 'lng': 131.4705},
            '徳島県': {'lat': 34.0658, 'lng': 134.5593},
            '香川県': {'lat': 34.3401, 'lng': 134.0434},
            '愛媛県': {'lat': 33.8416, 'lng': 132.7658},
            '高知県': {'lat': 33.5597, 'lng': 133.5311},
            '福岡県': {'lat': 33.6064, 'lng': 130.4183},
            '佐賀県': {'lat': 33.2494, 'lng': 130.2988},
            '長崎県': {'lat': 32.7448, 'lng': 129.8737},
            '熊本県': {'lat': 32.7898, 'lng': 130.7417},
            '大分県': {'lat': 33.2382, 'lng': 131.6126},
            '宮崎県': {'lat': 31.9111, 'lng': 131.4239},
            '鹿児島県': {'lat': 31.5602, 'lng': 130.5581},
            '沖縄県': {'lat': 26.2124, 'lng': 127.6809}
        }
        
        self.load_geocache()
    
    def _convert_to_json_serializable(self, obj):
        """JSONシリアライズ可能な形式に変換"""
        if isinstance(obj, dict):
            return {k: self._convert_to_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_json_serializable(item) for item in obj]
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        elif pd.isna(obj):
            return None
        else:
            return obj
    
    def get_coordinates_from_gsi_api(self, address, retry_count=3):
        """
        国土地理院APIから座標を取得（リトライ機能付き）

        Args:
            address: 検索する住所
            retry_count: リトライ回数（デフォルト3回）

        Returns:
            dict: {'lat': 緯度, 'lng': 経度} または None
        """
        import time

        try:
            import requests
        except ImportError:
            print("    警告: requestsモジュールがインストールされていません")
            return None

        # キャッシュチェック
        if address in self.geocache:
            return self.geocache[address]

        # リトライループ
        for attempt in range(retry_count):
            try:
                url = "https://msearch.gsi.go.jp/address-search/AddressSearch"
                params = {'q': address}
                time.sleep(0.5)  # レート制限対策

                response = requests.get(url, params=params, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        result = data[0]
                        coords = {
                            'lat': float(result['geometry']['coordinates'][1]),
                            'lng': float(result['geometry']['coordinates'][0])
                        }
                        self.geocache[address] = coords
                        return coords
                    else:
                        # データが空の場合はリトライ不要
                        return None
                else:
                    print(f"    警告: API応答エラー (status={response.status_code}) - {address}")
                    if attempt < retry_count - 1:
                        time.sleep(2 ** attempt)  # 指数バックオフ

            except requests.exceptions.Timeout:
                print(f"    警告: タイムアウト ({attempt+1}/{retry_count}) - {address}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
            except requests.exceptions.RequestException as e:
                print(f"    警告: リクエストエラー ({type(e).__name__}) - {address}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
            except (KeyError, ValueError, IndexError) as e:
                print(f"    警告: データ解析エラー ({type(e).__name__}) - {address}")
                return None
            except Exception as e:
                print(f"    警告: 予期しないエラー ({type(e).__name__}) - {address}")
                return None

        return None
    
    def run_complete_analysis(self):
        """完全な分析の実行"""
        print("\n" + "=" * 60)
        print("求職者データ包括分析システム - 拡張版")
        print("=" * 60)
        
        # 1. データ読み込み
        self.load_data()
        
        # 2. データ前処理
        self.process_data()
        
        # 3. 拡張可視化
        self.advanced_visualizations()
        
        # 4. 拡張インサイト生成
        self.generate_advanced_insights()
        
        # 5. 結果エクスポート
        self.export_results()
        
        # 6. サマリー表示
        self._display_summary()
        
        return self.analysis_results
    
    def _display_summary(self):
        """分析サマリーの表示"""
        print("\n" + "=" * 60)
        print("[SUCCESS] 分析完了！")
        print("=" * 60)
        
        print("\n【分析サマリー】")
        print(f"  総求職者数: {len(self.df_processed):,}人")
        
        if 'age' in self.df_processed.columns:
            print(f"  平均年齢: {self.df_processed['age'].mean():.1f}歳")
        
        if 'generation' in self.df_processed.columns:
            gen_dist = self.df_processed['generation'].value_counts()
            print(f"  世代分布: {gen_dist.to_dict()}")
        
        if 'desired_location_count' in self.df_processed.columns:
            print(f"  平均希望勤務地数: {self.df_processed['desired_location_count'].mean():.2f}箇所")
        
        if 'qualification_count' in self.df_processed.columns:
            print(f"  平均資格保有数: {self.df_processed['qualification_count'].mean():.2f}個")
        
        if 'has_national_license' in self.df_processed.columns:
            national_ratio = self.df_processed['has_national_license'].mean()
            print(f"  国家資格保有率: {national_ratio:.1%}")
        
        if 'clusters' in self.analysis_results:
            clusters = self.analysis_results['clusters']
            print(f"  検出セグメント数: {clusters.get('optimal_k', 0)}個")
        
        if 'mobility_patterns' in self.analysis_results:
            mobility = self.analysis_results['mobility_patterns']
            print(f"  平均移動距離: {mobility.get('average_mobility_distance', 0):.1f}km")
        
        print("\n【出力ファイル】")
        print("  - advanced_analysis.png （16種類の拡張分析グラフ）")
        print("  - processed_data_complete.csv （処理済みデータ）")
        print("  - analysis_results_complete.json （分析結果）")
        print("  - segment_*.csv （セグメント別データ）")
        
        if self.geocache_file.exists():
            print("  - geocache.json （座標キャッシュ）")
    
    def load_geocache(self):
        """ジオキャッシュの読み込み"""
        if self.geocache_file is None:
            print("  警告: geocache.jsonが見つかりません（新規作成します）")
            self.geocache = {}
            return

        if self.geocache_file.exists():
            try:
                with open(self.geocache_file, 'r', encoding='utf-8') as f:
                    self.geocache = json.load(f)
                print(f"  ジオキャッシュを読み込みました: {self.geocache_file.name} ({len(self.geocache)}件)")
            except Exception as e:
                print(f"  警告: ジオキャッシュ読み込みエラー ({type(e).__name__}): {e}")
                self.geocache = {}
        else:
            print(f"  情報: geocache.jsonが見つかりません（{self.geocache_file}）")
            self.geocache = {}
    
    def save_geocache(self):
        """ジオキャッシュの保存"""
        try:
            with open(self.geocache_file, 'w', encoding='utf-8') as f:
                json.dump(self.geocache, f, ensure_ascii=False, indent=2)
            print(f"  ジオキャッシュを保存しました（{len(self.geocache)}件）")
        except Exception as e:
            print(f"  ジオキャッシュ保存エラー: {e}")
    
    def load_data(self):
        """CSVファイルの読み込みと基本情報の表示"""
        print(f"データ読み込み中: {self.filepath.name}")
        
        # エンコーディングを自動検出
        encodings = ['utf-8', 'shift-jis', 'cp932', 'utf-8-sig']
        for encoding in encodings:
            try:
                self.df = pd.read_csv(self.filepath, encoding=encoding)
                print(f"[OK] エンコーディング: {encoding}")
                break
            except UnicodeDecodeError:
                continue
        
        if self.df is None:
            raise ValueError("ファイルの読み込みに失敗しました")
        
        print(f"[OK] データサイズ: {len(self.df):,} 行 × {len(self.df.columns)} 列")
        print(f"[OK] メモリ使用量: {self.df.memory_usage().sum() / 1024**2:.2f} MB")
        
        self._analyze_columns()
        return self.df
    
    def _analyze_columns(self):
        """カラム構造の分析"""
        print("\n【カラム構造分析】")
        
        column_patterns = {
            'o-line__item': [],
            'c-table__body-item': [],
            'u-fw-bold': [],
            'c-label': [],
            'others': []
        }
        
        for i, col in enumerate(self.df.columns):
            col_str = str(col)
            matched = False
            for pattern in column_patterns.keys():
                if pattern in col_str and pattern != 'others':
                    column_patterns[pattern].append((i, col))
                    matched = True
                    break
            if not matched:
                column_patterns['others'].append((i, col))
        
        for pattern, cols in column_patterns.items():
            if cols:
                print(f"  {pattern}: {len(cols)} 列")
                if pattern == 'o-line__item':
                    self._analyze_desired_work_columns(cols)
        
        self.column_patterns = column_patterns
    
    def _analyze_desired_work_columns(self, cols):
        """希望勤務地カラムの詳細分析"""
        print("    希望勤務地候補の分析中...")
        
        desired_cols = []
        for idx, col in cols:
            if idx < len(self.df.columns):
                series = self.df.iloc[:, idx]
                
                pref_pattern = r'(' + '|'.join(self.prefectures) + ')'
                has_pref = series.astype(str).str.contains(pref_pattern, na=False).sum()
                
                muni_pattern = r'[市区町村郡]'
                has_muni = series.astype(str).str.contains(muni_pattern, na=False).sum()
                
                if has_pref > 0 or has_muni > 0:
                    fill_rate = max(has_pref, has_muni) / len(series) * 100
                    desired_cols.append({
                        'index': idx,
                        'column': col,
                        'prefecture_count': has_pref,
                        'municipality_count': has_muni,
                        'fill_rate': fill_rate
                    })
        
        if desired_cols:
            print(f"    → {len(desired_cols)} 列で住所データを検出")
            top_cols = sorted(desired_cols, key=lambda x: x['prefecture_count'], reverse=True)[:5]
            for col_info in top_cols:
                print(f"      列{col_info['index']}: 都道府県{col_info['prefecture_count']}件, "
                      f"市区町村{col_info['municipality_count']}件 "
                      f"(充填率: {col_info['fill_rate']:.1f}%)")
        
        self.desired_work_columns = desired_cols
    
    def process_data(self):
        """データの前処理と特徴量エンジニアリング"""
        print("\n【データ前処理】")
        
        self.df_processed = pd.DataFrame()
        self.df_processed['id'] = range(1, len(self.df) + 1)
        
        self._extract_basic_info()
        self._extract_desired_locations()
        self._extract_qualifications()
        self._analyze_geographic_patterns()
        self._analyze_mobility_patterns()
        self._cluster_analysis()
        self._assess_data_quality()
        
        print(f"[OK] 処理済みデータ: {len(self.df_processed)} 行 × {len(self.df_processed.columns)} 列")
        
        return self.df_processed
    
    def _extract_basic_info(self):
        """基本情報の抽出"""
        print("  基本情報を抽出中...")
        
        age_gender_pattern = r'(\d+)歳.*([男女])性'
        
        for col in self.df.columns[:10]:
            series = self.df[col].astype(str)
            matches = series.str.extract(age_gender_pattern)
            if matches[0].notna().sum() > len(self.df) * 0.5:
                self.df_processed['age'] = pd.to_numeric(matches[0], errors='coerce')
                self.df_processed['gender'] = matches[1].map({'男': 'M', '女': 'F'})
                print(f"    → 年齢・性別を列 '{col}' から抽出")
                break
        
        if 'age' in self.df_processed.columns:
            # 詳細な年齢層
            bins = [0, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 100]
            labels = ['Under 20', '20-24', '25-29', '30-34', '35-39',
                     '40-44', '45-49', '50-54', '55-59', '60-64',
                     '65-69', '70+']
            self.df_processed['age_group'] = pd.cut(self.df_processed['age'], 
                                                     bins=bins, labels=labels)
            
            # 世代分類（英語表記）
            self.df_processed['generation'] = pd.cut(
                self.df_processed['age'],
                bins=[0, 35, 50, 65, 100],
                labels=['Young', 'Middle', 'Senior', 'Elderly']
            )
        
        # 居住地の抽出
        if len(self.df.columns) > 1:
            residence_col = self.df.iloc[:, 1].astype(str)
            self.df_processed['residence_raw'] = residence_col
            self._split_prefecture_municipality(residence_col, 'residence')
    
    def _split_prefecture_municipality(self, series, prefix):
        """都道府県と市区町村を分離"""
        pref_pattern = '(' + '|'.join(self.prefectures) + ')'
        
        self.df_processed[f'{prefix}_pref'] = series.str.extract(pref_pattern)[0]
        
        municipalities = []
        for idx, val in enumerate(series):
            val_str = str(val)
            pref = self.df_processed[f'{prefix}_pref'].iloc[idx]
            
            if pd.notna(pref) and pref in val_str:
                remaining = val_str.split(pref)[-1]
                muni_match = self.municipality_pattern.match(remaining)
                if muni_match:
                    municipalities.append(muni_match.group(1))
                else:
                    municipalities.append(remaining.strip() if remaining.strip() else None)
            else:
                municipalities.append(None)
        
        self.df_processed[f'{prefix}_muni'] = municipalities
        
        # 地方区分の追加
        if f'{prefix}_pref' in self.df_processed.columns:
            def get_region(pref):
                for region, prefs in self.regions.items():
                    if pref in prefs:
                        return region
                return None
            
            self.df_processed[f'{prefix}_region'] = self.df_processed[f'{prefix}_pref'].apply(get_region)
    
    def _extract_desired_locations(self):
        """希望勤務地の抽出（拡張版：生データ/加工済みデータ両対応）"""
        print("  希望勤務地を抽出中...")

        # ==========================================
        # モード1: 加工済みデータ検出 + パース
        # ==========================================
        if 'desired_locations_detail' in self.df.columns:
            print("  [検出] 加工済みデータを使用（desired_locations_detail列が既存）")

            import ast

            # パース対象カラムと期待型の定義
            processed_cols_mapping = {
                'desired_locations_detail': list,
                'desired_location_count': int,
                'desired_locations': list,
                'primary_desired_location': str,
                'primary_desired_location_detail': dict,
                'location_diversity': float,
                # Phase 7用の追加列
                'qualifications_list': list,
                'qualification_categories': list,
                'qualification_levels': list
            }

            parse_error_count = 0

            # まず、すべての列をそのままコピー（基本処理）
            for col in self.df.columns:
                if col in processed_cols_mapping:
                    # 特別な処理が必要な列はスキップ（後で処理）
                    continue

                # 通常の列はそのままコピー
                self.df_processed[col] = self.df[col].copy()

            # 次に、パース/変換が必要な列を処理
            for col, expected_type in processed_cols_mapping.items():
                if col not in self.df.columns:
                    continue

                # list/dict型: 文字列からパース
                if expected_type in [list, dict]:
                    def safe_parse(x):
                        """安全なパース処理"""
                        nonlocal parse_error_count

                        if pd.isna(x):
                            return [] if expected_type == list else {}
                        if not isinstance(x, str):
                            return x  # 既にlist/dictの場合はそのまま
                        if not x.strip():
                            return [] if expected_type == list else {}

                        try:
                            return ast.literal_eval(x)
                        except (ValueError, SyntaxError) as e:
                            parse_error_count += 1
                            if parse_error_count <= 3:  # 最初の3件のみ警告
                                print(f"    [警告] {col} パース失敗: {str(x)[:50]}... ({e})")
                            return [] if expected_type == list else {}

                    self.df_processed[col] = self.df[col].apply(safe_parse)
                    total_errors = parse_error_count
                    print(f"    [パース] {col} → {expected_type.__name__}型" + (f" (エラー: {total_errors}件)" if total_errors > 0 else ""))
                    parse_error_count = 0  # リセット

                # その他の型: そのままコピー
                else:
                    self.df_processed[col] = self.df[col].copy()
                    print(f"    [コピー] {col}")

            print(f"  [OK] 加工済みデータ使用完了（{len(self.df_processed.columns)}列コピー）")
            return

        # ==========================================
        # モード2: 生データからの抽出
        # ==========================================
        print("  [検出] 生データを使用（o-line__item列から抽出）")

        if not hasattr(self, 'desired_work_columns'):
            self.desired_work_columns = []

        if len(self.desired_work_columns) == 0:
            print("  [警告] 希望勤務地カラムが見つかりません")
            print("         - 生データの場合: o-line__item列が必要です")
            print("         - 加工済みデータの場合: desired_locations_detail列が必要です")
            print("         → 希望勤務地データなしで続行します")
            return
        
        desired_locations = []
        desired_locations_detail = []
        
        for _, row in self.df.iterrows():
            locations = []
            location_details = []
            
            for col_info in self.desired_work_columns[:100]:
                idx = col_info['index']
                if idx < len(row):
                    val = str(row.iloc[idx])
                    if val and val != 'nan':
                        for pref in self.prefectures:
                            if pref in val:
                                remaining = val.split(pref)[-1] if pref in val else ''
                                muni_match = self.municipality_pattern.match(remaining)
                                
                                if muni_match:
                                    muni = muni_match.group(1)
                                    location_details.append({
                                        'prefecture': pref,
                                        'municipality': muni,
                                        'full': f"{pref}{muni}",
                                        'region': self._get_region(pref)
                                    })
                                else:
                                    location_details.append({
                                        'prefecture': pref,
                                        'municipality': '',
                                        'full': pref,
                                        'region': self._get_region(pref)
                                    })
                                
                                locations.append(pref)
                                break
            
            desired_locations.append(locations)
            desired_locations_detail.append(location_details)
        
        self.df_processed['desired_location_count'] = [len(locs) for locs in desired_locations]
        self.df_processed['desired_locations'] = desired_locations
        self.df_processed['desired_locations_detail'] = desired_locations_detail
        
        self.df_processed['primary_desired_location'] = [
            locs[0] if locs else None for locs in desired_locations
        ]
        
        self.df_processed['primary_desired_location_detail'] = [
            details[0] if details else None for details in desired_locations_detail
        ]
        
        # 希望地域の多様性スコア
        self.df_processed['location_diversity'] = [
            len(set(locs)) / len(locs) if locs else 0 for locs in desired_locations
        ]
        
        print(f"    → 平均希望勤務地数: {self.df_processed['desired_location_count'].mean():.2f}")
    
    def _get_region(self, prefecture):
        """都道府県から地方を取得"""
        for region, prefs in self.regions.items():
            if prefecture in prefs:
                return region
        return None
    
    def _extract_qualifications(self):
        """資格情報の抽出（MECE版）"""
        print("  資格情報を抽出中...")
        
        all_qual_names = []
        qual_category_map = {}
        for category, quals in self.master.QUALIFICATIONS.items():
            for qual in quals:
                all_qual_names.append(qual)
                qual_category_map[qual] = category
        
        qual_cols = []
        for i, col in enumerate(self.df.columns):
            if 'c-table__body-item' in str(col):
                qual_cols.append(i)
        
        if not qual_cols:
            print("    → 資格データ列が見つかりません")
            self.df_processed['qualification_count'] = 0
            return
        
        print(f"    → {len(qual_cols)} 個の資格データ列を検出")

        # 資格関連のカラムを事前に初期化
        self.df_processed['qualifications_list'] = [[] for _ in range(len(self.df_processed))]
        self.df_processed['qualification_count'] = 0
        self.df_processed['qualification_categories'] = [[] for _ in range(len(self.df_processed))]
        self.df_processed['qualification_levels'] = [[] for _ in range(len(self.df_processed))]

        # 各求職者の資格を抽出
        for idx in range(len(self.df_processed)):
            person_quals = []
            person_categories = set()
            
            if idx < len(self.df):
                for col_idx in qual_cols:
                    if col_idx < len(self.df.columns):
                        cell_value = self.df.iloc[idx, col_idx]
                        if pd.notna(cell_value):
                            cell_str = str(cell_value).strip()
                            
                            for qual_name in all_qual_names:
                                if qual_name in cell_str:
                                    person_quals.append(qual_name)
                                    person_categories.add(qual_category_map[qual_name])
                                    break
            
            self.df_processed.at[idx, 'qualifications_list'] = person_quals
            self.df_processed.at[idx, 'qualification_count'] = len(set(person_quals))
            self.df_processed.at[idx, 'qualification_categories'] = list(person_categories)
            
            # 資格レベル分類
            qual_levels = []
            for qual in person_quals:
                if any(x in qual for x in ['医師', '看護師', '薬剤師', '理学療法士', '介護福祉士']):
                    qual_levels.append('国家資格')
                elif any(x in qual for x in ['ケアマネ', '初任者研修', '実務者研修']):
                    qual_levels.append('公的資格')
                elif '民間' in qual:
                    qual_levels.append('民間資格')
                else:
                    qual_levels.append('その他')
            
            self.df_processed.at[idx, 'qualification_levels'] = list(set(qual_levels))
        
        self.df_processed['qualification_count'] = self.df_processed['qualification_count'].fillna(0)
        
        # 資格プロファイル
        self.df_processed['has_national_license'] = self.df_processed['qualification_levels'].apply(
            lambda x: '国家資格' in x if isinstance(x, list) else False
        )
        
        print(f"    → 平均資格保有数: {self.df_processed['qualification_count'].mean():.2f}")
    
    def _analyze_geographic_patterns(self):
        """地理的パターンの分析（居住地ベース）"""
        print("  地理的パターンを分析中...")

        # 市区町村別の集計（居住地ベースに変更）
        municipal_stats = {}
        regional_flow = defaultdict(lambda: defaultdict(int))

        for idx, row in self.df_processed.iterrows():
            # 居住地の市区町村を集計
            residence_pref = row.get('residence_pref', None)
            residence_muni = row.get('residence_muni', None)
            residence_region = row.get('residence_region', None)

            if residence_pref and residence_muni:
                key = f"{residence_pref}{residence_muni}"
                municipal_stats[key] = municipal_stats.get(key, 0) + 1

            # 希望勤務地との地域間移動パターン（従来通り）
            if 'desired_locations_detail' in self.df_processed.columns:
                details = row.get('desired_locations_detail', [])
                if isinstance(details, list) and residence_region:
                    for detail in details:
                        if detail:
                            dest_region = detail.get('region', None)
                            if dest_region:
                                regional_flow[residence_region][dest_region] += 1
        
        # 地域間移動行列
        regions_list = list(self.regions.keys())
        flow_matrix = np.zeros((len(regions_list), len(regions_list)))
        for i, from_region in enumerate(regions_list):
            for j, to_region in enumerate(regions_list):
                flow_matrix[i, j] = regional_flow[from_region][to_region]
        
        self.analysis_results['geographic_patterns'] = {
            'municipal_stats': dict(sorted(municipal_stats.items(), 
                                         key=lambda x: x[1], reverse=True)[:20]),
            'regional_flow_matrix': flow_matrix.tolist(),
            'regions': regions_list
        }
        
        print(f"    → ユニーク市区町村数: {len(municipal_stats)}")
    
    def _analyze_mobility_patterns(self):
        """移動パターンの詳細分析"""
        print("  移動パターンを分析中...")
        
        mobility_stats = {
            'same_prefecture': 0,
            'same_region': 0,
            'different_region': 0,
            'mobility_distance': []
        }
        
        for _, row in self.df_processed.iterrows():
            residence_pref = row.get('residence_pref', None)
            residence_region = row.get('residence_region', None)
            
            if residence_pref and residence_pref in self.prefecture_coords:
                res_coords = self.prefecture_coords[residence_pref]
                
                desired_prefs = row.get('desired_locations', [])
                if desired_prefs:
                    for des_pref in desired_prefs:
                        if des_pref == residence_pref:
                            mobility_stats['same_prefecture'] += 1
                        
                        des_region = self._get_region(des_pref)
                        if des_region == residence_region:
                            mobility_stats['same_region'] += 1
                        else:
                            mobility_stats['different_region'] += 1
                        
                        # 距離計算
                        if des_pref in self.prefecture_coords:
                            des_coords = self.prefecture_coords[des_pref]
                            distance = self._calculate_distance(
                                res_coords['lat'], res_coords['lng'],
                                des_coords['lat'], des_coords['lng']
                            )
                            mobility_stats['mobility_distance'].append(distance)
        
        # 移動指標の計算
        if mobility_stats['mobility_distance']:
            avg_distance = np.mean(mobility_stats['mobility_distance'])
            median_distance = np.median(mobility_stats['mobility_distance'])
        else:
            avg_distance = median_distance = 0
        
        self.analysis_results['mobility_patterns'] = {
            'same_prefecture_ratio': mobility_stats['same_prefecture'] / len(self.df_processed),
            'same_region_ratio': mobility_stats['same_region'] / len(self.df_processed),
            'average_mobility_distance': avg_distance,
            'median_mobility_distance': median_distance
        }
        
        print(f"    → 平均移動距離: {avg_distance:.1f} km")
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """ハバースイン公式による距離計算（km）"""
        R = 6371  # 地球の半径（km）
        
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        delta_lat = np.radians(lat2 - lat1)
        delta_lon = np.radians(lon2 - lon1)
        
        a = np.sin(delta_lat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c
    
    def _cluster_analysis(self):
        """クラスター分析による求職者セグメンテーション"""
        print("  クラスター分析を実行中...")
        
        # 特徴量の準備
        features = []
        valid_indices = []
        
        for idx, row in self.df_processed.iterrows():
            if pd.notna(row.get('age')) and pd.notna(row.get('desired_location_count')):
                features.append([
                    row.get('age', 0),
                    1 if row.get('gender') == 'M' else 0,
                    row.get('desired_location_count', 0),
                    row.get('qualification_count', 0),
                    row.get('location_diversity', 0),
                    1 if row.get('has_national_license', False) else 0
                ])
                valid_indices.append(idx)
        
        if len(features) < 10:
            print("    → データ不足のためクラスター分析をスキップ")
            return
        
        # 正規化
        X = np.array(features)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # 最適クラスター数の決定（エルボー法）
        inertias = []
        silhouettes = []
        K_range = range(2, min(11, len(X)//10))
        
        for k in K_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(X_scaled)
            inertias.append(kmeans.inertia_)
            if k < len(X):
                silhouettes.append(silhouette_score(X_scaled, kmeans.labels_))
        
        # 最適クラスター数（シルエットスコアが最大）
        if silhouettes:
            optimal_k = list(K_range)[np.argmax(silhouettes)]
        else:
            optimal_k = 3
        
        # クラスタリング実行
        kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)
        
        # クラスターをDataFrameに追加
        self.df_processed['cluster'] = -1
        for i, idx in enumerate(valid_indices):
            self.df_processed.at[idx, 'cluster'] = clusters[i]
        
        # クラスター特性の分析
        cluster_profiles = []
        for c in range(optimal_k):
            cluster_mask = self.df_processed['cluster'] == c
            profile = {
                'cluster_id': c,
                'size': cluster_mask.sum(),
                'avg_age': self.df_processed[cluster_mask]['age'].mean(),
                'gender_ratio_m': (self.df_processed[cluster_mask]['gender'] == 'M').mean(),
                'avg_qualifications': self.df_processed[cluster_mask]['qualification_count'].mean(),
                'avg_desired_locations': self.df_processed[cluster_mask]['desired_location_count'].mean(),
                'national_license_ratio': self.df_processed[cluster_mask]['has_national_license'].mean()
            }
            cluster_profiles.append(profile)
        
        self.analysis_results['clusters'] = {
            'optimal_k': optimal_k,
            'profiles': cluster_profiles,
            'silhouette_score': silhouettes[optimal_k-2] if silhouettes else None
        }
        
        print(f"    → {optimal_k}個のクラスターを検出")
    
    def _assess_data_quality(self):
        """データ品質の評価"""
        print("  データ品質を評価中...")
        
        missing_ratio = self.df_processed.isnull().sum() / len(self.df_processed)
        
        quality_metrics = {
            'completeness': 1 - missing_ratio.mean(),
            'age_validity': self.df_processed['age'].between(18, 80).mean() if 'age' in self.df_processed else 0,
            'gender_validity': self.df_processed['gender'].isin(['M', 'F']).mean() if 'gender' in self.df_processed else 0,
            'location_validity': self.df_processed['primary_desired_location'].notna().mean() if 'primary_desired_location' in self.df_processed else 0
        }
        
        overall_quality = np.mean(list(quality_metrics.values()))
        print(f"    → データ品質スコア: {overall_quality:.2%}")
        
        self.analysis_results['data_quality'] = quality_metrics
    
    def advanced_visualizations(self):
        """拡張可視化機能"""
        print("\n【拡張可視化分析】")
        
        # Figure設定
        fig = plt.figure(figsize=(24, 20))
        
        # 1. 年齢分布（ヒストグラム＋KDE）
        ax1 = plt.subplot(4, 4, 1)
        if 'age' in self.df_processed.columns:
            self.df_processed['age'].hist(bins=30, edgecolor='black', alpha=0.7, ax=ax1, color='skyblue')
            self.df_processed['age'].plot(kind='kde', ax=ax1, color='red', secondary_y=True)
            ax1.set_title('Age Distribution with KDE')
            ax1.set_xlabel('Age')
            ax1.set_ylabel('Count')
            ax1.grid(True, alpha=0.3)
        
        # 2. 性別×世代のヒートマップ
        ax2 = plt.subplot(4, 4, 2)
        if 'generation' in self.df_processed.columns and 'gender' in self.df_processed.columns:
            cross_tab = pd.crosstab(self.df_processed['generation'], self.df_processed['gender'])
            sns.heatmap(cross_tab, annot=True, fmt='d', cmap='YlOrRd', ax=ax2)
            ax2.set_title('Generation x Gender Heatmap')
        
        # 3. 資格カテゴリー分布（円グラフ）
        ax3 = plt.subplot(4, 4, 3)
        if 'qualification_categories' in self.df_processed.columns:
            all_categories = []
            for cats in self.df_processed['qualification_categories']:
                if isinstance(cats, list):
                    all_categories.extend(cats)
            
            if all_categories:
                cat_counts = Counter(all_categories)
                ax3.pie(cat_counts.values(), labels=cat_counts.keys(), autopct='%1.1f%%')
                ax3.set_title('Qualification Categories')
        
        # 4. 地域間移動フロー（マトリックス）
        ax4 = plt.subplot(4, 4, 4)
        if 'geographic_patterns' in self.analysis_results:
            flow_matrix = np.array(self.analysis_results['geographic_patterns']['regional_flow_matrix'])
            regions = self.analysis_results['geographic_patterns']['regions']
            
            if flow_matrix.size > 0:
                sns.heatmap(flow_matrix, annot=False, cmap='Blues', ax=ax4,
                           xticklabels=regions, yticklabels=regions)
                ax4.set_title('Regional Flow Matrix')
                ax4.set_xlabel('To')
                ax4.set_ylabel('From')
        
        # 5. 希望勤務地数の分布（箱ひげ図）
        ax5 = plt.subplot(4, 4, 5)
        if 'desired_location_count' in self.df_processed.columns and 'generation' in self.df_processed.columns:
            self.df_processed.boxplot(column='desired_location_count', by='generation', ax=ax5)
            ax5.set_title('Desired Locations by Generation')
            ax5.set_xlabel('Generation')
            ax5.set_ylabel('Count')
        
        # 6. 資格保有数の分布（バイオリンプロット）
        ax6 = plt.subplot(4, 4, 6)
        if 'qualification_count' in self.df_processed.columns and 'gender' in self.df_processed.columns:
            data_for_violin = [
                self.df_processed[self.df_processed['gender'] == 'M']['qualification_count'].dropna(),
                self.df_processed[self.df_processed['gender'] == 'F']['qualification_count'].dropna()
            ]
            if all(len(d) > 0 for d in data_for_violin):
                ax6.violinplot(data_for_violin, positions=[1, 2], showmeans=True, showmedians=True)
                ax6.set_xticks([1, 2])
                ax6.set_xticklabels(['Male', 'Female'])
                ax6.set_title('Qualifications by Gender')
                ax6.set_ylabel('Count')
        
        # 7. クラスター分析結果（散布図）
        ax7 = plt.subplot(4, 4, 7)
        if 'cluster' in self.df_processed.columns:
            valid_data = self.df_processed[self.df_processed['cluster'] != -1]
            if len(valid_data) > 0:
                scatter = ax7.scatter(valid_data['age'], 
                                     valid_data['qualification_count'],
                                     c=valid_data['cluster'], 
                                     cmap='viridis',
                                     alpha=0.6)
                ax7.set_title('Cluster Analysis Results')
                ax7.set_xlabel('Age')
                ax7.set_ylabel('Qualifications')
                plt.colorbar(scatter, ax=ax7, label='Cluster')
        
        # 8. 市区町村TOP20（横棒グラフ）
        ax8 = plt.subplot(4, 4, 8)
        if 'geographic_patterns' in self.analysis_results:
            muni_stats = self.analysis_results['geographic_patterns'].get('municipal_stats', {})
            if muni_stats:
                top_munis = list(muni_stats.items())[:20]
                if top_munis:
                    munis, counts = zip(*top_munis)
                    y_pos = np.arange(len(munis))
                    ax8.barh(y_pos, counts, color='#FFA500')
                    ax8.set_yticks(y_pos)
                    ax8.set_yticklabels([f"City{i+1}" for i in range(len(munis))], fontsize=7)
                    ax8.set_title('Top 20 Municipalities')
                    ax8.set_xlabel('Count')
                    ax8.invert_yaxis()
        
        # 9. 年齢と希望勤務地数の相関（回帰線付き）
        ax9 = plt.subplot(4, 4, 9)
        if 'age' in self.df_processed.columns and 'desired_location_count' in self.df_processed.columns:
            valid_data = self.df_processed[['age', 'desired_location_count']].dropna()
            if len(valid_data) > 10:
                ax9.scatter(valid_data['age'], valid_data['desired_location_count'], alpha=0.3)
                z = np.polyfit(valid_data['age'], valid_data['desired_location_count'], 1)
                p = np.poly1d(z)
                ax9.plot(valid_data['age'].sort_values(), 
                        p(valid_data['age'].sort_values()), 
                        "r-", linewidth=2)
                ax9.set_title('Age vs Desired Locations')
                ax9.set_xlabel('Age')
                ax9.set_ylabel('Desired Location Count')
        
        # 10. 地域別求職者分布（円グラフ）
        ax10 = plt.subplot(4, 4, 10)
        if 'residence_region' in self.df_processed.columns:
            region_counts = self.df_processed['residence_region'].value_counts()
            if len(region_counts) > 0:
                ax10.pie(region_counts.values, labels=region_counts.index, autopct='%1.1f%%')
                ax10.set_title('Regional Distribution')
        
        # 11. 移動距離分布（ヒストグラム）
        ax11 = plt.subplot(4, 4, 11)
        if 'mobility_patterns' in self.analysis_results:
            avg_dist = self.analysis_results['mobility_patterns'].get('average_mobility_distance', 0)
            ax11.text(0.5, 0.5, f'Average Mobility\n{avg_dist:.1f} km', 
                     ha='center', va='center', fontsize=14, fontweight='bold')
            ax11.set_xlim(0, 1)
            ax11.set_ylim(0, 1)
            ax11.axis('off')
            ax11.set_title('Mobility Metrics')
        
        # 12. データ品質スコア（レーダーチャート風）
        ax12 = plt.subplot(4, 4, 12)
        if 'data_quality' in self.analysis_results:
            quality = self.analysis_results['data_quality']
            metrics = list(quality.keys())
            scores = list(quality.values())
            
            y_pos = np.arange(len(metrics))
            bars = ax12.barh(y_pos, scores, color='#E74C3C', alpha=0.7)
            ax12.set_yticks(y_pos)
            ax12.set_yticklabels(metrics)
            ax12.set_xlabel('Score')
            ax12.set_xlim(0, 1)
            ax12.set_title('Data Quality Scores')
            
            for i, (bar, score) in enumerate(zip(bars, scores)):
                ax12.text(score + 0.02, bar.get_y() + bar.get_height()/2, 
                        f'{score:.2f}', va='center')
        
        # 13-16. 地図可視化（日本地図上のプロット）
        ax13 = plt.subplot(4, 4, 13)
        self._plot_japan_map(ax13, 'residence')
        
        ax14 = plt.subplot(4, 4, 14)
        self._plot_japan_map(ax14, 'desired')
        
        ax15 = plt.subplot(4, 4, 15)
        self._plot_flow_map(ax15)
        
        ax16 = plt.subplot(4, 4, 16)
        self._plot_heatmap_on_map(ax16)
        
        plt.tight_layout()
        
        # 保存
        try:
            plt.savefig('advanced_analysis.png', dpi=100, bbox_inches='tight')
            print("→ 拡張分析グラフを保存しました（advanced_analysis.png）")
        except Exception as e:
            print(f"→ グラフ保存時にエラー: {e}")
        
        plt.show()
    
    def _plot_japan_map(self, ax, data_type='residence'):
        """日本地図上にデータをプロット"""
        ax.set_title(f'{data_type.capitalize()} Distribution Map')
        
        # 日本の輪郭（簡易版）
        japan_lat = [24, 46]
        japan_lng = [122, 146]
        ax.set_xlim(japan_lng)
        ax.set_ylim(japan_lat)
        
        # 都道府県ごとの集計
        if data_type == 'residence':
            col_name = 'residence_pref'
        else:
            col_name = 'primary_desired_location'
        
        if col_name in self.df_processed.columns:
            pref_counts = self.df_processed[col_name].value_counts()
            
            for pref, coords in self.prefecture_coords.items():
                count = pref_counts.get(pref, 0)
                if count > 0:
                    size = np.sqrt(count) * 10
                    ax.scatter(coords['lng'], coords['lat'], 
                              s=size, alpha=0.6, 
                              c='red' if data_type == 'residence' else 'blue')
        
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.grid(True, alpha=0.3)
    
    def _plot_flow_map(self, ax):
        """移動フローマップ"""
        ax.set_title('Migration Flow Map')
        
        japan_lat = [24, 46]
        japan_lng = [122, 146]
        ax.set_xlim(japan_lng)
        ax.set_ylim(japan_lat)
        
        # 移動パターンの可視化
        flow_counts = defaultdict(int)
        
        for _, row in self.df_processed.iterrows():
            from_pref = row.get('residence_pref')
            to_prefs = row.get('desired_locations', [])
            
            if from_pref and from_pref in self.prefecture_coords:
                from_coords = self.prefecture_coords[from_pref]
                
                for to_pref in to_prefs[:3]:  # 最初の3つまで
                    if to_pref in self.prefecture_coords and to_pref != from_pref:
                        to_coords = self.prefecture_coords[to_pref]
                        flow_counts[(from_pref, to_pref)] += 1
        
        # フローの描画
        for (from_pref, to_pref), count in flow_counts.items():
            if count > 5:  # 閾値以上のみ表示
                from_coords = self.prefecture_coords[from_pref]
                to_coords = self.prefecture_coords[to_pref]
                
                ax.plot([from_coords['lng'], to_coords['lng']], 
                       [from_coords['lat'], to_coords['lat']],
                       'b-', alpha=min(count/50, 0.5), linewidth=min(count/10, 3))
        
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.grid(True, alpha=0.3)
    
    def _plot_heatmap_on_map(self, ax):
        """ヒートマップ風の地図"""
        ax.set_title('Demand Heatmap')
        
        japan_lat = [24, 46]
        japan_lng = [122, 146]
        ax.set_xlim(japan_lng)
        ax.set_ylim(japan_lat)
        
        # 希望勤務地の密度を計算
        all_coords = []
        for _, row in self.df_processed.iterrows():
            desired_prefs = row.get('desired_locations', [])
            for pref in desired_prefs:
                if pref in self.prefecture_coords:
                    coords = self.prefecture_coords[pref]
                    all_coords.append([coords['lng'], coords['lat']])
        
        if all_coords:
            coords_array = np.array(all_coords)
            
            # グリッド作成
            x = np.linspace(japan_lng[0], japan_lng[1], 50)
            y = np.linspace(japan_lat[0], japan_lat[1], 50)
            X, Y = np.meshgrid(x, y)
            
            # 密度計算（簡易版）
            Z = np.zeros_like(X)
            for coord in coords_array:
                dist = np.sqrt((X - coord[0])**2 + (Y - coord[1])**2)
                Z += np.exp(-dist**2 / 10)
            
            # ヒートマップ描画
            im = ax.contourf(X, Y, Z, levels=20, cmap='YlOrRd', alpha=0.6)
            plt.colorbar(im, ax=ax, label='Demand Density')
        
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.grid(True, alpha=0.3)
    
    def generate_advanced_insights(self):
        """拡張インサイト生成"""
        print("\n【拡張インサイト分析】")
        print("=" * 60)
        
        insights = []
        
        # 1. 世代別分析
        if 'generation' in self.df_processed.columns:
            # 集計する列を動的に決定
            agg_cols = {'age': 'mean'}
            if 'qualification_count' in self.df_processed.columns:
                agg_cols['qualification_count'] = 'mean'
            if 'desired_location_count' in self.df_processed.columns:
                agg_cols['desired_location_count'] = 'mean'

            gen_stats = self.df_processed.groupby('generation').agg(agg_cols)

            finding_parts = []
            if 'qualification_count' in gen_stats.columns:
                finding_parts.append(f'世代別の平均資格数: {gen_stats["qualification_count"].to_dict()}')
            if 'desired_location_count' in gen_stats.columns:
                finding_parts.append(f'世代別の平均希望勤務地数: {gen_stats["desired_location_count"].to_dict()}')

            if finding_parts:
                insights.append({
                    'category': '世代別特性',
                    'finding': ', '.join(finding_parts),
                    'recommendation': '世代に応じたキャリア支援戦略の差別化'
            })
        
        # 2. クラスター分析結果
        if 'clusters' in self.analysis_results:
            clusters = self.analysis_results['clusters']
            if clusters.get('profiles'):
                insights.append({
                    'category': 'セグメンテーション',
                    'finding': f'{clusters["optimal_k"]}個の求職者セグメントを検出',
                    'recommendation': 'セグメント別のマッチング戦略の最適化'
                })
        
        # 3. 地域間移動パターン
        if 'mobility_patterns' in self.analysis_results:
            mobility = self.analysis_results['mobility_patterns']
            insights.append({
                'category': '移動傾向',
                'finding': f'平均移動距離: {mobility.get("average_mobility_distance", 0):.1f}km',
                'recommendation': '通勤圏を考慮した求人マッチングの実施'
            })
        
        # 4. 資格プロファイル
        if 'has_national_license' in self.df_processed.columns:
            national_ratio = self.df_processed['has_national_license'].mean()
            insights.append({
                'category': '資格保有',
                'finding': f'国家資格保有率: {national_ratio:.1%}',
                'recommendation': '資格レベルに応じた求人提案の差別化'
            })
        
        for insight in insights:
            print(f"\n【{insight['category']}】")
            print(f"  発見: {insight['finding']}")
            print(f"  提案: {insight['recommendation']}")
        
        print("\n" + "=" * 60)
        
        self.analysis_results['advanced_insights'] = insights
        return insights
    

    # ==========================================================
    # Phase 6: フロー・移動パターン分析（統合版）
    # ==========================================================

    def _analyze_flow(self, df, residence_col='residence_muni', desired_col='desired_muni'):
        """
        自治体間フローを分析

        Args:
            df: 分析対象DataFrame
            residence_col: 居住地市区町村カラム
            desired_col: 希望勤務地市区町村カラム

        Returns:
            (edges_df, nodes_df)のタプル
        """
        # エッジ集計
        df_clean = df[[residence_col, desired_col]].dropna()

        if len(df_clean) == 0:
            empty_edges = pd.DataFrame(columns=['Source_Municipality', 'Target_Municipality', 'Flow_Count'])
            empty_nodes = pd.DataFrame(columns=['Municipality', 'In_Degree', 'Out_Degree', 'Total_Degree', 'Centrality_Type'])
            return empty_edges, empty_nodes

        # グループ化して集計
        edges_df = df_clean.groupby([residence_col, desired_col]).size().reset_index(name='Flow_Count')
        edges_df.columns = ['Source_Municipality', 'Target_Municipality', 'Flow_Count']
        edges_df = edges_df.sort_values('Flow_Count', ascending=False).reset_index(drop=True)

        # ノード次数
        nodes_df = self._calculate_node_degree(edges_df)

        return edges_df, nodes_df

    def _calculate_node_degree(self, edges_df):
        """ノードの次数（中心性の簡易指標）を計算"""
        if edges_df.empty:
            return pd.DataFrame(columns=['Municipality', 'In_Degree', 'Out_Degree', 'Total_Degree', 'Centrality_Type'])

        # In-degree: 流入
        in_degree = edges_df.groupby('Target_Municipality')['Flow_Count'].sum()

        # Out-degree: 流出
        out_degree = edges_df.groupby('Source_Municipality')['Flow_Count'].sum()

        # 統合
        nodes = pd.DataFrame({'In_Degree': in_degree, 'Out_Degree': out_degree}).fillna(0)
        nodes['Total_Degree'] = nodes['In_Degree'] + nodes['Out_Degree']

        # 中心性タイプ判定
        nodes['Centrality_Type'] = nodes.apply(
            lambda row: self._classify_centrality(row['In_Degree'], row['Out_Degree'], row['Total_Degree']),
            axis=1
        )

        nodes = nodes.sort_values('Total_Degree', ascending=False)
        return nodes.reset_index().rename(columns={'index': 'Municipality'})

    def _classify_centrality(self, in_deg, out_deg, total):
        """ノードの中心性タイプを分類"""
        if total == 0:
            return 'isolated'

        in_ratio = in_deg / total if total > 0 else 0

        if in_ratio > 0.7:
            return 'hub'  # 求人集中
        elif in_ratio < 0.3:
            return 'source'  # 居住地
        elif 0.45 < in_ratio < 0.55:
            return 'balanced'  # バランス型
        elif in_ratio >= 0.55:
            return 'hub_leaning'
        else:
            return 'source_leaning'

    def _calculate_distances_phase6(self, df, res_lat='residence_lat', res_lng='residence_lng',
                                     des_lat='desired_lat', des_lng='desired_lng'):
        """居住地と希望勤務地の距離を計算"""
        df['geo_distance_km'] = df.apply(
            lambda row: self._haversine_distance(
                (row[res_lat], row[res_lng]),
                (row[des_lat], row[des_lng])
            ),
            axis=1
        )
        return df

    def _haversine_distance(self, coord1, coord2):
        """2点間の距離をHaversine公式で計算（km）"""
        from math import radians, sin, cos, sqrt, atan2

        lat1, lon1 = coord1
        lat2, lon2 = coord2

        # 欠損値チェック
        if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
            return None

        # 同一座標チェック
        if lat1 == lat2 and lon1 == lon2:
            return 0.0

        R = 6371  # 地球の半径（km）

        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)

        a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return round(R * c, 2)

    def _haversine_distance_vectorized(self, lat1, lon1, lat2, lon2):
        """
        ベクトル化されたHaversine距離計算（numpy配列対応）

        最適化内容:
        - numpy配列での一括計算により10-100倍高速化
        - 22,815回のループを1回の配列操作に削減

        Args:
            lat1: 緯度1の配列
            lon1: 経度1の配列
            lat2: 緯度2の配列
            lon2: 経度2の配列

        Returns:
            numpy.ndarray: 距離の配列（km）
        """
        import numpy as np

        # numpy配列に変換
        lat1 = np.array(lat1, dtype=float)
        lon1 = np.array(lon1, dtype=float)
        lat2 = np.array(lat2, dtype=float)
        lon2 = np.array(lon2, dtype=float)

        # 欠損値チェック
        valid_mask = ~(np.isnan(lat1) | np.isnan(lon1) | np.isnan(lat2) | np.isnan(lon2))

        # 結果配列の初期化
        distances = np.full(len(lat1), np.nan)

        if np.any(valid_mask):
            # 有効なデータのみで計算
            lat1_valid = lat1[valid_mask]
            lon1_valid = lon1[valid_mask]
            lat2_valid = lat2[valid_mask]
            lon2_valid = lon2[valid_mask]

            # 同一座標チェック
            same_coords = (lat1_valid == lat2_valid) & (lon1_valid == lon2_valid)

            # Haversine計算（ベクトル化）
            R = 6371  # 地球の半径（km）

            lat1_rad = np.radians(lat1_valid)
            lat2_rad = np.radians(lat2_valid)
            dlat = np.radians(lat2_valid - lat1_valid)
            dlon = np.radians(lon2_valid - lon1_valid)

            a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
            c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))

            result = np.round(R * c, 2)

            # 同一座標は0に設定
            result[same_coords] = 0.0

            # 有効な結果を元の配列に戻す
            distances[valid_mask] = result

        return distances

    def _analyze_proximity(self, df, distance_col='geo_distance_km'):
        """近接性を分析（距離バケット別統計）"""
        df = df.copy()
        df['proximity_bucket'] = df[distance_col].apply(self._classify_distance_bucket)

        # 集計
        agg_dict = {distance_col: ['count', 'mean', 'median', 'std']}
        if 'age' in df.columns:
            agg_dict['age'] = 'mean'

        proximity_stats = df.groupby('proximity_bucket').agg(agg_dict).reset_index()

        # カラム名をフラット化
        proximity_stats.columns = ['_'.join(col).strip('_') if isinstance(col, tuple) else col
                                     for col in proximity_stats.columns]

        # カラム名を整理
        proximity_stats = proximity_stats.rename(columns={
            f'{distance_col}_count': 'Count',
            f'{distance_col}_mean': 'Avg_Distance_km',
            f'{distance_col}_median': 'Median_Distance_km',
            f'{distance_col}_std': 'Std_Distance_km',
            'age_mean': 'Avg_Age'
        })

        # バケット順でソート
        bucket_order = ['same_muni', 'under_10km', '10_30km', '30_50km', '50_100km', 'over_100km', 'unknown']
        proximity_stats['bucket_order'] = proximity_stats['proximity_bucket'].map({b: i for i, b in enumerate(bucket_order)})
        proximity_stats = proximity_stats.sort_values('bucket_order').drop('bucket_order', axis=1)

        return proximity_stats.reset_index(drop=True)

    def _classify_distance_bucket(self, distance):
        """距離をバケットに分類"""
        if pd.isna(distance):
            return 'unknown'
        if distance == 0:
            return 'same_muni'
        if distance < 10:
            return 'under_10km'
        elif distance < 30:
            return '10_30km'
        elif distance < 50:
            return '30_50km'
        elif distance < 100:
            return '50_100km'
        else:
            return 'over_100km'


    # ==========================================================
    # Phase 1: 基盤データエクスポート
    # ==========================================================

    def export_phase1_data(self, output_dir='gas_output_phase1'):
        """
        Phase 1: 基盤データのエクスポート

        出力ファイル:
        - MapMetrics.csv: [都道府県, '', 都道府県, カウント, 緯度, 経度]
        - Applicants.csv: [ID, 性別, 年齢, 年齢バケット, 居住地都道府県, '']
        - DesiredWork.csv: [申請者ID, 希望勤務地都道府県, '', 希望勤務地都道府県]
        - AggDesired.csv: MapMetricsの最初の4列
        """
        print("\n" + "=" * 60)
        print("Phase 1: 基盤データエクスポート")
        print("=" * 60)

        if self.df is None:
            print("エラー: データが読み込まれていません")
            return None

        # 出力ディレクトリ作成
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        print(f"出力ディレクトリ: {output_path}")

        exported_files = []

        try:
            # ステップ1: データ処理（求職者情報の抽出）
            print("\n[1/5] データ処理中...")
            processed_data = self._process_applicant_data()

            # ステップ2: MapMetrics生成
            print("\n[2/5] MapMetrics生成中...")
            map_metrics = self._generate_map_metrics(processed_data)
            map_metrics_file = output_path / 'MapMetrics.csv'
            map_metrics.to_csv(map_metrics_file, index=False, encoding='utf-8-sig')
            exported_files.append(map_metrics_file)
            print(f"  [OK] MapMetrics.csv: {len(map_metrics)} 件")

            # ステップ3: Applicants生成
            print("\n[3/5] Applicants生成中...")
            applicants = self._generate_applicants(processed_data)
            applicants_file = output_path / 'Applicants.csv'
            applicants.to_csv(applicants_file, index=False, encoding='utf-8-sig')
            exported_files.append(applicants_file)
            print(f"  [OK] Applicants.csv: {len(applicants)} 件")

            # ステップ4: DesiredWork生成
            print("\n[4/5] DesiredWork生成中...")
            desired_work = self._generate_desired_work(processed_data)
            desired_work_file = output_path / 'DesiredWork.csv'
            desired_work.to_csv(desired_work_file, index=False, encoding='utf-8-sig')
            exported_files.append(desired_work_file)
            print(f"  [OK] DesiredWork.csv: {len(desired_work)} 件")

            # ステップ5: AggDesired生成（MapMetricsから）
            print("\n[5/5] AggDesired生成中...")
            if len(map_metrics) > 0:
                agg_desired = map_metrics[['都道府県', '市区町村', 'キー', 'カウント']].copy()
            else:
                # MapMetricsが空の場合、空のDataFrameを作成
                agg_desired = pd.DataFrame(columns=['都道府県', '市区町村', 'キー', 'カウント'])
            agg_desired_file = output_path / 'AggDesired.csv'
            agg_desired.to_csv(agg_desired_file, index=False, encoding='utf-8-sig')
            exported_files.append(agg_desired_file)
            print(f"  [OK] AggDesired.csv: {len(agg_desired)} 件")

            # サマリー表示
            print("\n" + "=" * 60)
            print("Phase 1 エクスポート完了")
            print("=" * 60)
            print(f"出力ファイル: {len(exported_files)} 件")
            for f in exported_files:
                print(f"  - {f.name}")
            print(f"\n出力先: {output_path.absolute()}")

            return exported_files

        except Exception as e:
            print(f"\nエラーが発生しました: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _process_applicant_data(self):
        """
        求職者データの処理（df_processedを利用）

        Returns:
            dict: {
                'applicants': DataFrame(ID, 性別, 年齢, 居住地都道府県),
                'desired_locations': list[(申請者ID, 希望勤務地都道府県, 市区町村)],
                'location_counts': dict{都道府県: カウント},
                'residence_counts': dict{都道府県: カウント}  # 居住地のカウント
            }
        """
        print("  データ処理を開始...")

        applicants_data = []
        desired_locations = []
        location_counts = {}  # 希望勤務地のカウント
        residence_counts = {}  # 居住地のカウント

        # df_processedから求職者情報を抽出（既に前処理済み）
        for idx in range(len(self.df_processed)):
            applicant_id = f"ID_{idx + 1}"
            row_data = self.df_processed.iloc[idx]

            # 年齢・性別の抽出
            age = None
            gender = None

            if 'age' in self.df_processed.columns:
                age_val = row_data['age']
                if pd.notna(age_val):
                    age = int(age_val)

            if 'gender' in self.df_processed.columns:
                gender_val = row_data['gender']
                if pd.notna(gender_val):
                    # 'M' → '男性', 'F' → '女性'
                    gender = '男性' if gender_val == 'M' else '女性' if gender_val == 'F' else ''

            # 居住地の抽出（df_processedから）
            residence_pref = row_data.get('residence_pref', '')
            residence_municipality = row_data.get('residence_muni', '')

            # 居住地のカウント（MapMetrics用）
            if residence_pref:
                residence_key = f"{residence_pref}{residence_municipality}" if residence_municipality else residence_pref
                residence_counts[residence_key] = residence_counts.get(residence_key, 0) + 1

            # 資格情報の抽出
            qualification_count = row_data.get('qualification_count', 0) if 'qualification_count' in self.df_processed.columns else 0
            has_national_license = row_data.get('has_national_license', False) if 'has_national_license' in self.df_processed.columns else False
            qualifications_list = row_data.get('qualifications_list', []) if 'qualifications_list' in self.df_processed.columns else []
            qualification_categories = row_data.get('qualification_categories', []) if 'qualification_categories' in self.df_processed.columns else []

            # 求職者データを保存（資格情報を含む）
            applicants_data.append({
                'ID': applicant_id,
                '性別': gender if gender else '',
                '年齢': age if age is not None else '',
                '居住地_都道府県': residence_pref if residence_pref else '',
                '居住地_市区町村': residence_municipality if residence_municipality else '',
                '資格数': int(qualification_count),
                '国家資格保有': '有' if has_national_license else '無',
                '資格リスト': ', '.join(qualifications_list) if qualifications_list else '',
                '資格カテゴリ': ', '.join(qualification_categories) if qualification_categories else ''
            })

            # 希望勤務地の抽出（df_processedのdesired_locations_detailから）
            if 'desired_locations_detail' in self.df_processed.columns:
                desired_details = row_data['desired_locations_detail']
                if isinstance(desired_details, list):
                    for detail in desired_details:
                        if isinstance(detail, dict):
                            desired_pref = detail.get('prefecture', '')
                            desired_municipality = detail.get('municipality', '')

                            if desired_pref:
                                # タプルに市区町村も含める
                                desired_locations.append((applicant_id, desired_pref, desired_municipality if desired_municipality else ''))
                                # キーは "都道府県+市区町村" の形式
                                location_key = f"{desired_pref}{desired_municipality}" if desired_municipality else desired_pref
                                location_counts[location_key] = location_counts.get(location_key, 0) + 1

        print(f"  [OK] 処理完了: {len(applicants_data)} 人")
        print(f"  [OK] 希望勤務地: {len(desired_locations)} 件")
        print(f"  [OK] 希望勤務地の都道府県数: {len(location_counts)} 箇所")
        print(f"  [OK] 居住地の都道府県数: {len(residence_counts)} 箇所")

        return {
            'applicants': pd.DataFrame(applicants_data),
            'desired_locations': desired_locations,
            'location_counts': location_counts,
            'residence_counts': residence_counts
        }

    def _generate_map_metrics(self, processed_data):
        """
        MapMetricsデータの生成（区レベルを保持）
        ※希望勤務地ベースでカウント（事業所の住所への希望者数）
        ※政令指定都市の区レベルまで詳細データを保持

        Args:
            processed_data: _process_applicant_data()の戻り値

        Returns:
            DataFrame: [都道府県, 市区町村, キー, カウント, 緯度, 経度]
        """
        import time

        # 希望勤務地のカウントを使用（区レベルを保持）
        location_counts = processed_data['location_counts']

        print(f"\n  [MapMetrics] 希望勤務地データ: {len(location_counts)}件（区レベル保持）")

        # 区レベルのデータをそのまま使用（集約しない）
        city_level_counts = location_counts

        # geocoding処理
        map_metrics_data = []
        total = len(city_level_counts)
        cache_hits = 0
        api_calls = 0
        start_time = time.time()

        print(f"\n  MapMetrics生成中... (全{total}件)")

        # 新規取得が必要な件数を事前計算
        new_addresses = []
        for location_key in city_level_counts.keys():
            pref, municipality = self._extract_prefecture_municipality(location_key)
            if municipality:
                full_address = f"{pref}{municipality}"
                if full_address not in self.geocache:
                    new_addresses.append(full_address)

        if new_addresses:
            print(f"  新規geocoding: {len(new_addresses)}件 (キャッシュ済み: {total - len(new_addresses)}件)")
            estimated_seconds = len(new_addresses) * 0.5
            print(f"  推定時間: 約{int(estimated_seconds // 60)}分{int(estimated_seconds % 60)}秒")
        else:
            print(f"  全てキャッシュ済み（API呼び出し不要）")

        # メイン処理ループ
        for idx, (location_key, count) in enumerate(city_level_counts.items(), 1):
            # location_keyは "都道府県+市区町村" または "都道府県" の形式
            # 都道府県と市区町村を分離
            pref, municipality = self._extract_prefecture_municipality(location_key)

            if pref:
                # キャッシュヒット判定
                was_cached = False
                if municipality:
                    full_address = f"{pref}{municipality}"
                    was_cached = (full_address in self.geocache)

                # 座標取得（市区町村レベル優先）
                lat, lng = self._get_coords(pref, municipality)

                # 統計更新
                if was_cached:
                    cache_hits += 1
                elif municipality:
                    api_calls += 1

                # 進捗表示（10件ごと）
                if idx % 10 == 0 or idx == total:
                    elapsed = time.time() - start_time
                    percentage = idx * 100 / total
                    print(f"  進捗: {idx}/{total} ({percentage:.1f}%) - 経過時間: {int(elapsed)}秒")

                map_metrics_data.append({
                    '都道府県': pref,
                    '市区町村': municipality if municipality else '',
                    'キー': location_key,
                    'カウント': count,
                    '緯度': lat,
                    '経度': lng
                })

        # 統計サマリー表示
        total_time = time.time() - start_time
        print(f"  MapMetrics生成完了 (処理時間: {int(total_time)}秒)")
        print(f"  - API呼び出し: {api_calls}件")
        print(f"  - キャッシュヒット: {cache_hits}件")
        print(f"  - 合計: {total}件")

        # キャッシュを保存
        if api_calls > 0:
            self.save_geocache()

        df_map_metrics = pd.DataFrame(map_metrics_data)

        # カウント降順でソート
        if len(df_map_metrics) > 0:
            df_map_metrics = df_map_metrics.sort_values('カウント', ascending=False).reset_index(drop=True)

        return df_map_metrics

    def _generate_applicants(self, processed_data):
        """
        Applicantsデータの生成

        Args:
            processed_data: _process_applicant_data()の戻り値

        Returns:
            DataFrame: [ID, 性別, 年齢, 年齢バケット, 居住地_都道府県, 居住地_市区町村]
        """
        df_applicants = processed_data['applicants'].copy()

        # 年齢バケットの生成
        def get_age_bucket(age):
            if pd.isna(age) or age == '':
                return ''
            age = int(age)
            if age < 30:
                return '20代'
            elif age < 40:
                return '30代'
            elif age < 50:
                return '40代'
            elif age < 60:
                return '50代'
            elif age < 70:
                return '60代'
            else:
                return '70歳以上'

        df_applicants['年齢バケット'] = df_applicants['年齢'].apply(get_age_bucket)

        # カラム順序を整える（資格情報を含む）
        columns = ['ID', '性別', '年齢', '年齢バケット', '居住地_都道府県', '居住地_市区町村']

        # 資格情報カラムを追加（存在する場合のみ）
        if '資格数' in df_applicants.columns:
            columns.append('資格数')
        if '国家資格保有' in df_applicants.columns:
            columns.append('国家資格保有')
        if '資格リスト' in df_applicants.columns:
            columns.append('資格リスト')
        if '資格カテゴリ' in df_applicants.columns:
            columns.append('資格カテゴリ')

        df_applicants = df_applicants[columns]

        return df_applicants

    def _generate_desired_work(self, processed_data):
        """
        DesiredWorkデータの生成

        Args:
            processed_data: _process_applicant_data()の戻り値

        Returns:
            DataFrame: [申請者ID, 希望勤務地_都道府県, 希望勤務地_市区町村, キー]
        """
        desired_locations = processed_data['desired_locations']

        desired_work_data = []

        for applicant_id, desired_pref, desired_municipality in desired_locations:
            # キーは "都道府県+市区町村" の形式
            location_key = f"{desired_pref}{desired_municipality}" if desired_municipality else desired_pref

            desired_work_data.append({
                '申請者ID': applicant_id,
                '希望勤務地_都道府県': desired_pref,
                '希望勤務地_市区町村': desired_municipality,
                'キー': location_key
            })

        df_desired_work = pd.DataFrame(desired_work_data)

        return df_desired_work

    def _extract_prefecture(self, address_str):
        """
        住所文字列から都道府県を抽出（後方互換性のため）

        Args:
            address_str: 住所文字列

        Returns:
            str: 都道府県名 or None
        """
        pref, _ = self._extract_prefecture_municipality(address_str)
        return pref

    def _extract_prefecture_municipality(self, address_str):
        """
        住所文字列から都道府県と市区町村を抽出

        Args:
            address_str: 住所文字列（例: "千葉県柏市"）

        Returns:
            tuple: (都道府県名, 市区町村名) or (None, None)
        """
        if not address_str or pd.isna(address_str):
            return None, None

        address_str = str(address_str).strip()

        # 都道府県パターンマッチング
        for pref in self.prefectures:
            if pref in address_str:
                # 都道府県名を除去して市区町村を取得
                municipality = address_str.replace(pref, '').strip()
                # 市区町村が空の場合はNoneを返す
                if not municipality:
                    municipality = None
                return pref, municipality

        return None, None


    # ==========================================================
    # Phase 2: 統計検定
    # ==========================================================

    def export_phase2_data(self, output_dir='gas_output_phase2'):
        """
        Phase 2: 統計検定のエクスポート

        出力ファイル:
        - ChiSquareTests.csv: カイ二乗検定結果
        - ANOVATests.csv: ANOVA検定結果
        """
        print("\n" + "=" * 60)
        print("Phase 2: 統計検定")
        print("=" * 60)

        if self.df is None:
            print("エラー: データが読み込まれていません")
            return None

        # 出力ディレクトリ作成
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        print(f"出力ディレクトリ: {output_path}")

        exported_files = []

        try:
            # Phase 1データの処理（必要な場合）
            print("\n[1/3] データ準備中...")
            processed_data = self._prepare_phase2_data()

            # ステップ1: カイ二乗検定
            print("\n[2/3] カイ二乗検定実施中...")
            chi_square_tests = self._run_chi_square_tests(processed_data)
            chi_square_file = output_path / 'ChiSquareTests.csv'
            chi_square_tests.to_csv(chi_square_file, index=False, encoding='utf-8-sig')
            exported_files.append(chi_square_file)
            print(f"  [OK] ChiSquareTests.csv: {len(chi_square_tests)} 件")

            # ステップ2: ANOVA検定
            print("\n[3/3] ANOVA検定実施中...")
            anova_tests = self._run_anova_tests(processed_data)
            anova_file = output_path / 'ANOVATests.csv'
            anova_tests.to_csv(anova_file, index=False, encoding='utf-8-sig')
            exported_files.append(anova_file)
            print(f"  [OK] ANOVATests.csv: {len(anova_tests)} 件")

            # サマリー表示
            print("\n" + "=" * 60)
            print("Phase 2 エクスポート完了")
            print("=" * 60)
            print(f"出力ファイル: {len(exported_files)} 件")
            for f in exported_files:
                print(f"  - {f.name}")
            print(f"\n出力先: {output_path.absolute()}")

            return exported_files

        except Exception as e:
            print(f"\nエラーが発生しました: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _prepare_phase2_data(self):
        """
        Phase 2用のデータ準備

        Returns:
            dict: {
                'applicants': DataFrame(ID, 性別, 年齢, 年齢バケット, 居住地),
                'desired_work': DataFrame(申請者ID, 希望勤務地),
                'applicants_with_desired': DataFrame(結合データ)
            }
        """
        print("  データ準備を開始...")

        # Phase 1と同様のデータ処理
        processed_phase1 = self._process_applicant_data()

        # 年齢バケット付きのapplicantsデータを生成
        applicants_df = self._generate_applicants(processed_phase1)
        desired_locations = processed_phase1['desired_locations']

        # 希望勤務地数を計算（3要素のタプル: ID, 都道府県, 市区町村）
        desired_counts = pd.DataFrame(desired_locations, columns=['ID', '希望勤務地_都道府県', '希望勤務地_市区町村'])
        desired_count_per_applicant = desired_counts.groupby('ID').size().reset_index(name='希望勤務地数')

        # 申請者データと結合
        applicants_with_desired = applicants_df.merge(
            desired_count_per_applicant,
            on='ID',
            how='left'
        )
        applicants_with_desired['希望勤務地数'] = applicants_with_desired['希望勤務地数'].fillna(0).astype(int)

        print(f"  [OK] 準備完了: {len(applicants_with_desired)} 人")

        return {
            'applicants': applicants_df,
            'desired_work': desired_counts,
            'applicants_with_desired': applicants_with_desired
        }

    def _run_chi_square_tests(self, processed_data):
        """
        カイ二乗検定を実施

        Args:
            processed_data: _prepare_phase2_data()の戻り値

        Returns:
            DataFrame: ChiSquareTests.csv形式のデータ
        """
        from scipy.stats import chi2_contingency
        import numpy as np

        df = processed_data['applicants_with_desired']

        # 空データや不適切なデータを除外
        df = df[(df['性別'].notna()) & (df['性別'] != '') &
                (df['年齢バケット'].notna()) & (df['年齢バケット'] != '')]

        results = []

        # パターン1: 性別 × 年齢バケット（希望勤務地数の有無）
        if len(df[df['性別'].notna()]) > 0 and len(df[df['年齢バケット'].notna()]) > 0:
            df_temp = df.copy()
            df_temp['希望勤務地あり'] = (df_temp['希望勤務地数'] > 0).astype(int)

            contingency_table = pd.crosstab(df_temp['性別'], df_temp['希望勤務地あり'])

            if contingency_table.shape[0] > 1 and contingency_table.shape[1] > 1:
                chi2, p_value, dof, expected = chi2_contingency(contingency_table)

                # 効果量（Cramér's V）
                n = contingency_table.sum().sum()
                min_dim = min(contingency_table.shape[0] - 1, contingency_table.shape[1] - 1)
                cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0

                # 解釈
                if cramers_v < 0.1:
                    interpretation = "効果量が非常に小さい"
                elif cramers_v < 0.3:
                    interpretation = "効果量が小さい"
                elif cramers_v < 0.5:
                    interpretation = "効果量が中程度"
                else:
                    interpretation = "効果量が大きい"

                results.append({
                    'pattern': '性別×希望勤務地の有無',
                    'group1': '性別',
                    'group2': '希望勤務地の有無',
                    'variable': '希望勤務地数',
                    'chi_square': round(chi2, 4),
                    'p_value': round(p_value, 6),
                    'df': dof,
                    'effect_size': round(cramers_v, 4),
                    'significant': p_value < 0.05,
                    'sample_size': n,
                    'interpretation': interpretation
                })

        # パターン2: 年齢バケット × 希望勤務地の有無
        if len(df[df['年齢バケット'].notna()]) > 0:
            df_temp = df.copy()
            df_temp['希望勤務地あり'] = (df_temp['希望勤務地数'] > 0).astype(int)

            contingency_table = pd.crosstab(df_temp['年齢バケット'], df_temp['希望勤務地あり'])

            if contingency_table.shape[0] > 1 and contingency_table.shape[1] > 1:
                chi2, p_value, dof, expected = chi2_contingency(contingency_table)

                # 効果量（Cramér's V）
                n = contingency_table.sum().sum()
                min_dim = min(contingency_table.shape[0] - 1, contingency_table.shape[1] - 1)
                cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0

                # 解釈
                if cramers_v < 0.1:
                    interpretation = "効果量が非常に小さい"
                elif cramers_v < 0.3:
                    interpretation = "効果量が小さい"
                elif cramers_v < 0.5:
                    interpretation = "効果量が中程度"
                else:
                    interpretation = "効果量が大きい"

                results.append({
                    'pattern': '年齢層×希望勤務地の有無',
                    'group1': '年齢層',
                    'group2': '希望勤務地の有無',
                    'variable': '希望勤務地数',
                    'chi_square': round(chi2, 4),
                    'p_value': round(p_value, 6),
                    'df': dof,
                    'effect_size': round(cramers_v, 4),
                    'significant': p_value < 0.05,
                    'sample_size': n,
                    'interpretation': interpretation
                })

        return pd.DataFrame(results)

    def _run_anova_tests(self, processed_data):
        """
        ANOVA検定を実施

        Args:
            processed_data: _prepare_phase2_data()の戻り値

        Returns:
            DataFrame: ANOVATests.csv形式のデータ
        """
        from scipy.stats import f_oneway
        import numpy as np

        df = processed_data['applicants_with_desired']

        # 空データや不適切なデータを除外
        df = df[(df['年齢バケット'].notna()) & (df['年齢バケット'] != '')]

        results = []

        # パターン1: 年齢層による希望勤務地数の差
        if len(df[df['年齢バケット'].notna()]) > 0:
            age_groups = df.groupby('年齢バケット')['希望勤務地数'].apply(list).to_dict()

            # 各グループが2件以上のデータを持つか確認
            valid_groups = [group for group in age_groups.values() if len(group) >= 2]

            if len(valid_groups) >= 2:
                f_stat, p_value = f_oneway(*valid_groups)

                # 効果量（η²）の計算
                all_data = df['希望勤務地数'].values
                grand_mean = np.mean(all_data)
                ss_total = np.sum((all_data - grand_mean) ** 2)

                ss_between = sum([
                    len(group) * (np.mean(group) - grand_mean) ** 2
                    for group in valid_groups
                ])

                eta_squared = ss_between / ss_total if ss_total > 0 else 0

                # 自由度
                k = len(valid_groups)
                n = len(all_data)
                df_between = k - 1
                df_within = n - k

                # 解釈
                if eta_squared < 0.01:
                    interpretation = "効果量が非常に小さい"
                elif eta_squared < 0.06:
                    interpretation = "効果量が小さい"
                elif eta_squared < 0.14:
                    interpretation = "効果量が中程度"
                else:
                    interpretation = "効果量が大きい"

                results.append({
                    'pattern': '年齢層×希望勤務地数',
                    'dependent_var': '希望勤務地数',
                    'independent_var': '年齢層',
                    'f_statistic': round(f_stat, 4),
                    'p_value': round(p_value, 6),
                    'df_between': df_between,
                    'df_within': df_within,
                    'effect_size': round(eta_squared, 4),
                    'significant': p_value < 0.05,
                    'interpretation': interpretation,
                    'tukey_pairs': '',  # Tukey HSD検定は省略（実装が複雑）
                    'tukey_pvals': ''
                })

        return pd.DataFrame(results)


    # ==========================================================
    # Phase 3: ペルソナ分析
    # ==========================================================

    def export_phase3_data(self, output_dir='gas_output_phase3', n_clusters=5):
        """
        Phase 3: ペルソナ分析のエクスポート

        Args:
            output_dir: 出力ディレクトリ
            n_clusters: クラスタ数（デフォルト: 5）

        出力ファイル:
        - PersonaSummary.csv: ペルソナサマリー
        - PersonaDetails.csv: ペルソナ詳細
        """
        print("\n" + "=" * 60)
        print("Phase 3: ペルソナ分析")
        print("=" * 60)

        if self.df is None:
            print("エラー: データが読み込まれていません")
            return None

        # 出力ディレクトリ作成
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        print(f"出力ディレクトリ: {output_path}")

        exported_files = []

        try:
            # ステップ1: データ準備
            print("\n[1/3] データ準備中...")
            persona_data = self._prepare_phase3_data()

            # ステップ2: クラスタリング実行
            print(f"\n[2/3] クラスタリング実行中（{n_clusters}クラスタ）...")
            clustered_data = self._run_clustering(persona_data, n_clusters=n_clusters)

            # ステップ3: ペルソナサマリー生成
            print("\n[3/3] ペルソナ生成中...")
            persona_summary = self._generate_persona_summary(clustered_data)
            persona_summary_file = output_path / 'PersonaSummary.csv'
            persona_summary.to_csv(persona_summary_file, index=False, encoding='utf-8-sig')
            exported_files.append(persona_summary_file)
            print(f"  [OK] PersonaSummary.csv: {len(persona_summary)} 件")

            # ステップ4: ペルソナ詳細生成
            persona_details = self._generate_persona_details(clustered_data, persona_summary)
            persona_details_file = output_path / 'PersonaDetails.csv'
            persona_details.to_csv(persona_details_file, index=False, encoding='utf-8-sig')
            exported_files.append(persona_details_file)
            print(f"  [OK] PersonaDetails.csv: {len(persona_details)} 件")

            # サマリー表示
            print("\n" + "=" * 60)
            print("Phase 3 エクスポート完了")
            print("=" * 60)
            print(f"出力ファイル: {len(exported_files)} 件")
            for f in exported_files:
                print(f"  - {f.name}")
            print(f"\n出力先: {output_path.absolute()}")

            return exported_files

        except Exception as e:
            print(f"\nエラーが発生しました: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _prepare_phase3_data(self):
        """
        Phase 3用のデータ準備

        Returns:
            DataFrame: クラスタリング用のデータ
        """
        print("  データ準備を開始...")

        # Phase 2と同様のデータ処理
        processed_phase1 = self._process_applicant_data()
        applicants_df = self._generate_applicants(processed_phase1)
        desired_locations = processed_phase1['desired_locations']

        # 希望勤務地数を計算（3要素のタプル: ID, 都道府県, 市区町村）
        desired_counts = pd.DataFrame(desired_locations, columns=['ID', '希望勤務地_都道府県', '希望勤務地_市区町村'])
        desired_count_per_applicant = desired_counts.groupby('ID').size().reset_index(name='希望勤務地数')

        # 申請者データと結合
        persona_data = applicants_df.merge(
            desired_count_per_applicant,
            on='ID',
            how='left'
        )
        persona_data['希望勤務地数'] = persona_data['希望勤務地数'].fillna(0).astype(int)

        print(f"  [OK] 準備完了: {len(persona_data)} 人")

        return persona_data

    def _run_clustering(self, persona_data, n_clusters=5):
        """
        クラスタリングを実行

        Args:
            persona_data: _prepare_phase3_data()の戻り値
            n_clusters: クラスタ数

        Returns:
            DataFrame: segment_id列が追加されたデータ
        """
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import LabelEncoder
        import numpy as np

        # クラスタリング用の特徴量を準備
        df_clustering = persona_data.copy()

        # === 外れ値除外（IQR法による希望勤務地数の異常値フィルタリング） ===
        print(f"  [開始] 外れ値検出（IQR法）")
        original_count = len(df_clustering)

        # 空データチェック
        if original_count == 0:
            print(f"  [警告] 入力データが空です")
            return df_clustering

        # 希望勤務地数の存在チェック
        if '希望勤務地数' not in df_clustering.columns:
            print(f"  [警告] '希望勤務地数'列が存在しません。外れ値除外をスキップします")
        else:
            # IQR計算
            Q1 = df_clustering['希望勤務地数'].quantile(0.25)
            Q3 = df_clustering['希望勤務地数'].quantile(0.75)
            IQR = Q3 - Q1

            # NaNチェック
            if pd.isna(Q1) or pd.isna(Q3) or pd.isna(IQR):
                print(f"  [警告] IQR計算に失敗しました（データ不足）。外れ値除外をスキップします")
            else:
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                print(f"  統計情報: Q1={Q1:.1f}, Q3={Q3:.1f}, IQR={IQR:.1f}")
                print(f"  外れ値基準: 下限={lower_bound:.1f}, 上限={upper_bound:.1f}")

                # 外れ値マスク
                outliers_mask = (df_clustering['希望勤務地数'] < lower_bound) | (df_clustering['希望勤務地数'] > upper_bound)
                outliers = df_clustering[outliers_mask]

                # 外れ値処理
                if len(outliers) > 0:
                    print(f"  [検出] 外れ値ユーザー: {len(outliers)}件")
                    for idx in outliers.index[:10]:  # 最初の10件のみ表示
                        location_count = outliers.loc[idx, '希望勤務地数']
                        print(f"    - ユーザーID_{idx}: 希望勤務地数={location_count}")
                    if len(outliers) > 10:
                        print(f"    ... 他{len(outliers)-10}件")

                    # フィルタリング実行
                    df_clustering = df_clustering[~outliers_mask].copy()

                    # 全件除外チェック
                    if len(df_clustering) == 0:
                        print(f"  [エラー] 全データが外れ値として除外されました。処理を中止します")
                        raise ValueError("全データが外れ値として除外されました")

                    print(f"  [OK] フィルタリング完了: {original_count}件 → {len(df_clustering)}件")
                else:
                    print(f"  [OK] 外れ値なし（全{original_count}件が正常範囲）")

        # 数値化が必要なカラム
        # 性別をエンコード
        le_gender = LabelEncoder()
        df_clustering['性別_encoded'] = 0
        gender_mask = (df_clustering['性別'].notna()) & (df_clustering['性別'] != '')
        if gender_mask.sum() > 0:
            df_clustering.loc[gender_mask, '性別_encoded'] = le_gender.fit_transform(
                df_clustering.loc[gender_mask, '性別']
            )

        # 年齢バケットをエンコード
        age_bucket_map = {
            '20代': 1, '30代': 2, '40代': 3,
            '50代': 4, '60代': 5, '70歳以上': 6, '': 0
        }
        df_clustering['年齢バケット_encoded'] = df_clustering['年齢バケット'].map(age_bucket_map).fillna(0)

        # 年齢の欠損値を平均値で補完
        # まず数値型に変換して平均を計算
        age_numeric = pd.to_numeric(df_clustering['年齢'], errors='coerce')
        age_mean = age_numeric.mean()

        df_clustering['年齢_filled'] = age_numeric.fillna(age_mean)

        # クラスタリング用の特徴量
        features = df_clustering[[
            '年齢_filled',
            '性別_encoded',
            '年齢バケット_encoded',
            '希望勤務地数'
        ]].values

        # K-meansクラスタリング
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        df_clustering['segment_id'] = kmeans.fit_predict(features)

        print(f"  [OK] クラスタリング完了: {n_clusters} セグメント")

        return df_clustering

    def _generate_persona_summary(self, clustered_data):
        """
        ペルソナサマリーを生成

        Args:
            clustered_data: _run_clustering()の戻り値

        Returns:
            DataFrame: PersonaSummary.csv形式のデータ
        """
        results = []

        total_count = len(clustered_data)

        # 各セグメントの特徴を計算
        for segment_id in sorted(clustered_data['segment_id'].unique()):
            segment_data = clustered_data[clustered_data['segment_id'] == segment_id]

            # 基本統計
            count = len(segment_data)
            percentage = (count / total_count) * 100

            # 年齢統計
            valid_ages = segment_data[segment_data['年齢_filled'] > 0]['年齢_filled']
            avg_age = valid_ages.mean() if len(valid_ages) > 0 else 0

            # 女性比率
            gender_counts = segment_data['性別'].value_counts()
            female_count = gender_counts.get('女性', 0)
            female_ratio = female_count / count if count > 0 else 0

            # 希望勤務地数
            avg_desired_locations = segment_data['希望勤務地数'].mean()

            # 主要希望地（希望勤務地数が0より大きい人のみ）
            # Phase 1データから希望勤務地を取得
            segment_ids = segment_data['ID'].tolist()
            processed_phase1 = self._process_applicant_data()
            desired_locations = processed_phase1['desired_locations']

            # このセグメントの希望勤務地を抽出（3要素: ID, 都道府県, 市区町村）
            segment_desired = [pref for aid, pref, _ in desired_locations if aid in segment_ids]

            if segment_desired:
                from collections import Counter
                location_counter = Counter(segment_desired)
                top_prefecture = location_counter.most_common(1)[0][0] if location_counter else ''
                top_prefectures_all = ';'.join([pref for pref, _ in location_counter.most_common(5)])
            else:
                top_prefecture = ''
                top_prefectures_all = ''

            # セグメント名を生成
            segment_name = self._generate_segment_name(segment_id, segment_data)

            results.append({
                'segment_id': segment_id,
                'segment_name': segment_name,
                'count': count,
                'percentage': round(percentage, 1),
                'avg_age': round(avg_age, 1),
                'female_ratio': round(female_ratio, 2),
                'avg_qualifications': 0,  # 資格データがないため0
                'top_prefecture': top_prefecture,
                'avg_desired_locations': round(avg_desired_locations, 1),
                'top_prefectures_all': top_prefectures_all
            })

        return pd.DataFrame(results)

    def _generate_segment_name(self, segment_id, segment_data):
        """
        セグメント名を生成

        Args:
            segment_id: セグメントID
            segment_data: セグメントデータ

        Returns:
            str: セグメント名
        """
        # 年齢層の判定
        valid_ages = segment_data[segment_data['年齢_filled'] > 0]['年齢_filled']
        avg_age = valid_ages.mean() if len(valid_ages) > 0 else 0

        if avg_age < 35:
            age_label = "若年層"
        elif avg_age < 50:
            age_label = "中年層"
        else:
            age_label = "中高年層"

        # 希望勤務地数の判定
        avg_desired = segment_data['希望勤務地数'].mean()

        if avg_desired < 2:
            location_label = "地元密着型"
        elif avg_desired < 4:
            location_label = "地域志向型"
        else:
            location_label = "広域志向型"

        return f"{age_label}{location_label}"

    def _generate_persona_details(self, clustered_data, persona_summary):
        """
        ペルソナ詳細を生成

        Args:
            clustered_data: _run_clustering()の戻り値
            persona_summary: _generate_persona_summary()の戻り値

        Returns:
            DataFrame: PersonaDetails.csv形式のデータ
        """
        results = []

        for _, row in persona_summary.iterrows():
            segment_id = row['segment_id']
            segment_name = row['segment_name']
            segment_data = clustered_data[clustered_data['segment_id'] == segment_id]

            # 特徴1: 年齢層
            age_buckets = segment_data['年齢バケット'].value_counts()
            if len(age_buckets) > 0:
                top_age_bucket = age_buckets.index[0]
                top_age_pct = (age_buckets.iloc[0] / len(segment_data)) * 100
                results.append({
                    'segment_id': segment_id,
                    'segment_name': segment_name,
                    'detail_type': '特徴',
                    'detail_key': '年齢層',
                    'detail_value': f"{top_age_bucket}が{top_age_pct:.0f}%を占める"
                })

            # 特徴2: 性別
            gender_counts = segment_data['性別'].value_counts()
            if len(gender_counts) > 0:
                results.append({
                    'segment_id': segment_id,
                    'segment_name': segment_name,
                    'detail_type': '特徴',
                    'detail_key': '性別',
                    'detail_value': f"女性{row['female_ratio']*100:.0f}%"
                })

            # 行動パターン: 希望地数
            results.append({
                'segment_id': segment_id,
                'segment_name': segment_name,
                'detail_type': '行動パターン',
                'detail_key': '希望地数',
                'detail_value': f"平均{row['avg_desired_locations']:.1f}箇所"
            })

            # 推奨アプローチ
            if row['avg_desired_locations'] < 2:
                approach = "地元密着型の求人を重点的に提供"
            elif row['avg_desired_locations'] < 4:
                approach = "地域内の複数選択肢を提示"
            else:
                approach = "広域の求人情報を提供し、キャリアの選択肢を拡大"

            results.append({
                'segment_id': segment_id,
                'segment_name': segment_name,
                'detail_type': '推奨アプローチ',
                'detail_key': '採用戦略',
                'detail_value': approach
            })

        return pd.DataFrame(results)

    def _get_coords(self, prefecture, municipality=None):
        """
        都道府県または市区町村の座標を取得

        Args:
            prefecture: 都道府県名
            municipality: 市区町村名（省略可）

        Returns:
            tuple: (緯度, 経度)
        """
        # Step 1: 市区町村レベルの座標を優先（市区町村が指定されている場合）
        if municipality:
            full_address = f"{prefecture}{municipality}"
            coords = self.get_coordinates_from_gsi_api(full_address)
            if coords:
                return coords['lat'], coords['lng']

        # Step 2: 市区町村が取得できない場合、都道府県レベルにフォールバック
        if prefecture and prefecture in self.prefecture_coords:
            coords = self.prefecture_coords[prefecture]
            return coords['lat'], coords['lng']

        # Step 3: 都道府県辞書にもない場合、都道府県名でAPI検索を試行
        if prefecture:
            coords = self.get_coordinates_from_gsi_api(prefecture)
            if coords:
                return coords['lat'], coords['lng']

        # Step 4: 最終フォールバック（東京）
        return 35.6762, 139.6503

    # ==========================================================
    # Phase 6: フロー・移動パターン分析
    # ==========================================================

    def export_phase6_data(self, output_dir='gas_output_phase6'):
        """
        Phase 6: フロー・移動パターン分析のエクスポート

        出力ファイル:
        - MunicipalityFlowEdges.csv: 市区町村間フローエッジ
        - MunicipalityFlowNodes.csv: 市区町村ノード情報
        - ProximityAnalysis.csv: 距離帯分析
        """
        print("\n" + "=" * 60)
        print("Phase 6: フロー・移動パターン分析")
        print("=" * 60)

        if self.df is None:
            print("エラー: データが読み込まれていません")
            return None

        # 出力ディレクトリ作成
        from pathlib import Path
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        print(f"出力ディレクトリ: {output_path}")

        exported_files = []

        try:
            # ステップ1: データ準備
            print("\n[1/4] データ準備中...")
            flow_data = self._prepare_phase6_data()

            # ステップ2: フロー分析
            print("\n[2/4] フロー分析実行中...")
            edges_df, nodes_df = self._analyze_flow_phase6(flow_data)

            if not edges_df.empty:
                edges_file = output_path / 'MunicipalityFlowEdges.csv'
                edges_df.to_csv(edges_file, index=False, encoding='utf-8-sig')
                exported_files.append(edges_file)
                print(f"  [OK] MunicipalityFlowEdges.csv: {len(edges_df)} エッジ")

            if not nodes_df.empty:
                nodes_file = output_path / 'MunicipalityFlowNodes.csv'
                nodes_df.to_csv(nodes_file, index=False, encoding='utf-8-sig')
                exported_files.append(nodes_file)
                print(f"  [OK] MunicipalityFlowNodes.csv: {len(nodes_df)} ノード")

            # ステップ3: 近接分析
            print("\n[3/4] 近接分析実行中...")
            proximity_df = self._analyze_proximity_phase6(flow_data)

            if not proximity_df.empty:
                proximity_file = output_path / 'ProximityAnalysis.csv'
                proximity_df.to_csv(proximity_file, index=False, encoding='utf-8-sig')
                exported_files.append(proximity_file)
                print(f"  [OK] ProximityAnalysis.csv: {len(proximity_df)} 距離帯")

            # サマリー表示
            print("\n" + "=" * 60)
            print("Phase 6 エクスポート完了")
            print("=" * 60)
            print(f"出力ファイル: {len(exported_files)} 件")
            for f in exported_files:
                print(f"  - {f.name}")
            print(f"\n出力先: {output_path.absolute()}")

            return exported_files

        except Exception as e:
            print(f"\nエラーが発生しました: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _prepare_phase6_data(self):
        """
        Phase 6用のデータ準備（最適化版）

        最適化内容:
        - iterrows()ループ（68,445回）→ ユニークアドレスマッピング（数百回）
        - 距離計算ループ（22,815回）→ ベクトル化（1回の配列操作）
        - 期待される高速化: 90-95%の処理時間短縮（30秒→1-3秒）

        Returns:
            DataFrame: フロー分析用データ
                - ID, 居住地都道府県, 居住地市区町村, 希望勤務地都道府県
                - residence_muni, desired_muni (市区町村キー)
                - residence_lat, residence_lng, desired_lat, desired_lng
                - geo_distance_km
        """
        print("  データ準備を開始...")

        # Phase 1と同様のデータ処理
        processed_phase1 = self._process_applicant_data()
        applicants_df = processed_phase1['applicants']  # 既にDataFrame
        desired_locations = processed_phase1['desired_locations']  # list of (ID, pref, municipality)

        # desired_locationsをDataFrameに変換（3要素のタプルを展開）
        desired_df = pd.DataFrame(desired_locations, columns=[
            'ID', '希望勤務地都道府県', '希望勤務地市区町村'
        ])

        # 結合
        flow_data = desired_df.merge(
            applicants_df[['ID', '居住地_都道府県', '居住地_市区町村']],
            on='ID',
            how='left'
        )

        # デバッグ: マージ後のデータ確認
        print(f"  マージ後のデータ: {len(flow_data)} 行")
        print(f"    居住地_都道府県: {flow_data['居住地_都道府県'].notna().sum()} 件")
        print(f"    希望勤務地都道府県: {flow_data['希望勤務地都道府県'].notna().sum()} 件")

        # 市区町村キーを作成（都道府県+市区町村）
        flow_data['residence_muni'] = (
            flow_data['居住地_都道府県'].fillna('') +
            flow_data['居住地_市区町村'].fillna('')
        )
        flow_data['desired_muni'] = (
            flow_data['希望勤務地都道府県'].fillna('') +
            flow_data['希望勤務地市区町村'].fillna('')
        )

        # 完全データのみフィルタリング（居住地_都道府県と希望勤務地都道府県が必須）
        complete_mask = (
            flow_data['居住地_都道府県'].notna() &
            (flow_data['居住地_都道府県'] != '') &
            flow_data['希望勤務地都道府県'].notna() &
            (flow_data['希望勤務地都道府県'] != '')
        )
        flow_data = flow_data[complete_mask].copy()

        print(f"  [OK] フローデータ: {len(flow_data)} 行")

        # ===== 最適化: 座標取得（ユニークアドレスマッピング） =====
        print("  座標データを取得中（最適化版）...")

        # 1. ユニークな居住地住所を抽出
        unique_residence = flow_data[['居住地_都道府県', '居住地_市区町村']].drop_duplicates()
        print(f"    ユニークな居住地: {len(unique_residence)} 件（元データ: {len(flow_data)} 件）")

        # 2. ユニークな居住地のみをジオコーディング
        residence_map = {}
        for _, row in unique_residence.iterrows():
            pref = row['居住地_都道府県']
            municipality = row['居住地_市区町村'] if pd.notna(row['居住地_市区町村']) else None
            lat, lng = self._get_coords(pref, municipality)
            key = (pref, municipality if municipality else '')
            residence_map[key] = (lat, lng)

        # 3. マッピングで一括変換
        def map_residence_coords(row):
            key = (row['居住地_都道府県'], row['居住地_市区町村'] if pd.notna(row['居住地_市区町村']) else '')
            return pd.Series(residence_map.get(key, (None, None)))

        flow_data[['residence_lat', 'residence_lng']] = flow_data.apply(map_residence_coords, axis=1)

        # 4. ユニークな希望勤務地住所を抽出
        unique_desired = flow_data[['希望勤務地都道府県', '希望勤務地市区町村']].drop_duplicates()
        print(f"    ユニークな希望勤務地: {len(unique_desired)} 件（元データ: {len(flow_data)} 件）")

        # 5. ユニークな希望勤務地のみをジオコーディング
        desired_map = {}
        for _, row in unique_desired.iterrows():
            pref = row['希望勤務地都道府県']
            municipality = row['希望勤務地市区町村'] if pd.notna(row['希望勤務地市区町村']) else None
            lat, lng = self._get_coords(pref, municipality)
            key = (pref, municipality if municipality else '')
            desired_map[key] = (lat, lng)

        # 6. マッピングで一括変換
        def map_desired_coords(row):
            key = (row['希望勤務地都道府県'], row['希望勤務地市区町村'] if pd.notna(row['希望勤務地市区町村']) else '')
            return pd.Series(desired_map.get(key, (None, None)))

        flow_data[['desired_lat', 'desired_lng']] = flow_data.apply(map_desired_coords, axis=1)

        # ===== 最適化: 距離計算（ベクトル化） =====
        print("  距離計算中（ベクトル化版）...")

        # ベクトル化された距離計算を使用
        flow_data['geo_distance_km'] = self._haversine_distance_vectorized(
            flow_data['residence_lat'].values,
            flow_data['residence_lng'].values,
            flow_data['desired_lat'].values,
            flow_data['desired_lng'].values
        )

        # 完全なデータのみ
        complete_phase6 = flow_data['geo_distance_km'].notna()
        flow_data = flow_data[complete_phase6].copy()

        print(f"  [OK] 完全データ: {len(flow_data)} 行")

        return flow_data

    def _analyze_flow_phase6(self, flow_data):
        """
        フロー分析を実行

        Args:
            flow_data: _prepare_phase6_data()の戻り値

        Returns:
            tuple: (edges_df, nodes_df)
        """
        # エッジ集計
        edges = flow_data.groupby(['residence_muni', 'desired_muni']).size().reset_index(name='Flow_Count')
        edges.columns = ['Source_Municipality', 'Target_Municipality', 'Flow_Count']
        edges = edges.sort_values('Flow_Count', ascending=False)

        # ノード集計
        # 流入度（In-Degree）: 目的地としての人気
        in_degree = edges.groupby('Target_Municipality')['Flow_Count'].sum().reset_index()
        in_degree.columns = ['Municipality', 'In_Degree']

        # 流出度（Out-Degree）: 出発地としての活発さ
        out_degree = edges.groupby('Source_Municipality')['Flow_Count'].sum().reset_index()
        out_degree.columns = ['Municipality', 'Out_Degree']

        # ノード統合
        nodes = in_degree.merge(out_degree, on='Municipality', how='outer').fillna(0)
        nodes['In_Degree'] = nodes['In_Degree'].astype(int)
        nodes['Out_Degree'] = nodes['Out_Degree'].astype(int)
        nodes['Total_Degree'] = nodes['In_Degree'] + nodes['Out_Degree']

        # 中心性タイプを分類
        centrality_types = []
        for _, row in nodes.iterrows():
            in_deg = row['In_Degree']
            out_deg = row['Out_Degree']
            total = row['Total_Degree']

            if total == 0:
                centrality_types.append('Isolated')
            elif in_deg > out_deg * 1.5:
                centrality_types.append('Hub')  # 流入型
            elif out_deg > in_deg * 1.5:
                centrality_types.append('Source')  # 流出型
            else:
                centrality_types.append('Balanced')  # 均衡型

        nodes['Centrality_Type'] = centrality_types
        nodes = nodes.sort_values('Total_Degree', ascending=False)

        # 座標データを追加（geocacheから取得）
        coords_list = []
        for municipality in nodes['Municipality']:
            # geocacheから座標を取得
            if municipality in self.geocache:
                coords = self.geocache[municipality]
                coords_list.append({'緯度': coords['lat'], '経度': coords['lng']})
            else:
                # geocacheにない場合は_get_coordsで取得
                pref, muni = self._extract_prefecture_municipality(municipality)
                lat, lng = self._get_coords(pref, muni)
                coords_list.append({'緯度': lat, '経度': lng})

        coords_df = pd.DataFrame(coords_list)
        nodes['緯度'] = coords_df['緯度']
        nodes['経度'] = coords_df['経度']

        # カラム順序を整える
        nodes = nodes[['Municipality', 'In_Degree', 'Out_Degree', 'Total_Degree', 'Centrality_Type', '緯度', '経度']]

        return edges, nodes

    def _analyze_proximity_phase6(self, flow_data):
        """
        近接分析を実行

        Args:
            flow_data: _prepare_phase6_data()の戻り値

        Returns:
            DataFrame: ProximityAnalysis.csv形式のデータ
        """
        # 距離帯を分類
        proximity_buckets = []
        for dist in flow_data['geo_distance_km']:
            if dist < 10:
                proximity_buckets.append('0-10km')
            elif dist < 20:
                proximity_buckets.append('10-20km')
            elif dist < 50:
                proximity_buckets.append('20-50km')
            elif dist < 100:
                proximity_buckets.append('50-100km')
            else:
                proximity_buckets.append('over_100km')

        flow_data['proximity_bucket'] = proximity_buckets

        # 距離帯別集計
        proximity_analysis = flow_data.groupby('proximity_bucket').agg({
            'geo_distance_km': ['count', 'mean', 'median']
        }).reset_index()

        proximity_analysis.columns = [
            'proximity_bucket',
            'Count',
            'Avg_Distance_km',
            'Median_Distance_km'
        ]

        # 距離帯の順序
        bucket_order = {
            '0-10km': 0,
            '10-20km': 1,
            '20-50km': 2,
            '50-100km': 3,
            'over_100km': 4
        }

        proximity_analysis['order'] = proximity_analysis['proximity_bucket'].map(bucket_order)
        proximity_analysis = proximity_analysis.sort_values('order').drop('order', axis=1)

        # 数値を丸める
        proximity_analysis['Avg_Distance_km'] = proximity_analysis['Avg_Distance_km'].round(1)
        proximity_analysis['Median_Distance_km'] = proximity_analysis['Median_Distance_km'].round(1)

        return proximity_analysis

    def _build_gas_compatible_json(self):
        """GAS期待形式のJSON構造を構築"""
        from datetime import datetime

        # メタデータ生成
        metadata = {
            "total_records": len(self.df_processed),
            "analysis_date": datetime.now().strftime('%Y年%m月%d日'),
            "region": self.df_processed['prefecture'].mode()[0] if 'prefecture' in self.df_processed.columns and len(self.df_processed) > 0 else '不明',
            "message": "Python分析システムにより生成されたデータです"
        }

        # 基本統計生成
        basic_stats = {
            "total_jobseekers": len(self.df_processed),
            "by_gender": {},
            "by_age_group": {},
            "by_city": {}
        }

        # 性別集計
        if 'gender' in self.df_processed.columns:
            gender_counts = self.df_processed['gender'].value_counts().to_dict()
            basic_stats['by_gender'] = {str(k): int(v) for k, v in gender_counts.items()}

        # 年齢層集計
        if 'age_group' in self.df_processed.columns:
            age_counts = self.df_processed['age_group'].value_counts().to_dict()
            basic_stats['by_age_group'] = {str(k): int(v) for k, v in age_counts.items()}

        # 市区町村集計
        if 'municipality' in self.df_processed.columns:
            city_counts = self.df_processed['municipality'].value_counts().head(20).to_dict()
            basic_stats['by_city'] = {str(k): int(v) for k, v in city_counts.items()}

        # セグメント情報生成
        segments = {}
        if 'employment_status' in self.df_processed.columns:
            emp_counts = self.df_processed['employment_status'].value_counts().to_dict()
            segments['by_employment_status'] = {str(k): int(v) for k, v in emp_counts.items()}

        # クラスタリング情報生成
        clustering = {
            "method": "none",
            "clusters": []
        }
        if 'cluster' in self.df_processed.columns:
            clustering['method'] = 'kmeans'
            for cluster_id in sorted(self.df_processed['cluster'].unique()):
                if cluster_id != -1:
                    cluster_data = self.df_processed[self.df_processed['cluster'] == cluster_id]
                    clustering['clusters'].append({
                        "id": int(cluster_id),
                        "size": len(cluster_data),
                        "avg_age": float(cluster_data['age'].mean()) if 'age' in cluster_data.columns else 0,
                        "gender_ratio": cluster_data['gender'].value_counts().to_dict() if 'gender' in cluster_data.columns else {}
                    })

        # 統計情報
        statistics = {}
        if hasattr(self, 'analysis_results') and self.analysis_results:
            # 既存の分析結果から統計を抽出
            for key, value in self.analysis_results.items():
                if isinstance(value, (int, float, str)):
                    statistics[key] = value
                elif isinstance(value, dict):
                    statistics[key] = self._convert_to_json_serializable(value)

        # クロス集計
        simple_cross_tabulation = {}
        if 'gender' in self.df_processed.columns and 'age_group' in self.df_processed.columns:
            cross_tab = pd.crosstab(self.df_processed['gender'], self.df_processed['age_group'])
            simple_cross_tabulation['gender_x_age'] = cross_tab.to_dict()

        # 完全なJSON構造を構築
        gas_json = {
            "metadata": metadata,
            "basic_stats": basic_stats,
            "segments": segments,
            "clustering": clustering,
            "statistics": statistics,
            "simple_cross_tabulation": simple_cross_tabulation,
            # 既存の分析結果も保持
            "mobility_patterns": self.analysis_results.get('mobility_patterns', {}),
            "data_quality": self.analysis_results.get('data_quality', {}),
            "advanced_insights": self.analysis_results.get('advanced_insights', [])
        }

        return gas_json

    def export_results(self, output_dir='.'):
        """結果のエクスポート（拡張版）"""
        print("\n【ファイルエクスポート】")
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 基本的なCSVファイル
        files_created = []
        
        # 1. 処理済みデータ
        processed_path = output_path / 'processed_data_complete.csv'
        self.df_processed.to_csv(processed_path, index=False, encoding='utf-8-sig')
        files_created.append(('processed_data_complete.csv', len(self.df_processed)))
        
        # 2. 分析結果JSON（GAS互換形式）
        results_path = output_path / 'analysis_results_complete.json'

        # GAS期待形式のJSON構造を構築
        json_results = self._build_gas_compatible_json()

        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(json_results, f, ensure_ascii=False, indent=2, default=str)
        files_created.append(('analysis_results_complete.json', 1))
        
        # 3. セグメント別データ
        if 'cluster' in self.df_processed.columns:
            for cluster_id in self.df_processed['cluster'].unique():
                if cluster_id != -1:
                    cluster_data = self.df_processed[self.df_processed['cluster'] == cluster_id]
                    cluster_path = output_path / f'segment_{cluster_id}.csv'
                    cluster_data.to_csv(cluster_path, index=False, encoding='utf-8-sig')
                    files_created.append((f'segment_{cluster_id}.csv', len(cluster_data)))
        
        print("\n【エクスポート完了】")
        for filename, count in files_created:
            print(f"  [OK] {filename}: {count:,}件")
        
        return files_created


def select_csv_file():
    """ファイル選択ダイアログ"""
    try:
        from tkinter import filedialog, Tk
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        file_path = filedialog.askopenfilename(
            title='分析するCSVファイルを選択してください',
            filetypes=[
                ('CSVファイル', '*.csv'),
                ('すべてのファイル', '*.*')
            ],
            initialdir=os.path.expanduser('~/Downloads')
        )
        
        root.destroy()
        
        return file_path if file_path else None
            
    except Exception as e:
        print(f"ファイル選択エラー: {e}")
        filepath = input("CSVファイルのパスを直接入力してください: ").strip().strip('"').strip("'")
        if Path(filepath).exists():
            return filepath
        return None


def main():
    """メイン実行関数"""
    print("=" * 60)
    print("求職者データ包括分析システム - 拡張版")
    print("完全統合版（拡張分析機能付き）")
    print("=" * 60)
    
    # ファイル選択
    print("\nCSVファイルを選択してください...")
    filepath = select_csv_file()
    
    if not filepath:
        print("ファイルが選択されませんでした。終了します。")
        return None, None
    
    print(f"\n選択されたファイル: {Path(filepath).name}")
    print("-" * 60)
    
    try:
        # 分析実行
        analyzer = AdvancedJobSeekerAnalyzer(filepath)
        results = analyzer.run_complete_analysis()

        # Phase 7: 高度分析機能を実行
        try:
            from phase7_advanced_analysis import run_phase7_analysis

            print("\n" + "=" * 60)
            print("Phase 7: 高度分析機能を開始します")
            print("=" * 60)

            phase7_analyzer = run_phase7_analysis(
                df=analyzer.df,
                df_processed=analyzer.df_processed,
                geocache=analyzer.geocache,
                master=analyzer.master,
                output_dir='gas_output_phase7'
            )

            print("\n" + "=" * 60)
            print("Phase 7: 高度分析機能が完了しました")
            print("=" * 60)

            # Phase 7結果を統合
            results['phase7'] = phase7_analyzer.results

        except ImportError as ie:
            print(f"\n[警告] Phase 7モジュールが見つかりません: {ie}")
            print("  Phase 7をスキップして続行します...")
        except Exception as e7:
            print(f"\n[警告] Phase 7実行中にエラーが発生しました: {e7}")
            print("  Phase 7をスキップして続行します...")
            import traceback
            traceback.print_exc()

        return analyzer, results

    except Exception as e:
        print(f"\n[ERROR] エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return None, None


# 自動実行
if __name__ == "__main__":
    analyzer, results = main()
