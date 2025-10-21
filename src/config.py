"""設定ファイルの読み込みと管理"""
import json
import os
from pathlib import Path
from typing import Dict, Any


class Config:
    """設定管理クラス"""

    def __init__(self, config_path: str = "config.json"):
        """
        設定を読み込む

        Args:
            config_path: 設定ファイルのパス
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        設定ファイルを読み込む

        Returns:
            設定辞書

        Raises:
            FileNotFoundError: 設定ファイルが見つからない場合
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"設定ファイル '{self.config_path}' が見つかりません。\n"
                f"config.example.json をコピーして config.json を作成してください。"
            )

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_email_config(self) -> Dict[str, Any]:
        """メール設定を取得"""
        return self.config.get('email', {})

    def get_download_config(self) -> Dict[str, Any]:
        """ダウンロード設定を取得"""
        return self.config.get('download', {})

    def get_browser_config(self) -> Dict[str, Any]:
        """ブラウザ設定を取得"""
        return self.config.get('browser', {})

    def get_logging_config(self) -> Dict[str, Any]:
        """ログ設定を取得"""
        return self.config.get('logging', {})

    def get_download_folder(self) -> Path:
        """ダウンロードフォルダのパスを取得"""
        folder = self.config.get('download', {}).get('folder', './downloads')
        path = Path(folder)
        path.mkdir(parents=True, exist_ok=True)
        return path
