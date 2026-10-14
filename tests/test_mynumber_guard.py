"""マイナンバー検査モジュールのテスト（ダミーデータのみ・合否判定あり）"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src import mynumber_guard as g

# 検査用数字が合う架空の12桁（実在の番号ではない）
VALID1 = "123456789018"
VALID2 = "987654321093"
# 検査用数字が合わない12桁
INVALID = "123456789012"


class CheckDigitTest(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(g.is_valid_mynumber_checkdigit(VALID1))
        self.assertTrue(g.is_valid_mynumber_checkdigit(VALID2))

    def test_invalid(self):
        self.assertFalse(g.is_valid_mynumber_checkdigit(INVALID))
        self.assertFalse(g.is_valid_mynumber_checkdigit("12345"))
        self.assertFalse(g.is_valid_mynumber_checkdigit("12345678901a"))


class Pattern1Test(unittest.TestCase):
    def test_detect(self):
        self.assertTrue(g.contains_mynumber_pattern1(VALID1))
        self.assertTrue(g.contains_mynumber_pattern1("1234-5678-9018"))
        self.assertTrue(g.contains_mynumber_pattern1("1234 5678 9018"))

    def test_no_detect(self):
        self.assertFalse(g.contains_mynumber_pattern1(INVALID))
        self.assertFalse(g.contains_mynumber_pattern1("090-1234-5678"))
        self.assertFalse(g.contains_mynumber_pattern1("12345678"))


class Pattern23Test(unittest.TestCase):
    def test_pattern2(self):
        self.assertTrue(g.contains_mynumber_pattern2("個人番号: 1234-5678-9012"))
        self.assertFalse(g.contains_mynumber_pattern2("法人番号: 1234567890123"))

    def test_pattern3(self):
        for word in ("個人番号カード", "通知カード", "マイナンバーカード"):
            self.assertTrue(g.contains_mynumber_pattern3(f"{word}のコピー"))
        self.assertFalse(g.contains_mynumber_pattern3("クレジットカード"))


class FileTest(unittest.TestCase):
    def _check(self, text):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.txt"
            p.write_text(text, encoding="utf-8")
            return g.contains_mynumber(str(p))

    def test_detected_file(self):
        self.assertTrue(self._check(f"従業員\n{VALID1}\n")[0])
        self.assertTrue(self._check("個人番号: 1234")[0])

    def test_safe_file(self):
        self.assertFalse(self._check("請求書 合計 10,000円")[0])
        self.assertFalse(self._check("電話 090-1234-5678")[0])


if __name__ == "__main__":
    unittest.main()
