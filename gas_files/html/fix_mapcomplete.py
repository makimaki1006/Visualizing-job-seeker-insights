# MapComplete.htmlを英語・日本語カラム名両対応に修正

html_content = """<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <meta charset="UTF-8">
  <title>求職者データ分析マップ</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.1/dist/MarkerCluster.css" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.1/dist/MarkerCluster.Default.css" />
  <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script src="https://unpkg.com/leaflet.markercluster@1.5.1/dist/leaflet.markercluster.js"></script>
  <script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Yu Gothic', 'Hiragino Kaku Gothic Pro', Meiryo, sans-serif; height: 100vh; overflow: hidden; }
    .container { display: flex; height: 100vh; }
    #map { flex: 1; height: 100%; }
    .sidebar { width: 350px; background: #2d2d5f; color: white; padding: 20px; overflow-y: auto; box-shadow: -5px 0 20px rgba(0,0,0,0.3); }
    .sidebar-title { font-size: 18px; font-weight: bold; margin-bottom: 20px; text-align: center; color: #667eea; }
    .stat-card { background: rgba(255,255,255,0.05); border-radius: 8px; padding: 15px; margin-bottom: 15px; }
    .stat-label { font-size: 12px; color: rgba(255,255,255,0.7); margin-bottom: 5px; }
    .stat-value { font-size: 24px; font-weight: bold; color: #667eea; }
    .chart-container { background: rgba(255,255,255,0.05); border-radius: 8px; padding: 15px; margin-bottom: 15px; height: 200px; }
    .control-group { margin-bottom: 15px; }
    .control-label { font-size: 12px; color: rgba(255,255,255,0.7); margin-bottom: 8px; display: block; }
    select { width: 100%; padding: 10px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.2); background: rgba(255,255,255,0.1); color: white; font-size: 13px; }
    .top10-list { list-style: none; max-height: 250px; overflow-y: auto; }
    .top10-item { display: flex; justify-content: space-between; padding: 8px; margin-bottom: 5px; background: rgba(255,255,255,0.05); border-radius: 4px; }
    .top10-rank { font-weight: bold; color: #667eea; margin-right: 10px; }
    .loading { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); z-index: 9999; }
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: rgba(255,255,255,0.05); }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 4px; }
  </style>
</head>
<body>
  <div class="loading" id="loading">データ読み込み中...</div>
  <div class="container">
    <div id="map"></div>
    <div class="sidebar">
      <div class="sidebar-title">求職者分析</div>
      <div class="stat-card">
        <div class="stat-label">総求職者数</div>
        <div class="stat-value" id="totalCount">-</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">平均年齢</div>
        <div class="stat-value" id="avgAge">-</div>
      </div>
      <div class="control-group">
        <label class="control-label">表示モード</label>
        <select id="displayMode" onchange="changeDisplayMode()">
          <option value="markers">個別マーカー</option>
          <option value="cluster">クラスター</option>
          <option value="heatmap">ヒートマップ</option>
        </select>
      </div>
      <div class="control-group">
        <label class="control-label">フィルター</label>
        <select id="dataFilter" onchange="applyFilter()">
          <option value="all">全データ</option>
          <option value="male">男性のみ</option>
          <option value="female">女性のみ</option>
          <option value="young">20-30代</option>
          <option value="middle">40-50代</option>
          <option value="senior">60代以上</option>
        </select>
      </div>
      <div class="stat-card">
        <div class="stat-label">希望勤務地 TOP10</div>
        <ul class="top10-list" id="top10List"></ul>
      </div>
      <div class="chart-container">
        <canvas id="genderChart"></canvas>
      </div>
    </div>
  </div>
  <script>
    let map, markers = [], markerCluster, heatLayer;
    let allData = {mapMetrics: [], applicants: [], desiredWork: [], aggDesired: []};

    const COL_MAP = {
      prefecture: ['都道府県', 'prefecture'],
      municipality: ['市区町村', 'municipality'],
      count: ['カウント', 'applicant_count', 'count'],
      latitude: ['緯度', 'latitude'],
      longitude: ['経度', 'longitude'],
      age: ['年齢', 'age'],
      gender: ['性別', 'gender'],
      id: ['ID', 'applicant_id', 'id'],
      applicant_id: ['申請者ID', 'applicant_id'],
      desired_municipality: ['希望勤務地_市区町村', 'municipality']
    };

    function getVal(row, key) {
      if (!row) return undefined;
      const candidates = COL_MAP[key] || [key];
      for (let candidate of candidates) {
        if (row[candidate] !== undefined && row[candidate] !== null) return row[candidate];
      }
      return undefined;
    }

    function initMap() {
      map = L.map('map', {center: [35.0116, 135.7681], zoom: 10});
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {attribution: '© OpenStreetMap', maxZoom: 18}).addTo(map);
      markerCluster = L.markerClusterGroup({chunkedLoading: true, maxClusterRadius: 60});
    }

    function loadData() {
      google.script.run
        .withSuccessHandler(function(data) {
          allData = data;
          document.getElementById('loading').style.display = 'none';
          processData();
        })
        .withFailureHandler(function(error) {
          alert('データ読み込みエラー: ' + error.message);
          document.getElementById('loading').style.display = 'none';
        })
        .getAllVisualizationData();
    }

    function processData() {
      updateStats();
      updateMap();
      updateTop10();
      updateGenderChart();
    }

    function updateStats() {
      const total = allData.applicants.length;
      document.getElementById('totalCount').textContent = total.toLocaleString();

      let totalAge = 0, validCount = 0;
      allData.applicants.forEach(row => {
        const age = getVal(row, 'age');
        if (age && age > 0) { totalAge += age; validCount++; }
      });

      const avgAge = validCount > 0 ? (totalAge / validCount).toFixed(1) : 0;
      document.getElementById('avgAge').textContent = avgAge + '歳';
    }

    function updateMap() {
      clearMap();
      const mode = document.getElementById('displayMode').value;
      const filter = document.getElementById('dataFilter').value;
      let data = allData.mapMetrics;

      if (filter !== 'all') data = applyFilterToData(data, filter);

      switch(mode) {
        case 'markers': displayMarkers(data); break;
        case 'cluster': displayClusters(data); break;
        case 'heatmap': displayHeatmap(data); break;
      }
    }

    function applyFilterToData(data, filterType) {
      const targetIds = new Set();
      allData.applicants.forEach(row => {
        let include = false;
        const gender = getVal(row, 'gender');
        const age = getVal(row, 'age');

        switch(filterType) {
          case 'male': include = gender === '男性' || gender === 'male'; break;
          case 'female': include = gender === '女性' || gender === 'female'; break;
          case 'young': include = age >= 20 && age < 40; break;
          case 'middle': include = age >= 40 && age < 60; break;
          case 'senior': include = age >= 60; break;
        }

        if (include) targetIds.add(getVal(row, 'id'));
      });

      const targetMunicipalities = new Set();
      allData.desiredWork.forEach(row => {
        if (targetIds.has(getVal(row, 'applicant_id'))) {
          targetMunicipalities.add(getVal(row, 'desired_municipality'));
        }
      });

      return data.filter(row => targetMunicipalities.has(getVal(row, 'municipality')));
    }

    function displayMarkers(data) {
      data.forEach(row => {
        const lat = getVal(row, 'latitude');
        const lng = getVal(row, 'longitude');
        const municipality = getVal(row, 'municipality');
        const prefecture = getVal(row, 'prefecture');
        const count = getVal(row, 'count');

        if (lat && lng) {
          const marker = L.marker([lat, lng])
            .bindPopup('<strong>' + municipality + '</strong><br>求職者数: ' + count + '名<br>都道府県: ' + prefecture);
          marker.on('click', function() { handleRegionSelection(prefecture, municipality); });
          markers.push(marker);
          marker.addTo(map);
        }
      });
    }

    function displayClusters(data) {
      markerCluster.clearLayers();
      data.forEach(row => {
        const lat = getVal(row, 'latitude');
        const lng = getVal(row, 'longitude');
        const municipality = getVal(row, 'municipality');
        const prefecture = getVal(row, 'prefecture');
        const count = getVal(row, 'count');

        if (lat && lng) {
          const marker = L.marker([lat, lng])
            .bindPopup('<strong>' + municipality + '</strong><br>求職者数: ' + count + '名');
          marker.on('click', function() { handleRegionSelection(prefecture, municipality); });
          markerCluster.addLayer(marker);
        }
      });
      map.addLayer(markerCluster);
    }

    function displayHeatmap(data) {
      const heatData = data
        .filter(row => getVal(row, 'latitude') && getVal(row, 'longitude') && getVal(row, 'count'))
        .map(row => [getVal(row, 'latitude'), getVal(row, 'longitude'), getVal(row, 'count')]);

      if (heatLayer) map.removeLayer(heatLayer);
      heatLayer = L.heatLayer(heatData, {radius: 25, blur: 15, maxZoom: 17}).addTo(map);
    }

    function clearMap() {
      markers.forEach(marker => map.removeLayer(marker));
      markers = [];
      markerCluster.clearLayers();
      map.removeLayer(markerCluster);
      if (heatLayer) map.removeLayer(heatLayer);
    }

    function handleRegionSelection(prefecture, municipality) {
      if (!prefecture) return;
      google.script.run
        .withSuccessHandler(function() { console.log('Region saved:', prefecture, municipality); })
        .withFailureHandler(function(error) { console.error('Failed to save region', error); })
        .saveSelectedRegion(prefecture, municipality || null);
    }

    function updateTop10() {
      const listEl = document.getElementById('top10List');
      listEl.innerHTML = '';

      const top10 = allData.aggDesired
        .sort(function(a, b) { return (getVal(b, 'count') || 0) - (getVal(a, 'count') || 0); })
        .slice(0, 10);

      top10.forEach(function(item, index) {
        const municipality = getVal(item, 'municipality') || getVal(item, 'desired_municipality');
        const count = getVal(item, 'count');

        const li = document.createElement('li');
        li.className = 'top10-item';
        li.innerHTML = '<span><span class="top10-rank">' + (index + 1) + '</span>' + (municipality || '不明') + '</span><span><strong>' + (count || 0) + '人</strong></span>';
        listEl.appendChild(li);
      });
    }

    function updateGenderChart() {
      const ctx = document.getElementById('genderChart');
      if (!ctx) return;

      const genderCounts = {};
      allData.applicants.forEach(function(row) {
        const gender = getVal(row, 'gender') || '不明';
        genderCounts[gender] = (genderCounts[gender] || 0) + 1;
      });

      new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: Object.keys(genderCounts),
          datasets: [{
            data: Object.values(genderCounts),
            backgroundColor: ['rgba(102, 126, 234, 0.8)', 'rgba(255, 99, 132, 0.8)', 'rgba(255, 206, 86, 0.8)']
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: 'bottom', labels: { color: 'white' } } }
        }
      });
    }

    function changeDisplayMode() { updateMap(); }
    function applyFilter() { updateMap(); }

    window.addEventListener('DOMContentLoaded', function() {
      try {
        initMap();
        loadData();
      } catch (error) {
        alert('初期化エラー: ' + error.message);
      }
    });
  </script>
</body>
</html>"""

with open('MapComplete.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print('MapComplete.html修正完了')
