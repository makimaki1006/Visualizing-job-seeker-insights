/**
 * Google Maps API キー管理（セキュア実装）
 *
 * セキュリティベストプラクティス:
 * 1. APIキーをスクリプトプロパティに保存
 * 2. コード内にハードコーディングしない
 * 3. 環境変数として管理
 *
 * 設定方法:
 * 1. GASエディタ > プロジェクト設定（歯車アイコン）
 * 2. 「スクリプトのプロパティ」セクション
 * 3. 「スクリプト プロパティを追加」をクリック
 * 4. プロパティ名: GOOGLE_MAPS_API_KEY
 * 5. 値: あなたのGoogle Maps APIキー
 * 6. 保存
 */

/**
 * Google Maps APIキー取得（セキュア版・オプショナル対応）
 *
 * @param {boolean} throwError - APIキー未設定時にエラーをスローするか（デフォルト: false）
 * @return {string|null} Google Maps APIキー（未設定時はnull）
 */
function getGoogleMapsAPIKey(throwError = false) {
  const properties = PropertiesService.getScriptProperties();
  const apiKey = properties.getProperty('GOOGLE_MAPS_API_KEY');

  if (!apiKey) {
    if (throwError) {
      throw new Error(
        'Google Maps APIキーが設定されていません。\n\n' +
        '設定方法:\n' +
        '1. GASエディタ > プロジェクト設定（歯車アイコン）\n' +
        '2. 「スクリプトのプロパティ」セクション\n' +
        '3. 「スクリプト プロパティを追加」\n' +
        '4. プロパティ名: GOOGLE_MAPS_API_KEY\n' +
        '5. 値: あなたのGoogle Maps APIキー\n' +
        '6. 保存後、再度この機能を実行してください'
      );
    }

    // エラーをスローしない場合は警告をログに出力
    console.warn('⚠️ Google Maps APIキーが未設定です。一部の地図機能が制限される場合があります。');
    return null;
  }

  return apiKey;
}

/**
 * Google Maps APIキー設定（初回セットアップ用）
 *
 * 注意: この関数は初回セットアップ時に一度だけ実行してください
 * セキュリティ上、APIキーをコード内に直接書かないでください
 *
 * @param {string} apiKey - Google Maps APIキー
 */
function setGoogleMapsAPIKey(apiKey) {
  if (!apiKey || apiKey.trim() === '') {
    throw new Error('APIキーが空です');
  }

  if (apiKey === 'YOUR_API_KEY_HERE') {
    throw new Error('プレースホルダーのままです。実際のAPIキーを設定してください');
  }

  const properties = PropertiesService.getScriptProperties();
  properties.setProperty('GOOGLE_MAPS_API_KEY', apiKey);

  Logger.log('Google Maps APIキーを設定しました');
  Logger.log('セキュリティのため、この関数内のAPIキーは削除してください');
}

/**
 * Google Maps APIキー検証
 *
 * @return {boolean} APIキーが設定されている場合true
 */
function validateGoogleMapsAPIKey() {
  try {
    const apiKey = getGoogleMapsAPIKey();
    return apiKey && apiKey.length > 0 && apiKey !== 'YOUR_API_KEY_HERE';
  } catch (error) {
    return false;
  }
}

/**
 * Google Maps スクリプトタグ生成（セキュア版・オプショナル対応）
 *
 * @param {Array<string>} libraries - 読み込むライブラリ（例: ['visualization', 'geometry']）
 * @return {string} Google Maps スクリプトタグHTML（APIキー未設定時は警告コメント）
 */
function generateGoogleMapsScriptTag(libraries) {
  const apiKey = getGoogleMapsAPIKey(false); // エラーをスローしない

  if (!apiKey) {
    // APIキーが未設定の場合は警告コメントを返す
    return `<!-- ⚠️ Google Maps APIキーが未設定です。地図機能が制限されています。 -->`;
  }

  let scriptUrl = `https://maps.googleapis.com/maps/api/js?key=${apiKey}`;

  if (libraries && libraries.length > 0) {
    scriptUrl += `&libraries=${libraries.join(',')}`;
  }

  return `<script src="${scriptUrl}"></script>`;
}

/**
 * APIキー設定状況確認（デバッグ用）
 */
function checkAPIKeyStatus() {
  const ui = SpreadsheetApp.getUi();

  try {
    const apiKey = getGoogleMapsAPIKey();
    const maskedKey = apiKey.substring(0, 10) + '...' + apiKey.substring(apiKey.length - 4);

    ui.alert(
      'APIキー設定確認',
      `✅ Google Maps APIキーが設定されています\n\n` +
      `マスク済みキー: ${maskedKey}\n` +
      `キー長: ${apiKey.length}文字\n\n` +
      `セキュリティのため、完全なキーは表示されません。`,
      ui.ButtonSet.OK
    );
  } catch (error) {
    ui.alert(
      'APIキー未設定',
      `❌ Google Maps APIキーが設定されていません\n\n` +
      error.message,
      ui.ButtonSet.OK
    );
  }
}

/**
 * APIキーリセット（管理者用）
 *
 * 注意: この操作は取り消せません
 */
function resetGoogleMapsAPIKey() {
  const ui = SpreadsheetApp.getUi();

  const response = ui.alert(
    'APIキーリセット',
    '本当にGoogle Maps APIキーをリセットしますか？\n\n' +
    'この操作は取り消せません。',
    ui.ButtonSet.YES_NO
  );

  if (response === ui.Button.YES) {
    const properties = PropertiesService.getScriptProperties();
    properties.deleteProperty('GOOGLE_MAPS_API_KEY');

    ui.alert(
      'リセット完了',
      'Google Maps APIキーをリセットしました。\n\n' +
      '再度setGoogleMapsAPIKey()関数を使用して設定してください。',
      ui.ButtonSet.OK
    );

    Logger.log('Google Maps APIキーをリセットしました');
  }
}
