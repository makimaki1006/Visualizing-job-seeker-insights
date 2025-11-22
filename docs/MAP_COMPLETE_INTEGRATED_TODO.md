# Phase 12-14統合ダッシュボード 改善タスク一覧

**作成日**: 2025年11月12日
**ファイル**: `map_complete_integrated.html`
**ステータス**: Phase 5実装待ち

---

## タスク概要

| ID | タスク名 | 優先度 | ステータス | 担当 | 期限 |
|----|---------|--------|-----------|------|------|
| T-001 | 総合概要：年齢大別求職者数の市町村フィルタリング | 🔴 高 | 🔄 計画中 | - | - |
| T-002 | キャリア分析：就業ステータス×年齢帯の市町村フィルタリング | 🔴 高 | 🔄 計画中 | - | - |
| T-003 | 緊急度分析：緊急度サマリー/チャートの市町村フィルタリング | 🔴 高 | 🔄 計画中 | - | - |
| T-004 | ペルソナ分析：絞り込み実行ボタンの修正 | 🔴 高 | 🔄 計画中 | - | - |
| T-005 | クロス分析タブ：データ表示実装 | 🔴 高 | 🔄 計画中 | - | - |
| T-006 | フロー分析タブ：データ表示実装 | 🔴 高 | 🔄 計画中 | - | - |
| T-007 | ダッシュボードタブの削除 | 🟡 中 | 🔄 計画中 | - | - |

---

## T-001: 総合概要タブ - 年齢大別求職者数の市町村フィルタリング

### 問題の詳細

**現状**:
- 総合概要タブの「年齢大別求職者数」縦棒グラフが、都道府県全体のデータを表示している
- 市町村を選択しても、グラフが市町村別にフィルタリングされない

**再現手順**:
1. Phase 12-14統合ダッシュボードを開く
2. 任意の市町村を選択（例: 京都府京都市）
3. 総合概要タブの「年齢大別求職者数」グラフを確認
4. 結果: 京都府全体のデータが表示される（期待: 京都市のみのデータ）

**影響**:
- ユーザーが市町村別の年齢分布を正確に把握できない
- データの誤解釈のリスク

### 技術調査

#### 調査箇所

1. **グラフ生成関数の特定**:
   ```javascript
   // 総合概要タブのレンダリング関数を探す
   function renderTab_overview() { ... }
   // または
   function renderCity(c) { ... }
   ```

2. **データソースの確認**:
   - 使用しているrow_type: `AGE_GENDER`
   - データ構造を確認:
     ```javascript
     {
       row_type: 'AGE_GENDER',
       prefecture: '京都府',
       municipality: '', // 都道府県全体の場合は空
       age_group: '20代',
       gender: '男性',
       count: 123
     }
     ```

3. **現在のフィルタリングロジック**:
   ```javascript
   // 推測される現在のコード
   const ageData = DATA[activeCity].age_gender;
   // → すべての行を取得（市町村フィルタなし）
   ```

#### 修正方針

1. **市町村選択状態を取得**:
   ```javascript
   const selectedMunicipality = selectedRegion?.municipality || '';
   ```

2. **データフィルタリング**:
   ```javascript
   // AGE_GENDERは都道府県レベルのデータなので、
   // 市町村が選択されている場合はその市町村のみフィルタリング

   let ageData = DATA[activeCity].age_gender || [];

   if (selectedMunicipality) {
     // 市町村が選択されている場合
     ageData = ageData.filter(row =>
       row.municipality === selectedMunicipality ||
       row.region_name === selectedMunicipality ||
       row.region_name.endsWith(selectedMunicipality)
     );
   }
   ```

3. **グラフデータ集計**:
   ```javascript
   // 年齢層別に集計
   const ageGroupCounts = {};
   ageData.forEach(row => {
     const ageGroup = row.age_group || row.age_range;
     ageGroupCounts[ageGroup] = (ageGroupCounts[ageGroup] || 0) + (row.count || 0);
   });
   ```

4. **Google Charts描画**:
   ```javascript
   const chartData = [['年齢層', '求職者数']];
   Object.keys(ageGroupCounts).forEach(ageGroup => {
     chartData.push([ageGroup, ageGroupCounts[ageGroup]]);
   });

   const chart = new google.visualization.ColumnChart(container);
   chart.draw(google.visualization.arrayToDataTable(chartData), options);
   ```

### 実装手順

1. ✅ `renderTab_overview` 関数を特定
2. ✅ データソース取得箇所を特定
3. ✅ 市町村フィルタリングロジックを追加
4. ⬜ ローカルテスト（clasp pull → 修正 → clasp push）
5. ⬜ GASで動作確認
6. ⬜ ドキュメント更新

### テストケース

| ケース | 選択市町村 | 期待結果 |
|--------|-----------|---------|
| TC-001-1 | 京都府全体 | 京都府全体の年齢分布が表示 |
| TC-001-2 | 京都市 | 京都市のみの年齢分布が表示 |
| TC-001-3 | 与謝郡与謝野町 | 与謝野町のみの年齢分布が表示 |
| TC-001-4 | データなし市町村 | 空のグラフまたは「データなし」表示 |

### 備考

- `AGE_GENDER` row_typeは都道府県レベルのデータ
- `municipality`カラムが空の場合は都道府県全体を表す
- `region_name`カラムには「京都府京都市」のような形式でデータが格納されている可能性あり

---

## T-002: キャリア分析タブ - 就業ステータス×年齢帯の市町村フィルタリング

### 問題の詳細

**現状**:
- キャリア分析タブの「就業ステータス×年齢帯」縦棒グラフが、都道府県全体のデータを表示している
- 市町村を選択しても、グラフが市町村別にフィルタリングされない

**再現手順**:
1. Phase 12-14統合ダッシュボードを開く
2. 任意の市町村を選択（例: 京都府京都市）
3. キャリア分析タブを開く
4. 「就業ステータス×年齢帯」グラフを確認
5. 結果: 京都府全体のデータが表示される（期待: 京都市のみのデータ）

**影響**:
- ユーザーが市町村別のキャリア分布を正確に把握できない
- 就業支援戦略の立案に支障

### 技術調査

#### 調査箇所

1. **グラフ生成関数の特定**:
   ```javascript
   function renderTab_career() { ... }
   ```

2. **データソースの確認**:
   - 使用しているrow_type: `CAREER_CROSS`
   - データ構造を確認:
     ```javascript
     {
       row_type: 'CAREER_CROSS',
       prefecture: '京都府',
       municipality: '', // または具体的な市町村名
       age_group: '20代',
       employment_status: '在職中',
       count: 45
     }
     ```

3. **現在のフィルタリングロジック**:
   ```javascript
   // 推測される現在のコード
   const careerData = DATA[activeCity].career_cross;
   // → すべての行を取得（市町村フィルタなし）
   ```

#### 修正方針

1. **市町村選択状態を取得**:
   ```javascript
   const selectedMunicipality = selectedRegion?.municipality || '';
   ```

2. **データフィルタリング**:
   ```javascript
   let careerData = DATA[activeCity].career_cross || [];

   if (selectedMunicipality) {
     careerData = careerData.filter(row =>
       row.municipality === selectedMunicipality ||
       row.region_name === selectedMunicipality ||
       row.region_name.endsWith(selectedMunicipality)
     );
   }
   ```

3. **クロス集計データ生成**:
   ```javascript
   // 就業ステータス×年齢帯のマトリクスを作成
   const matrix = {};
   careerData.forEach(row => {
     const status = row.employment_status || row.career_status;
     const age = row.age_group || row.age_range;
     if (!matrix[status]) matrix[status] = {};
     matrix[status][age] = (matrix[status][age] || 0) + (row.count || 0);
   });
   ```

4. **Google Charts描画（Stacked Column Chart）**:
   ```javascript
   const ageGroups = [...new Set(careerData.map(r => r.age_group))];
   const chartData = [['年齢帯', ...Object.keys(matrix)]];

   ageGroups.forEach(age => {
     const row = [age];
     Object.keys(matrix).forEach(status => {
       row.push(matrix[status][age] || 0);
     });
     chartData.push(row);
   });

   const chart = new google.visualization.ColumnChart(container);
   chart.draw(google.visualization.arrayToDataTable(chartData), {
     isStacked: true,
     ...options
   });
   ```

### 実装手順

1. ⬜ `renderTab_career` 関数を特定
2. ⬜ データソース取得箇所を特定
3. ⬜ 市町村フィルタリングロジックを追加
4. ⬜ ローカルテスト（clasp pull → 修正 → clasp push）
5. ⬜ GASで動作確認
6. ⬜ ドキュメント更新

### テストケース

| ケース | 選択市町村 | 期待結果 |
|--------|-----------|---------|
| TC-002-1 | 京都府全体 | 京都府全体のキャリア分布が表示 |
| TC-002-2 | 京都市 | 京都市のみのキャリア分布が表示 |
| TC-002-3 | 与謝郡与謝野町 | 与謝野町のみのキャリア分布が表示 |
| TC-002-4 | データなし市町村 | 空のグラフまたは「データなし」表示 |

---

## T-003: 緊急度分析タブ - 緊急度サマリー/チャートの市町村フィルタリング

### 問題の詳細

**現状**:
- 緊急度分析タブの「緊急度サマリー」と「緊急度チャート」が、都道府県全体のデータを表示している
- 市町村を選択しても、グラフが市町村別にフィルタリングされない

**再現手順**:
1. Phase 12-14統合ダッシュボードを開く
2. 任意の市町村を選択（例: 京都府京都市）
3. 緊急度分析タブを開く
4. 「緊急度サマリー」と「緊急度チャート」を確認
5. 結果: 京都府全体のデータが表示される（期待: 京都市のみのデータ）

**影響**:
- ユーザーが市町村別の転職緊急度を正確に把握できない
- 採用優先度の判断に支障

### 技術調査

#### 調査箇所

1. **グラフ生成関数の特定**:
   ```javascript
   function renderTab_urgency() { ... }
   ```

2. **データソースの確認**:
   - 使用しているrow_type: `URGENCY_AGE`, `URGENCY_EMPLOYMENT`
   - データ構造を確認:
     ```javascript
     {
       row_type: 'URGENCY_AGE',
       prefecture: '京都府',
       municipality: '', // または具体的な市町村名
       urgency_level: '高',
       age_group: '30代',
       count: 78
     }
     ```

3. **現在のフィルタリングロジック**:
   ```javascript
   // 推測される現在のコード
   const urgencyData = DATA[activeCity].urgency_age;
   // → すべての行を取得（市町村フィルタなし）
   ```

#### 修正方針

1. **市町村選択状態を取得**:
   ```javascript
   const selectedMunicipality = selectedRegion?.municipality || '';
   ```

2. **データフィルタリング**:
   ```javascript
   let urgencyAgeData = DATA[activeCity].urgency_age || [];
   let urgencyEmploymentData = DATA[activeCity].urgency_employment || [];

   if (selectedMunicipality) {
     urgencyAgeData = urgencyAgeData.filter(row =>
       row.municipality === selectedMunicipality ||
       row.region_name === selectedMunicipality ||
       row.region_name.endsWith(selectedMunicipality)
     );

     urgencyEmploymentData = urgencyEmploymentData.filter(row =>
       row.municipality === selectedMunicipality ||
       row.region_name === selectedMunicipality ||
       row.region_name.endsWith(selectedMunicipality)
     );
   }
   ```

3. **緊急度サマリー集計**:
   ```javascript
   const urgencySummary = {
     '高': 0,
     '中': 0,
     '低': 0
   };

   urgencyAgeData.forEach(row => {
     const level = row.urgency_level || row.urgency_score;
     urgencySummary[level] = (urgencySummary[level] || 0) + (row.count || 0);
   });
   ```

4. **緊急度チャート描画（Pie Chart）**:
   ```javascript
   const chartData = [['緊急度', '求職者数']];
   Object.keys(urgencySummary).forEach(level => {
     chartData.push([level, urgencySummary[level]]);
   });

   const chart = new google.visualization.PieChart(container);
   chart.draw(google.visualization.arrayToDataTable(chartData), options);
   ```

### 実装手順

1. ⬜ `renderTab_urgency` 関数を特定
2. ⬜ データソース取得箇所を特定
3. ⬜ 市町村フィルタリングロジックを追加（2つのデータソース）
4. ⬜ ローカルテスト（clasp pull → 修正 → clasp push）
5. ⬜ GASで動作確認
6. ⬜ ドキュメント更新

### テストケース

| ケース | 選択市町村 | 期待結果 |
|--------|-----------|---------|
| TC-003-1 | 京都府全体 | 京都府全体の緊急度分布が表示 |
| TC-003-2 | 京都市 | 京都市のみの緊急度分布が表示 |
| TC-003-3 | 与謝郡与謝野町 | 与謝野町のみの緊急度分布が表示 |
| TC-003-4 | データなし市町村 | 空のグラフまたは「データなし」表示 |

---

## T-004: ペルソナ分析タブ - 絞り込み実行ボタンの修正

### 問題の詳細

**現状**:
- ペルソナ分析タブの「絞り込み実行」ボタンをクリックしても、フィルタリングが実行されない
- ボタンセレクタ: `#sidebar > div.panels > section.panel.active > div:nth-child(2) > div.persona-filter-panel > div:nth-child(2) > button.btn-filter-apply`

**再現手順**:
1. Phase 12-14統合ダッシュボードを開く
2. ペルソナ分析タブを開く
3. フィルターを設定（例: 年齢層=30代、性別=女性）
4. 「絞り込み実行」ボタンをクリック
5. 結果: フィルタリングが実行されない（期待: 絞り込み結果が表示される）

**影響**:
- ペルソナ分析機能が使用不可能
- 細かいセグメント分析ができない

### 技術調査

#### 調査箇所

1. **ボタンのイベントリスナー登録**:
   ```javascript
   // イベントリスナーが登録されているか確認
   qs('.btn-filter-apply').addEventListener('click', () => {
     // この部分が存在するか、または正しく動作するか
   });
   ```

2. **フィルター取得ロジック**:
   ```javascript
   function getPersonaFilters() {
     const difficultyFilter = Array.from((qs('#difficultyFilter') && qs('#difficultyFilter').selectedOptions) || []).map(o => o.value);
     const ageGroupFilter = Array.from((qs('#ageGroupFilter') && qs('#ageGroupFilter').selectedOptions) || []).map(o => o.value);
     const genderFilter = Array.from((qs('#genderFilter') && qs('#genderFilter').selectedOptions) || []).map(o => o.value);
     const qualificationFilter = Array.from((qs('#qualificationFilter') && qs('#qualificationFilter').selectedOptions) || []).map(o => o.value);
     const residenceFilter = Array.from((qs('#residenceFilter') && qs('#residenceFilter').selectedOptions) || []).map(o => o.value);

     return {
       difficulty: difficultyFilter,
       ageGroup: ageGroupFilter,
       gender: genderFilter,
       qualification: qualificationFilter,
       residence: residenceFilter
     };
   }
   ```

3. **フィルター適用ロジック**:
   ```javascript
   function applyPersonaFilters(filters) {
     let personaData = DATA[activeCity].persona_muni || [];

     // 各フィルターを適用
     if (filters.difficulty.length > 0) {
       personaData = personaData.filter(row => filters.difficulty.includes(row.difficulty));
     }
     if (filters.ageGroup.length > 0) {
       personaData = personaData.filter(row => filters.ageGroup.includes(row.age_group));
     }
     // ... 他のフィルターも同様

     return personaData;
   }
   ```

4. **結果表示ロジック**:
   ```javascript
   function renderPersonaResults(personaData) {
     // テーブルまたはグラフに結果を表示
     const container = qs('#personaResultsContainer');
     container.innerHTML = generatePersonaTable(personaData);
   }
   ```

#### 修正方針

1. **イベントリスナーの修正**:
   ```javascript
   // 既存のイベントリスナーを探す
   // 見つからない場合は追加

   document.addEventListener('DOMContentLoaded', () => {
     const filterButton = qs('.btn-filter-apply');
     if (filterButton) {
       filterButton.addEventListener('click', () => {
         console.log('[ペルソナフィルター] 絞り込み実行ボタンクリック');

         // フィルター取得
         const filters = getPersonaFilters();
         console.log('[ペルソナフィルター] フィルター:', filters);

         // フィルター適用
         const filteredData = applyPersonaFilters(filters);
         console.log('[ペルソナフィルター] 絞り込み結果:', filteredData.length, '件');

         // 結果表示
         renderPersonaResults(filteredData);
       });
     } else {
       console.warn('[ペルソナフィルター] 絞り込みボタンが見つかりません');
     }
   });
   ```

2. **デバッグログ追加**:
   - イベントリスナーが正しく登録されているか確認
   - フィルター値が正しく取得されているか確認
   - フィルタリング後のデータ件数を確認

### 実装手順

1. ⬜ `.btn-filter-apply` ボタンの存在確認
2. ⬜ イベントリスナーの登録確認
3. ⬜ フィルター取得ロジックの実装/修正
4. ⬜ フィルター適用ロジックの実装/修正
5. ⬜ 結果表示ロジックの実装/修正
6. ⬜ ローカルテスト（clasp pull → 修正 → clasp push）
7. ⬜ GASで動作確認
8. ⬜ ドキュメント更新

### テストケース

| ケース | フィルター設定 | 期待結果 |
|--------|--------------|---------|
| TC-004-1 | フィルターなし | すべてのペルソナが表示 |
| TC-004-2 | 年齢層=30代 | 30代のペルソナのみ表示 |
| TC-004-3 | 年齢層=30代, 性別=女性 | 30代女性のペルソナのみ表示 |
| TC-004-4 | 該当なしの組み合わせ | 「該当なし」メッセージ表示 |
| TC-004-5 | フィルタークリア | すべてのペルソナが再表示 |

---

## T-005: クロス分析タブ - データ表示実装

### 問題の詳細

**現状**:
- クロス分析タブを開いても、データが何も表示されない
- タブ自体は存在するが、コンテンツが空

**再現手順**:
1. Phase 12-14統合ダッシュボードを開く
2. クロス分析タブを開く
3. 結果: 何も表示されない（期待: クロス集計データが表示される）

**影響**:
- クロス分析機能が使用不可能
- 多変量分析ができない

### 技術調査

#### 調査箇所

1. **タブ切り替えロジック**:
   ```javascript
   function switchTab(tabName) {
     if (tabName === 'cross') {
       renderTab_cross();
     }
   }
   ```

2. **レンダリング関数の存在確認**:
   ```javascript
   function renderTab_cross() {
     // この関数が存在するか、実装されているか確認
   }
   ```

3. **データソースの確認**:
   - 使用可能なrow_type: `CAREER_CROSS`, `AGE_GENDER`, その他
   - どのデータを表示すべきか仕様を確認

#### 修正方針

1. **データソースの決定**:
   ```javascript
   // 例: キャリア×年齢のクロス集計を表示
   const crossData = DATA[activeCity].career_cross || [];
   ```

2. **市町村フィルタリング**:
   ```javascript
   const selectedMunicipality = selectedRegion?.municipality || '';

   let filteredData = crossData;
   if (selectedMunicipality) {
     filteredData = crossData.filter(row =>
       row.municipality === selectedMunicipality ||
       row.region_name === selectedMunicipality ||
       row.region_name.endsWith(selectedMunicipality)
     );
   }
   ```

3. **クロス集計テーブル生成**:
   ```javascript
   function generateCrossTable(data, rowKey, colKey) {
     // 行ラベルと列ラベルを取得
     const rowLabels = [...new Set(data.map(r => r[rowKey]))];
     const colLabels = [...new Set(data.map(r => r[colKey]))];

     // マトリクス作成
     const matrix = {};
     rowLabels.forEach(row => {
       matrix[row] = {};
       colLabels.forEach(col => {
         matrix[row][col] = 0;
       });
     });

     // データ集計
     data.forEach(row => {
       const rowVal = row[rowKey];
       const colVal = row[colKey];
       matrix[rowVal][colVal] += (row.count || 0);
     });

     return { rowLabels, colLabels, matrix };
   }
   ```

4. **HTMLテーブル表示**:
   ```javascript
   function renderCrossTable(container, rowLabels, colLabels, matrix) {
     let html = '<table class="cross-table">';

     // ヘッダー行
     html += '<thead><tr><th></th>';
     colLabels.forEach(col => {
       html += `<th>${col}</th>`;
     });
     html += '</tr></thead>';

     // データ行
     html += '<tbody>';
     rowLabels.forEach(row => {
       html += `<tr><th>${row}</th>`;
       colLabels.forEach(col => {
         html += `<td>${matrix[row][col]}</td>`;
       });
       html += '</tr>';
     });
     html += '</tbody></table>';

     container.innerHTML = html;
   }
   ```

5. **Google Charts Heatmap（オプション）**:
   ```javascript
   function renderCrossHeatmap(container, rowLabels, colLabels, matrix) {
     const chartData = [['', ...colLabels]];

     rowLabels.forEach(row => {
       const rowData = [row];
       colLabels.forEach(col => {
         rowData.push(matrix[row][col]);
       });
       chartData.push(rowData);
     });

     const chart = new google.visualization.Table(container);
     // またはHeatmap（要プラグイン）
     chart.draw(google.visualization.arrayToDataTable(chartData), options);
   }
   ```

### 実装手順

1. ⬜ `renderTab_cross` 関数の存在確認
2. ⬜ データソースの決定（CAREER_CROSS, AGE_GENDER, etc.）
3. ⬜ クロス集計ロジックの実装
4. ⬜ HTMLテーブル表示の実装
5. ⬜ 市町村フィルタリングの実装
6. ⬜ ローカルテスト（clasp pull → 修正 → clasp push）
7. ⬜ GASで動作確認
8. ⬜ ドキュメント更新

### テストケース

| ケース | 選択市町村 | 期待結果 |
|--------|-----------|---------|
| TC-005-1 | 京都府全体 | 京都府全体のクロス集計表示 |
| TC-005-2 | 京都市 | 京都市のみのクロス集計表示 |
| TC-005-3 | 与謝郡与謝野町 | 与謝野町のみのクロス集計表示 |
| TC-005-4 | データなし市町村 | 空のテーブルまたは「データなし」表示 |

---

## T-006: フロー分析タブ - データ表示実装

### 問題の詳細

**現状**:
- フロー分析タブを開いても、データが何も表示されない
- タブ自体は存在するが、コンテンツが空

**再現手順**:
1. Phase 12-14統合ダッシュボードを開く
2. フロー分析タブを開く
3. 結果: 何も表示されない（期待: フローデータが表示される）

**影響**:
- フロー分析機能が使用不可能
- 人材移動パターンが把握できない

### 技術調査

#### 調査箇所

1. **タブ切り替えロジック**:
   ```javascript
   function switchTab(tabName) {
     if (tabName === 'flow') {
       renderTab_flow();
     }
   }
   ```

2. **レンダリング関数の存在確認**:
   ```javascript
   function renderTab_flow() {
     // この関数が存在するか、実装されているか確認
   }
   ```

3. **データソースの確認**:
   - 使用しているrow_type: `FLOW`
   - データ構造:
     ```javascript
     {
       row_type: 'FLOW',
       prefecture: '京都府',
       municipality: '京都市',
       flow: {
         nearby_regions: [
           { region: '大阪府大阪市', count: 50, percentage: 25.5 },
           { region: '滋賀県大津市', count: 30, percentage: 15.3 }
         ]
       }
     }
     ```

#### 修正方針

1. **データソースの取得**:
   ```javascript
   const flowData = DATA[activeCity].flow || {};
   const nearbyRegions = flowData.nearby_regions || [];
   ```

2. **市町村フィルタリング**:
   ```javascript
   const selectedMunicipality = selectedRegion?.municipality || '';

   // FLOWデータは市町村ごとに格納されているため、
   // 選択市町村のデータのみ取得
   let regionFlowData = [];

   if (selectedMunicipality) {
     const municipalityFlowRow = DATA[activeCity].data.find(row =>
       row.row_type === 'FLOW' &&
       (row.municipality === selectedMunicipality ||
        row.region_name === selectedMunicipality)
     );

     if (municipalityFlowRow && municipalityFlowRow.flow) {
       regionFlowData = municipalityFlowRow.flow.nearby_regions || [];
     }
   }
   ```

3. **Sankey図の生成（Google Charts）**:
   ```javascript
   function renderFlowSankey(container, sourceRegion, flowData) {
     const chartData = [['From', 'To', 'Count']];

     flowData.forEach(flow => {
       chartData.push([sourceRegion, flow.region, flow.count]);
     });

     const chart = new google.visualization.Sankey(container);
     chart.draw(google.visualization.arrayToDataTable(chartData), {
       width: 800,
       height: 400
     });
   }
   ```

4. **テーブル表示（代替）**:
   ```javascript
   function renderFlowTable(container, flowData) {
     let html = '<table class="flow-table">';
     html += '<thead><tr><th>移動先</th><th>求職者数</th><th>割合</th></tr></thead>';
     html += '<tbody>';

     flowData.forEach(flow => {
       html += `<tr>
         <td>${flow.region}</td>
         <td>${flow.count}人</td>
         <td>${flow.percentage}%</td>
       </tr>`;
     });

     html += '</tbody></table>';
     container.innerHTML = html;
   }
   ```

### 実装手順

1. ⬜ `renderTab_flow` 関数の存在確認
2. ⬜ FLOWデータの構造確認
3. ⬜ 市町村フィルタリングの実装
4. ⬜ Sankey図またはテーブル表示の実装
5. ⬜ ローカルテスト（clasp pull → 修正 → clasp push）
6. ⬜ GASで動作確認
7. ⬜ ドキュメント更新

### テストケース

| ケース | 選択市町村 | 期待結果 |
|--------|-----------|---------|
| TC-006-1 | 京都市 | 京都市からの人材移動フローが表示 |
| TC-006-2 | 与謝郡与謝野町 | 与謝野町からの人材移動フローが表示 |
| TC-006-3 | データなし市町村 | 空のグラフまたは「データなし」表示 |

---

## T-007: ダッシュボードタブの削除

### 問題の詳細

**現状**:
- 「ダッシュボード」タブが存在するが、不要

**影響**:
- UI上の不要な要素
- ユーザーの混乱を招く可能性

### 技術調査

#### 調査箇所

1. **タブ定義部分**:
   ```html
   <nav class="tabs">
     <ul>
       <li data-tab="overview">総合概要</li>
       <li data-tab="supply">人材供給</li>
       <li data-tab="persona">ペルソナ分析</li>
       <li data-tab="career">キャリア分析</li>
       <li data-tab="urgency">緊急度分析</li>
       <li data-tab="cross">クロス分析</li>
       <li data-tab="flow">フロー分析</li>
       <li data-tab="dashboard">ダッシュボード</li> <!-- 削除対象 -->
     </ul>
   </nav>
   ```

2. **レンダリング関数**:
   ```javascript
   function renderTab_dashboard() {
     // この関数も削除またはコメントアウト
   }
   ```

3. **タブコンテンツ**:
   ```html
   <section class="panel" data-panel="dashboard">
     <!-- このセクション全体を削除 -->
   </section>
   ```

#### 修正方針

1. **タブ定義の削除**:
   ```html
   <!-- BEFORE -->
   <li data-tab="dashboard">ダッシュボード</li>

   <!-- AFTER -->
   <!-- <li data-tab="dashboard">ダッシュボード</li> -->
   ```

2. **レンダリング関数の削除**:
   ```javascript
   // BEFORE
   function renderTab_dashboard() { ... }

   // AFTER
   // function renderTab_dashboard() { ... }
   ```

3. **タブコンテンツの削除**:
   ```html
   <!-- BEFORE -->
   <section class="panel" data-panel="dashboard">
     ...
   </section>

   <!-- AFTER -->
   <!-- <section class="panel" data-panel="dashboard">
     ...
   </section> -->
   ```

### 実装手順

1. ⬜ タブ定義部分を特定
2. ⬜ タブ定義をコメントアウトまたは削除
3. ⬜ レンダリング関数をコメントアウトまたは削除
4. ⬜ タブコンテンツをコメントアウトまたは削除
5. ⬜ ローカルテスト（clasp pull → 修正 → clasp push）
6. ⬜ GASで動作確認
7. ⬜ ドキュメント更新

### テストケース

| ケース | 操作 | 期待結果 |
|--------|------|---------|
| TC-007-1 | ダッシュボード起動 | 「ダッシュボード」タブが表示されない |
| TC-007-2 | 他のタブ切り替え | 正常に動作する |

---

## 実装優先順位

### Phase 5A: 市町村フィルタリング修正（高優先度）

1. **T-001**: 総合概要 - 年齢大別求職者数
2. **T-002**: キャリア分析 - 就業ステータス×年齢帯
3. **T-003**: 緊急度分析 - 緊急度サマリー/チャート

**推定工数**: 4-6時間
**完了条件**: 市町村を選択すると、すべてのグラフが市町村別にフィルタリングされる

### Phase 5B: UI機能修正（高優先度）

4. **T-004**: ペルソナ分析 - 絞り込み実行ボタン

**推定工数**: 2-3時間
**完了条件**: 絞り込みボタンをクリックすると、フィルタリングが実行される

### Phase 5C: 未実装タブの実装（高優先度）

5. **T-005**: クロス分析タブ - データ表示実装
6. **T-006**: フロー分析タブ - データ表示実装

**推定工数**: 6-8時間
**完了条件**: すべてのタブでデータが表示される

### Phase 5D: UI整理（中優先度）

7. **T-007**: ダッシュボードタブの削除

**推定工数**: 0.5時間
**完了条件**: ダッシュボードタブが削除される

---

## 完了条件

### 全体の完了条件

- ✅ すべてのタブでデータが表示される
- ✅ 市町村を選択すると、すべてのグラフが市町村別にフィルタリングされる
- ✅ ペルソナ分析の絞り込みボタンが正常に動作する
- ✅ 不要なタブが削除される
- ✅ すべてのテストケースが成功する

### 検証方法

1. **機能テスト**: 各タブを順番に開いて、データが表示されることを確認
2. **フィルタリングテスト**: 複数の市町村を選択して、データが正しくフィルタリングされることを確認
3. **回帰テスト**: 既存の機能（総合概要、人材供給）が正常に動作することを確認

---

## 備考

- すべての修正は `map_complete_integrated.html` に対して実施
- 修正前に必ずバックアップを作成
- 各タスク完了後、GASにデプロイして動作確認を実施
- 問題が発生した場合は、バックアップから復元して再度修正

---

**次回作業**: T-001（総合概要 - 年齢大別求職者数）の実装
