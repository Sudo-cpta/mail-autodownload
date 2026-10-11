# セットアップガイド：メール請求書自動保存（段階4）

**作成日**：2026-10-11  
**対象者**：システム管理者・所長

---

## 1. 環境準備

### 1.1 必要なソフトウェア

#### Python環境
- Python 3.8以上
- pip（Pythonパッケージマネージャー）

#### Tesseract OCR（PDFや画像からのマイナンバー検出に必要）

**Windows の場合**：
```powershell
# Tesseract OCR インストーラーをダウンロード
# https://github.com/UB-Mannheim/tesseract/wiki

# インストール後、環境変数に追加
# C:\Program Files\Tesseract-OCR\tesseract.exe
```

**日本語データのインストール**：
```powershell
# Tesseract のインストールフォルダ内の tessdata フォルダに配置
# https://github.com/tesseract-ocr/tessdata/raw/main/jpn.traineddata
```

#### Google Drive デスクトップアプリ
- 共有ドライブをローカルにマウントするために必要
- ダウンロード：https://www.google.com/drive/download/

---

## 2. Python ライブラリのインストール

### 2.1 依存パッケージのインストール

```bash
cd /path/to/mail-autodownload
pip install -r requirements.txt
```

### 2.2 playwright のセットアップ（GASのみの場合は不要）

```bash
playwright install chromium
```

---

## 3. Google Apps Script（GAS）の設定

### 3.1 スプレッドシート作成

1. Google スプレッドシートを新規作成
2. シート名を「設定」にする
3. 以下の内容を入力：

| 設定項目 | 設定値 |
|---------|--------|
| CHECK_DAYS | 7 |
| DRIVE_FOLDER_ID | （Google DriveのフォルダIDを入力） |
| LABEL_PROCESSED | 処理済み |
| NOTIFY_EMAIL | （所長のメールアドレス） |

#### フォルダIDの取得方法

1. Google Drive で `02_仕分け待ち（顧問先不明）` フォルダを開く
2. URLから `folders/` の後の文字列をコピー
   - 例：`https://drive.google.com/drive/folders/1ABC...XYZ`
   - フォルダID：`1ABC...XYZ`

### 3.2 GAS スクリプトの作成

1. スプレッドシートから `拡張機能` → `Apps Script` を開く
2. `gas/gmail_invoice_saver.gs` の内容をコピー＆ペースト
3. スクリプト内の `CONFIG_SHEET_ID` を、作成したスプレッドシートのIDに置き換える
   - スプレッドシートのURL：`https://docs.google.com/spreadsheets/d/SHEET_ID/...`

### 3.3 トリガーの設定

1. GAS エディタで `トリガー` アイコン（時計マーク）をクリック
2. `トリガーを追加` をクリック
3. 以下の設定：
   - 実行する関数：`main`
   - イベントのソース：`時間主導型`
   - 時間ベースのトリガー：`時間ベースのタイマー`
   - 時間の間隔：`1時間おき`
4. `保存` をクリック

### 3.4 テスト実行

1. GAS エディタで `test` 関数を選択
2. `実行` ボタンをクリック
3. 初回実行時は権限の承認が必要
4. ログを確認して、メール検索が動作することを確認

---

## 4. deliver.py の設定

### 4.1 顧問先マスタの作成

`config/client_master.csv` を作成：

```csv
client_code,client_name,sender_email,sender_domain,notes
0000,事務所,office@example.com,example.com,自事務所
0001,顧問先A,billing@company-a.co.jp,company-a.co.jp,A社請求書
0002,顧問先B,invoice@company-b.com,company-b.com,B社請求書
```

**配置場所**：
```
H:\マイドライブ\04_業務ツール開発\20_会計・税務\証憑運用パイプライン\config\client_master.csv
```

### 4.2 Google Drive のマウント

1. Google Drive デスクトップアプリをインストール
2. 共有ドライブ「須戸美敦税理士事務所」をマウント
3. マウントパスを確認（例：`G:\共有ドライブ\須戸美敦税理士事務所\`）

### 4.3 deliver.py への統合

**注意**：deliver.py の実装は、証憑運用パイプラインのリポジトリで行います。

1. `src/mynumber_guard.py` を証憑運用パイプラインの `src/` にコピー
2. `deliver.py` に以下を追加：

```python
import mynumber_guard

# 見張りフォルダに追加
WATCH_FOLDERS = [
    # ... 既存 ...
    r"G:\共有ドライブ\須戸美敦税理士事務所\02_仕分け待ち（顧問先不明）"
]

# process_file_auto 関数内でマイナンバー検査を追加
def process_file_auto(file_path: Path) -> None:
    # 1. マイナンバー検査
    contains_mn, pattern = mynumber_guard.contains_mynumber(str(file_path))
    
    if contains_mn:
        logger.warning(f"マイナンバー検出: {file_path.name} (パターン: {pattern})")
        send_mynumber_alert_email(file_path, pattern)
        return  # その場に残す
    
    # 2. 顧問先判定・配達（既存ロジック）
    # ...
```

### 4.4 メール通知の設定

`deliver.py` に以下の関数を追加（`DELIVER_PY_SPEC.md` 参照）：

```python
def send_mynumber_alert_email(file_path: Path, pattern: str) -> None:
    # SMTP設定
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "office@example.com"  # 実際のメールアドレス
    sender_password = "app-password"      # アプリパスワード
    recipient_email = "director@example.com"  # 所長のメールアドレス
    
    # メール送信ロジック
    # ...
```

---

## 5. テスト手順

### 5.1 マイナンバー検査のテスト

```bash
cd /path/to/mail-autodownload
python tests/test_mynumber_guard.py
```

**期待結果**：
```
✓ 全テスト完了
```

### 5.2 ダミーファイルでのテスト

1. `02_仕分け待ち（顧問先不明）` にダミーファイルを配置
   - ファイル名：`20261011_100000_test@example.com_テスト請求書_invoice.txt`
   - 内容：マイナンバーを含まない通常のテキスト

2. deliver.py を手動実行
   ```bash
   python deliver.py auto
   ```

3. ファイルが正しく配達されることを確認

### 5.3 マイナンバー検出のテスト

1. マイナンバーを含むダミーファイルを配置
   - ファイル名：`20261011_100100_test@example.com_テスト資料_document.txt`
   - 内容：`個人番号: 1234-5678-9012`

2. deliver.py を手動実行

3. 以下を確認：
   - ファイルがその場に残っている
   - 所長にメール通知が届いている

---

## 6. 本番稼働

### 6.1 事前確認チェックリスト

- [ ] GAS スクリプトがデプロイ済み
- [ ] GAS トリガーが設定済み（1時間ごと）
- [ ] Google Drive フォルダ構成が整備済み
- [ ] 顧問先マスタが作成済み
- [ ] mynumber_guard.py が deliver.py に統合済み
- [ ] メール通知設定が完了済み
- [ ] ダミーデータでのテストが完了済み
- [ ] 所長の最終承認済み

### 6.2 稼働開始

1. タスクスケジューラで deliver.py を定期実行
   - 実行間隔：5分おき
   - 実行時間：平日 8:00〜19:00

2. GAS の自動実行を有効化（トリガーが設定済みなら自動実行）

### 6.3 初期監視（最初の1週間）

- 毎日ログを確認
- マイナンバー検出通知の頻度を確認
- 誤検出・見逃しがないか確認

---

## 7. 運用

### 7.1 日次運用

- **自動実行**（人手不要）
- **マイナンバー検出通知が来た場合**：
  1. ファイルの内容を確認
  2. 本当にマイナンバーが含まれている場合：手動で適切に処理
  3. 誤検出の場合：ログに記録し、必要に応じてパターンを調整

### 7.2 週次運用

- `02_仕分け待ち（顧問先不明）` フォルダを確認
- 顧問先不明ファイルを手動で振り分け

### 7.3 月次運用

- ログ確認
- エラー件数確認
- 顧問先マスタの更新（新規顧問先・送信元変更）

---

## 8. トラブルシューティング

### 8.1 GAS でエラーが発生する

**症状**：GAS の実行ログにエラーが表示される

**対処**：
1. エラーメッセージを確認
2. スプレッドシートの設定が正しいか確認
3. Google Drive のフォルダIDが正しいか確認

### 8.2 マイナンバーが検出されない

**症状**：マイナンバーを含むファイルが配達されてしまう

**対処**：
1. `python tests/test_mynumber_guard.py` でテストを実行
2. OCRライブラリがインストールされているか確認
3. Tesseract OCR がインストールされているか確認
4. ログでテキスト抽出の結果を確認

### 8.3 誤検出が多い

**症状**：マイナンバーではない数字が検出される

**対処**：
1. ログで検出パターンを確認
2. 必要に応じて検出パターンを調整
3. 所長と相談して、検出精度と見逃しリスクのバランスを調整

---

## 9. セキュリティ上の注意

### 9.1 機密情報の管理

- ❌ `config.json`、`client_master.csv` をGitにコミットしない
- ✅ パスワードは環境変数または設定ファイルで管理
- ✅ 設定ファイルのアクセス権限を制限

### 9.2 マイナンバーの取り扱い

- ❌ マイナンバーを外部（Claude API・Claude Code）に送信しない
- ✅ ローカル検査（deliver.py）で完結
- ✅ 検出したファイルは自動配達しない
- ✅ 所長に即座に通知

### 9.3 Gmail 読み取り専用原則

- ✅ メールの読み取り：許可
- ✅ ラベルの追加：許可
- ❌ メールの削除：禁止
- ❌ メールの送信・転送：禁止

---

## 10. 参考資料

- `IMPLEMENTATION_SPEC.md`：実装仕様書
- `DELIVER_PY_SPEC.md`：deliver.py 拡張仕様書
- `gas/gmail_invoice_saver.gs`：GAS スクリプト
- `src/mynumber_guard.py`：マイナンバー検査モジュール
- `tests/test_mynumber_guard.py`：テストスクリプト

---

## 付録：よくある質問

### Q1. GAS の実行頻度を変更したい

A1. GAS エディタのトリガー設定で変更できます。現在は1時間おきですが、30分おき、15分おきなども選択可能です。

### Q2. マイナンバー検出の感度を調整したい

A2. `src/mynumber_guard.py` の検出パターンを調整してください。ただし、見逃しを防ぐため、現在の設定は保守的（やや厳しめ）になっています。

### Q3. 顧問先マスタを Excel で管理したい

A3. 可能です。`client_master.xlsx` を作成し、deliver.py で読み込むコードを追加してください（pandas を使用）。

### Q4. メール通知の内容を変更したい

A4. `deliver.py` の `send_mynumber_alert_email` 関数を編集してください。

---

**作成者**：須戸美敦税理士事務所  
**バージョン**：1.0.0  
**最終更新**：2026-10-11
