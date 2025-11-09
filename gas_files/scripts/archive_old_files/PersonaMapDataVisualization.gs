/**
 * PersonaMapData.csv 地図可視化（セキュア実装）
 *
 * 機能:
 * - 792地点のペルソナ別マーカー表示
 * - ペルソナ別色分け（10色 + グレー）
 * - MarkerClustererによるクラスタリング表示
 * - マーカークリック → ペルソナ詳細表示
 * - フィルター機能（ペルソナ選択）
 * - リアルタイム統計表示
 *
 * セキュリティ:
 * - Google Maps APIキーをScript Propertiesから取得
 * - コード内にAPIキーをハードコーディングしない
 *
 * エラーハンドリング:
 * - シート不在時の明確なエラーメッセージ
 * - 座標データ検証（NaN/Null チェック）
 * - Google Maps API読み込み失敗時のフォールバック
 *
 * パフォーマンス:
 * - MarkerClustererで50+マーカーを自動グループ化
 * - 遅延ロードなし（792地点は十分軽量）
 *
 * 工数: 4時間
 * 作成日: 2025-10-27
 */

/**
 * PersonaMapData地図可視化（メインエントリーポイント）
 */
function showPersonaMapVisualization() {
  const ui = SpreadsheetApp.getUi();

  try {
    // Step 1: データ読み込み
    const mapData = loadPersonaMapData();

    if (!mapData || mapData.length === 0) {
      ui.alert(
        'データなし',
        'Phase7_PersonaMapDataシートにデータがありません。\n\n' +
        '【対処方法】\n' +
        '1. スプレッドシートメニュー > 「📊 データ処理」\n' +
        '2. 「🐍 Python連携」 > 「📥 Python結果CSVを取り込み」\n' +
        '3. gas_output_phase7フォルダを指定してインポート',
        ui.ButtonSet.OK
      );
      return;
    }

    // Step 2: HTML生成（セキュアAPIキー取得）
    const html = generatePersonaMapHTML(mapData);

    // Step 3: 全画面モーダルダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1400)
      .setHeight(900);

    ui.showModalDialog(htmlOutput, 'ペルソナ地図可視化（792地点）');

  } catch (error) {
    ui.alert(
      'エラー',
      `地図可視化中にエラーが発生しました:\n\n${error.message}\n\n` +
      `スタックトレース:\n${error.stack}`,
      ui.ButtonSet.OK
    );
    Logger.log(`[ERROR] PersonaMap可視化エラー: ${error.stack}`);
  }
}

/**
 * PersonaMapData読み込み
 *
 * @return {Array<Object>} 地図データ配列（792要素）
 * @throws {Error} シートが見つからない場合
 */
function loadPersonaMapData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase7_PersonaMapData');

  if (!sheet) {
    throw new Error(
      'Phase7_PersonaMapDataシートが見つかりません。\n' +
      'Pythonスクリプト実行後、「Phase 7データ取り込み」を実行してください。'
    );
  }

  const lastRow = sheet.getLastRow();
  Logger.log(`[INFO] PersonaMapData行数: ${lastRow - 1}行（ヘッダー除く）`);

  if (lastRow <= 1) {
    Logger.log('[WARNING] PersonaMapData: データが0行です');
    return [];
  }

  // 9列すべて取得: 市区町村, 緯度, 経度, ペルソナID, ペルソナ名, 求職者数, 平均年齢, 女性比率, 資格保有率
  const data = sheet.getRange(2, 1, lastRow - 1, 9).getValues();

  // データ変換 & 座標検証
  const validData = [];
  let invalidCount = 0;

  data.forEach((row, index) => {
    const lat = parseFloat(row[1]);
    const lng = parseFloat(row[2]);

    // 座標検証
    if (isNaN(lat) || isNaN(lng) || lat === 0 || lng === 0) {
      Logger.log(`[WARNING] 行${index + 2}: 無効な座標 (lat=${row[1]}, lng=${row[2]})`);
      invalidCount++;
      return;  // スキップ
    }

    validData.push({
      municipality: row[0],
      lat: lat,
      lng: lng,
      personaId: parseInt(row[3]),
      personaName: row[4],
      applicantCount: parseInt(row[5]),
      avgAge: parseFloat(row[6]),
      femaleRatio: parseFloat(row[7]),
      qualificationRate: parseFloat(row[8])
    });
  });

  if (invalidCount > 0) {
    Logger.log(`[INFO] スキップされた無効データ: ${invalidCount}件`);
  }

  Logger.log(`[OK] 有効なPersonaMapDataロード完了: ${validData.length}地点`);

  return validData;
}

/**
 * 地図HTML生成（セキュア実装）
 *
 * @param {Array<Object>} mapData - 地図データ
 * @return {string} HTML文字列
 */
function generatePersonaMapHTML(mapData) {
  const mapDataJson = JSON.stringify(mapData);

  // ペルソナ別色定義（10色 + グレー）
  const personaColors = {
    '-1': '#808080',  // セグメント-1: グレー
    '0': '#4285F4',   // セグメント0: 青
    '1': '#34A853',   // セグメント1: 緑
    '2': '#FBBC04',   // セグメント2: 黄
    '3': '#EA4335',   // セグメント3: 赤
    '4': '#9C27B0',   // セグメント4: 紫
    '5': '#FF6D00',   // セグメント5: オレンジ
    '6': '#00BCD4',   // セグメント6: シアン
    '7': '#8BC34A',   // セグメント7: ライムグリーン
    '8': '#E91E63',   // セグメント8: ピンク
    '9': '#795548'    // セグメント9: ブラウン
  };

  const personaColorsJson = JSON.stringify(personaColors);

  // 🔒 セキュアAPIキー取得（GoogleMapsAPIConfig.gs使用）
  const apiKeyScript = generateGoogleMapsScriptTag(['visualization']);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  ${apiKeyScript}
  <script src="https://unpkg.com/@googlemaps/markerclusterer/dist/index.min.js"></script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Segoe UI', Arial, sans-serif; }

    #map { height: 100vh; width: 100%; }

    .controls {
      position: absolute;
      top: 20px;
      left: 20px;
      background: white;
      padding: 20px;
      border-radius: 12px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.2);
      max-width: 350px;
      z-index: 1000;
      max-height: 80vh;
      overflow-y: auto;
    }

    .controls h3 {
      margin-bottom: 15px;
      color: #1a73e8;
      font-size: 18px;
      display: flex;
      align-items: center;
    }

    .controls h3::before {
      content: '🔍';
      margin-right: 8px;
    }

    .persona-filter {
      margin-bottom: 10px;
    }

    .persona-filter label {
      display: flex;
      align-items: center;
      padding: 8px 0;
      cursor: pointer;
      transition: background 0.2s;
      border-radius: 4px;
      padding-left: 5px;
    }

    .persona-filter label:hover {
      background: #f5f5f5;
    }

    .persona-filter input[type="checkbox"] {
      margin-right: 10px;
      cursor: pointer;
    }

    .color-box {
      width: 20px;
      height: 20px;
      display: inline-block;
      margin-right: 10px;
      border-radius: 4px;
      border: 2px solid #ddd;
    }

    .stats {
      margin-top: 20px;
      padding-top: 15px;
      border-top: 2px solid #e0e0e0;
    }

    .stats p {
      margin: 5px 0;
      font-size: 14px;
      color: #555;
    }

    .stats strong {
      color: #1a73e8;
      font-weight: 600;
    }

    .info-window {
      max-width: 300px;
      font-family: 'Segoe UI', Arial, sans-serif;
    }

    .info-window h4 {
      margin-bottom: 12px;
      color: #1a73e8;
      font-size: 16px;
      border-bottom: 2px solid #1a73e8;
      padding-bottom: 5px;
    }

    .info-window p {
      margin: 8px 0;
      font-size: 14px;
      line-height: 1.5;
    }

    .info-window .metric {
      display: flex;
      justify-content: space-between;
      padding: 4px 0;
    }

    .info-window .metric-label {
      color: #666;
    }

    .info-window .metric-value {
      font-weight: 600;
      color: #333;
    }
  </style>
</head>
<body>
  <div id="map"></div>

  <div class="controls">
    <h3>フィルター</h3>
    <div id="persona-filters"></div>
    <div class="stats">
      <p><strong>表示中:</strong> <span id="visible-count">0</span> / <span id="total-count">0</span> 地点</p>
      <p><strong>総求職者:</strong> <span id="total-applicants">0</span> 名</p>
    </div>
  </div>

  <script>
    const mapData = ${mapDataJson};
    const personaColors = ${personaColorsJson};

    let map;
    let markers = [];
    let markerClusterer;

    /**
     * Google Maps初期化
     */
    function initMap() {
      console.log('[INFO] Google Maps初期化開始');
      console.log('[INFO] データ地点数:', mapData.length);

      // 地図中心計算（全マーカーの平均座標）
      const avgLat = mapData.reduce((sum, d) => sum + d.lat, 0) / mapData.length;
      const avgLng = mapData.reduce((sum, d) => sum + d.lng, 0) / mapData.length;

      const center = { lat: avgLat, lng: avgLng };

      console.log('[INFO] 地図中心:', center);

      // 地図作成
      map = new google.maps.Map(document.getElementById('map'), {
        zoom: 9,
        center: center,
        mapTypeId: 'roadmap',
        mapTypeControl: true,
        streetViewControl: true,
        fullscreenControl: true
      });

      // フィルターUI作成
      createPersonaFilters();

      // マーカー作成
      createMarkers();

      // クラスタリング適用
      applyMarkerClustering();

      // 統計表示
      updateStats();

      console.log('[OK] Google Maps初期化完了');
    }

    /**
     * ペルソナフィルターUI作成
     */
    function createPersonaFilters() {
      const container = document.getElementById('persona-filters');

      // ユニークなペルソナIDを取得
      const personaIds = [...new Set(mapData.map(d => d.personaId))].sort((a, b) => a - b);

      console.log('[INFO] ユニークペルソナ数:', personaIds.length);

      personaIds.forEach(personaId => {
        const color = personaColors[personaId.toString()] || '#808080';
        const personaName = mapData.find(d => d.personaId === personaId).personaName;
        const count = mapData.filter(d => d.personaId === personaId).length;

        const label = document.createElement('label');
        label.className = 'persona-filter';
        label.innerHTML = \`
          <input type="checkbox" checked data-persona-id="\${personaId}">
          <span class="color-box" style="background-color: \${color};"></span>
          \${personaName} (\${count})
        \`;

        const checkbox = label.querySelector('input');
        checkbox.addEventListener('change', () => filterMarkers());

        container.appendChild(label);
      });

      console.log('[OK] フィルターUI作成完了');
    }

    /**
     * マーカー作成
     */
    function createMarkers() {
      console.log('[INFO] マーカー作成開始');

      mapData.forEach((data, index) => {
        const color = personaColors[data.personaId.toString()] || '#808080';

        // カスタムマーカーアイコン
        const icon = {
          path: google.maps.SymbolPath.CIRCLE,
          scale: 8,
          fillColor: color,
          fillOpacity: 0.85,
          strokeColor: 'white',
          strokeWeight: 2
        };

        const marker = new google.maps.Marker({
          position: { lat: data.lat, lng: data.lng },
          icon: icon,
          title: \`\${data.municipality} - \${data.personaName}\`,
          personaId: data.personaId
        });

        // 情報ウィンドウ
        const infoWindow = new google.maps.InfoWindow({
          content: generateInfoWindowContent(data)
        });

        marker.addListener('click', () => {
          // 他の情報ウィンドウを閉じる
          markers.forEach(m => {
            if (m.infoWindow) {
              m.infoWindow.close();
            }
          });

          infoWindow.open(map, marker);
        });

        marker.infoWindow = infoWindow;
        markers.push(marker);

        if ((index + 1) % 100 === 0) {
          console.log(\`[PROGRESS] マーカー作成: \${index + 1} / \${mapData.length}\`);
        }
      });

      console.log(\`[OK] マーカー作成完了: \${markers.length}個\`);
    }

    /**
     * 情報ウィンドウ内容生成
     *
     * @param {Object} data - ペルソナデータ
     * @return {string} HTML文字列
     */
    function generateInfoWindowContent(data) {
      const femaleRatioPercent = (data.femaleRatio * 100).toFixed(1);
      const qualificationRatePercent = (data.qualificationRate * 100).toFixed(1);

      return \`
        <div class="info-window">
          <h4>\${data.municipality}</h4>
          <div class="metric">
            <span class="metric-label">ペルソナ:</span>
            <span class="metric-value">\${data.personaName}</span>
          </div>
          <div class="metric">
            <span class="metric-label">求職者数:</span>
            <span class="metric-value">\${data.applicantCount}名</span>
          </div>
          <div class="metric">
            <span class="metric-label">平均年齢:</span>
            <span class="metric-value">\${data.avgAge}歳</span>
          </div>
          <div class="metric">
            <span class="metric-label">女性比率:</span>
            <span class="metric-value">\${femaleRatioPercent}%</span>
          </div>
          <div class="metric">
            <span class="metric-label">資格保有率:</span>
            <span class="metric-value">\${qualificationRatePercent}%</span>
          </div>
        </div>
      \`;
    }

    /**
     * クラスタリング適用
     */
    function applyMarkerClustering() {
      console.log('[INFO] クラスタリング適用開始');

      if (markerClusterer) {
        markerClusterer.clearMarkers();
      }

      const visibleMarkers = markers.filter(m => {
        const checkbox = document.querySelector(\`input[data-persona-id="\${m.personaId}"]\`);
        return checkbox && checkbox.checked;
      });

      console.log(\`[INFO] 表示マーカー数: \${visibleMarkers.length}\`);

      markerClusterer = new markerClusterer.MarkerClusterer({
        map,
        markers: visibleMarkers,
        algorithm: new markerClusterer.GridAlgorithm({ gridSize: 60 })
      });

      console.log('[OK] クラスタリング適用完了');
    }

    /**
     * フィルター適用
     */
    function filterMarkers() {
      console.log('[INFO] フィルター適用');
      applyMarkerClustering();
      updateStats();
    }

    /**
     * 統計更新
     */
    function updateStats() {
      const visibleMarkers = markers.filter(m => {
        const checkbox = document.querySelector(\`input[data-persona-id="\${m.personaId}"]\`);
        return checkbox && checkbox.checked;
      });

      const visibleCount = visibleMarkers.length;

      // 総求職者数計算
      const visibleDataPoints = mapData.filter(d => {
        const checkbox = document.querySelector(\`input[data-persona-id="\${d.personaId}"]\`);
        return checkbox && checkbox.checked;
      });

      const totalApplicants = visibleDataPoints.reduce((sum, d) => sum + d.applicantCount, 0);

      document.getElementById('visible-count').textContent = visibleCount;
      document.getElementById('total-count').textContent = markers.length;
      document.getElementById('total-applicants').textContent = totalApplicants.toLocaleString();

      console.log(\`[STATS] 表示: \${visibleCount} / \${markers.length}, 総求職者: \${totalApplicants}名\`);
    }

    /**
     * エラーハンドリング
     */
    window.onerror = function(message, source, lineno, colno, error) {
      console.error('[ERROR] JavaScript エラー:', message);
      console.error('[ERROR] ファイル:', source);
      console.error('[ERROR] 行番号:', lineno);
      alert('地図の初期化中にエラーが発生しました:\\n' + message);
      return false;
    };

    /**
     * 初期化実行（Google Maps API読み込み後）
     */
    window.onload = function() {
      if (typeof google === 'undefined' || !google.maps) {
        console.error('[ERROR] Google Maps APIの読み込みに失敗しました');
        alert(
          'Google Maps APIの読み込みに失敗しました。\\n\\n' +
          '【対処方法】\\n' +
          '1. インターネット接続を確認\\n' +
          '2. Google Maps APIキーが正しく設定されているか確認\\n' +
          '3. Google Cloud ConsoleでMaps JavaScript APIが有効化されているか確認'
        );
        return;
      }

      if (typeof markerClusterer === 'undefined') {
        console.error('[ERROR] MarkerClustererの読み込みに失敗しました');
        alert('MarkerClustererライブラリの読み込みに失敗しました。');
        return;
      }

      try {
        initMap();
      } catch (error) {
        console.error('[ERROR] 初期化エラー:', error);
        alert('地図の初期化中にエラーが発生しました:\\n' + error.message);
      }
    };
  </script>
</body>
</html>
  `;
}
