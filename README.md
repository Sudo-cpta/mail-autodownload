# 請求書自動ダウンロードシステム

特定のメールアドレスから受信したメールに記載されたURLにログインして、請求書を自動ダウンロードするシステムです。

## 機能

- IMAPを使用してメールボックスを監視
- 特定の送信者からのメールを検出
- メール本文からURLを抽出
- スプレッドシートで管理された認証情報を使用してログイン
- 請求書PDFを自動ダウンロード
- 指定フォルダに整理して保存

## 必要要件

- Python 3.8以上
- Chromiumブラウザ（Playwrightが自動インストール）

## インストール

```bash
pip install -r requirements.txt
playwright install chromium
```

## 設定

### 1. メール設定 (config.json)

`config.example.json`を`config.json`にコピーして編集：

```json
{
  "email": {
    "imap_server": "imap.gmail.com",
    "imap_port": 993,
    "email_address": "your-email@gmail.com",
    "password": "your-app-password"
  },
  "download": {
    "folder": "./downloads",
    "file_pattern": "invoice*.pdf"
  }
}
```

### 2. 認証情報スプレッドシート (credentials.csv)

`credentials.example.csv`を`credentials.csv`にコピーして編集：

```csv
sender_email,login_url,username,password,notes
billing@example.com,https://example.com/login,user@example.com,password123,Example社の請求書
```

## 使用方法

### 一度だけ実行

```bash
python src/main.py
```

### 定期実行（cron設定例）

毎日午前9時に実行：
```bash
0 9 * * * cd /path/to/mail-autodownload && /usr/bin/python3 src/main.py
```

## セキュリティ上の注意

- `config.json`と`credentials.csv`には機密情報が含まれるため、Gitにコミットしないでください
- `.gitignore`で除外されています
- Gmailを使用する場合は、アプリパスワードを使用してください

## トラブルシューティング

### Gmailで接続できない場合

1. Googleアカウントで2段階認証を有効化
2. アプリパスワードを生成して使用
3. IMAP設定が有効になっているか確認

### ログインが失敗する場合

- `credentials.csv`のログイン情報が正しいか確認
- ウェブサイトのログインフォームの構造が変わっていないか確認
- `src/web_automation.py`のセレクタを調整する必要がある場合があります

## ライセンス

MIT License
