"""
マイナンバー検査モジュール

証憑運用パイプライン 段階4
個人番号（マイナンバー）を検出し、外部への送信を防止する

@author 須戸美敦税理士事務所
@date 2026-10-11
"""

import re
import logging
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


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
    # 12桁の数字を検索
    # ハイフン区切り（123-4567-8901）やスペース区切りも考慮
    # 区切り文字を除去してから検証
    pattern = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b|\b\d{12}\b'
    matches = re.findall(pattern, text)

    for match in matches:
        # 区切り文字を除去
        digits = re.sub(r'[-\s]', '', match)

        if len(digits) == 12 and is_valid_mynumber_checkdigit(digits):
            logger.warning("マイナンバー検出（パターン1）: 12桁数字（番号はログに出力しない）")
            return True

    return False


def contains_mynumber_pattern2(text: str) -> bool:
    """
    パターン2：「個人番号」の語 + 数字

    Args:
        text: 検査対象テキスト

    Returns:
        マイナンバーを含むならTrue
    """
    # 「個人番号」の後に数字が続くパターン
    pattern = r'個人番号.*?\d{4}'

    if re.search(pattern, text):
        logger.warning("マイナンバー検出（パターン2）: 個人番号の語")
        return True

    return False


def contains_mynumber_pattern3(text: str) -> bool:
    """
    パターン3：個人番号カード／通知カードの名前

    Args:
        text: 検査対象テキスト

    Returns:
        マイナンバーを含むならTrue
    """
    keywords = ['個人番号カード', '通知カード', 'マイナンバーカード']

    for keyword in keywords:
        if keyword in text:
            logger.warning(f"マイナンバー検出（パターン3）: {keyword}")
            return True

    return False


def extract_text_from_pdf(file_path: str) -> str:
    """
    PDFからテキストを抽出（OCR含む）

    Args:
        file_path: PDFファイルパス

    Returns:
        抽出されたテキスト
    """
    text = ""

    try:
        import PyPDF2

        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)

            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        logger.debug(f"PDFテキスト抽出: {len(text)} 文字")

    except ImportError:
        logger.warning("PyPDF2がインストールされていません。PDFの検査をスキップします。")
        logger.warning("インストール方法: pip install PyPDF2")
    except Exception as e:
        logger.error(f"PDF読み込みエラー: {e}")

    # テキストレイヤーが空の場合はOCRを試行
    if not text.strip():
        logger.info("PDFにテキストレイヤーがありません。OCRを試行します。")
        text = extract_text_from_pdf_ocr(file_path)

    return text


def extract_text_from_pdf_ocr(file_path: str) -> str:
    """
    PDFをOCR処理してテキストを抽出

    Args:
        file_path: PDFファイルパス

    Returns:
        抽出されたテキスト
    """
    text = ""

    try:
        from pdf2image import convert_from_path
        import pytesseract

        # PDFを画像に変換
        images = convert_from_path(file_path, dpi=300)

        for i, image in enumerate(images):
            # OCR処理（日本語）
            page_text = pytesseract.image_to_string(image, lang='jpn')
            text += page_text + "\n"
            logger.debug(f"OCR処理: ページ {i+1}/{len(images)}")

        logger.debug(f"OCRテキスト抽出: {len(text)} 文字")

    except ImportError:
        logger.warning("pdf2image または pytesseract がインストールされていません。")
        logger.warning("インストール方法: pip install pdf2image pytesseract")
        logger.warning("Tesseract OCR のインストールも必要です。")
    except Exception as e:
        logger.error(f"OCR処理エラー: {e}")

    return text


def extract_text_from_image(file_path: str) -> str:
    """
    画像からテキストを抽出（OCR）

    Args:
        file_path: 画像ファイルパス

    Returns:
        抽出されたテキスト
    """
    text = ""

    try:
        import pytesseract
        from PIL import Image

        image = Image.open(file_path)
        text = pytesseract.image_to_string(image, lang='jpn')

        logger.debug(f"画像OCR: {len(text)} 文字")

    except ImportError:
        logger.warning("pytesseract または Pillow がインストールされていません。")
        logger.warning("インストール方法: pip install pytesseract Pillow")
    except Exception as e:
        logger.error(f"画像OCRエラー: {e}")

    return text


def extract_text_from_file(file_path: str) -> str:
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
    path = Path(file_path)
    ext = path.suffix.lower()

    # PDF
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)

    # 画像
    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
        return extract_text_from_image(file_path)

    # テキスト
    elif ext in ['.txt', '.csv']:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            logger.debug(f"テキストファイル読み込み: {len(text)} 文字")
            return text
        except Exception as e:
            logger.error(f"テキストファイル読み込みエラー: {e}")
            return ""

    # 未対応形式
    else:
        logger.debug(f"未対応のファイル形式: {ext}")
        return ""


def contains_mynumber(file_path: str) -> Tuple[bool, str]:
    """
    ファイルにマイナンバーが含まれているか検査

    Args:
        file_path: 検査対象ファイルのパス

    Returns:
        (検出フラグ, 検出パターン)
        例: (True, "12桁数字（検査用数字検証済み）") または (False, "")
    """
    if not Path(file_path).exists():
        logger.error(f"ファイルが存在しません: {file_path}")
        return (False, "")

    # テキストを抽出
    text = extract_text_from_file(file_path)

    if not text:
        logger.debug("テキストが抽出できませんでした。検査をスキップします。")
        return (False, "")

    # パターン1: 12桁の数字（検査用数字検証済み）
    if contains_mynumber_pattern1(text):
        return (True, "12桁数字（検査用数字検証済み）")

    # パターン2: 「個人番号」の語 + 数字
    if contains_mynumber_pattern2(text):
        return (True, "個人番号の語")

    # パターン3: カード名称
    if contains_mynumber_pattern3(text):
        return (True, "カード名称")

    logger.debug("マイナンバーは検出されませんでした。")
    return (False, "")


def check_directory(directory: str) -> list:
    """
    ディレクトリ内の全ファイルをマイナンバー検査

    Args:
        directory: 検査対象ディレクトリ

    Returns:
        マイナンバーを含むファイルのリスト [(ファイルパス, 検出パターン), ...]
    """
    dir_path = Path(directory)

    if not dir_path.exists():
        logger.error(f"ディレクトリが存在しません: {directory}")
        return []

    detected_files = []

    for file_path in dir_path.rglob('*'):
        if file_path.is_file():
            contains, pattern = contains_mynumber(str(file_path))

            if contains:
                detected_files.append((str(file_path), pattern))
                logger.warning(f"マイナンバー検出: {file_path.name} ({pattern})")

    return detected_files


if __name__ == "__main__":
    # コマンドライン実行時のテスト
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if len(sys.argv) < 2:
        print("使用方法: python mynumber_guard.py <ファイルパス または ディレクトリパス>")
        sys.exit(1)

    target = sys.argv[1]
    target_path = Path(target)

    if target_path.is_file():
        # ファイル検査
        contains, pattern = contains_mynumber(target)

        if contains:
            print(f"⚠️ マイナンバー検出: {pattern}")
            sys.exit(1)
        else:
            print("✓ マイナンバーは検出されませんでした")
            sys.exit(0)

    elif target_path.is_dir():
        # ディレクトリ検査
        detected_files = check_directory(target)

        if detected_files:
            print(f"⚠️ {len(detected_files)} 件のファイルでマイナンバーを検出:")
            for file_path, pattern in detected_files:
                print(f"  - {file_path} ({pattern})")
            sys.exit(1)
        else:
            print("✓ マイナンバーは検出されませんでした")
            sys.exit(0)

    else:
        print(f"エラー: {target} はファイルでもディレクトリでもありません")
        sys.exit(1)
