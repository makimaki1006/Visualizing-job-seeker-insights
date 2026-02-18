#!/usr/bin/env python3
"""
セグメント集約スクリプト

classified CSVから地域別セグメント分布をSQLiteに集約する。
Rustダッシュボードの競合調査タブで消費するデータを生成。

テーブル構成:
  1. segment_prefecture       - 都道府県×軸×カテゴリ別の件数・比率
  2. segment_municipality     - 市区町村×軸×カテゴリ別の件数・比率
  3. segment_tier3            - Tier3パターンの地域別分布
  4. segment_tags             - 個別タグの地域別出現率
  5. segment_tag_combos       - タグ組み合わせパターンの地域別分布
  6. segment_text_features    - フリーテキスト辞書マッチの地域別分布
  7. segment_salary           - セグメント別の給与統計
  8. segment_job_desc         - 仕事内容カテゴリの地域別分布
  9. segment_age_decade       - 年代分布 (20/30/40/50/60代)
  10. segment_gender_lifecycle - 性別シグナル・女性ライフステージ分布
  11. segment_exp_qual         - 未経験×資格の4象限分布
  12. segment_meta             - メタ情報

使用例:
  python aggregate_segments.py \
    --input "data/classified/classified_看護師・准看護師_20260215.csv" \
    --input "data/classified/classified_介護職・ヘルパー_20260215.csv" \
    --output "data/classified/segment_summary.db"
"""

import argparse
import gzip
import re
import shutil
import sqlite3
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from segment_classifier import TIER2_LABELS, TIER3_PATTERNS


# ============================================================
# 軸マッピング（CSVカラム名 → 軸コード）
# ============================================================
AXIS_MAP = {
    'A': 'tier1_experience',
    'B': 'tier1_career_stage',
    'C': 'tier1_lifestyle',
    'D': 'tier1_appeal',
    'E': 'tier1_urgency',
}


# ============================================================
# フリーテキスト分類辞書
# ============================================================
TEXT_FEATURE_DICT = {
    # --- 施設形態 ---
    'facility_hospital': {
        'category': '施設形態',
        'label': '病院',
        'patterns': [r'病院', r'総合病院', r'大学病院', r'急性期病院'],
        'fields': ['service_type', 'facility_name', 'job_description'],
    },
    'facility_clinic': {
        'category': '施設形態',
        'label': 'クリニック・診療所',
        'patterns': [r'クリニック', r'診療所', r'医院'],
        'fields': ['service_type', 'facility_name', 'job_description'],
    },
    'facility_visiting': {
        'category': '施設形態',
        'label': '訪問系',
        'patterns': [r'訪問(看護|介護|リハ)', r'訪問(ステーション|事業所)'],
        'fields': ['service_type', 'facility_name', 'job_description'],
    },
    'facility_dayservice': {
        'category': '施設形態',
        'label': 'デイサービス',
        'patterns': [r'デイサービス', r'通所(介護|リハ)', r'デイケア'],
        'fields': ['service_type', 'facility_name', 'job_description'],
    },
    'facility_tokuyou': {
        'category': '施設形態',
        'label': '特養・老健',
        'patterns': [r'特別養護', r'特養', r'老健', r'介護老人保健施設'],
        'fields': ['service_type', 'facility_name', 'job_description'],
    },
    'facility_grouphome': {
        'category': '施設形態',
        'label': 'グループホーム',
        'patterns': [r'グループホーム'],
        'fields': ['service_type', 'facility_name', 'job_description'],
    },
    'facility_yuuryou': {
        'category': '施設形態',
        'label': '有料老人ホーム',
        'patterns': [r'有料老人ホーム', r'住宅型有料', r'介護付有料'],
        'fields': ['service_type', 'facility_name', 'job_description'],
    },
    'facility_hoiku': {
        'category': '施設形態',
        'label': '保育園・こども園',
        'patterns': [r'保育(園|所)', r'こども園', r'認定こども園', r'認可保育'],
        'fields': ['service_type', 'facility_name', 'job_description'],
    },
    'facility_shougai': {
        'category': '施設形態',
        'label': '障害福祉',
        'patterns': [r'障(害|がい)(者|児)', r'就労(継続|移行)', r'放課後.{0,3}デイ', r'生活介護'],
        'fields': ['service_type', 'facility_name', 'job_description'],
    },
    # --- 勤務形態 ---
    'work_nightshift': {
        'category': '勤務形態',
        'label': '夜勤あり',
        'patterns': [r'夜勤(あり|含む|月\d)', r'二交代', r'三交代', r'2交代', r'3交代'],
        'fields': ['working_hours', 'job_description'],
    },
    'work_dayonly': {
        'category': '勤務形態',
        'label': '日勤のみ',
        'patterns': [r'日勤のみ', r'日勤(だけ|専従)', r'夜勤(なし|免除)'],
        'fields': ['working_hours', 'job_description'],
    },
    'work_oncall': {
        'category': '勤務形態',
        'label': 'オンコール',
        'patterns': [r'オンコール', r'待機(あり|当番)'],
        'fields': ['working_hours', 'job_description'],
    },
    'work_shift': {
        'category': '勤務形態',
        'label': 'シフト制',
        'patterns': [r'シフト制', r'ローテーション'],
        'fields': ['working_hours', 'job_description'],
    },
    'work_fixedtime': {
        'category': '勤務形態',
        'label': '固定時間',
        'patterns': [r'固定(時間|勤務)', r'(8|9)時.{0,3}(17|18)時'],
        'fields': ['working_hours'],
    },
    # --- 教育・研修 ---
    'edu_ojt': {
        'category': '教育・研修',
        'label': 'OJT・マンツーマン',
        'patterns': [r'OJT', r'マンツーマン', r'先輩がつい'],
        'fields': ['education_training', 'job_description'],
    },
    'edu_preceptor': {
        'category': '教育・研修',
        'label': 'プリセプター制度',
        'patterns': [r'プリセプター', r'チューター', r'メンター'],
        'fields': ['education_training', 'job_description'],
    },
    'edu_external': {
        'category': '教育・研修',
        'label': '外部研修・学会',
        'patterns': [r'外部研修', r'学会(参加|発表)', r'セミナー', r'勉強会'],
        'fields': ['education_training', 'job_description'],
    },
    'edu_ladder': {
        'category': '教育・研修',
        'label': 'ラダー・キャリアパス',
        'patterns': [r'(クリニカル)?ラダー', r'キャリアパス', r'段階(的|別)'],
        'fields': ['education_training', 'job_description'],
    },
    # --- 福利厚生 ---
    'benefit_housing': {
        'category': '福利厚生',
        'label': '住宅手当・寮',
        'patterns': [r'(社員|職員)?寮', r'住宅(手当|補助)', r'家賃補助', r'借り上げ'],
        'fields': ['benefits', 'salary_detail'],
    },
    'benefit_childcare': {
        'category': '福利厚生',
        'label': '託児所・保育',
        'patterns': [r'託児(所|施設)', r'院内保育', r'企業(主導型|内)保育'],
        'fields': ['benefits', 'job_description'],
    },
    'benefit_vehicle': {
        'category': '福利厚生',
        'label': '車通勤可',
        'patterns': [r'(マイカー|車|バイク|自動車).{0,5}通勤(可|OK)', r'駐車場(あり|完備|無料)'],
        'fields': ['benefits', 'access'],
    },
    'benefit_uniform': {
        'category': '福利厚生',
        'label': '制服貸与',
        'patterns': [r'制服(貸与|支給)', r'白衣(貸与|支給)', r'ユニフォーム'],
        'fields': ['benefits'],
    },
    # --- 訴求表現 ---
    'appeal_team': {
        'category': '訴求表現',
        'label': 'チームワーク',
        'patterns': [r'チーム(ワーク|医療|ケア)', r'多職種(連携|協働)'],
        'fields': ['job_description'],
    },
    'appeal_community': {
        'category': '訴求表現',
        'label': '地域密着',
        'patterns': [r'地域(密着|に根(差|ざ)し)', r'地域(医療|包括|連携)'],
        'fields': ['job_description'],
    },
    'appeal_patient': {
        'category': '訴求表現',
        'label': '患者・利用者重視',
        'patterns': [r'(患者|利用者|入居者).{0,5}(寄り添|第一|中心|主体)', r'その人らしく'],
        'fields': ['job_description'],
    },
    'appeal_opening': {
        'category': '訴求表現',
        'label': 'オープニング',
        'patterns': [r'オープニング', r'新(規|設)', r'新しい施設', r'立ち上げ'],
        'fields': ['job_description', 'headline'],
    },
    'appeal_noovertime': {
        'category': '訴求表現',
        'label': '残業少・なし',
        'patterns': [r'残業(ほぼ|ほとんど)?(なし|ゼロ|少な)', r'定時(退社|帰り|上がり)', r'持ち帰り.{0,3}なし'],
        'fields': ['job_description', 'working_hours'],
    },
    'appeal_stable': {
        'category': '訴求表現',
        'label': '安定経営',
        'patterns': [r'安定(した|の)(経営|基盤|運営)', r'創業\d+年', r'設立\d+年', r'黒字経営'],
        'fields': ['job_description', 'headline'],
    },
    'appeal_diversity': {
        'category': '訴求表現',
        'label': '多様性重視',
        'patterns': [r'ダイバーシティ', r'多様(性|な人材)', r'外国(人|籍).{0,5}(活躍|歓迎)', r'LGBTQ'],
        'fields': ['job_description'],
    },
    'appeal_ict': {
        'category': '訴求表現',
        'label': 'ICT・DX推進',
        'patterns': [r'ICT', r'DX', r'IT.{0,5}(化|活用|導入)', r'電子カルテ', r'ペーパーレス', r'タブレット'],
        'fields': ['job_description'],
    },
    # --- 給与・報酬 ---
    'salary_high': {
        'category': '給与・報酬',
        'label': '高給与',
        'patterns': [r'高(給|収入|年収|時給)', r'業界(最高|トップ|高水準)'],
        'fields': ['headline', 'job_description', 'salary_detail'],
    },
    'salary_bonus_high': {
        'category': '給与・報酬',
        'label': '賞与4ヶ月以上',
        'patterns': [r'賞与.{0,5}([4-9]|1[0-2])\s*[ヶヵか箇ケ]?\s*月', r'ボーナス.{0,5}([4-9]|1[0-2])\s*[ヶヵか箇ケ]?\s*月'],
        'fields': ['benefits', 'salary_detail'],
    },
    'salary_raise': {
        'category': '給与・報酬',
        'label': '昇給制度',
        'patterns': [r'昇給.{0,5}(あり|年\d回|制度)', r'定期昇給', r'ベースアップ'],
        'fields': ['benefits', 'salary_detail'],
    },
    'salary_incentive': {
        'category': '給与・報酬',
        'label': 'インセンティブ',
        'patterns': [r'インセンティブ', r'歩合', r'成果(給|報酬)'],
        'fields': ['salary_detail', 'benefits'],
    },
    'salary_model': {
        'category': '給与・報酬',
        'label': 'モデル年収',
        'patterns': [r'(想定|モデル)年収', r'年収\d{3}万', r'年収例'],
        'fields': ['salary_detail', 'job_description'],
    },
    'salary_allowance': {
        'category': '給与・報酬',
        'label': '手当充実',
        'patterns': [r'手当.{0,5}充実', r'各種手当', r'手当\d+種'],
        'fields': ['benefits', 'salary_detail'],
    },
    'salary_family': {
        'category': '給与・報酬',
        'label': '家族手当',
        'patterns': [r'家族手当', r'扶養手当', r'配偶者手当', r'子ども手当'],
        'fields': ['benefits', 'salary_detail'],
    },
    # --- キャリア・成長 ---
    'career_promotion': {
        'category': 'キャリア・成長',
        'label': '昇進・管理職',
        'patterns': [r'(管理職|リーダー|主任|施設長).{0,5}(候補|登用|目指)', r'キャリアアップ', r'昇進'],
        'fields': ['job_description', 'headline'],
    },
    'career_regular': {
        'category': 'キャリア・成長',
        'label': '正社員登用',
        'patterns': [r'正社員登用', r'正社員への(登用|切替|転換)', r'社員登用(制度|あり)'],
        'fields': ['job_description', 'benefits'],
    },
    'career_certification': {
        'category': 'キャリア・成長',
        'label': '資格取得費用負担',
        'patterns': [r'資格取得.{0,5}(費用|全額|一部).{0,5}(負担|補助|支援)', r'受験料.{0,5}(負担|補助)'],
        'fields': ['benefits', 'education_training'],
    },
    'career_grade': {
        'category': 'キャリア・成長',
        'label': '等級制度',
        'patterns': [r'等級(制度|制)', r'職能(資格|等級)', r'グレード制'],
        'fields': ['education_training', 'job_description'],
    },
    'career_specialist': {
        'category': 'キャリア・成長',
        'label': '専門特化',
        'patterns': [r'専門(性|特化|分野)', r'スペシャリスト', r'認定.{0,3}(看護師|介護福祉士)'],
        'fields': ['job_description', 'education_training'],
    },
    # --- 通勤・立地 ---
    'commute_station': {
        'category': '通勤・立地',
        'label': '駅近',
        'patterns': [r'駅.{0,3}(近|チカ)', r'駅.{0,5}徒歩\d分', r'駅(前|直結)'],
        'fields': ['access', 'job_description', 'headline'],
    },
    'commute_notransfer': {
        'category': '通勤・立地',
        'label': '転勤なし',
        'patterns': [r'転勤(なし|無し|ありません)', r'異動(なし|無し)'],
        'fields': ['job_description', 'benefits'],
    },
    'commute_parking': {
        'category': '通勤・立地',
        'label': '無料駐車場',
        'patterns': [r'(無料|職員用).{0,3}駐車場', r'駐車場.{0,3}(無料|完備)'],
        'fields': ['benefits', 'access'],
    },
    'commute_direct': {
        'category': '通勤・立地',
        'label': '直行直帰',
        'patterns': [r'直行直帰', r'直行.{0,3}直帰'],
        'fields': ['working_hours', 'job_description'],
    },
    # --- ワークライフバランス ---
    'wlb_telework': {
        'category': 'ワークライフバランス',
        'label': 'テレワーク',
        'patterns': [r'テレワーク', r'リモートワーク', r'在宅勤務', r'在宅(で|での)'],
        'fields': ['working_hours', 'job_description', 'benefits'],
    },
    'wlb_flex': {
        'category': 'ワークライフバランス',
        'label': 'フレックス',
        'patterns': [r'フレックス(タイム)?', r'時差出勤', r'コアタイム'],
        'fields': ['working_hours', 'job_description'],
    },
    'wlb_maternity': {
        'category': 'ワークライフバランス',
        'label': '産休育休実績',
        'patterns': [r'産(休|前産後)', r'育(休|児休(暇|業)).{0,5}(実績|取得率)', r'育休復帰'],
        'fields': ['benefits', 'job_description'],
    },
    'wlb_paidleave': {
        'category': 'ワークライフバランス',
        'label': '有給取得推進',
        'patterns': [r'有給.{0,5}(取得率|消化率|推進|奨励)', r'有給.{0,3}\d{2}%'],
        'fields': ['holidays', 'benefits'],
    },
    'wlb_shorttime': {
        'category': 'ワークライフバランス',
        'label': '育児短時間',
        'patterns': [r'(育児|介護).{0,3}短時間', r'時短勤務', r'短時間正社員'],
        'fields': ['working_hours', 'benefits'],
    },
    'wlb_holidays125': {
        'category': 'ワークライフバランス',
        'label': '年間休日125日+',
        'patterns': [r'年間休日.{0,3}(12[5-9]|1[3-9]\d)', r'完全週休2日.{0,5}祝日'],
        'fields': ['holidays', 'job_description'],
    },
    # --- 採用プロセス ---
    'process_webinterview': {
        'category': '採用プロセス',
        'label': 'Web面接',
        'patterns': [r'(Web|オンライン|リモート|Zoom).{0,3}面(接|談)', r'ウェブ面接'],
        'fields': ['selection_process', 'job_description'],
    },
    'process_oneinterview': {
        'category': '採用プロセス',
        'label': '面接1回',
        'patterns': [r'面(接|談)\s*(1|１)\s*回', r'面接回数.{0,3}(1|１)回'],
        'fields': ['selection_process', 'job_description'],
    },
    'process_visit': {
        'category': '採用プロセス',
        'label': '見学・体験',
        'patterns': [r'(見学|体験|職場体験).{0,5}(可|OK|歓迎|受付)', r'見学会'],
        'fields': ['selection_process', 'job_description'],
    },
    # --- 仕事内容分析 ---
    'task_direct_care': {
        'category': '仕事内容分析',
        'label': '直接介護・看護',
        'patterns': [r'身体介護', r'入浴(介助|支援)', r'食事(介助|支援)', r'排(せつ|泄)(介助|支援)',
                     r'バイタル', r'点滴', r'採血', r'注射', r'褥瘡'],
        'fields': ['job_description'],
    },
    'task_indirect': {
        'category': '仕事内容分析',
        'label': '間接業務',
        'patterns': [r'記録(業務|作成)', r'書類(作成|業務)', r'事務(作業|業務)', r'電話対応',
                     r'レセプト', r'請求(業務|事務)'],
        'fields': ['job_description'],
    },
    'task_counseling': {
        'category': '仕事内容分析',
        'label': '相談支援',
        'patterns': [r'相談(支援|業務|対応)', r'ケアマネジメント', r'ケアプラン',
                     r'アセスメント', r'退院(支援|調整)'],
        'fields': ['job_description'],
    },
    'task_rehab': {
        'category': '仕事内容分析',
        'label': 'リハビリ',
        'patterns': [r'リハビリ(テーション)?', r'機能(訓練|回復)', r'理学療法', r'作業療法',
                     r'言語(聴覚|療法)'],
        'fields': ['job_description'],
    },
    'task_management': {
        'category': '仕事内容分析',
        'label': 'マネジメント',
        'patterns': [r'(スタッフ|職員).{0,3}(管理|マネジメント|指導)', r'シフト(管理|作成)',
                     r'人(事|材)(管理|育成)', r'施設(運営|管理)'],
        'fields': ['job_description'],
    },
    'task_childcare': {
        'category': '仕事内容分析',
        'label': '保育',
        'patterns': [r'保育(業務|活動)', r'(乳児|幼児).{0,3}(クラス|担当)',
                     r'お散歩', r'制作活動', r'連絡帳'],
        'fields': ['job_description'],
    },
    'task_cooking': {
        'category': '仕事内容分析',
        'label': '調理',
        'patterns': [r'調理(業務|補助)?', r'配(膳|食)', r'厨房', r'栄養(管理|指導)'],
        'fields': ['job_description'],
    },
}


def create_tables(conn):
    """SQLiteテーブル作成"""
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS segment_prefecture")
    c.execute("DROP TABLE IF EXISTS segment_municipality")
    c.execute("DROP TABLE IF EXISTS segment_tier3")
    c.execute("DROP TABLE IF EXISTS segment_tags")
    c.execute("DROP TABLE IF EXISTS segment_tag_combos")
    c.execute("DROP TABLE IF EXISTS segment_text_features")
    c.execute("DROP TABLE IF EXISTS segment_salary")
    c.execute("DROP TABLE IF EXISTS segment_job_desc")
    c.execute("DROP TABLE IF EXISTS segment_meta")
    c.execute("DROP TABLE IF EXISTS segment_age_decade")
    c.execute("DROP TABLE IF EXISTS segment_gender_lifecycle")
    c.execute("DROP TABLE IF EXISTS segment_exp_qual")

    c.execute("""
        CREATE TABLE segment_prefecture (
            job_type         TEXT NOT NULL,
            employment_type  TEXT NOT NULL,
            prefecture       TEXT NOT NULL,
            axis             TEXT NOT NULL,
            category         TEXT NOT NULL,
            label            TEXT NOT NULL,
            count            INTEGER NOT NULL,
            ratio            REAL NOT NULL,
            total            INTEGER NOT NULL,
            PRIMARY KEY (job_type, employment_type, prefecture, axis, category)
        )
    """)
    c.execute("CREATE INDEX idx_sp_pref ON segment_prefecture(job_type, employment_type, prefecture)")

    c.execute("""
        CREATE TABLE segment_municipality (
            job_type         TEXT NOT NULL,
            employment_type  TEXT NOT NULL,
            prefecture       TEXT NOT NULL,
            municipality     TEXT NOT NULL,
            axis             TEXT NOT NULL,
            category         TEXT NOT NULL,
            label            TEXT NOT NULL,
            count            INTEGER NOT NULL,
            ratio            REAL NOT NULL,
            total            INTEGER NOT NULL,
            PRIMARY KEY (job_type, employment_type, prefecture, municipality, axis, category)
        )
    """)
    c.execute("CREATE INDEX idx_sm_muni ON segment_municipality(job_type, employment_type, prefecture, municipality)")

    c.execute("""
        CREATE TABLE segment_tier3 (
            job_type         TEXT NOT NULL,
            employment_type  TEXT NOT NULL,
            prefecture       TEXT NOT NULL,
            municipality     TEXT,
            tier3_id         TEXT NOT NULL,
            label_short      TEXT NOT NULL,
            count            INTEGER NOT NULL,
            ratio            REAL NOT NULL,
            total            INTEGER NOT NULL
        )
    """)
    c.execute("CREATE INDEX idx_st3_pref ON segment_tier3(job_type, employment_type, prefecture)")

    c.execute("""
        CREATE TABLE segment_tags (
            job_type         TEXT NOT NULL,
            employment_type  TEXT NOT NULL,
            prefecture       TEXT NOT NULL,
            municipality     TEXT,
            tag              TEXT NOT NULL,
            count            INTEGER NOT NULL,
            ratio            REAL NOT NULL,
            total            INTEGER NOT NULL
        )
    """)
    c.execute("CREATE INDEX idx_stag_pref ON segment_tags(job_type, employment_type, prefecture)")

    c.execute("""
        CREATE TABLE segment_tag_combos (
            job_type         TEXT NOT NULL,
            employment_type  TEXT NOT NULL,
            prefecture       TEXT NOT NULL,
            combo            TEXT NOT NULL,
            combo_size       INTEGER NOT NULL,
            count            INTEGER NOT NULL,
            ratio            REAL NOT NULL,
            total            INTEGER NOT NULL
        )
    """)
    c.execute("CREATE INDEX idx_stc_pref ON segment_tag_combos(job_type, employment_type, prefecture)")

    c.execute("""
        CREATE TABLE segment_text_features (
            job_type         TEXT NOT NULL,
            employment_type  TEXT NOT NULL,
            prefecture       TEXT NOT NULL,
            municipality     TEXT,
            feature_id       TEXT NOT NULL,
            category         TEXT NOT NULL,
            label            TEXT NOT NULL,
            count            INTEGER NOT NULL,
            ratio            REAL NOT NULL,
            total            INTEGER NOT NULL
        )
    """)
    c.execute("CREATE INDEX idx_stf_pref ON segment_text_features(job_type, employment_type, prefecture)")

    c.execute("""
        CREATE TABLE segment_salary (
            job_type         TEXT NOT NULL,
            employment_type  TEXT NOT NULL,
            prefecture       TEXT NOT NULL,
            axis             TEXT NOT NULL,
            category         TEXT NOT NULL,
            count            INTEGER NOT NULL,
            salary_min_avg   INTEGER,
            salary_min_med   INTEGER,
            salary_max_avg   INTEGER,
            salary_max_med   INTEGER,
            holidays_avg     REAL,
            benefits_avg     REAL,
            PRIMARY KEY (job_type, employment_type, prefecture, axis, category)
        )
    """)

    c.execute("""
        CREATE TABLE segment_job_desc (
            job_type         TEXT NOT NULL,
            employment_type  TEXT NOT NULL,
            prefecture       TEXT NOT NULL,
            municipality     TEXT,
            task_label       TEXT NOT NULL,
            count            INTEGER NOT NULL,
            ratio            REAL NOT NULL,
            total            INTEGER NOT NULL
        )
    """)
    c.execute("CREATE INDEX idx_sjd_pref ON segment_job_desc(job_type, employment_type, prefecture)")

    # 年代分布テーブル (v2.0)
    c.execute("""
        CREATE TABLE segment_age_decade (
            job_type         TEXT NOT NULL,
            employment_type  TEXT NOT NULL,
            prefecture       TEXT NOT NULL,
            municipality     TEXT,
            decade           TEXT NOT NULL,
            count            INTEGER NOT NULL,
            ratio            REAL NOT NULL,
            total            INTEGER NOT NULL
        )
    """)
    c.execute("CREATE INDEX idx_sad_pref ON segment_age_decade(job_type, employment_type, prefecture)")

    # 性別・ライフステージテーブル (v2.0)
    c.execute("""
        CREATE TABLE segment_gender_lifecycle (
            job_type         TEXT NOT NULL,
            employment_type  TEXT NOT NULL,
            prefecture       TEXT NOT NULL,
            municipality     TEXT,
            dimension        TEXT NOT NULL,
            category         TEXT NOT NULL,
            count            INTEGER NOT NULL,
            ratio            REAL NOT NULL,
            total            INTEGER NOT NULL
        )
    """)
    c.execute("CREATE INDEX idx_sgl_pref ON segment_gender_lifecycle(job_type, employment_type, prefecture)")

    # 未経験×資格テーブル (v2.0)
    c.execute("""
        CREATE TABLE segment_exp_qual (
            job_type         TEXT NOT NULL,
            employment_type  TEXT NOT NULL,
            prefecture       TEXT NOT NULL,
            municipality     TEXT,
            segment          TEXT NOT NULL,
            count            INTEGER NOT NULL,
            ratio            REAL NOT NULL,
            total            INTEGER NOT NULL
        )
    """)
    c.execute("CREATE INDEX idx_seq_pref ON segment_exp_qual(job_type, employment_type, prefecture)")

    c.execute("""
        CREATE TABLE segment_meta (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    conn.commit()


def extract_text_features(df):
    """フリーテキストから特徴を抽出して列を追加"""
    print("  テキスト特徴抽出中...")
    for feat_id, feat_def in TEXT_FEATURE_DICT.items():
        patterns = feat_def['patterns']
        fields = feat_def['fields']
        compiled = [re.compile(p) for p in patterns]

        def check_row(row):
            for field in fields:
                val = row.get(field)
                if pd.isna(val):
                    continue
                text = str(val)
                for pat in compiled:
                    if pat.search(text):
                        return 1
            return 0

        df[f'feat_{feat_id}'] = df.apply(check_row, axis=1)

    feat_cols = [c for c in df.columns if c.startswith('feat_')]
    matched_any = df[feat_cols].sum(axis=1) > 0
    print(f"  テキスト特徴: {len(feat_cols)}種類, マッチ率 {matched_any.mean()*100:.1f}%")
    return df


def aggregate_prefecture(df, job_type, employment_type):
    """都道府県レベルの全軸集約"""
    rows = []
    for pref, pref_df in df.groupby('prefecture'):
        total = len(pref_df)
        for axis_code, col in AXIS_MAP.items():
            if col not in pref_df.columns:
                continue
            for cat, cnt in pref_df[col].value_counts().items():
                label = TIER2_LABELS.get(cat, cat)
                rows.append((job_type, employment_type, pref, axis_code, cat, label, cnt, cnt / total, total))
    return rows


def aggregate_municipality(df, job_type, employment_type):
    """市区町村レベルの全軸集約"""
    rows = []
    for (pref, muni), muni_df in df.groupby(['prefecture', 'municipality']):
        total = len(muni_df)
        if total < 5:
            continue
        for axis_code, col in AXIS_MAP.items():
            if col not in muni_df.columns:
                continue
            for cat, cnt in muni_df[col].value_counts().items():
                label = TIER2_LABELS.get(cat, cat)
                rows.append((job_type, employment_type, pref, muni, axis_code, cat, label, cnt, cnt / total, total))
    return rows


def aggregate_tier3(df, job_type, employment_type):
    """Tier3パターンの地域別集約"""
    rows = []
    if 'tier3_id' not in df.columns:
        return rows

    # 都道府県レベル
    for pref, pref_df in df.groupby('prefecture'):
        total = len(pref_df)
        for t3, cnt in pref_df['tier3_id'].value_counts().items():
            matched = pref_df[pref_df['tier3_id'] == t3]
            label = str(matched.iloc[0].get('tier3_label_short', t3))
            rows.append((job_type, employment_type, pref, None, t3, label, cnt, cnt / total, total))

    # 市区町村レベル（10件以上のみ）
    for (pref, muni), muni_df in df.groupby(['prefecture', 'municipality']):
        if len(muni_df) < 10:
            continue
        total = len(muni_df)
        for t3, cnt in muni_df['tier3_id'].value_counts().items():
            if cnt < 2:
                continue
            matched = muni_df[muni_df['tier3_id'] == t3]
            label = str(matched.iloc[0].get('tier3_label_short', t3))
            rows.append((job_type, employment_type, pref, muni, t3, label, cnt, cnt / total, total))

    return rows


def aggregate_tags(df, job_type, employment_type):
    """個別タグの地域別分布（都道府県＋市区町村）"""
    rows = []
    if 'tags' not in df.columns:
        return rows

    def split_tags(tags_str):
        if pd.isna(tags_str):
            return []
        return [t.strip() for t in str(tags_str).split(',') if t.strip()]

    # 都道府県レベル
    for pref, pref_df in df.groupby('prefecture'):
        total = len(pref_df)
        tag_counter = Counter()
        for tags_str in pref_df['tags']:
            for tag in split_tags(tags_str):
                tag_counter[tag] += 1
        for tag, cnt in tag_counter.items():
            rows.append((job_type, employment_type, pref, None, tag, cnt, cnt / total, total))

    # 市区町村レベル（10件以上のみ）
    for (pref, muni), muni_df in df.groupby(['prefecture', 'municipality']):
        if len(muni_df) < 10:
            continue
        total = len(muni_df)
        tag_counter = Counter()
        for tags_str in muni_df['tags']:
            for tag in split_tags(tags_str):
                tag_counter[tag] += 1
        for tag, cnt in tag_counter.items():
            if cnt < 2:
                continue
            rows.append((job_type, employment_type, pref, muni, tag, cnt, cnt / total, total))

    return rows


def aggregate_tag_combos(df, job_type, employment_type, top_n=30):
    """タグ組み合わせパターンの都道府県別分布"""
    rows = []
    if 'tags' not in df.columns:
        return rows

    def normalize_combo(tags_str):
        if pd.isna(tags_str):
            return None
        tags = sorted(t.strip() for t in str(tags_str).split(',') if t.strip())
        if len(tags) < 2:
            return None
        # 頻出2-3タグの組み合わせを生成
        return '+'.join(tags[:5])  # 最大5タグまで

    for pref, pref_df in df.groupby('prefecture'):
        total = len(pref_df)
        combo_counter = Counter()
        for tags_str in pref_df['tags']:
            combo = normalize_combo(tags_str)
            if combo:
                combo_counter[combo] += 1
        # 上位30パターンのみ
        for combo, cnt in combo_counter.most_common(top_n):
            combo_size = combo.count('+') + 1
            rows.append((job_type, employment_type, pref, combo, combo_size, cnt, cnt / total, total))

    return rows


def aggregate_text_features(df, job_type, employment_type):
    """テキスト特徴の地域別分布"""
    rows = []
    feat_cols = [c for c in df.columns if c.startswith('feat_')]
    if not feat_cols:
        return rows

    # 都道府県レベル
    for pref, pref_df in df.groupby('prefecture'):
        total = len(pref_df)
        for col in feat_cols:
            feat_id = col.replace('feat_', '')
            feat_def = TEXT_FEATURE_DICT.get(feat_id, {})
            cnt = int(pref_df[col].sum())
            if cnt == 0:
                continue
            rows.append((
                job_type, employment_type, pref, None, feat_id,
                feat_def.get('category', ''),
                feat_def.get('label', feat_id),
                cnt, cnt / total, total
            ))

    # 市区町村レベル（10件以上のみ）
    for (pref, muni), muni_df in df.groupby(['prefecture', 'municipality']):
        if len(muni_df) < 10:
            continue
        total = len(muni_df)
        for col in feat_cols:
            feat_id = col.replace('feat_', '')
            feat_def = TEXT_FEATURE_DICT.get(feat_id, {})
            cnt = int(muni_df[col].sum())
            if cnt < 2:
                continue
            rows.append((
                job_type, employment_type, pref, muni, feat_id,
                feat_def.get('category', ''),
                feat_def.get('label', feat_id),
                cnt, cnt / total, total
            ))

    return rows


def aggregate_job_desc(df, job_type, employment_type):
    """仕事内容カテゴリの地域別分布"""
    rows = []
    if 'jd_categories' not in df.columns:
        return rows

    def split_cats(cats_str):
        if pd.isna(cats_str) or not str(cats_str).strip():
            return []
        return [c.strip() for c in str(cats_str).split(',') if c.strip()]

    # 都道府県レベル
    for pref, pref_df in df.groupby('prefecture'):
        total = len(pref_df)
        cat_counter = Counter()
        for cats_str in pref_df['jd_categories']:
            for cat in split_cats(cats_str):
                cat_counter[cat] += 1
        for cat, cnt in cat_counter.items():
            rows.append((job_type, employment_type, pref, None, cat, cnt, cnt / total, total))

    # 市区町村レベル（10件以上のみ）
    for (pref, muni), muni_df in df.groupby(['prefecture', 'municipality']):
        if len(muni_df) < 10:
            continue
        total = len(muni_df)
        cat_counter = Counter()
        for cats_str in muni_df['jd_categories']:
            for cat in split_cats(cats_str):
                cat_counter[cat] += 1
        for cat, cnt in cat_counter.items():
            if cnt < 2:
                continue
            rows.append((job_type, employment_type, pref, muni, cat, cnt, cnt / total, total))

    return rows


def aggregate_salary(df, job_type, employment_type):
    """セグメント別の給与統計"""
    rows = []
    sal_min_col = 'salary_min'
    sal_max_col = 'salary_max'
    hol_col = 'annual_holidays'
    ben_col = 'benefits_score'

    if sal_min_col not in df.columns:
        return rows

    for pref, pref_df in df.groupby('prefecture'):
        # 5軸のカテゴリ別
        for axis_code, col in AXIS_MAP.items():
            if col not in pref_df.columns:
                continue
            for cat, cat_df in pref_df.groupby(col):
                cnt = len(cat_df)
                if cnt < 3:
                    continue
                s_min = cat_df[sal_min_col].dropna()
                s_max = cat_df[sal_max_col].dropna()
                hol = cat_df[hol_col].dropna() if hol_col in cat_df.columns else pd.Series(dtype=float)
                ben = cat_df[ben_col].dropna() if ben_col in cat_df.columns else pd.Series(dtype=float)
                rows.append((
                    job_type, employment_type, pref, axis_code, cat, cnt,
                    int(s_min.mean()) if len(s_min) > 0 else None,
                    int(s_min.median()) if len(s_min) > 0 else None,
                    int(s_max.mean()) if len(s_max) > 0 else None,
                    int(s_max.median()) if len(s_max) > 0 else None,
                    round(float(hol.mean()), 1) if len(hol) > 0 else None,
                    round(float(ben.mean()), 1) if len(ben) > 0 else None,
                ))

        # Tier3パターン別
        if 'tier3_id' in pref_df.columns:
            for t3, t3_df in pref_df.groupby('tier3_id'):
                cnt = len(t3_df)
                if cnt < 3:
                    continue
                s_min = t3_df[sal_min_col].dropna()
                s_max = t3_df[sal_max_col].dropna()
                hol = t3_df[hol_col].dropna() if hol_col in t3_df.columns else pd.Series(dtype=float)
                ben = t3_df[ben_col].dropna() if ben_col in t3_df.columns else pd.Series(dtype=float)
                rows.append((
                    job_type, employment_type, pref, 'tier3', t3, cnt,
                    int(s_min.mean()) if len(s_min) > 0 else None,
                    int(s_min.median()) if len(s_min) > 0 else None,
                    int(s_max.mean()) if len(s_max) > 0 else None,
                    int(s_max.median()) if len(s_max) > 0 else None,
                    round(float(hol.mean()), 1) if len(hol) > 0 else None,
                    round(float(ben.mean()), 1) if len(ben) > 0 else None,
                ))

    return rows


def aggregate_age_decade(df, job_type, employment_type):
    """年代分布の地域別集約 (v2.0)"""
    rows = []
    decades = ['20代', '30代', '40代', '50代', '60代']
    score_cols = {
        '20代': 'age_20s_score', '30代': 'age_30s_score',
        '40代': 'age_40s_score', '50代': 'age_50s_score',
        '60代': 'age_60s_score',
    }

    # スコアカラムがなければ空で返す
    if not any(c in df.columns for c in score_cols.values()):
        return rows

    # 都道府県レベル
    for pref, pref_df in df.groupby('prefecture'):
        total = len(pref_df)
        for dec in decades:
            col = score_cols[dec]
            if col not in pref_df.columns:
                continue
            cnt = int((pref_df[col] >= 1).sum())
            if cnt > 0:
                rows.append((job_type, employment_type, pref, None, dec, cnt, cnt / total, total))

    # 市区町村レベル（10件以上のみ）
    for (pref, muni), muni_df in df.groupby(['prefecture', 'municipality']):
        if len(muni_df) < 10:
            continue
        total = len(muni_df)
        for dec in decades:
            col = score_cols[dec]
            if col not in muni_df.columns:
                continue
            cnt = int((muni_df[col] >= 1).sum())
            if cnt >= 2:
                rows.append((job_type, employment_type, pref, muni, dec, cnt, cnt / total, total))

    return rows


def aggregate_gender_lifecycle(df, job_type, employment_type):
    """性別・ライフステージ分布の地域別集約 (v2.0)"""
    rows = []

    # 性別シグナル集約（都道府県レベル）
    if 'gender_signal' in df.columns:
        for pref, pref_df in df.groupby('prefecture'):
            total = len(pref_df)
            for signal in ['female_leaning', 'male_leaning', 'neutral']:
                cnt = int((pref_df['gender_signal'] == signal).sum())
                if cnt > 0:
                    rows.append((job_type, employment_type, pref, None, 'gender', signal, cnt, cnt / total, total))

        # 性別シグナル集約（市区町村レベル、10件以上）
        for (pref, muni), muni_df in df.groupby(['prefecture', 'municipality']):
            if len(muni_df) < 10:
                continue
            total = len(muni_df)
            for signal in ['female_leaning', 'male_leaning', 'neutral']:
                cnt = int((muni_df['gender_signal'] == signal).sum())
                if cnt >= 2:
                    rows.append((job_type, employment_type, pref, muni, 'gender', signal, cnt, cnt / total, total))

    # ライフステージ集約（都道府県レベル）
    if 'lifecycle_stages' in df.columns:
        stages = [
            '新卒・キャリア初期', 'キャリア形成期', '結婚・出産期',
            '育児期', '復職期', 'セカンドキャリア期', '介護離職・復帰期',
        ]
        for pref, pref_df in df.groupby('prefecture'):
            total = len(pref_df)
            for stage in stages:
                cnt = int(pref_df['lifecycle_stages'].fillna('').str.contains(re.escape(stage)).sum())
                if cnt > 0:
                    rows.append((job_type, employment_type, pref, None, 'lifecycle', stage, cnt, cnt / total, total))

        # ライフステージ集約（市区町村レベル、10件以上）
        for (pref, muni), muni_df in df.groupby(['prefecture', 'municipality']):
            if len(muni_df) < 10:
                continue
            total = len(muni_df)
            for stage in stages:
                cnt = int(muni_df['lifecycle_stages'].fillna('').str.contains(re.escape(stage)).sum())
                if cnt >= 2:
                    rows.append((job_type, employment_type, pref, muni, 'lifecycle', stage, cnt, cnt / total, total))

    return rows


def aggregate_exp_qual(df, job_type, employment_type):
    """未経験×資格セグメントの地域別集約 (v2.0)"""
    rows = []
    if 'exp_qual_segment' not in df.columns:
        return rows

    segments = [
        '未経験・無資格OK', '未経験歓迎・資格必要',
        '経験者・無資格可', '経験者・資格必須', '条件不明',
    ]

    for pref, pref_df in df.groupby('prefecture'):
        total = len(pref_df)
        for seg in segments:
            cnt = int((pref_df['exp_qual_segment'] == seg).sum())
            if cnt > 0:
                rows.append((job_type, employment_type, pref, None, seg, cnt, cnt / total, total))

    # 市区町村レベル
    for (pref, muni), muni_df in df.groupby(['prefecture', 'municipality']):
        if len(muni_df) < 10:
            continue
        total = len(muni_df)
        for seg in segments:
            cnt = int((muni_df['exp_qual_segment'] == seg).sum())
            if cnt >= 2:
                rows.append((job_type, employment_type, pref, muni, seg, cnt, cnt / total, total))

    return rows


def process_csv(csv_path, conn):
    """1つのCSVを読み込み、全集約を実行してDBに書き込み"""
    print(f"\n{'='*60}")
    print(f"処理: {csv_path.name}")
    print(f"{'='*60}")

    t0 = time.time()

    # 職種名をファイル名から推定
    stem = csv_path.stem
    # classified_看護師・准看護師_20260215 → 看護師・准看護師
    parts = stem.split('_')
    if len(parts) >= 3 and parts[0] == 'classified':
        job_type = '_'.join(parts[1:-1])
    else:
        job_type = stem

    print(f"職種: {job_type}")

    # CSV読み込み
    df = pd.read_csv(csv_path, encoding='utf-8-sig', low_memory=False)
    print(f"行数: {len(df):,}")

    # 必須カラム確認
    required = ['prefecture', 'municipality', 'tier1_experience']
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"  エラー: 必須カラム不足: {missing}")
        return job_type, 0

    # テキスト特徴抽出
    df = extract_text_features(df)
    t1 = time.time()
    print(f"  テキスト特徴抽出: {t1 - t0:.1f}s")

    # 雇用形態グループを構築
    emp_col = 'employment_type'
    groups = [('全て', df)]  # 全て = 全雇用形態合計（現行動作と同等）
    if emp_col in df.columns:
        df[emp_col] = df[emp_col].fillna('不明')
        for emp_type in sorted(df[emp_col].unique()):
            emp_df = df[df[emp_col] == emp_type]
            if len(emp_df) >= 10:
                groups.append((emp_type, emp_df))
        print(f"  雇用形態: {len(groups)-1}種類 + 全て")
    else:
        print(f"  雇用形態: カラムなし（全てのみ）")

    # 1. 都道府県集約
    pref_rows = []
    for emp_type, group_df in groups:
        pref_rows.extend(aggregate_prefecture(group_df, job_type, emp_type))
    conn.executemany(
        "INSERT INTO segment_prefecture VALUES (?,?,?,?,?,?,?,?,?)",
        pref_rows
    )
    print(f"  segment_prefecture: {len(pref_rows):,}行")

    # 2. 市区町村集約
    muni_rows = []
    for emp_type, group_df in groups:
        muni_rows.extend(aggregate_municipality(group_df, job_type, emp_type))
    conn.executemany(
        "INSERT INTO segment_municipality VALUES (?,?,?,?,?,?,?,?,?,?)",
        muni_rows
    )
    print(f"  segment_municipality: {len(muni_rows):,}行")

    # 3. Tier3集約
    t3_rows = []
    for emp_type, group_df in groups:
        t3_rows.extend(aggregate_tier3(group_df, job_type, emp_type))
    conn.executemany(
        "INSERT INTO segment_tier3 VALUES (?,?,?,?,?,?,?,?,?)",
        t3_rows
    )
    print(f"  segment_tier3: {len(t3_rows):,}行")

    # 4. タグ集約
    tag_rows = []
    for emp_type, group_df in groups:
        tag_rows.extend(aggregate_tags(group_df, job_type, emp_type))
    conn.executemany(
        "INSERT INTO segment_tags VALUES (?,?,?,?,?,?,?,?)",
        tag_rows
    )
    print(f"  segment_tags: {len(tag_rows):,}行")

    # 5. タグ組み合わせ集約
    combo_rows = []
    for emp_type, group_df in groups:
        combo_rows.extend(aggregate_tag_combos(group_df, job_type, emp_type))
    conn.executemany(
        "INSERT INTO segment_tag_combos VALUES (?,?,?,?,?,?,?,?)",
        combo_rows
    )
    print(f"  segment_tag_combos: {len(combo_rows):,}行")

    # 6. テキスト特徴集約
    tf_rows = []
    for emp_type, group_df in groups:
        tf_rows.extend(aggregate_text_features(group_df, job_type, emp_type))
    conn.executemany(
        "INSERT INTO segment_text_features VALUES (?,?,?,?,?,?,?,?,?,?)",
        tf_rows
    )
    print(f"  segment_text_features: {len(tf_rows):,}行")

    # 7. 給与統計
    sal_rows = []
    for emp_type, group_df in groups:
        sal_rows.extend(aggregate_salary(group_df, job_type, emp_type))
    conn.executemany(
        "INSERT INTO segment_salary VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        sal_rows
    )
    print(f"  segment_salary: {len(sal_rows):,}行")

    # 8. 仕事内容カテゴリ集約
    jd_rows = []
    for emp_type, group_df in groups:
        jd_rows.extend(aggregate_job_desc(group_df, job_type, emp_type))
    conn.executemany(
        "INSERT INTO segment_job_desc VALUES (?,?,?,?,?,?,?,?)",
        jd_rows
    )
    print(f"  segment_job_desc: {len(jd_rows):,}行")

    # 9. 年代分布集約 (v2.0)
    age_rows = []
    for emp_type, group_df in groups:
        age_rows.extend(aggregate_age_decade(group_df, job_type, emp_type))
    conn.executemany(
        "INSERT INTO segment_age_decade VALUES (?,?,?,?,?,?,?,?)",
        age_rows
    )
    print(f"  segment_age_decade: {len(age_rows):,}行")

    # 10. 性別・ライフステージ集約 (v2.0)
    gl_rows = []
    for emp_type, group_df in groups:
        gl_rows.extend(aggregate_gender_lifecycle(group_df, job_type, emp_type))
    conn.executemany(
        "INSERT INTO segment_gender_lifecycle VALUES (?,?,?,?,?,?,?,?,?)",
        gl_rows
    )
    print(f"  segment_gender_lifecycle: {len(gl_rows):,}行")

    # 11. 未経験×資格セグメント集約 (v2.0)
    eq_rows = []
    for emp_type, group_df in groups:
        eq_rows.extend(aggregate_exp_qual(group_df, job_type, emp_type))
    conn.executemany(
        "INSERT INTO segment_exp_qual VALUES (?,?,?,?,?,?,?,?)",
        eq_rows
    )
    print(f"  segment_exp_qual: {len(eq_rows):,}行")

    conn.commit()

    elapsed = time.time() - t0
    print(f"  完了: {elapsed:.1f}s")

    # 雇用形態リストを返す
    emp_list = sorted(df[emp_col].unique().tolist()) if emp_col in df.columns else []
    return job_type, len(df), emp_list


def write_meta(conn, job_types_info, classifier_version="v2.0"):
    """メタ情報をDBに書き込み"""
    now = datetime.now().isoformat(timespec='seconds')
    job_types = ','.join(item[0] for item in job_types_info)
    total = sum(item[1] for item in job_types_info)

    # 全雇用形態を収集
    all_emp_types = set()
    for item in job_types_info:
        if len(item) >= 3:
            all_emp_types.update(item[2])

    meta = [
        ('generated_at', now),
        ('classifier_version', classifier_version),
        ('job_types', job_types),
        ('total_records', str(total)),
        ('tier3_patterns', str(len(TIER3_PATTERNS))),
        ('text_feature_count', str(len(TEXT_FEATURE_DICT))),
        ('employment_types', ','.join(sorted(all_emp_types))),
    ]
    for item in job_types_info:
        jt = item[0]
        cnt = item[1]
        safe_key = jt.replace('・', '_').replace('ー', '_')
        meta.append((f'count_{safe_key}', str(cnt)))

    conn.executemany("INSERT INTO segment_meta VALUES (?,?)", meta)
    conn.commit()


def verify_db(conn):
    """DB内容の検証"""
    c = conn.cursor()
    print(f"\n{'='*60}")
    print("検証結果")
    print(f"{'='*60}")

    tables = [
        'segment_prefecture', 'segment_municipality', 'segment_tier3',
        'segment_tags', 'segment_tag_combos', 'segment_text_features',
        'segment_salary', 'segment_job_desc',
        'segment_age_decade', 'segment_gender_lifecycle', 'segment_exp_qual',
        'segment_meta',
    ]
    for table in tables:
        cnt = c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {cnt:,}行")

    # 都道府県数チェック
    prefs = c.execute(
        "SELECT DISTINCT prefecture FROM segment_prefecture"
    ).fetchall()
    print(f"\n  都道府県数: {len(prefs)}")
    if len(prefs) != 47:
        print(f"  警告: 47都道府県ではありません（{len(prefs)}）")

    # 雇用形態一覧
    emp_types = c.execute(
        "SELECT DISTINCT employment_type FROM segment_prefecture ORDER BY employment_type"
    ).fetchall()
    print(f"  雇用形態: {[r[0] for r in emp_types]}")

    # サンプルクエリ: 東京都の看護師セグメント
    print(f"\n--- 東京都 看護師 軸A TOP3 ---")
    rows = c.execute("""
        SELECT category, label, count, ROUND(ratio*100,1) as pct
        FROM segment_prefecture
        WHERE job_type LIKE '%看護師%' AND prefecture='東京都' AND axis='A'
        ORDER BY count DESC LIMIT 3
    """).fetchall()
    for row in rows:
        print(f"  {row[0]} {row[1]}: {row[2]:,}件 ({row[3]}%)")

    # テキスト特徴サンプル
    print(f"\n--- 東京都 看護師 テキスト特徴 TOP5 ---")
    rows = c.execute("""
        SELECT feature_id, category, label, count, ROUND(ratio*100,1) as pct
        FROM segment_text_features
        WHERE job_type LIKE '%看護師%' AND prefecture='東京都' AND municipality IS NULL
        ORDER BY count DESC LIMIT 5
    """).fetchall()
    for row in rows:
        print(f"  [{row[1]}] {row[2]}: {row[3]:,}件 ({row[4]}%)")

    # タグサンプル
    print(f"\n--- 東京都 看護師 タグ TOP5 ---")
    rows = c.execute("""
        SELECT tag, count, ROUND(ratio*100,1) as pct
        FROM segment_tags
        WHERE job_type LIKE '%看護師%' AND prefecture='東京都' AND municipality IS NULL
        ORDER BY count DESC LIMIT 5
    """).fetchall()
    for row in rows:
        print(f"  {row[0]}: {row[1]:,}件 ({row[2]}%)")

    # タグ組み合わせサンプル
    print(f"\n--- 東京都 看護師 タグ組み合わせ TOP3 ---")
    rows = c.execute("""
        SELECT combo, combo_size, count, ROUND(ratio*100,1) as pct
        FROM segment_tag_combos
        WHERE job_type LIKE '%看護師%' AND prefecture='東京都'
        ORDER BY count DESC LIMIT 3
    """).fetchall()
    for row in rows:
        print(f"  [{row[1]}タグ] {row[0]}: {row[2]:,}件 ({row[3]}%)")


def main():
    parser = argparse.ArgumentParser(description="セグメント集約スクリプト")
    parser.add_argument("--input", type=str, action='append', required=True,
                        help="classified CSVパス（複数指定可）")
    parser.add_argument("--output", type=str, default=None,
                        help="出力SQLiteパス（デフォルト: 入力と同ディレクトリ）")
    args = parser.parse_args()

    input_paths = [Path(p) for p in args.input]
    for p in input_paths:
        if not p.exists():
            print(f"エラー: {p} が見つかりません")
            sys.exit(1)

    output_path = Path(args.output) if args.output else input_paths[0].parent / 'segment_summary.db'

    print(f"出力先: {output_path}")
    print(f"入力ファイル: {len(input_paths)}件")
    for p in input_paths:
        print(f"  - {p.name}")

    # DB作成
    if output_path.exists():
        output_path.unlink()
    conn = sqlite3.connect(str(output_path))
    create_tables(conn)

    # 各CSV処理
    job_types_info = []
    for csv_path in input_paths:
        result = process_csv(csv_path, conn)
        job_types_info.append(result)

    # メタ情報
    write_meta(conn, job_types_info)

    # 検証
    verify_db(conn)

    conn.close()

    # 圧縮
    gz_path = Path(str(output_path) + '.gz')
    print(f"\n圧縮中: {gz_path.name}")
    with open(output_path, 'rb') as f_in:
        with gzip.open(gz_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    db_size = output_path.stat().st_size / 1024 / 1024
    gz_size = gz_path.stat().st_size / 1024 / 1024
    print(f"  DB: {db_size:.1f}MB → 圧縮: {gz_size:.1f}MB")

    print(f"\n完了")


if __name__ == '__main__':
    main()
