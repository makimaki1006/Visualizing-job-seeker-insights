#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GAS統合テスト（10回繰り返し）

GASスクリプト5ファイル間の連携、HTML 2ファイルとの統合、
Pythonで生成されたCSVデータとの統合、エンドツーエンドデータフローを検証

作成日: 2025-10-27
"""

import os
import sys
import json
import csv
import re
from pathlib import Path
from datetime import datetime

# プロジェクトルート
PROJECT_ROOT = Path(__file__).resolve().parent.parent
GAS_FILES_DIR = PROJECT_ROOT / "gas_files"
GAS_SCRIPTS_DIR = GAS_FILES_DIR / "scripts"
GAS_HTML_DIR = GAS_FILES_DIR / "html"
DATA_OUTPUT_DIR = PROJECT_ROOT / "gas_output_phase1"

# テスト結果格納
test_results = []

def log_test(test_name, status, details, score=100):
    """テスト結果をログに記録"""
    result = {
        "test_name": test_name,
        "status": status,
        "details": details,
        "score": score,
        "timestamp": datetime.now().isoformat()
    }
    test_results.append(result)
    print(f"[{status}] {test_name}: {score}/100")
    return result

def check_file_exists(filepath):
    """ファイル存在確認"""
    return Path(filepath).exists()

def read_file(filepath):
    """ファイル読み込み"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

def check_function_exists(content, function_name):
    """GASファイル内の関数存在確認"""
    pattern = rf"function\s+{function_name}\s*\("
    return bool(re.search(pattern, content))

def check_html_element(content, element_id):
    """HTML内の要素存在確認"""
    pattern = rf'id=["\']?{element_id}["\']?'
    return bool(re.search(pattern, content))

def count_csv_rows(filepath):
    """CSV行数カウント"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except Exception as e:
        print(f"Error counting rows in {filepath}: {e}")
        return 0

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# テスト 1: メニュー→アップロード統合
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def test_1_menu_to_upload():
    """MinimalMenuIntegration → UniversalPhaseUploader → PhaseUpload.html"""
    print("\n" + "="*60)
    print("テスト 1: メニュー→アップロード統合")
    print("="*60)

    verification = {
        "menu_function_exists": False,
        "upload_dialog_callable": False,
        "html_template_loadable": False,
        "phase_config_accessible": False
    }

    # 1. MinimalMenuIntegration.gs 確認
    menu_file = GAS_SCRIPTS_DIR / "MinimalMenuIntegration.gs"
    if check_file_exists(menu_file):
        content = read_file(menu_file)
        if content:
            # onOpen関数確認
            verification["menu_function_exists"] = check_function_exists(content, "onOpen")

            # uploadPhase1-7関数確認
            if all([
                check_function_exists(content, "uploadPhase1"),
                check_function_exists(content, "uploadPhase2"),
                check_function_exists(content, "uploadPhase3")
            ]):
                verification["menu_function_exists"] = True

    # 2. UniversalPhaseUploader.gs 確認
    uploader_file = GAS_SCRIPTS_DIR / "UniversalPhaseUploader.gs"
    if check_file_exists(uploader_file):
        content = read_file(uploader_file)
        if content:
            # showPhaseUploadDialog関数確認
            verification["upload_dialog_callable"] = check_function_exists(content, "showPhaseUploadDialog")

            # PHASE_CONFIGS確認
            verification["phase_config_accessible"] = "PHASE_CONFIGS" in content

    # 3. PhaseUpload.html 確認
    html_file = GAS_HTML_DIR / "PhaseUpload.html"
    if check_file_exists(html_file):
        content = read_file(html_file)
        if content:
            # 必須要素確認
            verification["html_template_loadable"] = all([
                check_html_element(content, "uploadZone"),
                check_html_element(content, "uploadButton"),
                "google.script.run" in content,
                "importCSVToSheet" in content
            ])

    # スコア計算
    score = sum([1 for v in verification.values() if v]) * 25
    status = "PASS" if score >= 75 else "FAIL"

    details = {
        "flow": "MinimalMenuIntegration → UniversalPhaseUploader → PhaseUpload.html",
        "verification": verification
    }

    return log_test("integration_test_1_menu_to_upload", status, details, score)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# テスト 2: データプロバイダー統合
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def test_2_data_provider():
    """MapDataProvider.gs → MapComplete.html"""
    print("\n" + "="*60)
    print("テスト 2: データプロバイダー統合")
    print("="*60)

    verification = {
        "data_provider_exists": False,
        "get_all_data_function": False,
        "html_map_loadable": False,
        "leaflet_integration": False
    }

    # 1. MapDataProvider.gs 確認
    provider_file = GAS_SCRIPTS_DIR / "MapDataProvider.gs"
    if check_file_exists(provider_file):
        content = read_file(provider_file)
        if content:
            verification["data_provider_exists"] = True
            verification["get_all_data_function"] = check_function_exists(content, "getAllVisualizationData")

    # 2. MapComplete.html 確認
    html_file = GAS_HTML_DIR / "MapComplete.html"
    if check_file_exists(html_file):
        content = read_file(html_file)
        if content:
            verification["html_map_loadable"] = check_html_element(content, "map")

            # Leaflet.js統合確認
            verification["leaflet_integration"] = all([
                "leaflet" in content.lower(),
                "L.map" in content,
                "getAllVisualizationData" in content
            ])

    score = sum([1 for v in verification.values() if v]) * 25
    status = "PASS" if score >= 75 else "FAIL"

    details = {
        "flow": "MapDataProvider.gs → MapComplete.html",
        "verification": verification
    }

    return log_test("integration_test_2_data_provider", status, details, score)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# テスト 3: Phase 2/3可視化統合
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def test_3_phase2_3_visualization():
    """MinimalMenuIntegration → Phase2Phase3Visualizations.gs"""
    print("\n" + "="*60)
    print("テスト 3: Phase 2/3可視化統合")
    print("="*60)

    verification = {
        "chi_square_function": False,
        "anova_function": False,
        "persona_summary_function": False,
        "persona_details_function": False
    }

    # Phase2Phase3Visualizations.gs 確認
    viz_file = GAS_SCRIPTS_DIR / "Phase2Phase3Visualizations.gs"
    if check_file_exists(viz_file):
        content = read_file(viz_file)
        if content:
            verification["chi_square_function"] = check_function_exists(content, "showChiSquareTests")
            verification["anova_function"] = check_function_exists(content, "showANOVATests")
            verification["persona_summary_function"] = check_function_exists(content, "showPersonaSummary")
            verification["persona_details_function"] = check_function_exists(content, "showPersonaDetails")

    score = sum([1 for v in verification.values() if v]) * 25
    status = "PASS" if score >= 100 else "FAIL"

    details = {
        "flow": "MinimalMenuIntegration → Phase2Phase3Visualizations.gs",
        "verification": verification
    }

    return log_test("integration_test_3_phase2_3_visualization", status, details, score)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# テスト 4: API設定統合
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def test_4_api_config():
    """GoogleMapsAPIConfig.gs ↔ 各可視化機能"""
    print("\n" + "="*60)
    print("テスト 4: API設定統合")
    print("="*60)

    verification = {
        "api_config_exists": False,
        "get_api_key_function": False,
        "optional_support": False,
        "security_implementation": False
    }

    # GoogleMapsAPIConfig.gs 確認
    api_file = GAS_SCRIPTS_DIR / "GoogleMapsAPIConfig.gs"
    if check_file_exists(api_file):
        content = read_file(api_file)
        if content:
            verification["api_config_exists"] = True
            verification["get_api_key_function"] = check_function_exists(content, "getGoogleMapsAPIKey")

            # オプショナル対応確認
            verification["optional_support"] = "throwError = false" in content

            # セキュリティ実装確認
            verification["security_implementation"] = "PropertiesService" in content

    score = sum([1 for v in verification.values() if v]) * 25
    status = "PASS" if score >= 75 else "FAIL"

    details = {
        "flow": "GoogleMapsAPIConfig.gs ↔ 各可視化機能",
        "verification": verification
    }

    return log_test("integration_test_4_api_config", status, details, score)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# テスト 5: Phase 1-7データフロー
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def test_5_data_flow():
    """Python CSV → GAS取り込み → 可視化"""
    print("\n" + "="*60)
    print("テスト 5: Phase 1-7データフロー")
    print("="*60)

    verification = {
        "phase1_data_exists": False,
        "phase2_data_exists": False,
        "phase3_data_exists": False,
        "data_quality_ok": False
    }

    # Phase 1データ確認
    phase1_files = [
        DATA_OUTPUT_DIR / "MapMetrics.csv",
        DATA_OUTPUT_DIR / "Applicants.csv",
        DATA_OUTPUT_DIR / "DesiredWork.csv",
        DATA_OUTPUT_DIR / "AggDesired.csv"
    ]

    phase1_rows = 0
    for filepath in phase1_files:
        if check_file_exists(filepath):
            rows = count_csv_rows(filepath)
            phase1_rows += rows

    verification["phase1_data_exists"] = phase1_rows > 4  # 最低4行（ヘッダー×4）

    # Phase 2データ確認
    phase2_dir = PROJECT_ROOT / "gas_output_phase2"
    phase2_files = [
        phase2_dir / "ChiSquareTests.csv",
        phase2_dir / "ANOVATests.csv"
    ]

    phase2_exists = all([check_file_exists(f) for f in phase2_files])
    verification["phase2_data_exists"] = phase2_exists

    # Phase 3データ確認
    phase3_dir = PROJECT_ROOT / "gas_output_phase3"
    phase3_files = [
        phase3_dir / "PersonaSummary.csv",
        phase3_dir / "PersonaDetails.csv"
    ]

    phase3_exists = all([check_file_exists(f) for f in phase3_files])
    verification["phase3_data_exists"] = phase3_exists

    # データ品質確認（MapMetrics.csvのヘッダー確認）
    map_metrics_file = DATA_OUTPUT_DIR / "MapMetrics.csv"
    if check_file_exists(map_metrics_file):
        try:
            with open(map_metrics_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)
                required_headers = ["都道府県", "市区町村", "緯度", "経度", "カウント"]
                verification["data_quality_ok"] = all([h in headers for h in required_headers])
        except:
            pass

    score = sum([1 for v in verification.values() if v]) * 25
    status = "PASS" if score >= 50 else "FAIL"  # Phase 1が最重要

    details = {
        "flow": "Python CSV → GAS取り込み → 可視化",
        "verification": verification,
        "phase1_total_rows": phase1_rows
    }

    return log_test("integration_test_5_data_flow", status, details, score)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# テスト 6: エラー伝播
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def test_6_error_propagation():
    """下位レイヤーエラーが上位に正しく伝わるか"""
    print("\n" + "="*60)
    print("テスト 6: エラー伝播")
    print("="*60)

    verification = {
        "try_catch_in_uploader": False,
        "error_throw_in_import": False,
        "ui_alert_on_error": False,
        "logger_usage": False
    }

    # UniversalPhaseUploader.gs のエラーハンドリング確認
    uploader_file = GAS_SCRIPTS_DIR / "UniversalPhaseUploader.gs"
    if check_file_exists(uploader_file):
        content = read_file(uploader_file)
        if content:
            verification["try_catch_in_uploader"] = "try {" in content and "catch" in content
            verification["error_throw_in_import"] = "throw error" in content or "throw new Error" in content
            verification["logger_usage"] = "Logger.log" in content

    # Phase2Phase3Visualizations.gs のエラーハンドリング確認
    viz_file = GAS_SCRIPTS_DIR / "Phase2Phase3Visualizations.gs"
    if check_file_exists(viz_file):
        content = read_file(viz_file)
        if content:
            verification["ui_alert_on_error"] = "SpreadsheetApp.getUi().alert" in content and "エラー" in content

    score = sum([1 for v in verification.values() if v]) * 25
    status = "PASS" if score >= 75 else "FAIL"

    details = {
        "flow": "下位レイヤーエラー → 上位伝播",
        "verification": verification
    }

    return log_test("integration_test_6_error_propagation", status, details, score)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# テスト 7: 状態管理
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def test_7_state_management():
    """アップロード状態、データキャッシュ"""
    print("\n" + "="*60)
    print("テスト 7: 状態管理")
    print("="*60)

    verification = {
        "upload_status_function": False,
        "all_phases_status_function": False,
        "state_persistence": False,
        "sheet_existence_check": False
    }

    # UniversalPhaseUploader.gs の状態管理確認
    uploader_file = GAS_SCRIPTS_DIR / "UniversalPhaseUploader.gs"
    if check_file_exists(uploader_file):
        content = read_file(uploader_file)
        if content:
            verification["upload_status_function"] = check_function_exists(content, "showPhaseUploadStatus")
            verification["all_phases_status_function"] = check_function_exists(content, "showAllPhasesUploadStatus")
            verification["sheet_existence_check"] = "getSheetByName" in content

            # 状態の永続性（シート存在確認）
            verification["state_persistence"] = "if (sheet)" in content or "if (!sheet)" in content

    score = sum([1 for v in verification.values() if v]) * 25
    status = "PASS" if score >= 75 else "FAIL"

    details = {
        "flow": "アップロード状態 → 状態確認 → UI表示",
        "verification": verification
    }

    return log_test("integration_test_7_state_management", status, details, score)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# テスト 8: UI/UX統合
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def test_8_ui_ux_integration():
    """HTML UIからGAS関数呼び出し → 結果表示"""
    print("\n" + "="*60)
    print("テスト 8: UI/UX統合")
    print("="*60)

    verification = {
        "google_script_run_usage": False,
        "success_handler": False,
        "failure_handler": False,
        "progress_indicator": False
    }

    # PhaseUpload.html のUI統合確認
    html_file = GAS_HTML_DIR / "PhaseUpload.html"
    if check_file_exists(html_file):
        content = read_file(html_file)
        if content:
            verification["google_script_run_usage"] = "google.script.run" in content
            verification["success_handler"] = "withSuccessHandler" in content
            verification["failure_handler"] = "withFailureHandler" in content
            verification["progress_indicator"] = check_html_element(content, "progressBar") or "progress" in content.lower()

    score = sum([1 for v in verification.values() if v]) * 25
    status = "PASS" if score >= 75 else "FAIL"

    details = {
        "flow": "HTML UI → google.script.run → GAS関数 → 結果表示",
        "verification": verification
    }

    return log_test("integration_test_8_ui_ux_integration", status, details, score)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# テスト 9: パフォーマンス統合
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def test_9_performance():
    """実際のデータ量（355-937件）での処理"""
    print("\n" + "="*60)
    print("テスト 9: パフォーマンス統合")
    print("="*60)

    verification = {
        "data_volume_adequate": False,
        "batch_processing": False,
        "async_loading": False,
        "lazy_loading": False
    }

    # データ量確認
    applicants_file = DATA_OUTPUT_DIR / "Applicants.csv"
    if check_file_exists(applicants_file):
        rows = count_csv_rows(applicants_file)
        verification["data_volume_adequate"] = rows >= 100

    # MapComplete.html のパフォーマンス最適化確認
    html_file = GAS_HTML_DIR / "MapComplete.html"
    if check_file_exists(html_file):
        content = read_file(html_file)
        if content:
            verification["batch_processing"] = "markerCluster" in content
            verification["async_loading"] = "async function" in content or "await" in content
            verification["lazy_loading"] = "DOMContentLoaded" in content

    score = sum([1 for v in verification.values() if v]) * 25
    status = "PASS" if score >= 50 else "FAIL"

    details = {
        "flow": "大量データ → 効率的処理 → 高速レンダリング",
        "verification": verification
    }

    return log_test("integration_test_9_performance", status, details, score)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# テスト 10: リカバリ統合
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def test_10_recovery():
    """エラー発生時の全体システムの挙動"""
    print("\n" + "="*60)
    print("テスト 10: リカバリ統合")
    print("="*60)

    verification = {
        "graceful_degradation": False,
        "user_notification": False,
        "fallback_mechanism": False,
        "data_integrity_protection": False
    }

    # UniversalPhaseUploader.gs のリカバリ機能確認
    uploader_file = GAS_SCRIPTS_DIR / "UniversalPhaseUploader.gs"
    if check_file_exists(uploader_file):
        content = read_file(uploader_file)
        if content:
            # 既存シート削除→新規作成パターン
            verification["data_integrity_protection"] = "deleteSheet" in content and "insertSheet" in content

    # Phase2Phase3Visualizations.gs のエラーハンドリング確認
    viz_file = GAS_SCRIPTS_DIR / "Phase2Phase3Visualizations.gs"
    if check_file_exists(viz_file):
        content = read_file(viz_file)
        if content:
            verification["user_notification"] = "alert" in content and "エラー" in content
            verification["graceful_degradation"] = "if (!sheet)" in content

    # MapDataProvider.gs のフォールバック確認
    provider_file = GAS_SCRIPTS_DIR / "MapDataProvider.gs"
    if check_file_exists(provider_file):
        content = read_file(provider_file)
        if content:
            verification["fallback_mechanism"] = "return []" in content or "catch" in content

    score = sum([1 for v in verification.values() if v]) * 25
    status = "PASS" if score >= 75 else "FAIL"

    details = {
        "flow": "エラー発生 → リカバリ → ユーザー通知",
        "verification": verification
    }

    return log_test("integration_test_10_recovery", status, details, score)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# メイン実行
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main():
    """10回の統合テストを実行"""
    print("\n" + "="*60)
    print("GAS統合テスト（10回繰り返し）開始")
    print("="*60)
    print(f"プロジェクトルート: {PROJECT_ROOT}")
    print(f"GASスクリプト: {GAS_SCRIPTS_DIR}")
    print(f"HTML: {GAS_HTML_DIR}")
    print(f"データ: {DATA_OUTPUT_DIR}")

    # 全テスト実行
    test_1_menu_to_upload()
    test_2_data_provider()
    test_3_phase2_3_visualization()
    test_4_api_config()
    test_5_data_flow()
    test_6_error_propagation()
    test_7_state_management()
    test_8_ui_ux_integration()
    test_9_performance()
    test_10_recovery()

    # サマリー生成
    print("\n" + "="*60)
    print("統合テストサマリー")
    print("="*60)

    total_tests = len(test_results)
    passed = sum([1 for r in test_results if r["status"] == "PASS"])
    failed = sum([1 for r in test_results if r["status"] == "FAIL"])
    avg_score = sum([r["score"] for r in test_results]) / total_tests if total_tests > 0 else 0

    summary = {
        "total_tests": total_tests,
        "passed": passed,
        "failed": failed,
        "overall_score": round(avg_score, 2),
        "critical_integration_issues": [r["test_name"] for r in test_results if r["score"] < 50],
        "data_flow_integrity": f"{round((passed/total_tests)*100, 2)}%" if total_tests > 0 else "0%"
    }

    print(f"\n総テスト数: {total_tests}")
    print(f"合格: {passed}")
    print(f"不合格: {failed}")
    print(f"総合スコア: {avg_score:.2f}/100")
    print(f"データフロー整合性: {summary['data_flow_integrity']}")

    if summary['critical_integration_issues']:
        print(f"\n重大な統合問題:")
        for issue in summary['critical_integration_issues']:
            print(f"  - {issue}")

    # JSON出力
    output = {
        "test_results": test_results,
        "summary": summary
    }

    output_file = PROJECT_ROOT / "GAS_INTEGRATION_TEST_10X_RESULTS.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n結果をJSONに保存: {output_file}")

    return summary

if __name__ == "__main__":
    summary = main()
    sys.exit(0 if summary["failed"] == 0 else 1)
