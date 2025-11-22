import re

# 正しいマッピング（ドキュメント準拠）
correct_mapping = {
    # Phase 1: 接頭辞なし
    "'Applicants.csv': 'Phase1_Applicants'": "'Applicants.csv': 'Applicants'",
    "'DesiredWork.csv': 'Phase1_DesiredWork'": "'DesiredWork.csv': 'DesiredWork'",
    "'AggDesired.csv': 'Phase1_AggDesired'": "'AggDesired.csv': 'AggDesired'",
    "'MapMetrics.csv': 'Phase1_MapMetrics'": "'MapMetrics.csv': 'MapMetrics'",
    
    # Phase 2: 接頭辞なし
    "'ChiSquareTests.csv': 'Phase2_ChiSquare'": "'ChiSquareTests.csv': 'ChiSquareTests'",
    "'ANOVATests.csv': 'Phase2_ANOVA'": "'ANOVATests.csv': 'ANOVATests'",
    
    # Phase 3: 接頭辞なし
    "'PersonaSummary.csv': 'Phase3_PersonaSummary'": "'PersonaSummary.csv': 'PersonaSummary'",
    "'PersonaDetails.csv': 'Phase3_PersonaDetails'": "'PersonaDetails.csv': 'PersonaDetails'",
    "'PersonaSummaryByMunicipality.csv': 'Phase3_PersonaByMunicipality'": "'PersonaSummaryByMunicipality.csv': 'PersonaSummaryByMunicipality'",
    
    # Phase 6: 混在（FlowはPhase6_接頭辞、Proximityは接頭辞なし）
    "'MunicipalityFlowEdges.csv': 'Phase6_FlowEdges'": "'MunicipalityFlowEdges.csv': 'Phase6_MunicipalityFlowEdges'",
    "'MunicipalityFlowNodes.csv': 'Phase6_FlowNodes'": "'MunicipalityFlowNodes.csv': 'Phase6_MunicipalityFlowNodes'",
    
    # Phase 7: Phase7_接頭辞（これは正しい）
    # Phase 8, 10: Phase8_, Phase10_接頭辞（これも正しい）
}

with open('UnifiedDataImporter.gs', 'r', encoding='utf-8') as f:
    content = f.read()

for old, new in correct_mapping.items():
    content = content.replace(old, new)

with open('UnifiedDataImporter.gs', 'w', encoding='utf-8') as f:
    f.write(content)

print("UnifiedDataImporter.gs修正完了")
