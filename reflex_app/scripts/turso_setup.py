# -*- coding: utf-8 -*-
"""
Turso データベースセットアップスクリプト
- テーブル作成
- インデックス作成
- CSVデータインポート
"""

import os
import sys
import asyncio
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
import libsql_client

# .env ファイルを読み込み
load_dotenv()

# 環境変数から接続情報を取得
DATABASE_URL = os.getenv('TURSO_DATABASE_URL')
AUTH_TOKEN = os.getenv('TURSO_AUTH_TOKEN')

if not DATABASE_URL or not AUTH_TOKEN:
    print("Error: TURSO_DATABASE_URL または TURSO_AUTH_TOKEN が設定されていません")
    print(".env ファイルを確認してください")
    sys.exit(1)

# libsql:// を https:// に変換
if DATABASE_URL.startswith('libsql://'):
    DATABASE_URL = DATABASE_URL.replace('libsql://', 'https://')


async def create_table(client):
    """メインテーブルを作成"""
    print("テーブル作成中...")

    # 既存テーブルを削除（開発用）
    await client.execute("DROP TABLE IF EXISTS job_seeker_data")

    # テーブル作成
    await client.execute("""
        CREATE TABLE job_seeker_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            row_type TEXT NOT NULL,
            prefecture TEXT NOT NULL,
            municipality TEXT,
            category1 TEXT,
            category2 TEXT,
            category3 TEXT,
            applicant_count REAL,
            avg_age REAL,
            male_count REAL,
            female_count REAL,
            avg_qualifications REAL,
            latitude REAL,
            longitude REAL,
            count REAL,
            avg_desired_areas REAL,
            employment_rate TEXT,
            national_license_rate REAL,
            has_national_license TEXT,
            avg_mobility_score REAL,
            total_in_municipality REAL,
            market_share_pct REAL,
            avg_urgency_score REAL,
            inflow REAL,
            outflow REAL,
            net_flow REAL,
            demand_count REAL,
            supply_count REAL,
            gap REAL,
            demand_supply_ratio REAL,
            rarity_score REAL,
            total_applicants REAL,
            top_age_ratio REAL,
            female_ratio REAL,
            male_ratio REAL,
            top_employment_ratio REAL,
            avg_qualification_count REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    print("[OK] テーブル作成完了")


async def create_indexes(client):
    """インデックスを作成"""
    print("インデックス作成中...")

    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_prefecture ON job_seeker_data(prefecture)",
        "CREATE INDEX IF NOT EXISTS idx_municipality ON job_seeker_data(prefecture, municipality)",
        "CREATE INDEX IF NOT EXISTS idx_row_type ON job_seeker_data(row_type)",
        "CREATE INDEX IF NOT EXISTS idx_pref_type ON job_seeker_data(prefecture, row_type)",
    ]

    for idx_sql in indexes:
        await client.execute(idx_sql)

    print("[OK] インデックス作成完了")


async def import_csv(client, csv_path: str):
    """CSVファイルをデータベースにインポート"""
    print(f"CSVインポート中: {csv_path}")

    # CSVファイルを読み込み
    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    print(f"  行数: {len(df)}")
    print(f"  カラム数: {len(df.columns)}")

    # カラム名のマッピング（CSVカラム名 → DBカラム名）
    column_mapping = {
        'row_type': 'row_type',
        'prefecture': 'prefecture',
        'municipality': 'municipality',
        'category1': 'category1',
        'category2': 'category2',
        'category3': 'category3',
        'applicant_count': 'applicant_count',
        'avg_age': 'avg_age',
        'male_count': 'male_count',
        'female_count': 'female_count',
        'avg_qualifications': 'avg_qualifications',
        'latitude': 'latitude',
        'longitude': 'longitude',
        'count': 'count',
        'avg_desired_areas': 'avg_desired_areas',
        'employment_rate': 'employment_rate',
        'national_license_rate': 'national_license_rate',
        'has_national_license': 'has_national_license',
        'avg_mobility_score': 'avg_mobility_score',
        'total_in_municipality': 'total_in_municipality',
        'market_share_pct': 'market_share_pct',
        'avg_urgency_score': 'avg_urgency_score',
        'inflow': 'inflow',
        'outflow': 'outflow',
        'net_flow': 'net_flow',
        'demand_count': 'demand_count',
        'supply_count': 'supply_count',
        'gap': 'gap',
        'demand_supply_ratio': 'demand_supply_ratio',
        'rarity_score': 'rarity_score',
        'total_applicants': 'total_applicants',
        'top_age_ratio': 'top_age_ratio',
        'female_ratio': 'female_ratio',
        'male_ratio': 'male_ratio',
        'top_employment_ratio': 'top_employment_ratio',
        'avg_qualification_count': 'avg_qualification_count',
    }

    # 存在するカラムのみを使用
    available_columns = [col for col in column_mapping.keys() if col in df.columns]

    if not available_columns:
        print("[ERROR] CSVに有効なカラムがありません")
        return 0

    # データをインサート
    inserted = 0
    batch_size = 100

    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]

        for _, row in batch.iterrows():
            columns = []
            values = []
            placeholders = []

            for csv_col in available_columns:
                db_col = column_mapping[csv_col]
                value = row[csv_col]

                # NaN を None に変換
                if pd.isna(value):
                    value = None

                columns.append(db_col)
                values.append(value)
                placeholders.append('?')

            sql = f"INSERT INTO job_seeker_data ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            await client.execute(sql, values)
            inserted += 1

        print(f"  進捗: {min(i + batch_size, len(df))}/{len(df)} 行")

    print(f"[OK] CSVインポート完了: {inserted} 行")
    return inserted


async def verify_data(client):
    """インポートされたデータを検証"""
    print("\nデータ検証中...")

    # 総行数
    result = await client.execute("SELECT COUNT(*) FROM job_seeker_data")
    total_rows = result.rows[0][0]
    print(f"  総行数: {total_rows}")

    # row_type別件数
    result = await client.execute("""
        SELECT row_type, COUNT(*) as cnt
        FROM job_seeker_data
        GROUP BY row_type
        ORDER BY cnt DESC
    """)

    print("  row_type別件数:")
    for row in result.rows:
        print(f"    {row[0]}: {row[1]}")

    # 都道府県数
    result = await client.execute("""
        SELECT COUNT(DISTINCT prefecture) FROM job_seeker_data
    """)
    print(f"  都道府県数: {result.rows[0][0]}")

    # 市区町村数
    result = await client.execute("""
        SELECT COUNT(DISTINCT municipality) FROM job_seeker_data
        WHERE municipality IS NOT NULL
    """)
    print(f"  市区町村数: {result.rows[0][0]}")

    print("[OK] データ検証完了")

    return total_rows


async def main():
    """メイン処理"""
    print("=" * 50)
    print("Turso データベースセットアップ")
    print("=" * 50)
    print(f"Database URL: {DATABASE_URL}")
    print()

    # CSVファイルのパスを確認
    csv_path = Path(__file__).parent.parent / "MapComplete_Complete_All_FIXED.csv"

    if not csv_path.exists():
        print(f"[ERROR] CSVファイルが見つかりません: {csv_path}")
        sys.exit(1)

    # データベース接続
    async with libsql_client.create_client(
        url=DATABASE_URL,
        auth_token=AUTH_TOKEN
    ) as client:
        print("[OK] データベース接続成功")

        # テーブル作成
        await create_table(client)

        # インデックス作成
        await create_indexes(client)

        # CSVインポート
        await import_csv(client, str(csv_path))

        # データ検証
        total_rows = await verify_data(client)

        print()
        print("=" * 50)
        print("セットアップ完了")
        print(f"  インポート行数: {total_rows}")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
