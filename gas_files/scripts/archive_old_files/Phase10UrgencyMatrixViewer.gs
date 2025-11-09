/**
 * Phase 10 緊急度×年齢層マトリックスビューアー
 *
 * UrgencyAgeCross_Matrix.csvをヒートマップで可視化します。
 */

/**
 * 緊急度×年齢マトリックス表示（メニューから呼び出し）
 */
function showUrgencyAgeMatrix() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadUrgencyAgeMatrixData();

    if (!data || data.rows.length === 0) {
      ui.alert(
        'データなし',
        'P10_UrgencyAgeMatrixシートにデータがありません。\n' +
        '先に「Python結果CSVを取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateUrgencyAgeMatrixHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1400)
      .setHeight(900);

    ui.showModalDialog(htmlOutput, 'Phase 10: 緊急度×年齢層マトリックス');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`緊急度×年齢マトリックスエラー: ${error.stack}`);
  }
}


/**
 * 緊急度×年齢マトリックスデータ読み込み
 * @return {Object} データオブジェクト
 */
function loadUrgencyAgeMatrixData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('P10_UrgencyAgeMatrix');

  if (!sheet) {
    throw new Error('P10_UrgencyAgeMatrixシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return { headers: [], rows: [], metadata: {} };
  }

  // ヘッダー行取得
  const headers = sheet.getRange(1, 1, 1, 7).getValues()[0];

  // データ範囲取得（ヘッダー除く）
  const range = sheet.getRange(2, 1, lastRow - 1, 7);
  const values = range.getValues();

  // メタデータ計算
  const metadata = calculateMatrixMetadata(values);

  Logger.log(`緊急度×年齢マトリックスデータ読み込み: ${values.length}件`);

  return {
    headers,
    rows: values,
    metadata,
    totalRows: lastRow - 1
  };
}


/**
 * マトリックスメタデータ計算
 * @param {Array} rows - データ行
 * @return {Object} メタデータ
 */
function calculateMatrixMetadata(rows) {
  const values = [];
  let totalCount = 0;

  rows.forEach(row => {
    row.slice(1).forEach(cell => {
      const num = Number(cell) || 0;
      if (num > 0) {
        values.push(num);
        totalCount += num;
      }
    });
  });

  values.sort((a, b) => a - b);

  return {
    totalCells: rows.length * 6,  // 6列（年齢層）
    valueCells: values.length,
    emptyCells: (rows.length * 6) - values.length,
    totalCount,
    min: values.length > 0 ? values[0] : 0,
    max: values.length > 0 ? values[values.length - 1] : 0,
    mean: values.length > 0 ? values.reduce((sum, v) => sum + v, 0) / values.length : 0,
    median: values.length > 0 ? values[Math.floor(values.length / 2)] : 0
  };
}


/**
 * 緊急度×年齢マトリックスHTML生成
 * @param {Object} data - データオブジェクト
 * @return {string} HTML文字列
 */
function generateUrgencyAgeMatrixHTML(data) {
  const { headers, rows, metadata, totalRows } = data;
  const dataJson = JSON.stringify({ headers, rows });

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <style>
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      margin: 20px;
      background-color: #f5f5f5;
    }
    h1 {
      color: #1a73e8;
      border-bottom: 3px solid #1a73e8;
      padding-bottom: 10px;
    }
    .container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
    }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 15px;
      margin-bottom: 20px;
    }
    .stat-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      border-radius: 8px;
      text-align: center;
    }
    .stat-label {
      font-size: 12px;
      opacity: 0.9;
      margin-bottom: 5px;
    }
    .stat-value {
      font-size: 28px;
      font-weight: bold;
    }
    .heatmap-container {
      overflow: auto;
      max-height: 600px;
      border: 1px solid #ddd;
      border-radius: 4px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    th {
      background-color: #1a73e8;
      color: white;
      padding: 12px;
      text-align: center;
      position: sticky;
      top: 0;
      z-index: 10;
      font-weight: bold;
    }
    td {
      padding: 10px;
      text-align: center;
      border: 1px solid #e0e0e0;
    }
    .row-header {
      background-color: #f8f9fa;
      font-weight: bold;
      text-align: left;
      position: sticky;
      left: 0;
      z-index: 5;
      border-right: 2px solid #1a73e8;
      max-width: 150px;
      white-space: nowrap;
    }
    .legend {
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 20px 0;
      flex-wrap: wrap;
    }
    .legend-item {
      margin: 5px 10px;
      display: flex;
      align-items: center;
    }
    .legend-box {
      width: 30px;
      height: 20px;
      margin-right: 5px;
      border: 1px solid #ddd;
    }
    .note {
      background-color: #fff3cd;
      border-left: 4px solid #ffc107;
      padding: 15px;
      margin-top: 10px;
      border-radius: 4px;
    }
  </style>
</head>
<body>
  <h1>🔥 Phase 10: 緊急度×年齢層マトリックス</h1>

  <div class="container">
    <h2>統計サマリー</h2>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">総緊急度ランク数</div>
        <div class="stat-value">${totalRows.toLocaleString()}</div>
        <div class="stat-label">種類</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">総人数</div>
        <div class="stat-value">${metadata.totalCount.toLocaleString()}</div>
        <div class="stat-label">名</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">最大値</div>
        <div class="stat-value">${metadata.max}</div>
        <div class="stat-label">名</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">平均値</div>
        <div class="stat-value">${metadata.mean.toFixed(1)}</div>
        <div class="stat-label">名</div>
      </div>
    </div>
  </div>

  <div class="container">
    <h2>ヒートマップ（緊急度×年齢層）</h2>
    <div class="note">
      <strong>📊 表示説明:</strong> 緊急度ランク（A-D）と年齢層（20代-70歳以上）の分布をヒートマップで表示しています。色が濃いほど人数が多いことを示します。
      <ul style="margin: 10px 0; padding-left: 20px;">
        <li><strong>A: 高い</strong> - 緊急度スコア7以上（即座に対応すべき）</li>
        <li><strong>B: 中程度</strong> - 緊急度スコア5-7（優先的に対応）</li>
        <li><strong>C: やや低い</strong> - 緊急度スコア3-5（計画的に対応）</li>
        <li><strong>D: 低い</strong> - 緊急度スコア3未満（長期的に対応）</li>
      </ul>
    </div>

    <div class="legend" id="legend"></div>

    <div class="heatmap-container">
      <table id="heatmap-table"></table>
    </div>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};
    const metadata = ${JSON.stringify(metadata)};

    // カラースケール生成（赤系グラデーション - 緊急度を表現）
    function getHeatmapColor(value, max) {
      if (value === 0) return '#f8f9fa';  // 空セル

      const intensity = Math.min(value / max, 1);
      const r = 255;
      const g = Math.round(255 * (1 - intensity));
      const b = Math.round(255 * (1 - intensity));

      return \`rgb(\${r}, \${g}, \${b})\`;
    }

    // 凡例生成
    function renderLegend() {
      const container = document.getElementById('legend');

      const legendSteps = [
        { label: '0名', value: 0 },
        { label: \`\${Math.round(metadata.max * 0.25)}名\`, value: metadata.max * 0.25 },
        { label: \`\${Math.round(metadata.max * 0.5)}名\`, value: metadata.max * 0.5 },
        { label: \`\${Math.round(metadata.max * 0.75)}名\`, value: metadata.max * 0.75 },
        { label: \`\${metadata.max}名\`, value: metadata.max }
      ];

      legendSteps.forEach(step => {
        const item = document.createElement('div');
        item.className = 'legend-item';

        const box = document.createElement('div');
        box.className = 'legend-box';
        box.style.backgroundColor = getHeatmapColor(step.value, metadata.max);

        const label = document.createElement('span');
        label.textContent = step.label;

        item.appendChild(box);
        item.appendChild(label);
        container.appendChild(item);
      });
    }

    // ヒートマップテーブル生成
    function renderHeatmapTable() {
      const table = document.getElementById('heatmap-table');

      // ヘッダー行
      const thead = document.createElement('thead');
      const headerRow = document.createElement('tr');

      data.headers.forEach((header, index) => {
        const th = document.createElement('th');
        th.textContent = header;
        if (index === 0) {
          th.style.minWidth = '150px';
          th.style.textAlign = 'left';
        }
        headerRow.appendChild(th);
      });

      thead.appendChild(headerRow);
      table.appendChild(thead);

      // データ行
      const tbody = document.createElement('tbody');

      data.rows.forEach(row => {
        const tr = document.createElement('tr');

        row.forEach((cell, colIndex) => {
          const td = document.createElement('td');

          if (colIndex === 0) {
            // 緊急度ランク（行ヘッダー）
            td.className = 'row-header';
            td.textContent = cell;
          } else {
            // 数値セル
            const value = Number(cell) || 0;
            td.textContent = value > 0 ? value : '－';
            td.style.backgroundColor = getHeatmapColor(value, metadata.max);

            // 値が大きい場合は文字色を白に
            if (value > metadata.max * 0.6) {
              td.style.color = 'white';
              td.style.fontWeight = 'bold';
            }
          }

          tr.appendChild(td);
        });

        tbody.appendChild(tr);
      });

      table.appendChild(tbody);
    }

    // 初期化
    renderLegend();
    renderHeatmapTable();
  </script>
</body>
</html>
  `;
}
