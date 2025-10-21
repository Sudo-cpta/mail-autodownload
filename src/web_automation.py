"""Webブラウザ自動化によるログインとダウンロード"""
import logging
import time
from pathlib import Path
from typing import Optional, List
from playwright.sync_api import sync_playwright, Page, Browser, Download


logger = logging.getLogger(__name__)


class WebAutomation:
    """Web自動化クラス"""

    def __init__(self, download_folder: Path, headless: bool = True, timeout: int = 30000):
        """
        Web自動化を初期化

        Args:
            download_folder: ダウンロード先フォルダ
            headless: ヘッドレスモードで実行するか
            timeout: タイムアウト時間（ミリ秒）
        """
        self.download_folder = download_folder
        self.download_folder.mkdir(parents=True, exist_ok=True)
        self.headless = headless
        self.timeout = timeout
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    def start(self) -> None:
        """ブラウザを起動"""
        try:
            logger.info("ブラウザを起動中...")
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            context = self.browser.new_context(
                accept_downloads=True,
                downloads_path=str(self.download_folder)
            )
            self.page = context.new_page()
            self.page.set_default_timeout(self.timeout)
            logger.info("ブラウザを起動しました")
        except Exception as e:
            logger.error(f"ブラウザ起動エラー: {e}")
            raise

    def stop(self) -> None:
        """ブラウザを終了"""
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            logger.info("ブラウザを終了しました")
        except Exception as e:
            logger.warning(f"ブラウザ終了エラー: {e}")

    def login_and_download(self, url: str, username: str, password: str,
                          download_selector: str = "") -> List[str]:
        """
        URLにログインしてファイルをダウンロード

        Args:
            url: ログインURL
            username: ユーザー名
            password: パスワード
            download_selector: ダウンロードボタンのCSSセレクタ

        Returns:
            ダウンロードされたファイルのパスリスト
        """
        if not self.page:
            raise RuntimeError("ブラウザが起動していません")

        try:
            logger.info(f"URL {url} にアクセス中...")
            self.page.goto(url, wait_until='networkidle')

            # ログイン処理
            logger.info("ログイン処理を実行中...")
            self._perform_login(username, password)

            # ページが読み込まれるまで待機
            time.sleep(3)

            # ダウンロード処理
            logger.info("ダウンロード処理を実行中...")
            downloaded_files = self._perform_download(download_selector)

            logger.info(f"{len(downloaded_files)} 件のファイルをダウンロードしました")
            return downloaded_files

        except Exception as e:
            logger.error(f"ログイン・ダウンロードエラー: {e}")
            # エラー時のスクリーンショット
            try:
                screenshot_path = self.download_folder / f"error_{int(time.time())}.png"
                self.page.screenshot(path=str(screenshot_path))
                logger.info(f"エラースクリーンショット: {screenshot_path}")
            except Exception:
                pass
            raise

    def _perform_login(self, username: str, password: str) -> None:
        """
        ログイン処理を実行

        Args:
            username: ユーザー名
            password: パスワード
        """
        # 一般的なログインフォームのセレクタパターン
        username_selectors = [
            'input[type="email"]',
            'input[type="text"][name*="user"]',
            'input[type="text"][name*="email"]',
            'input[type="text"][name*="login"]',
            'input[id*="user"]',
            'input[id*="email"]',
            'input[id*="login"]',
            'input[name="username"]',
            'input[name="email"]',
        ]

        password_selectors = [
            'input[type="password"]',
            'input[name="password"]',
            'input[id*="password"]',
        ]

        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("ログイン")',
            'button:has-text("Login")',
            'button:has-text("Sign in")',
            'button:has-text("サインイン")',
        ]

        # ユーザー名入力
        username_filled = False
        for selector in username_selectors:
            try:
                if self.page.query_selector(selector):
                    self.page.fill(selector, username)
                    logger.debug(f"ユーザー名入力: {selector}")
                    username_filled = True
                    break
            except Exception:
                continue

        if not username_filled:
            logger.warning("ユーザー名フィールドが見つかりませんでした")

        # パスワード入力
        password_filled = False
        for selector in password_selectors:
            try:
                if self.page.query_selector(selector):
                    self.page.fill(selector, password)
                    logger.debug(f"パスワード入力: {selector}")
                    password_filled = True
                    break
            except Exception:
                continue

        if not password_filled:
            logger.warning("パスワードフィールドが見つかりませんでした")

        # ログインボタンをクリック
        for selector in submit_selectors:
            try:
                if self.page.query_selector(selector):
                    self.page.click(selector)
                    logger.debug(f"ログインボタンクリック: {selector}")
                    # ページ遷移を待つ
                    self.page.wait_for_load_state('networkidle', timeout=10000)
                    return
            except Exception:
                continue

        logger.warning("ログインボタンが見つかりませんでした")

    def _perform_download(self, download_selector: str = "") -> List[str]:
        """
        ダウンロード処理を実行

        Args:
            download_selector: ダウンロードボタンのCSSセレクタ

        Returns:
            ダウンロードされたファイルパスのリスト
        """
        downloaded_files = []

        # カスタムセレクタが指定されている場合
        if download_selector:
            try:
                downloaded_file = self._click_and_download(download_selector)
                if downloaded_file:
                    downloaded_files.append(downloaded_file)
                    return downloaded_files
            except Exception as e:
                logger.warning(f"カスタムセレクタでのダウンロード失敗: {e}")

        # 一般的なダウンロードリンクのセレクタパターン
        download_selectors = [
            'a[href*="download"]',
            'a[href*="invoice"]',
            'a[href*="pdf"]',
            'button:has-text("ダウンロード")',
            'button:has-text("Download")',
            'a:has-text("ダウンロード")',
            'a:has-text("Download")',
            'a:has-text("請求書")',
            'a:has-text("Invoice")',
            'a[download]',
        ]

        for selector in download_selectors:
            try:
                elements = self.page.query_selector_all(selector)
                if elements:
                    logger.debug(f"{len(elements)} 個のダウンロード候補が見つかりました: {selector}")
                    # 最初の要素をクリック
                    downloaded_file = self._click_and_download(selector)
                    if downloaded_file:
                        downloaded_files.append(downloaded_file)
                        break
            except Exception as e:
                logger.debug(f"セレクタ {selector} でエラー: {e}")
                continue

        return downloaded_files

    def _click_and_download(self, selector: str) -> Optional[str]:
        """
        要素をクリックしてダウンロード

        Args:
            selector: CSSセレクタ

        Returns:
            ダウンロードされたファイルパス
        """
        try:
            with self.page.expect_download(timeout=30000) as download_info:
                self.page.click(selector)
                download: Download = download_info.value

                # ファイル名を取得
                filename = download.suggested_filename
                file_path = self.download_folder / filename

                # ファイルを保存
                download.save_as(str(file_path))
                logger.info(f"ファイルをダウンロード: {file_path}")

                return str(file_path)

        except Exception as e:
            logger.debug(f"ダウンロード待機タイムアウト: {e}")
            return None

    def __enter__(self):
        """コンテキストマネージャー: 起動"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー: 終了"""
        self.stop()
