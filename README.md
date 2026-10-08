# 請求書自動ダウンロードシステム

> **⚠️ アーカイブ済み - 試作・参考実装**
> 
> このプロジェクトは試作として実装されましたが、所長の決定により、メール請求書の自動保存は「証憑運用パイプライン」の段階4として、既存のGAS「Gmail請求書自動保存」を拡張する形で進めることになりました（2026-10-06決定）。
> 
> - **実装方針**：GASベースで顧問先マスタと連携
> - **保存先**：各顧問先の `08_受領資料\00_受信箱`
> - **前提条件**：電子帳簿保存法の措置決定後に段階4開始
> 
> このリポジトリは参考資料として保存されています。

---

## 概要

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
