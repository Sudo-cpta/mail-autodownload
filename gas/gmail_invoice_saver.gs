/**
 * Gmail請求書自動保存スクリプト
 *
 * 証憑運用パイプライン 段階4
 *
 * @version 1.0.0
 * @author 須戸美敦税理士事務所
 * @date 2026-10-09
 */

// ==========================================
// 設定（スプレッドシートから読み込み）
// ==========================================

/**
 * 設定スプレッドシートのID
 * 実装時に実際のスプレッドシートIDに置き換える
 */
const CONFIG_SHEET_ID = 'YOUR_SPREADSHEET_ID_HERE';

/**
 * 設定を読み込む
 */
function loadConfig() {
  const sheet = SpreadsheetApp.openById(CONFIG_SHEET_ID).getSheetByName('設定');
  const values = sheet.getRange('A2:B10').getValues();

  const config = {};
  values.forEach(row => {
    if (row[0]) {
      config[row[0]] = row[1];
    }
  });

  return config;
}

// ==========================================
// メイン処理
// ==========================================

/**
 * メイン関数（トリガーから実行）
 */
function main() {
  try {
    Logger.log('===== Gmail請求書自動保存 開始 =====');

    const config = loadConfig();
    const checkDays = config['CHECK_DAYS'] || 7;
    const driveFolderId = config['DRIVE_FOLDER_ID'];
    const notifyEmail = config['NOTIFY_EMAIL'];

    // 設定チェック
    if (!driveFolderId) {
      throw new Error('DRIVE_FOLDER_ID が設定されていません');
    }

    Logger.log(`設定: CHECK_DAYS=${checkDays}, DRIVE_FOLDER_ID=${driveFolderId}`);

    // 処理済みメッセージIDを読み込む（Gmailのラベルは変更しない）
    const processedIds = loadProcessedIds();

    // メールを検索
    const threads = searchInvoiceEmails(checkDays);
    Logger.log(`検索結果: ${threads.length} 件のスレッド`);

    let totalSaved = 0;
    let errorCount = 0;

    // 各スレッドを処理
    for (let i = 0; i < threads.length; i++) {
      const thread = threads[i];

      try {
        const savedCount = processThread(thread, driveFolderId, processedIds);
        totalSaved += savedCount;

        Logger.log(`スレッド ${i + 1}/${threads.length}: ${savedCount} 件保存`);

      } catch (error) {
        errorCount++;
        Logger.log(`エラー（スレッド ${i + 1}）: ${error.message}`);

        // エラー通知
        if (notifyEmail) {
          sendErrorNotification(notifyEmail, thread, error);
        }
      }
    }

    Logger.log(`===== 処理完了: ${totalSaved} 件保存、${errorCount} 件エラー =====`);

  } catch (error) {
    Logger.log(`致命的エラー: ${error.message}`);
    throw error;
  }
}

// ==========================================
// メール検索
// ==========================================

/**
 * 請求書メールを検索
 *
 * @param {number} days - 検索対象日数
 * @return {GmailThread[]} - スレッドの配列
 */
function searchInvoiceEmails(days) {
  const sinceDate = new Date();
  sinceDate.setDate(sinceDate.getDate() - days);
  const sinceDateStr = Utilities.formatDate(sinceDate, 'JST', 'yyyy/MM/dd');

  // 検索クエリ
  // - 添付ファイルあり
  // - 指定日以降
  const query = `has:attachment after:${sinceDateStr}`;

  Logger.log(`検索クエリ: ${query}`);

  return GmailApp.search(query);
}

// ==========================================
// スレッド処理
// ==========================================

/**
 * スレッドを処理
 *
 * @param {GmailThread} thread - スレッド
 * @param {string} driveFolderId - 保存先フォルダID
 * @param {Set<string>} processedIds - 処理済みメッセージID
 * @return {number} - 保存したファイル数
 */
function processThread(thread, driveFolderId, processedIds) {
  const messages = thread.getMessages();
  let savedCount = 0;

  for (const message of messages) {
    const id = message.getId();
    if (processedIds.has(id)) continue;
    const n = processMessage(message, driveFolderId);
    recordProcessedId(id);
    processedIds.add(id);
    savedCount += n;
  }

  return savedCount;
}

/**
 * メッセージを処理
 *
 * @param {GmailMessage} message - メッセージ
 * @param {string} driveFolderId - 保存先フォルダID
 * @return {number} - 保存したファイル数
 */
function processMessage(message, driveFolderId) {
  const attachments = message.getAttachments();

  if (attachments.length === 0) {
    return 0;
  }

  const folder = DriveApp.getFolderById(driveFolderId);
  const senderEmail = extractEmail(message.getFrom());
  const senderName = extractName(message.getFrom());
  const subject = message.getSubject();
  const receivedDate = message.getDate();
  const messageId = message.getId();

  let savedCount = 0;

  for (const attachment of attachments) {
    try {
      // ファイル名を生成
      const filename = generateFilename(receivedDate, senderEmail, subject, attachment.getName());

      // Google Driveに保存
      const file = folder.createFile(attachment.copyBlob().setName(filename));

      // メタデータを記録（カスタムプロパティ）
      file.setDescription(JSON.stringify({
        senderEmail: senderEmail,
        senderName: senderName,
        subject: subject,
        receivedDate: receivedDate.toISOString(),
        messageId: messageId,
        savedDate: new Date().toISOString()
      }));

      Logger.log(`保存: ${filename}`);
      savedCount++;

    } catch (error) {
      Logger.log(`添付ファイル保存エラー: ${attachment.getName()} - ${error.message}`);
    }
  }

  return savedCount;
}

// ==========================================
// ユーティリティ関数
// ==========================================

/**
 * 処理済みメッセージIDを「処理済み」シートから読み込む
 *
 * @return {Set<string>}
 */
function loadProcessedIds() {
  const sheet = getProcessedSheet();
  const last = sheet.getLastRow();
  const ids = last >= 2 ? sheet.getRange(2, 1, last - 1, 1).getValues().flat() : [];
  return new Set(ids.map(String));
}

/**
 * 処理済みメッセージIDを記録
 *
 * @param {string} id - GmailメッセージID
 */
function recordProcessedId(id) {
  getProcessedSheet().appendRow([id, new Date()]);
}

function getProcessedSheet() {
  const ss = SpreadsheetApp.openById(CONFIG_SHEET_ID);
  let sheet = ss.getSheetByName('処理済み');
  if (!sheet) {
    sheet = ss.insertSheet('処理済み');
    sheet.appendRow(['messageId', '処理日時']);
  }
  return sheet;
}

/**
 * ファイル名を生成
 *
 * @param {Date} date - 受信日時
 * @param {string} senderEmail - 送信者メールアドレス
 * @param {string} subject - 件名
 * @param {string} originalName - 元のファイル名
 * @return {string} - ファイル名
 */
function generateFilename(date, senderEmail, subject, originalName) {
  const dateStr = Utilities.formatDate(date, 'JST', 'yyyyMMdd_HHmmss');

  // ファイル名に使えない文字を除去
  const safeSender = sanitizeFilename(senderEmail);
  const safeSubject = sanitizeFilename(subject);

  // ファイル名が長すぎる場合は切り詰め
  const maxLength = 100;
  let truncatedSubject = safeSubject;
  if (truncatedSubject.length > 30) {
    truncatedSubject = truncatedSubject.substring(0, 30);
  }

  return `${dateStr}_${safeSender}_${truncatedSubject}_${originalName}`;
}

/**
 * ファイル名に使えない文字を除去
 *
 * @param {string} str - 文字列
 * @return {string} - サニタイズ後の文字列
 */
function sanitizeFilename(str) {
  return str.replace(/[\\/:*?"<>|]/g, '_').substring(0, 50);
}

/**
 * From フィールドからメールアドレスを抽出
 *
 * @param {string} from - From フィールド
 * @return {string} - メールアドレス
 */
function extractEmail(from) {
  const match = from.match(/<(.+?)>/);
  return match ? match[1] : from;
}

/**
 * From フィールドから表示名を抽出
 *
 * @param {string} from - From フィールド
 * @return {string} - 表示名
 */
function extractName(from) {
  const match = from.match(/^(.+?)\s*</);
  return match ? match[1].replace(/"/g, '') : from;
}

/**
 * エラー通知メールを送信
 *
 * @param {string} email - 送信先メールアドレス
 * @param {GmailThread} thread - エラーが発生したスレッド
 * @param {Error} error - エラー
 */
function sendErrorNotification(email, thread, error) {
  // 送信は nextaxion.jp ドメイン宛てに限定（所長方針 2026-10-12）
  if (!/@nextaxion\.jp$/i.test(String(email).trim())) {
    Logger.log(`通知先が許可ドメイン外のため送信しません: ${email}`);
    return;
  }
  const subject = '【エラー通知】Gmail請求書自動保存';
  const body = `
Gmail請求書自動保存でエラーが発生しました。

■ エラー内容
${error.message}

■ スレッド情報
件名: ${thread.getFirstMessageSubject()}
送信者: ${thread.getMessages()[0].getFrom()}
日時: ${thread.getLastMessageDate()}

■ 対応
手動でファイルを保存してください。
  `.trim();

  try {
    MailApp.sendEmail(email, subject, body);
    Logger.log(`エラー通知メール送信: ${email}`);
  } catch (e) {
    Logger.log(`エラー通知メール送信失敗: ${e.message}`);
  }
}

// ==========================================
// テスト関数
// ==========================================

/**
 * テスト実行（手動実行用）
 */
function test() {
  Logger.log('===== テスト実行 =====');

  // 設定を読み込む
  const config = loadConfig();
  Logger.log('設定:');
  Logger.log(config);

  // メールを検索（直近1日間）
  const threads = searchInvoiceEmails(1);

  Logger.log(`検索結果: ${threads.length} 件`);

  if (threads.length > 0) {
    Logger.log('最初のスレッド:');
    const thread = threads[0];
    Logger.log(`  件名: ${thread.getFirstMessageSubject()}`);
    Logger.log(`  送信者: ${thread.getMessages()[0].getFrom()}`);

    const messages = thread.getMessages();
    Logger.log(`  メッセージ数: ${messages.length}`);

    if (messages.length > 0) {
      const attachments = messages[0].getAttachments();
      Logger.log(`  添付ファイル数: ${attachments.length}`);
    }
  }

  Logger.log('===== テスト完了 =====');
}
