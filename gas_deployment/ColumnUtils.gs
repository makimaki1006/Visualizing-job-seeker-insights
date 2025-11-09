/**
 * ColumnUtils.gs
 * カラム名・シート名の言語不一致問題を解決するための共通ユーティリティライブラリ
 *
 * 【目的】
 * - 日本語/英語カラム名の両方に対応
 * - snake_case/camelCaseの両方に対応
 * - Phase接頭辞あり/なしの両方に対応
 * - エラーハンドリングの統一
 */

/**
 * カラム名マッピング定数
 * 各論理カラムに対して、考えられるすべての命名バリエーションを定義
 */
const COLUMN_MAPPING = {
  // 都道府県
  prefecture: ['都道府県', '都道府県名', 'prefecture', 'Prefecture', 'PREFECTURE', 'pref'],

  // 市区町村
  municipality: ['市区町村', '市区町村名', '自治体', 'municipality', 'Municipality', 'MUNICIPALITY', 'muni', 'city'],

  // 地域キー
  location_key: ['キー', '地域キー', 'location_key', 'locationKey', 'key', 'Key', 'KEY'],

  // 申請者ID
  applicant_id: ['申請者ID', 'applicant_id', 'applicantId', 'applicant_ID', 'ApplicantID', 'id', 'ID'],

  // 人数・カウント
  count: ['人数', 'カウント', '件数', 'count', 'Count', 'COUNT', 'applicant_count', 'applicantCount'],

  // 年齢
  age: ['年齢', 'age', 'Age', 'AGE'],

  // 年齢層
  age_group: ['年齢層', '年齢グループ', 'age_group', 'ageGroup', 'age_bracket', 'ageBracket'],

  // 性別
  gender: ['性別', 'gender', 'Gender', 'GENDER', 'sex', 'Sex'],

  // 平均年齢
  avg_age: ['平均年齢', 'avg_age', 'avgAge', 'average_age', 'averageAge', 'mean_age'],

  // 男性数
  male_count: ['男性数', 'male_count', 'maleCount', 'male', 'Male'],

  // 女性数
  female_count: ['女性数', 'female_count', 'femaleCount', 'female', 'Female'],

  // 平均資格数
  avg_qualifications: ['平均資格数', 'avg_qualifications', 'avgQualifications', 'average_qualifications'],

  // 資格数
  qualification_count: ['資格数', 'qualification_count', 'qualificationCount', 'qualifications'],

  // 緯度
  latitude: ['緯度', 'latitude', 'Latitude', 'LATITUDE', 'lat'],

  // 経度
  longitude: ['経度', 'longitude', 'Longitude', 'LONGITUDE', 'lng', 'lon'],

  // 希望都道府県
  desired_prefecture: ['希望都道府県', 'desired_prefecture', 'desiredPrefecture', 'desired_pref'],

  // 希望市区町村
  desired_municipality: ['希望市区町村', 'desired_municipality', 'desiredMunicipality', 'desired_muni'],

  // 希望勤務地（完全）
  desired_location_full: ['希望勤務地', 'desired_location_full', 'desiredLocationFull', 'desired_location'],

  // 居住都道府県
  residence_prefecture: ['居住都道府県', 'residence_prefecture', 'residencePrefecture', 'residence_pref'],

  // 居住市区町村
  residence_municipality: ['居住市区町村', 'residence_municipality', 'residenceMunicipality', 'residence_muni'],

  // 希望勤務地数
  desired_area_count: ['希望勤務地数', 'desired_area_count', 'desiredAreaCount', 'desired_areas'],

  // 国家資格保有
  has_national_license: ['国家資格保有', 'has_national_license', 'hasNationalLicense', 'national_license'],

  // 就業ステータス
  employment_status: ['就業ステータス', '雇用状態', 'employment_status', 'employmentStatus', 'employment'],

  // 需要数
  demand_count: ['需要数', 'demand_count', 'demandCount', 'demand'],

  // 供給数
  supply_count: ['供給数', 'supply_count', 'supplyCount', 'supply'],

  // ギャップ
  gap: ['ギャップ', 'gap', 'Gap', 'GAP', 'difference'],

  // 緊急度
  urgency_rank: ['緊急度', '緊急度ランク', 'urgency_rank', 'urgencyRank', 'urgency', 'rank'],

  // 緊急度スコア
  urgency_score: ['緊急度スコア', 'urgency_score', 'urgencyScore'],

  // 学歴
  education: ['学歴', '最終学歴', 'education', 'Education', 'EDUCATION'],

  // 卒業年
  graduation_year: ['卒業年', '卒業年度', 'graduation_year', 'graduationYear', 'grad_year']
};

/**
 * 複数のカラム名候補から最初に見つかったインデックスを返す
 * @param {Array<string>} headers - ヘッダー行の配列
 * @param {string} logicalColumnName - 論理カラム名（COLUMN_MAPPINGのキー）
 * @return {number} - 見つかったカラムのインデックス、見つからない場合は-1
 */
function findColumnIndexByLogicalName(headers, logicalColumnName) {
  Logger.log('[findColumnIndex] 検索開始 - logicalColumnName: ' + logicalColumnName);

  if (!headers || !Array.isArray(headers)) {
    Logger.log('[findColumnIndex] エラー - headersが配列ではありません');
    return -1;
  }

  const candidates = COLUMN_MAPPING[logicalColumnName];
  if (!candidates) {
    Logger.log('[findColumnIndex] 警告 - 未定義の論理カラム名: ' + logicalColumnName);
    return -1;
  }

  Logger.log('[findColumnIndex] 候補: ' + JSON.stringify(candidates));

  for (let i = 0; i < headers.length; i += 1) {
    const header = String(headers[i] || '').trim();

    for (let j = 0; j < candidates.length; j += 1) {
      const candidate = candidates[j];

      // 完全一致
      if (header === candidate) {
        Logger.log('[findColumnIndex] 成功 - インデックス ' + i + ' で "' + header + '" が一致（候補: ' + candidate + '）');
        return i;
      }

      // 大文字小文字を無視した一致
      if (header.toLowerCase() === candidate.toLowerCase()) {
        Logger.log('[findColumnIndex] 成功 - インデックス ' + i + ' で "' + header + '" が一致（大文字小文字無視、候補: ' + candidate + '）');
        return i;
      }
    }
  }

  Logger.log('[findColumnIndex] 見つかりませんでした - logicalColumnName: ' + logicalColumnName);
  return -1;
}

/**
 * 複数のカラム名候補から必須カラムのインデックスを取得
 * 見つからない場合はエラーをスロー
 * @param {Array<string>} headers - ヘッダー行の配列
 * @param {string} logicalColumnName - 論理カラム名
 * @param {string} contextMessage - エラーメッセージのコンテキスト（例: "MapMetrics読み込み時"）
 * @return {number} - カラムのインデックス
 * @throws {Error} - カラムが見つからない場合
 */
function findRequiredColumnIndex(headers, logicalColumnName, contextMessage) {
  const index = findColumnIndex(headers, logicalColumnName);

  if (index === -1) {
    const candidates = COLUMN_MAPPING[logicalColumnName];
    const errorMessage = contextMessage +
      ' - 必須カラム "' + logicalColumnName + '" が見つかりません。' +
      ' 候補: [' + (candidates ? candidates.join(', ') : 'なし') + ']';
    Logger.log('[findRequiredColumnIndex] エラー: ' + errorMessage);
    throw new Error(errorMessage);
  }

  return index;
}

/**
 * 複数のシート名候補から最初に見つかったシートを返す
 * @param {Spreadsheet} spreadsheet - スプレッドシートオブジェクト
 * @param {Array<string>} sheetNames - シート名候補の配列
 * @return {Sheet|null} - 見つかったシート、またはnull
 */
function findSheetByNames(spreadsheet, sheetNames) {
  Logger.log('[findSheetByNames] シート名候補: ' + JSON.stringify(sheetNames));

  if (!Array.isArray(sheetNames)) {
    Logger.log('[findSheetByNames] エラー - sheetNamesが配列ではありません');
    return null;
  }

  for (let i = 0; i < sheetNames.length; i += 1) {
    const sheetName = sheetNames[i];
    Logger.log('[findSheetByNames] 試行 ' + (i + 1) + '/' + sheetNames.length + ': ' + sheetName);

    const sheet = spreadsheet.getSheetByName(sheetName);
    if (sheet) {
      Logger.log('[findSheetByNames] 成功 - シート "' + sheetName + '" を使用します');
      return sheet;
    }
  }

  Logger.log('[findSheetByNames] 警告 - 有効なシートが見つかりませんでした');
  return null;
}

/**
 * 必須シートを取得（見つからない場合はエラーをスロー）
 * @param {Spreadsheet} spreadsheet - スプレッドシートオブジェクト
 * @param {Array<string>} sheetNames - シート名候補の配列
 * @param {string} contextMessage - エラーメッセージのコンテキスト
 * @return {Sheet} - 見つかったシート
 * @throws {Error} - シートが見つからない場合
 */
function findRequiredSheet(spreadsheet, sheetNames, contextMessage) {
  const sheet = findSheetByNames(spreadsheet, sheetNames);

  if (!sheet) {
    const errorMessage = contextMessage +
      ' - 必須シートが見つかりません。候補: [' + sheetNames.join(', ') + ']';
    Logger.log('[findRequiredSheet] エラー: ' + errorMessage);
    throw new Error(errorMessage);
  }

  return sheet;
}

/**
 * カラム値を安全に取得（インデックスが-1の場合にundefinedを返さない）
 * @param {Array} row - データ行
 * @param {number} columnIndex - カラムのインデックス
 * @param {*} defaultValue - デフォルト値（省略可、デフォルトは空文字列）
 * @return {*} - カラムの値、またはデフォルト値
 */
function safeGetColumn(row, columnIndex, defaultValue) {
  if (columnIndex === -1) {
    return defaultValue !== undefined ? defaultValue : '';
  }

  const value = row[columnIndex];
  if (value === null || value === undefined) {
    return defaultValue !== undefined ? defaultValue : '';
  }

  return value;
}

/**
 * シート名の標準的な候補リストを生成
 * Phase接頭辞あり/なしの両方をカバー
 * @param {string} baseName - 基本シート名（例: "MapMetrics"）
 * @param {number|string} phaseNumber - フェーズ番号（例: 1, "1"）
 * @return {Array<string>} - シート名候補の配列
 */
function generateSheetNameCandidates(baseName, phaseNumber) {
  const phase = String(phaseNumber);
  return [
    'Phase' + phase + '_' + baseName,
    'P' + phase + '_' + baseName,
    'phase' + phase + '_' + baseName,
    baseName
  ];
}

/**
 * デバッグ用：ヘッダー行とCOLUMN_MAPPINGの対応関係を表示
 * @param {Array<string>} headers - ヘッダー行の配列
 */
function debugColumnMapping(headers) {
  Logger.log('[debugColumnMapping] ===== カラムマッピング診断 =====');
  Logger.log('[debugColumnMapping] ヘッダー: ' + JSON.stringify(headers));

  const logicalColumns = Object.keys(COLUMN_MAPPING);
  const found = [];
  const notFound = [];

  for (let i = 0; i < logicalColumns.length; i += 1) {
    const logicalName = logicalColumns[i];
    const index = findColumnIndex(headers, logicalName);

    if (index !== -1) {
      found.push(logicalName + ' → インデックス ' + index + ' ("' + headers[index] + '")');
    } else {
      notFound.push(logicalName + ' → 見つかりません（候補: [' + COLUMN_MAPPING[logicalName].join(', ') + ']）');
    }
  }

  Logger.log('[debugColumnMapping] ===== 見つかったカラム (' + found.length + '件) =====');
  found.forEach(function(msg) {
    Logger.log('[debugColumnMapping] ✅ ' + msg);
  });

  Logger.log('[debugColumnMapping] ===== 見つからなかったカラム (' + notFound.length + '件) =====');
  notFound.forEach(function(msg) {
    Logger.log('[debugColumnMapping] ❌ ' + msg);
  });
}
