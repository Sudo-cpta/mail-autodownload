# deliver.py 拡張仕様書

**対象システム**：証憑運用パイプライン  
**作成日**：2026-10-09  
**承認者**：所長税理士

---

## 1. 拡張概要

### 1.1 現状

```python
# 見張りフォルダ（既存）
WATCH_FOLDERS = [
    "Downloads",
    "wsv1", 
    "ts0",
    "ts1",
    "ts2",
    "ts3",
    "事務所受付箱"  # \\192.168.0.203\shared\事務所受付箱
]
```

### 1.2 追加

```python
# 見張りフォルダ（追加）
WATCH_FOLDERS = [
    # ... 既存 ...
    "02_仕分け待ち（顧問先不明）"  # Google Drive マウント
]
```

---

## 2. マイナンバー検査機能

### 2.1 mynumber_guard.py の実装

#### 2.1.1 検出パターン

**パターン1：12桁の数字（検査用数字検証あり）**

```python
def is_valid_mynumber_checkdigit(digits: str) -> bool:
    """
    マイナンバーの検査用数字を検証
    
    アルゴリズム：
    1. 先頭から11桁目までの各桁に、以下の係数を掛ける
       6,5,4,3,2,7,6,5,4,3,2
    2. 合計を11で割った余りを求める
    3. 11 - 余り の1桁目が検査用数字（12桁目）と一致すればOK
       ※ 余りが0,1の場合は検査用数字は0
    
    Args:
        digits: 12桁の数字文字列
    
    Returns:
        検査用数字が正しければTrue
    """
    if len(digits) != 12 or not digits.isdigit():
        return False
    
    # 係数
    coefficients = [6, 5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    
    # 先頭11桁の各桁に係数を掛けて合計
    total = sum(int(digits[i]) * coefficients[i] for i in range(11))
    
    # 11で割った余り
    remainder = total % 11
    
    # 検査用数字を計算
    if remainder <= 1:
        check_digit = 0
    else:
        check_digit = 11 - remainder
    
    # 12桁目と一致するか
    return int(digits[11]) == check_digit


def contains_mynumber_pattern1(text: str) -> bool:
    """
    パターン1：12桁の数字（検査用数字検証あり）
    
    Args:
        text: 検査対象テキスト
    
    Returns:
        マイナンバーを含むならTrue
    """
    import re
    
    # 12桁の数字を検索
    pattern = r'\b\d{12}\b'
    matches = re.findall(pattern, text)
    
    for match in matches:
        if is_valid_mynumber_checkdigit(match):
            return True
    
    return False
```

**パターン2：「個人番号」の語 + 数字**

```python
def contains_mynumber_pattern2(text: str) -> bool:
    """
    パターン2：「個人番号」の語 + 数字
    
    Args:
        text: 検査対象テキスト
    
    Returns:
        マイナンバーを含むならTrue
    """
    import re
    
    # 「個人番号」の後に数字が続くパターン
    pattern = r'個人番号.*\d{4}'
    
    return bool(re.search(pattern, text))
```

**パターン3：個人番号カード／通知カードの名前**

```python
def contains_mynumber_pattern3(text: str) -> bool:
    """
    パターン3：個人番号カード／通知カードの名前
    
    Args:
        text: 検査対象テキスト
    
    Returns:
        マイナンバーを含むならTrue
    """
    keywords = ['個人番号カード', '通知カード']
    
    for keyword in keywords:
        if keyword in text:
            return True
    
    return False
```

#### 2.1.2 統合関数

```python
def contains_mynumber(file_path: str) -> tuple[bool, str]:
    """
    ファイルにマイナンバーが含まれているか検査
    
    Args:
        file_path: 検査対象ファイルのパス
    
    Returns:
        (検出フラグ, 検出パターン)
        例: (True, "12桁数字") または (False, "")
    """
    text = extract_text(file_path)
    
    if not text:
        return (False, "")
    
    # パターン1: 12桁の数字
    if contains_mynumber_pattern1(text):
        return (True, "12桁数字（検査用数字検証済み）")
    
    # パターン2: 「個人番号」の語 + 数字
    if contains_mynumber_pattern2(text):
        return (True, "個人番号の語")
    
    # パターン3: カード名称
    if contains_mynumber_pattern3(text):
        return (True, "カード名称")
    
    return (False, "")


def extract_text(file_path: str) -> str:
    """
    ファイルからテキストを抽出
    
    対応形式:
    - PDF（OCR処理）
    - 画像（JPG, PNG）（OCR処理）
    - テキストファイル（TXT, CSV）
    
    Args:
        file_path: ファイルパス
    
    Returns:
        抽出されたテキスト
    """
    import os
    from pathlib import Path
    
    ext = Path(file_path).suffix.lower()
    
    # PDF
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    
    # 画像
    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
        return extract_text_from_image(file_path)
    
    # テキスト
    elif ext in ['.txt', '.csv']:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    # 未対応形式
    else:
        return ""


def extract_text_from_pdf(file_path: str) -> str:
    """
    PDFからテキストを抽出（OCR含む）
    
    使用ライブラリ:
    - PyPDF2（テキストレイヤー抽出）
    - pdf2image + pytesseract（OCR）
    
    Args:
        file_path: PDFファイルパス
    
    Returns:
        抽出されたテキスト
    """
    try:
        import PyPDF2
        
        text = ""
        
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            
            for page in reader.pages:
                text += page.extract_text() or ""
        
        # テキストレイヤーが空の場合はOCR
        if not text.strip():
            text = extract_text_from_pdf_ocr(file_path)
        
        return text
        
    except Exception as e:
        # エラー時はOCRを試行
        return extract_text_from_pdf_ocr(file_path)


def extract_text_from_pdf_ocr(file_path: str) -> str:
    """
    PDFをOCR処理してテキストを抽出
    
    Args:
        file_path: PDFファイルパス
    
    Returns:
        抽出されたテキスト
    """
    try:
        from pdf2image import convert_from_path
        import pytesseract
        
        # PDFを画像に変換
        images = convert_from_path(file_path, dpi=300)
        
        text = ""
        for image in images:
            # OCR処理（日本語）
            text += pytesseract.image_to_string(image, lang='jpn')
        
        return text
        
    except Exception as e:
        return ""


def extract_text_from_image(file_path: str) -> str:
    """
    画像からテキストを抽出（OCR）
    
    Args:
        file_path: 画像ファイルパス
    
    Returns:
        抽出されたテキスト
    """
    try:
        import pytesseract
        from PIL import Image
        
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image, lang='jpn')
        
        return text
        
    except Exception as e:
        return ""
```

### 2.2 deliver.py への統合

```python
# deliver.py

import mynumber_guard
import logging
from pathlib import Path

def process_file_auto(file_path: Path) -> None:
    """
    ファイルを自動処理（autoモード）
    
    Args:
        file_path: 処理対象ファイルのパス
    """
    logger = logging.getLogger(__name__)
    
    try:
        # 1. マイナンバー検査
        contains_mn, pattern = mynumber_guard.contains_mynumber(str(file_path))
        
        if contains_mn:
            logger.warning(f"マイナンバー検出: {file_path.name} (パターン: {pattern})")
            send_mynumber_alert_email(file_path, pattern)
            return  # その場に残す（移動しない）
        
        # 2. 顧問先判定
        client_code = determine_client_from_filename(file_path.name)
        
        # 3. 配達
        if client_code:
            dest_folder = get_client_inbox_path(client_code)
            move_file(file_path, dest_folder)
            logger.info(f"配達: {file_path.name} -> {dest_folder}")
        else:
            # すでに 02_仕分け待ち にあるので移動不要
            logger.info(f"顧問先不明: {file_path.name} (仕分け待ちのまま)")
    
    except Exception as e:
        logger.error(f"ファイル処理エラー: {file_path.name} - {e}")


def determine_client_from_filename(filename: str) -> str:
    """
    ファイル名から顧問先コードを判定
    
    ファイル名形式: YYYYMMDD_HHMMSS_送信者メール_件名_元ファイル名
    
    Args:
        filename: ファイル名
    
    Returns:
        顧問先コード（判定できない場合は空文字列）
    """
    # ファイル名から送信者メールアドレスを抽出
    parts = filename.split('_')
    if len(parts) < 3:
        return ""
    
    sender_email = parts[2]
    
    # 顧問先マスタで照合
    return lookup_client_by_email(sender_email)


def lookup_client_by_email(sender_email: str) -> str:
    """
    送信者メールアドレスから顧問先コードを検索
    
    Args:
        sender_email: 送信者メールアドレス
    
    Returns:
        顧問先コード（見つからない場合は空文字列）
    """
    # 顧問先マスタを読み込み（実装例：CSVファイル）
    import csv
    
    master_path = Path("config/client_master.csv")
    
    if not master_path.exists():
        return ""
    
    with open(master_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # 完全一致
            if row['sender_email'].lower() == sender_email.lower():
                return row['client_code']
            
            # ドメイン一致
            sender_domain = sender_email.split('@')[-1]
            if row['sender_domain'] and row['sender_domain'].lower() == sender_domain.lower():
                return row['client_code']
    
    return ""


def send_mynumber_alert_email(file_path: Path, pattern: str) -> None:
    """
    マイナンバー検出時のアラートメールを送信
    
    Args:
        file_path: 検出されたファイルのパス
        pattern: 検出パターン
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from datetime import datetime
    
    # 設定（config.jsonから読み込む想定）
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "office@example.com"
    sender_password = "app-password"
    recipient_email = "director@example.com"  # 所長のメールアドレス
    
    # メール本文
    subject = "【マイナンバー検出】ファイルの自動配達を中止しました"
    
    body = f"""
ファイル名: {file_path.name}
保存場所: {file_path.parent}
検出日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
検出パターン: {pattern}

※ このファイルは自動配達されていません。
※ 内容を確認の上、手動で適切な場所に移動してください。

---
証憑運用パイプライン 自動配達システム
    """.strip()
    
    # メール送信
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        logging.info(f"マイナンバー検出メール送信: {recipient_email}")
        
    except Exception as e:
        logging.error(f"メール送信エラー: {e}")
```

---

## 3. 顧問先マスタ

### 3.1 フォーマット（CSV）

```csv
client_code,client_name,sender_email,sender_domain,notes
0000,事務所,office@example.com,example.com,自事務所
0001,顧問先A,billing@company-a.co.jp,company-a.co.jp,A社請求書
0002,顧問先B,invoice@company-b.com,company-b.com,B社請求書
```

### 3.2 配置場所

```
H:\マイドライブ\04_業務ツール開発\20_会計・税務\証憑運用パイプライン\config\client_master.csv
```

---

## 4. 必要ライブラリ

### 4.1 Python ライブラリ

```bash
# OCR処理
pip install pytesseract
pip install pdf2image
pip install Pillow

# PDF処理
pip install PyPDF2

# 画像処理
pip install opencv-python
```

### 4.2 システムツール

- **Tesseract OCR**：https://github.com/tesseract-ocr/tesseract
  - 日本語データのインストール：`tessdata/jpn.traineddata`
  - Windows: インストーラーでインストール
  - パスを環境変数に追加

---

## 5. テスト手順

### 5.1 マイナンバー検査テスト

```python
# test_mynumber_guard.py

import mynumber_guard

def test_valid_mynumber():
    """有効なマイナンバーを検出"""
    text = "個人番号: 123456789012"  # ※ ダミー数字
    result, pattern = mynumber_guard.contains_mynumber_pattern2(text)
    assert result == True
    print("✓ パターン2検出成功")

def test_invalid_mynumber():
    """無効なマイナンバーは検出しない"""
    text = "電話番号: 090-1234-5678"
    result, pattern = mynumber_guard.contains_mynumber(text)
    assert result == False
    print("✓ 誤検出なし")

if __name__ == "__main__":
    test_valid_mynumber()
    test_invalid_mynumber()
    print("全テスト完了")
```

---

## 6. 運用開始前チェックリスト

- [ ] Tesseract OCR インストール済み
- [ ] Python ライブラリインストール済み
- [ ] 顧問先マスタ作成済み（`config/client_master.csv`）
- [ ] Google Drive マウント済み（`G:\共有ドライブ\須戸美敦税理士事務所\`）
- [ ] メール送信設定完了（SMTP設定）
- [ ] テスト実施済み（ダミーデータ）
- [ ] 所長承認済み

---

## 付録：検査用数字の計算例

```
マイナンバー: 123456789012

1. 係数との積
   1×6 + 2×5 + 3×4 + 4×3 + 5×2 + 6×7 + 7×6 + 8×5 + 9×4 + 10×3 + 11×2
   = 6 + 10 + 12 + 12 + 10 + 42 + 42 + 40 + 36 + 30 + 22
   = 262

2. 11で割った余り
   262 % 11 = 9

3. 検査用数字
   11 - 9 = 2

4. 検証
   12桁目が 2 ならOK（この例では一致しない → 無効なマイナンバー）
```
