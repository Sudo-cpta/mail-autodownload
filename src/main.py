#!/usr/bin/env python3
"""請求書自動ダウンロードメインスクリプト"""
import logging
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.email_handler import EmailHandler
from src.url_extractor import URLExtractor
from src.spreadsheet_handler import SpreadsheetHandler, CredentialEntry
from src.web_automation import WebAutomation


def setup_logging(config: Config) -> None:
    """
    ロギングを設定

    Args:
        config: 設定オブジェクト
    """
    log_config = config.get_logging_config()
    log_level = getattr(logging, log_config.get('level', 'INFO'))
    log_file = log_config.get('file', 'automation.log')

    # ログフォーマット
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # ファイルハンドラー
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # ルートロガーの設定
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def process_credential(credential: CredentialEntry, email_handler: EmailHandler,
                       web_automation: WebAutomation, check_days: int) -> int:
    """
    認証情報に基づいてメールをチェックし、請求書をダウンロード

    Args:
        credential: 認証情報エントリ
        email_handler: メールハンドラー
        web_automation: Web自動化オブジェクト
        check_days: チェックする日数

    Returns:
        ダウンロードしたファイルの数
    """
    logger = logging.getLogger(__name__)
    downloaded_count = 0

    try:
        logger.info(f"=" * 60)
        logger.info(f"処理中: {credential.sender_email}")
        logger.info(f"ログインURL: {credential.login_url}")
        logger.info(f"備考: {credential.notes}")

        # メールを取得
        emails = email_handler.get_emails_from_sender(
            credential.sender_email,
            days=check_days
        )

        if not emails:
            logger.info(f"送信者 '{credential.sender_email}' からのメールはありません")
            return 0

        logger.info(f"{len(emails)} 件のメールを処理します")

        # 各メールからURLを抽出
        all_urls = set()
        for email_data in emails:
            logger.info(f"メール件名: {email_data['subject']}")

            # URLを抽出
            urls = URLExtractor.extract_urls(email_data['body'], html=True)
            logger.info(f"  {len(urls)} 件のURLを発見")

            for url in urls:
                logger.debug(f"  - {url}")
                all_urls.add(url)

        if not all_urls:
            logger.warning("メールからURLが見つかりませんでした")

        # ログインURLが含まれているか確認
        login_url_found = False
        for url in all_urls:
            if credential.login_url.lower() in url.lower() or \
               url.lower() in credential.login_url.lower():
                login_url_found = True
                break

        # ログインしてダウンロード
        logger.info(f"ログインURL '{credential.login_url}' を使用してダウンロードを開始")

        downloaded_files = web_automation.login_and_download(
            url=credential.login_url,
            username=credential.username,
            password=credential.password,
            download_selector=credential.download_selector
        )

        downloaded_count = len(downloaded_files)
        logger.info(f"{downloaded_count} 件のファイルをダウンロードしました")

        for file_path in downloaded_files:
            logger.info(f"  - {file_path}")

    except Exception as e:
        logger.error(f"認証情報 '{credential.sender_email}' の処理中にエラー: {e}")

    return downloaded_count


def main():
    """メイン処理"""
    logger = logging.getLogger(__name__)

    try:
        # 設定を読み込む
        logger.info("設定を読み込み中...")
        config = Config()

        # ロギングを設定
        setup_logging(config)

        logger.info("=" * 60)
        logger.info("請求書自動ダウンロードシステム 開始")
        logger.info("=" * 60)

        # 認証情報を読み込む
        logger.info("認証情報を読み込み中...")
        spreadsheet_handler = SpreadsheetHandler()
        credentials = spreadsheet_handler.load_credentials()

        if not credentials:
            logger.warning("認証情報が見つかりません。終了します。")
            return

        # メール設定を取得
        email_config = config.get_email_config()
        check_days = email_config.get('check_days', 7)

        # ブラウザ設定を取得
        browser_config = config.get_browser_config()
        headless = browser_config.get('headless', True)
        timeout = browser_config.get('timeout', 30000)

        # ダウンロードフォルダを取得
        download_folder = config.get_download_folder()
        logger.info(f"ダウンロードフォルダ: {download_folder}")

        total_downloaded = 0

        # メールハンドラーを初期化
        with EmailHandler(
            imap_server=email_config['imap_server'],
            imap_port=email_config['imap_port'],
            email_address=email_config['email_address'],
            password=email_config['password']
        ) as email_handler:

            # Web自動化を初期化
            with WebAutomation(
                download_folder=download_folder,
                headless=headless,
                timeout=timeout
            ) as web_automation:

                # 各認証情報を処理
                for credential in credentials:
                    count = process_credential(
                        credential=credential,
                        email_handler=email_handler,
                        web_automation=web_automation,
                        check_days=check_days
                    )
                    total_downloaded += count

        logger.info("=" * 60)
        logger.info(f"処理完了: 合計 {total_downloaded} 件のファイルをダウンロードしました")
        logger.info("=" * 60)

    except FileNotFoundError as e:
        logger.error(f"ファイルが見つかりません: {e}")
        logger.error("config.example.json と credentials.example.csv を参考に設定ファイルを作成してください")
        sys.exit(1)

    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
