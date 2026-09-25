"""就活ボードの解析テスト。標準ライブラリだけで動く。

実行: python3 -m unittest discover apps/job-hunt-board/tests
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))
import parse  # noqa: E402

WORKSPACE = APP_DIR.parents[1]

MASTER_FIXTURE = """# テスト用

## 9月

| 日 | 案件 | 出典 |
|---|---|---|
| 9/13 23:59 | ✅提出済み KDDI 技術系IS 事後アンケート | メール確認済み |
| 9/14 | ❌未提出 ダイフク 3days（ES+コース予約の両方） | メール確認済み |
| 9/15 | リクルート エンジニア職 | ナビ |
| 9/25 9:00 | 三菱UFJ銀行 トレードビジネスWS（ES+Web適性A/B+顔写真） | メール確認済み |

## 11月以降

- 11/4 リクルート データスペシャリスト IS【ナビ】
- 12月 三菱UFJ信託 5daysファンドマネジメント【メール確認済み】

## 併願制限・前提条件（重要）

- **EY SC**：国内とBCFは併願不可

## 既に応募済み・関係がある企業

Speee（本選考エントリー済）、マネーフォワード（サマーIS選考参加済）
"""

NAVI_FIXTURE = """# テスト用

## 9月中の優先候補

| 締切 | 企業・募集 | 状態 |
|---|---|---|
| 9/25 | 三菱UFJ銀行 トレードビジネスWS | 締め切りナビのみ。マイページで確認 |
| 9/28 | マネーフォワード ビジネス職 オフィスツアー | 今回の再収集で追加 |

## 日付が食い違うもの

| 企業・募集 | 締め切りナビ | 本人宛メール |
|---|---:|---:|
| アクセンチュア 本選考 | 10/9 | 10/8 10:00 |
"""


class ParseFixtureTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "private/job-hunt/2026-09-13").mkdir(parents=True)
        (self.root / "private/job-hunt/2026-09-16").mkdir(parents=True)
        (self.root / parse.SOURCES[0]["file"]).write_text(MASTER_FIXTURE, encoding="utf-8")
        (self.root / parse.SOURCES[1]["file"]).write_text(NAVI_FIXTURE, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_master_rows(self):
        items, rules, applied, legend, warnings = parse.parse_master(
            self.root / parse.SOURCES[0]["file"]
        )
        self.assertEqual(warnings, [])
        by_title = {i["title"]: i for i in items}
        self.assertEqual(by_title["KDDI 技術系IS 事後アンケート"]["status"], "done")
        self.assertEqual(by_title["KDDI 技術系IS 事後アンケート"]["date"], "2026-09-13")
        self.assertEqual(by_title["KDDI 技術系IS 事後アンケート"]["time"], "23:59")
        self.assertEqual(by_title["ダイフク 3days（ES+コース予約の両方）"]["status"], "missed")
        self.assertEqual(by_title["リクルート エンジニア職"]["source"], "navi")
        self.assertEqual(rules, ["**EY SC**：国内とBCFは併願不可"])
        self.assertEqual(len(applied), 2)

    def test_bullets_and_month_only(self):
        items, *_ = parse.parse_master(self.root / parse.SOURCES[0]["file"])
        by_title = {i["title"]: i for i in items}
        self.assertEqual(by_title["リクルート データスペシャリスト IS"]["date"], "2026-11-04")
        december = by_title["三菱UFJ信託 5daysファンドマネジメント"]
        self.assertIsNone(december["date"])
        self.assertIn("12月中", december["notes"])

    def test_conflict_uses_email_date(self):
        items, conflicts, warnings = parse.parse_navi(self.root / parse.SOURCES[1]["file"])
        self.assertEqual(warnings, [])
        self.assertEqual(len(conflicts), 1)
        conflict = conflicts[0]
        self.assertEqual(conflict["date"], "2026-10-08")
        self.assertEqual(conflict["conflict"]["navi"], "2026-10-09")

    def test_merge_collapses_and_marks_mixed(self):
        data = parse.load(self.root)
        keys = [(i["date"], i["firm"]) for i in data["items"]]
        self.assertEqual(len(keys), len(set(keys)), "同じ日・同じ会社が2件残っている")
        mufg = [i for i in data["items"] if i["firm"] == "三菱UFJ銀行"]
        self.assertEqual(len(mufg), 1)
        self.assertEqual(mufg[0]["source"], "mixed")

    def test_every_item_has_required_fields(self):
        data = parse.load(self.root)
        self.assertTrue(data["items"])
        for item in data["items"]:
            self.assertTrue(item["id"])
            self.assertTrue(item["title"])
            self.assertIn(item["bucket"], {"master", "candidate", "conflict"})
            self.assertIn(item["source"], {"email", "navi", "mixed"})
            if item["date"] is not None:
                date.fromisoformat(item["date"])


class RealDataTest(unittest.TestCase):
    """実際のワークスペースの Markdown が読めることを確かめる。"""

    @classmethod
    def setUpClass(cls):
        cls.data = parse.load(WORKSPACE)

    def test_no_parse_warnings(self):
        self.assertEqual(self.data["warnings"], [])

    def test_volume(self):
        self.assertGreaterEqual(len(self.data["items"]), 50)
        self.assertGreaterEqual(len(self.data["rules"]), 5)
        self.assertGreaterEqual(len(self.data["applied"]), 5)

    def test_sources_exist(self):
        for rel in self.data["sources"]:
            self.assertTrue((WORKSPACE / rel).exists(), rel)

    def test_dated_items_in_expected_year(self):
        for item in self.data["items"]:
            if item["date"]:
                self.assertTrue(item["date"].startswith("2026-"), item["date"])


if __name__ == "__main__":
    unittest.main()
