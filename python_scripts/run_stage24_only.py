"""Stage 24のみ実行してGAP計算不整合を確認"""
import sys
sys.path.append('.')
from ultrathink_stage21_40 import UltrathinkValidatorStage2140

# MapComplete統合CSV（修正後）
validator = UltrathinkValidatorStage2140('data/output_v2/mapcomplete_complete_sheets/MapComplete_Complete_All.csv')

print('='*100)
print('Stage 24: GAP計算論理的整合性検証（修正後のCSV）')
print('='*100)

validator.stage24_numeric_logical_consistency()
