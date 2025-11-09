from pathlib import Path
path = Path(r'gas_files/scripts/Phase8UnifiedVisualizations.gs')
text = path.read_text(encoding='utf-8')
text = text.replace("P8_CareerDist", "Phase8_CareerDistribution")
text = text.replace("Phase8_CareerDistributionリスト", "Phase8_CareerDistributionリスト")
text = text.replace("Phase8_CareerDistributionシート", "Phase8_CareerDistributionシート")
text = text.replace("Phase8_CareerDistribution", "Phase8_CareerDistribution")
