"""メール受信とチェック機能"""
import email
from datetime import datetime, timedelta
from email.header import decode_header
from typing import List, Dict, Optional
import logging
from imapclient import IMAPClient


logger = logging.getLogger(__name__)


class EmailHandler:
    """メール処理クラス"""

    def __init__(self, imap_server: str, imap_port: int, email_address: str, password: str):
        """
        メールハンドラーを初期化

        Args:
            imap_server: IMAPサーバーアドレス
            imap_port: IMAPポート番号
            email_address: メールアドレス
            password: パスワード
        """
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.email_address = email_address
        self.password = password
        self.client: Optional[IMAPClient] = None

    def connect(self) -> None:
        """IMAPサーバーに接続"""
        try:
            logger.info(f"IMAPサーバー {self.imap_server}:{self.imap_port} に接続中...")
            self.client = IMAPClient(self.imap_server, port=self.imap_port, ssl=True)
            self.client.login(self.email_address, self.password)
            logger.info("IMAPサーバーに接続しました")
        except Exception as e:
            logger.error(f"IMAP接続エラー: {e}")
            raise

    def disconnect(self) -> None:
        """IMAPサーバーから切断"""
        if self.client:
            try:
                self.client.logout()
                logger.info("IMAPサーバーから切断しました")
            except Exception as e:
                logger.warning(f"IMAP切断エラー: {e}")

    def get_emails_from_sender(self, sender_email: str, days: int = 7) -> List[Dict]:
        """
        特定の送信者からのメールを取得

        Args:
            sender_email: 送信者のメールアドレス
            days: 何日前までのメールを取得するか

        Returns:
            メール情報のリスト
        """
        if not self.client:
            raise RuntimeError("IMAPサーバーに接続されていません")

        try:
            # INBOXを選択
            self.client.select_folder('INBOX', readonly=True)

            # 日付範囲を計算
            since_date = datetime.now() - timedelta(days=days)

            # メールを検索
            logger.info(f"送信者 '{sender_email}' からのメールを検索中...")
            messages = self.client.search([
                'FROM', sender_email,
                'SINCE', since_date
            ])

            logger.info(f"{len(messages)} 件のメールが見つかりました")

            emails = []
            for msg_id in messages:
                try:
                    email_data = self._fetch_email(msg_id)
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    logger.error(f"メールID {msg_id} の取得エラー: {e}")
                    continue

            return emails

        except Exception as e:
            logger.error(f"メール検索エラー: {e}")
            raise

    def _fetch_email(self, msg_id: int) -> Optional[Dict]:
        """
        メールを取得してパース

        Args:
            msg_id: メッセージID

        Returns:
            メール情報辞書
        """
        try:
            # メールデータを取得
            response = self.client.fetch([msg_id], ['RFC822'])
            email_message = email.message_from_bytes(response[msg_id][b'RFC822'])

            # 件名をデコード
            subject = self._decode_header(email_message.get('Subject', ''))

            # 送信者を取得
            from_addr = email_message.get('From', '')

            # 本文を取得
            body = self._get_email_body(email_message)

            # 日付を取得
            date_str = email_message.get('Date', '')

            return {
                'id': msg_id,
                'subject': subject,
                'from': from_addr,
                'date': date_str,
                'body': body
            }

        except Exception as e:
            logger.error(f"メール取得エラー: {e}")
            return None

    def _decode_header(self, header: str) -> str:
        """
        メールヘッダーをデコード

        Args:
            header: エンコードされたヘッダー

        Returns:
            デコードされた文字列
        """
        if not header:
            return ''

        decoded_parts = []
        for part, encoding in decode_header(header):
            if isinstance(part, bytes):
                decoded_parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
            else:
                decoded_parts.append(str(part))

        return ''.join(decoded_parts)

    def _get_email_body(self, email_message) -> str:
        """
        メール本文を取得

        Args:
            email_message: emailメッセージオブジェクト

        Returns:
            メール本文
        """
        body = ""

        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # 添付ファイルをスキップ
                if "attachment" in content_disposition:
                    continue

                # テキスト部分を取得
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode(errors='ignore')
                        break
                    except Exception:
                        continue
                elif content_type == "text/html" and not body:
                    try:
                        body = part.get_payload(decode=True).decode(errors='ignore')
                    except Exception:
                        continue
        else:
            try:
                body = email_message.get_payload(decode=True).decode(errors='ignore')
            except Exception:
                body = str(email_message.get_payload())

        return body

    def __enter__(self):
        """コンテキストマネージャー: 接続"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー: 切断"""
        self.disconnect()
