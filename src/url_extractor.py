"""メール本文からURLを抽出する機能"""
import re
from typing import List
import logging
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class URLExtractor:
    """URL抽出クラス"""

    # URLパターン（http, https）
    URL_PATTERN = re.compile(
        r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}'
        r'\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)',
        re.IGNORECASE
    )

    @staticmethod
    def extract_urls(text: str, html: bool = False) -> List[str]:
        """
        テキストからURLを抽出

        Args:
            text: 検索対象のテキスト
            html: HTMLとして処理するかどうか

        Returns:
            抽出されたURLのリスト
        """
        urls = []

        if html:
            urls.extend(URLExtractor._extract_from_html(text))

        # 正規表現でURLを抽出
        matches = URLExtractor.URL_PATTERN.findall(text)
        urls.extend(matches)

        # 重複を削除
        unique_urls = list(dict.fromkeys(urls))

        logger.info(f"{len(unique_urls)} 件のURLを抽出しました")
        return unique_urls

    @staticmethod
    def _extract_from_html(html_text: str) -> List[str]:
        """
        HTMLからリンクを抽出

        Args:
            html_text: HTML文字列

        Returns:
            抽出されたURLのリスト
        """
        urls = []

        try:
            soup = BeautifulSoup(html_text, 'lxml')

            # aタグのhref属性を取得
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('http'):
                    urls.append(href)

            logger.debug(f"HTMLから {len(urls)} 件のリンクを抽出")
        except Exception as e:
            logger.warning(f"HTML解析エラー: {e}")

        return urls

    @staticmethod
    def filter_urls(urls: List[str], keywords: List[str] = None) -> List[str]:
        """
        URLをキーワードでフィルタリング

        Args:
            urls: URLのリスト
            keywords: フィルタリングキーワード（含まれるもののみ）

        Returns:
            フィルタリング後のURLリスト
        """
        if not keywords:
            return urls

        filtered = []
        for url in urls:
            for keyword in keywords:
                if keyword.lower() in url.lower():
                    filtered.append(url)
                    break

        logger.info(f"キーワードフィルタリング: {len(urls)} -> {len(filtered)} 件")
        return filtered

    @staticmethod
    def extract_login_urls(text: str) -> List[str]:
        """
        ログインページと思われるURLを抽出

        Args:
            text: 検索対象のテキスト

        Returns:
            ログインURLのリスト
        """
        all_urls = URLExtractor.extract_urls(text, html=True)

        # ログイン関連のキーワード
        login_keywords = ['login', 'signin', 'auth', 'portal', 'account', 'invoice', 'billing']

        return URLExtractor.filter_urls(all_urls, login_keywords)
