/**
 * GAS/HTML バンドル生成スクリプト
 *
 * - dist/ に各種バンドルを生成
 * - apps_script_bundle/ にコピー（コピー＆ペースト用）
 * - apps_script_bundle/phases/ にフェーズ単位のバンドルを出力
 *
 * 事前にバックアップとして `tools/build_regional_dashboard_bundle.js.bak`
 * を残しています。
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const DIST_DIR = path.join(ROOT, 'dist');
const BUNDLE_DIR = path.join(ROOT, 'apps_script_bundle');
const PHASE_DIR = path.join(BUNDLE_DIR, 'phases');

function ensureDir(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function collectSources(dir, extension) {
  const files = fs.readdirSync(dir)
    .filter(name => path.extname(name).toLowerCase() === extension.toLowerCase())
    .sort();
  return files.map(name => {
    const rel = path.join(path.relative(ROOT, dir), name);
    if (extension === '.html') {
      return { file: rel, banner: `<!-- ===== ${name} ===== -->` };
    }
    return { file: rel, banner: `// ===== ${name} =====` };
  });
}

function bundleSources(sources, outputPath) {
  if (!sources.length) return;
  const parts = sources.map(({ file, banner }) => {
    const fullPath = path.join(ROOT, file);
    const content = fs.readFileSync(fullPath, 'utf8');
    return `${banner}\n${content.trim()}\n`;
  });
  fs.writeFileSync(outputPath, parts.join('\n'), 'utf8');
  console.log(`✅ Generated ${outputPath}`);
}

function copyToBundle(src, dest) {
  fs.copyFileSync(src, dest);
  console.log(`📄 Copied ${path.basename(src)} → ${dest}`);
}

function main() {
  ensureDir(DIST_DIR);
  ensureDir(BUNDLE_DIR);
  ensureDir(PHASE_DIR);

  // 1. Regional dashboard (最新追加分のみ)
  const regionalGs = [
    { file: 'gas_files/scripts/RegionStateService.gs', banner: '// ===== RegionStateService.gs =====' },
    { file: 'gas_files/scripts/RegionDashboard.gs', banner: '// ===== RegionDashboard.gs =====' },
    { file: 'gas_files/scripts/MapVisualization.gs', banner: '// ===== MapVisualization.gs (with region selection integration) =====' }
  ];
  const regionalHtml = [
    { file: 'gas_files/html/RegionalDashboard.html', banner: '<!-- ===== RegionalDashboard.html ===== -->' }
  ];
  bundleSources(regionalGs, path.join(DIST_DIR, 'regional_dashboard.gs'));
  bundleSources(regionalHtml, path.join(DIST_DIR, 'regional_dashboard.html'));
  bundleSources(
    [
      { file: 'gas_files/html/RegionalDashboard.html', banner: '<!-- ===== RegionalDashboard.html ===== -->' },
      { file: 'gas_files/html/MapComplete.html', banner: '<!-- ===== MapComplete.html ===== -->' }
    ],
    path.join(DIST_DIR, 'regional_dashboard_with_map.html')
  );

  // 2. 全体バンドル（gas_files, gas_files_production）
  const devGsAll = collectSources(path.join(ROOT, 'gas_files', 'scripts'), '.gs');
  const devHtmlAll = collectSources(path.join(ROOT, 'gas_files', 'html'), '.html');
  bundleSources(devGsAll, path.join(DIST_DIR, 'all_scripts_bundle.gs'));
  bundleSources(devHtmlAll, path.join(DIST_DIR, 'all_html_bundle.html'));

  const prodGsAll = collectSources(path.join(ROOT, 'gas_files_production', 'scripts'), '.gs');
  const prodHtmlAll = collectSources(path.join(ROOT, 'gas_files_production', 'html'), '.html');
  bundleSources(prodGsAll, path.join(DIST_DIR, 'production_scripts_bundle.gs'));
  bundleSources(prodHtmlAll, path.join(DIST_DIR, 'production_html_bundle.html'));

  // 3. フェーズ単位のバンドル（production フォルダから）
  const phaseBundles = [
    {
      name: 'phase1_core.gs',
      sources: [
        { file: 'gas_files_production/scripts/DataValidationEnhanced.gs', banner: '// ===== Phase1: DataValidationEnhanced =====' },
        { file: 'gas_files_production/scripts/MapVisualization.gs', banner: '// ===== Phase1: MapVisualization =====' }
      ]
    },
    {
      name: 'phase2_phase3_viz.gs',
      sources: [
        { file: 'gas_files_production/scripts/Phase2Phase3Visualizations.gs', banner: '// ===== Phase2/Phase3: Visualizations =====' }
      ]
    },
    {
      name: 'phase6_flow.gs',
      sources: [
        { file: 'gas_files_production/scripts/MunicipalityFlowNetworkViz.gs', banner: '// ===== Phase6: MunicipalityFlowNetworkViz =====' },
        { file: 'gas_files_production/scripts/MatrixHeatmapViewer.gs', banner: '// ===== Phase6: MatrixHeatmapViewer =====' }
      ]
    },
    {
      name: 'phase7_import.gs',
      sources: [
        { file: 'gas_files_production/scripts/Phase7DataImporter.gs', banner: '// ===== Phase7: DataImporter =====' },
        { file: 'gas_files_production/scripts/Phase7CompleteDashboard.gs', banner: '// ===== Phase7: CompleteDashboard =====' }
      ]
    },
    {
      name: 'phase7_visualization.gs',
      sources: [
        { file: 'gas_files_production/scripts/Phase7SupplyDensityViz.gs', banner: '// ===== Phase7: SupplyDensityViz =====' },
        { file: 'gas_files_production/scripts/Phase7QualificationDistViz.gs', banner: '// ===== Phase7: QualificationDistViz =====' },
        { file: 'gas_files_production/scripts/Phase7AgeGenderCrossViz.gs', banner: '// ===== Phase7: AgeGenderCrossViz =====' },
        { file: 'gas_files_production/scripts/Phase7MobilityScoreViz.gs', banner: '// ===== Phase7: MobilityScoreViz =====' },
        { file: 'gas_files_production/scripts/Phase7PersonaProfileViz.gs', banner: '// ===== Phase7: PersonaProfileViz =====' }
      ]
    },
    {
      name: 'phase8_career.gs',
      sources: [
        { file: 'gas_files_production/scripts/Phase8DataImporter.gs', banner: '// ===== Phase8: DataImporter =====' }
      ]
    },
    {
      name: 'phase10_urgency.gs',
      sources: [
        { file: 'gas_files_production/scripts/Phase10DataImporter.gs', banner: '// ===== Phase10: DataImporter =====' }
      ]
    },
    {
      name: 'persona_tools.gs',
      sources: [
        { file: 'gas_files_production/scripts/PersonaDifficultyChecker.gs', banner: '// ===== Persona: DifficultyChecker =====' }
      ]
    },
    {
      name: 'integration_core.gs',
      sources: [
        { file: 'gas_files_production/scripts/MenuIntegration.gs', banner: '// ===== Integration: MenuIntegration =====' },
        { file: 'gas_files_production/scripts/PythonCSVImporter.gs', banner: '// ===== Integration: PythonCSVImporter =====' },
        { file: 'gas_files_production/scripts/QualityDashboard.gs', banner: '// ===== Integration: QualityDashboard =====' }
      ]
    }
  ];

  phaseBundles.forEach(bundle => {
    bundleSources(bundle.sources, path.join(PHASE_DIR, bundle.name));
  });

  // 4. Copy to apps_script_bundle for convenience
  copyToBundle(path.join(DIST_DIR, 'regional_dashboard.gs'), path.join(BUNDLE_DIR, 'regional_dashboard.gs'));
  copyToBundle(path.join(DIST_DIR, 'regional_dashboard_with_map.html'), path.join(BUNDLE_DIR, 'regional_dashboard_with_map.html'));
  copyToBundle(path.join(DIST_DIR, 'all_scripts_bundle.gs'), path.join(BUNDLE_DIR, 'all_scripts_bundle.gs'));
  copyToBundle(path.join(DIST_DIR, 'all_html_bundle.html'), path.join(BUNDLE_DIR, 'all_html_bundle.html'));
  copyToBundle(path.join(DIST_DIR, 'production_scripts_bundle.gs'), path.join(BUNDLE_DIR, 'production_scripts_bundle.gs'));
  copyToBundle(path.join(DIST_DIR, 'production_html_bundle.html'), path.join(BUNDLE_DIR, 'production_html_bundle.html'));
  phaseBundles.forEach(bundle => {
    copyToBundle(path.join(PHASE_DIR, bundle.name), path.join(PHASE_DIR, bundle.name));
  });
}

main();
