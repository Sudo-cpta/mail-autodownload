"""スプレッドシート（CSV/Excel）から認証情報を読み込む"""
import csv
from pathlib import Path
from typing import List, Dict, Optional
import logging
import pandas as pd


logger = logging.getLogger(__name__)


class CredentialEntry:
    """認証情報エントリ"""

    def __init__(self, sender_email: str, login_url: str, username: str,
                 password: str, download_selector: str = "", notes: str = ""):
        """
        認証情報を初期化

        Args:
            sender_email: 送信者のメールアドレス
            login_url: ログインURL
            username: ログインユーザー名
            password: ログインパスワード
            download_selector: ダウンロードボタンのCSSセレクタ
            notes: 備考
        """
        self.sender_email = sender_email
        self.login_url = login_url
        self.username = username
        self.password = password
        self.download_selector = download_selector
        self.notes = notes

    def __repr__(self):
        return f"<Credential sender={self.sender_email} url={self.login_url}>"


class SpreadsheetHandler:
    """スプレッドシート処理クラス"""

    def __init__(self, file_path: str = "credentials.csv"):
        """
        スプレッドシートハンドラーを初期化

        Args:
            file_path: 認証情報ファイルのパス（CSV or Excel）
        """
        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(
                f"認証情報ファイル '{self.file_path}' が見つかりません。\n"
                f"credentials.example.csv をコピーして credentials.csv を作成してください。"
            )

    def load_credentials(self) -> List[CredentialEntry]:
        """
        認証情報を読み込む

        Returns:
            認証情報エントリのリスト
        """
        ext = self.file_path.suffix.lower()

        if ext == '.csv':
            return self._load_from_csv()
        elif ext in ['.xlsx', '.xls']:
            return self._load_from_excel()
        else:
            raise ValueError(f"未対応のファイル形式: {ext}")

    def _load_from_csv(self) -> List[CredentialEntry]:
        """
        CSVファイルから認証情報を読み込む

        Returns:
            認証情報エントリのリスト
        """
        credentials = []

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    if not row.get('sender_email') or not row.get('login_url'):
                        logger.warning(f"不完全な行をスキップ: {row}")
                        continue

                    credential = CredentialEntry(
                        sender_email=row.get('sender_email', '').strip(),
                        login_url=row.get('login_url', '').strip(),
                        username=row.get('username', '').strip(),
                        password=row.get('password', '').strip(),
                        download_selector=row.get('download_selector', '').strip(),
                        notes=row.get('notes', '').strip()
                    )
                    credentials.append(credential)

            logger.info(f"{len(credentials)} 件の認証情報を読み込みました")
            return credentials

        except Exception as e:
            logger.error(f"CSV読み込みエラー: {e}")
            raise

    def _load_from_excel(self) -> List[CredentialEntry]:
        """
        Excelファイルから認証情報を読み込む

        Returns:
            認証情報エントリのリスト
        """
        credentials = []

        try:
            df = pd.read_excel(self.file_path)

            for _, row in df.iterrows():
                if pd.isna(row.get('sender_email')) or pd.isna(row.get('login_url')):
                    logger.warning(f"不完全な行をスキップ: {row.to_dict()}")
                    continue

                credential = CredentialEntry(
                    sender_email=str(row.get('sender_email', '')).strip(),
                    login_url=str(row.get('login_url', '')).strip(),
                    username=str(row.get('username', '')).strip(),
                    password=str(row.get('password', '')).strip(),
                    download_selector=str(row.get('download_selector', '')).strip(),
                    notes=str(row.get('notes', '')).strip()
                )
                credentials.append(credential)

            logger.info(f"{len(credentials)} 件の認証情報を読み込みました")
            return credentials

        except Exception as e:
            logger.error(f"Excel読み込みエラー: {e}")
            raise

    def get_credential_for_sender(self, sender_email: str) -> Optional[CredentialEntry]:
        """
        特定の送信者の認証情報を取得

        Args:
            sender_email: 送信者のメールアドレス

        Returns:
            認証情報エントリ（見つからない場合はNone）
        """
        credentials = self.load_credentials()

        for cred in credentials:
            if cred.sender_email.lower() == sender_email.lower():
                return cred

        logger.warning(f"送信者 '{sender_email}' の認証情報が見つかりません")
        return None
