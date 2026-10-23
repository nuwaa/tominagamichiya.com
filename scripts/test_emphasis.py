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

**能動的サイバー防御（ACD）** は仕組みの説明です。

文中の **「引用符で囲む強調」** も表示します。

`**コードの記号はそのまま**`

```markdown
**コードブロックの記号もそのまま**
```
""", encoding="utf-8")

        # Rendering checks include saved drafts only in this temporary test site.
        result = subprocess.run(
            ["hugo", "--buildDrafts", "--source", str(cls.site),
             "--cacheDir", str(cls.site / "cache")],
            text=True, capture_output=True,
        )
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    def article_body(self, slug):
        html = (self.site / f"public/articles/{slug}/index.html").read_text(encoding="utf-8")
        doc = Document(html).root
        bodies = [node for node in doc.all("div") if node.attrs.get("class") == "post-body"]
        self.assertEqual(len(bodies), 1, f"Missing article body: {slug}")
        return bodies[0]

    def strong_texts(self, slug):
        return [node.text() for node in self.article_body(slug).all("strong")]

    def test_japanese_prose_fixture(self):
        strongs = self.strong_texts("emphasis-fixture")
        self.assertIn("強調する部分", strongs)
        self.assertIn("読者に必要な情報", strongs)
        self.assertIn("リスト内の強調", strongs)

    def test_existing_kawaii_gpt_article(self):
        self.assertIn("「AI対AI」の攻防", self.strong_texts("kawaii_gpt_report"))

    def test_existing_acd_article(self):
        strongs = self.strong_texts("acd")
        for text in (
            "能動的サイバー防御（ACD）",
            "怪しい兆しを早めに見つけて先回りし、攻撃に使われる仕組みを止める（無害化する）",
            "「サイバー通信情報監理委員会」",
            "「やる側」だけで勝手にやらせないための“監視員”",
        ):
            with self.subTest(text=text):
                self.assertIn(text, strongs)

    def test_punctuation_boundaries_and_literal_code(self):
        body = self.article_body("emphasis-fixture")
        self.assertIn("能動的サイバー防御（ACD）", self.strong_texts("emphasis-fixture"))
        self.assertIn("「引用符で囲む強調」", self.strong_texts("emphasis-fixture"))
        self.assertEqual(
            [node.text().strip() for node in body.all("code")],
            ["**コードの記号はそのまま**", "**コードブロックの記号もそのまま**"],
        )

    def test_all_articles_have_no_unrendered_strong_markers(self):
        # Inspect text nodes, not HTML source; code samples may legitimately
        # contain literal Markdown. Include drafts in this temporary build.
        def prose(node):
            if isinstance(node, str):
                return node
            if node.tag in {"code", "pre", "script", "style"}:
                return ""
            return "".join(prose(child) for child in node.children)

        self.assertTrue(list((self.site / "public/articles").glob("*/index.html")))
        for page in sorted((self.site / "public/articles").glob("*/index.html")):
            with self.subTest(article=page.parent.name):
                self.assertNotIn("**", prose(self.article_body(page.parent.name)))

    def test_existing_online_casino_article(self):
        self.assertIn(
            "「ゲームとギャンブルの境目」がますますあいまいになる",
            self.strong_texts("online-casino-teens"),
        )

    def test_technologist_general_article_strong(self):
        self.assertIn(
            "技術の「難しい」を、社会の言葉へ。",
            self.strong_texts("why-i-call-myself-a-technologist"),
        )

    def test_technologist_technical_article_strong(self):
        self.assertIn(
            "架空の事例",
            self.strong_texts("why-i-call-myself-a-technologist-technical"),
        )



if __name__ == "__main__":
    unittest.main(verbosity=2)
