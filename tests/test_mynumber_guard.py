"""
マイナンバー検査モジュールのテスト

ダミーデータを使用してマイナンバー検出機能をテスト

@author 須戸美敦税理士事務所
@date 2026-10-11
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src import mynumber_guard


def test_checkdigit_validation():
    """検査用数字の検証テスト"""
    print("=" * 60)
    print("テスト1: 検査用数字の検証")
    print("=" * 60)

    # 有効なマイナンバー（ダミー）
    # 注: これは実在しない架空の番号です
    valid_numbers = [
        "123456789012",  # ダミー番号1
        "987654321098",  # ダミー番号2
    ]

    # 無効なマイナンバー
    invalid_numbers = [
        "123456789013",  # 検査用数字が間違っている
        "000000000000",  # オール0
        "111111111111",  # オール1
    ]

    print("\n有効なマイナンバーの検証:")
    for number in valid_numbers:
        is_valid = mynumber_guard.is_valid_mynumber_checkdigit(number)
        # 実際には検査用数字が正しくないダミー番号なので、Falseになることを期待
        print(f"  {number}: {'✓ 有効' if is_valid else '✗ 無効'}")

    print("\n無効なマイナンバーの検証:")
    for number in invalid_numbers:
        is_valid = mynumber_guard.is_valid_mynumber_checkdigit(number)
        print(f"  {number}: {'✓ 有効' if is_valid else '✗ 無効（期待通り）'}")

    print()


def test_pattern1():
    """パターン1: 12桁の数字検出テスト"""
    print("=" * 60)
    print("テスト2: パターン1（12桁の数字）")
    print("=" * 60)

    test_cases = [
        ("123456789012", True, "ハイフンなし12桁"),
        ("1234-5678-9012", True, "ハイフン区切り"),
        ("1234 5678 9012", True, "スペース区切り"),
        ("090-1234-5678", False, "電話番号（11桁）"),
        ("12345678", False, "8桁の数字"),
    ]

    for text, expected, description in test_cases:
        result = mynumber_guard.contains_mynumber_pattern1(text)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {description}: '{text}' -> {result}")

    print()


def test_pattern2():
    """パターン2: 「個人番号」の語検出テスト"""
    print("=" * 60)
    print("テスト3: パターン2（個人番号の語）")
    print("=" * 60)

    test_cases = [
        ("個人番号: 1234-5678-9012", True, "個人番号の語あり"),
        ("個人番号 1234", True, "個人番号 + 4桁"),
        ("マイナンバー: 1234-5678-9012", False, "マイナンバーの語（パターン2では検出しない）"),
        ("法人番号: 1234567890123", False, "法人番号"),
    ]

    for text, expected, description in test_cases:
        result = mynumber_guard.contains_mynumber_pattern2(text)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {description}: '{text}' -> {result}")

    print()


def test_pattern3():
    """パターン3: カード名称検出テスト"""
    print("=" * 60)
    print("テスト4: パターン3（カード名称）")
    print("=" * 60)

    test_cases = [
        ("個人番号カードのコピー", True, "個人番号カード"),
        ("通知カードを添付します", True, "通知カード"),
        ("マイナンバーカードを提出", True, "マイナンバーカード"),
        ("クレジットカード番号", False, "クレジットカード"),
    ]

    for text, expected, description in test_cases:
        result = mynumber_guard.contains_mynumber_pattern3(text)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {description}: '{text}' -> {result}")

    print()


def test_file_detection():
    """ファイル検出テスト"""
    print("=" * 60)
    print("テスト5: ファイル検出")
    print("=" * 60)

    # テストファイルを作成
    test_dir = Path(__file__).parent / "test_data"
    test_dir.mkdir(exist_ok=True)

    # ケース1: マイナンバーを含むテキストファイル
    file1 = test_dir / "test_mynumber.txt"
    with open(file1, 'w', encoding='utf-8') as f:
        f.write("【重要】個人番号カードのコピー\n")
        f.write("個人番号: 1234-5678-9012\n")

    # ケース2: マイナンバーを含まないテキストファイル
    file2 = test_dir / "test_safe.txt"
    with open(file2, 'w', encoding='utf-8') as f:
        f.write("請求書\n")
        f.write("合計金額: 10,000円\n")

    # ケース3: 電話番号のみ（マイナンバーではない）
    file3 = test_dir / "test_phone.txt"
    with open(file3, 'w', encoding='utf-8') as f:
        f.write("連絡先\n")
        f.write("電話番号: 090-1234-5678\n")

    test_files = [
        (file1, True, "マイナンバーあり"),
        (file2, False, "マイナンバーなし"),
        (file3, False, "電話番号のみ"),
    ]

    for file_path, expected, description in test_files:
        contains, pattern = mynumber_guard.contains_mynumber(str(file_path))
        status = "✓" if contains == expected else "✗"
        result_str = f"検出（{pattern}）" if contains else "検出なし"
        print(f"  {status} {description}: {file_path.name} -> {result_str}")

    # テストファイルを削除
    for file_path, _, _ in test_files:
        if file_path.exists():
            file_path.unlink()

    if test_dir.exists() and not any(test_dir.iterdir()):
        test_dir.rmdir()

    print()


def test_integration():
    """統合テスト"""
    print("=" * 60)
    print("テスト6: 統合テスト")
    print("=" * 60)

    # 実際のワークフローをシミュレート
    test_dir = Path(__file__).parent / "test_data"
    test_dir.mkdir(exist_ok=True)

    # シナリオ: メールから保存された請求書ファイル
    invoice_file = test_dir / "20261011_100000_billing@example.com_請求書_invoice.txt"
    with open(invoice_file, 'w', encoding='utf-8') as f:
        f.write("株式会社サンプル\n")
        f.write("請求書\n")
        f.write("合計: 50,000円\n")

    # シナリオ: マイナンバー付きファイル（誤って送信された）
    mynumber_file = test_dir / "20261011_100100_sender@example.com_資料_document.txt"
    with open(mynumber_file, 'w', encoding='utf-8') as f:
        f.write("従業員情報\n")
        f.write("個人番号: 1234-5678-9012\n")

    print("\nシナリオ1: 通常の請求書ファイル")
    contains, pattern = mynumber_guard.contains_mynumber(str(invoice_file))
    if not contains:
        print(f"  ✓ {invoice_file.name}")
        print(f"    → 配達可能（マイナンバー検出なし）")
    else:
        print(f"  ✗ {invoice_file.name}")
        print(f"    → 配達中止（{pattern}）")

    print("\nシナリオ2: マイナンバー付きファイル")
    contains, pattern = mynumber_guard.contains_mynumber(str(mynumber_file))
    if contains:
        print(f"  ✓ {mynumber_file.name}")
        print(f"    → 配達中止（{pattern}）")
        print(f"    → 所長にメール通知を送信")
    else:
        print(f"  ✗ {mynumber_file.name}")
        print(f"    → マイナンバー検出失敗（期待: 検出）")

    # クリーンアップ
    if invoice_file.exists():
        invoice_file.unlink()
    if mynumber_file.exists():
        mynumber_file.unlink()
    if test_dir.exists() and not any(test_dir.iterdir()):
        test_dir.rmdir()

    print()


def main():
    """テストメイン関数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "マイナンバー検査モジュール テスト" + " " * 13 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    try:
        test_checkdigit_validation()
        test_pattern1()
        test_pattern2()
        test_pattern3()
        test_file_detection()
        test_integration()

        print("=" * 60)
        print("✓ 全テスト完了")
        print("=" * 60)
        print()
        print("注意:")
        print("- PDFや画像ファイルの検査には PyPDF2、pytesseract が必要です")
        print("- インストール方法: pip install PyPDF2 pytesseract Pillow pdf2image")
        print("- Tesseract OCR のインストールも必要です")
        print()

        return 0

    except Exception as e:
        print(f"\n✗ テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
