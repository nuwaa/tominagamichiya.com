#!/usr/bin/env python3
"""Check that Hugo renders Markdown emphasis as semantic <strong> elements."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from test_tables import Document

ROOT = Path(__file__).resolve().parents[1]


class EmphasisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="hugo-emphasis-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.site = Path(cls.temp.name)
        for folder in ("content", "layouts", "static"):
            shutil.copytree(ROOT / folder, cls.site / folder)
        shutil.copy2(ROOT / "config.toml", cls.site / "config.toml")

        fixture = cls.site / "content/articles/emphasis-fixture/index.md"
        fixture.parent.mkdir(parents=True, exist_ok=True)
        fixture.write_text("""---
title: Emphasis fixture
date: 2000-01-01T00:00:00+09:00
draft: false
---

日本語の文中で**強調する部分**は太字になります。

「**読者に必要な情報**」を伝えます。

- **リスト内の強調**も表示します。
""", encoding="utf-8")

        result = subprocess.run(
            ["hugo", "--source", str(cls.site),
             "--cacheDir", str(cls.site / "cache")],
            text=True, capture_output=True,
        )
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    def strong_texts(self, slug):
        html = (self.site / f"public/articles/{slug}/index.html").read_text(encoding="utf-8")
        doc = Document(html).root
        bodies = [node for node in doc.all("div") if node.attrs.get("class") == "post-body"]
        self.assertEqual(len(bodies), 1, f"Missing article body: {slug}")
        return [node.text() for node in bodies[0].all("strong")]

    def test_japanese_prose_fixture(self):
        strongs = self.strong_texts("emphasis-fixture")
        self.assertIn("強調する部分", strongs)
        self.assertIn("読者に必要な情報", strongs)
        self.assertIn("リスト内の強調", strongs)

    def test_existing_kawaii_gpt_article(self):
        self.assertIn("「AI対AI」の攻防", self.strong_texts("kawaii_gpt_report"))

    def test_existing_online_casino_article(self):
        self.assertIn(
            "「ゲームとギャンブルの境目」がますますあいまいになる",
            self.strong_texts("online-casino-teens"),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
