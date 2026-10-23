#!/usr/bin/env python3
"""Publication/companion regression checks; fixtures never enter the repository content."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class EditorialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="hugo-editorial-")
        self.addCleanup(self.temp.cleanup)
        self.site = Path(self.temp.name)
        for folder in ("layouts", "static", "archetypes"):
            shutil.copytree(ROOT / folder, self.site / folder)
        shutil.copy2(ROOT / "config.toml", self.site / "config.toml")
        shutil.copytree(ROOT / "content/audiences", self.site / "content/audiences")
        (self.site / "content/articles").mkdir()
        (self.site / "content/articles/_index.md").write_text('---\ntitle: Articles\n---\n')

    def article(self, slug, audience=None, companion=None, **extra):
        front = dict(title=f"Fixture {slug}", date="2000-01-01T00:00:00+09:00", draft=False)
        if audience is not None:
            front["audiences"] = audience
        if companion is not None:
            front["companion"] = companion
        front.update(extra)
        path = self.site / f"content/articles/{slug}/index.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("---\n" + "\n".join(f"{k}: {json.dumps(v)}" for k, v in front.items()) + "\n---\n\nFixture body.\n")

    def build(self, *flags, success=True):
        result = subprocess.run(
            ["hugo", "--source", str(self.site), "--cacheDir", str(self.site / "cache"), *flags],
            text=True, capture_output=True,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("ERROR", result.stdout + result.stderr)
        return result

    def html(self, path):
        return (self.site / "public" / path / "index.html").read_text()

    def pair(self):
        self.article("general", ["general"], "/articles/technical")
        self.article("technical", ["technical"], "/articles/general")

    def test_archetypes_create_japan_time_drafts(self):
        for kind in ("general", "technical"):
            result = subprocess.run(
                ["hugo", "new", "content", "--source", str(self.site), "--kind", kind,
                 f"articles/new-{kind}/index.md"], text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            front = (self.site / f"content/articles/new-{kind}/index.md").read_text()
            self.assertIn("draft: true", front)
            self.assertIn(f'audiences: ["{kind}"]', front)
            self.assertIn("+09:00", front)
        self.build()
        self.assertFalse((self.site / "public/articles/new-general/index.html").exists())
        self.assertFalse((self.site / "public/articles/new-technical/index.html").exists())

    def test_published_pair_and_japanese_taxonomy(self):
        self.pair()
        self.build()
        for slug, other, label in [
            ("general", "technical", "もっと詳しく知りたい人へ：技術者向けの解説"),
            ("technical", "general", "まず全体像を知りたい人へ：一般向けの解説"),
        ]:
            html = self.html(f"articles/{slug}")
            self.assertEqual(html.count('class="companion-notice"'), 2)
            self.assertEqual(html.count(label), 2)
            self.assertIn(f'href="/articles/{other}/"', html)
            term = self.html(f"audiences/{slug}")
            self.assertIn(f"Fixture {slug}", term)
            self.assertNotIn(f"Fixture {other}", term)
            self.assertNotIn("この分類の記事は準備中", term)
        self.assertIn('aria-current="page"', self.html("audiences/general"))

    def test_unclassified_and_empty_terms(self):
        self.article("legacy")
        self.build()
        self.assertIn("Fixture legacy", self.html("articles"))
        self.assertNotIn('class="audience-badge"', self.html("articles/legacy"))
        self.assertNotIn('class="companion-notice"', self.html("articles/legacy"))
        for term in ("general", "technical"):
            self.assertIn("この分類の記事は準備中", self.html(f"audiences/{term}"))
            self.assertNotIn("Fixture legacy", self.html(f"audiences/{term}"))

    def test_nonpublic_targets_absent_from_output(self):
        cases = [dict(draft=True), dict(date="2999-01-01T00:00:00+09:00"),
                 dict(publishDate="2999-01-01T00:00:00+09:00"),
                 dict(expiryDate="2001-01-01T00:00:00+09:00")]
        for index, settings in enumerate(cases):
            self.article(f"source-{index}", ["general"], f"/articles/hidden-{index}")
            self.article(f"hidden-{index}", ["technical"], f"/articles/source-{index}", **settings)
        self.build()
        for index in range(len(cases)):
            self.assertFalse((self.site / f"public/articles/hidden-{index}/index.html").exists())
            self.assertNotIn('class="companion-notice"', self.html(f"articles/source-{index}"))
        for output in (self.site / "public").rglob("*"):
            if output.suffix in (".html", ".xml"):
                self.assertNotIn("Fixture hidden-", output.read_text(), str(output))

    def test_missing_target_and_draft_preview_do_not_show_links(self):
        self.article("general", ["general"], "/articles/absent")
        self.article("draft", ["technical"], "/articles/general", draft=True)
        self.build("-D", "-F", "-E")
        for slug in ("general", "draft"):
            self.assertNotIn('class="companion-notice"', self.html(f"articles/{slug}"))
        # Even a draft included by -D must not be linked as a companion.
        self.article("general", ["general"], "/articles/draft")
        self.build("-D", "-F", "-E")
        self.assertNotIn('class="companion-notice"', self.html("articles/general"))

    def test_future_target_hidden_even_with_future_build(self):
        self.article("general", ["general"], "/articles/future")
        self.article("future", ["technical"], "/articles/general", date="2999-01-01T00:00:00+09:00")
        self.build("-F")
        self.assertNotIn('class="companion-notice"', self.html("articles/general"))

    def test_non_html_target_not_linked(self):
        self.article("general", ["general"], "/articles/nonhtml")
        self.article("nonhtml", ["technical"], "/articles/general", outputs=["RSS"])
        self.build()
        self.assertNotIn('class="companion-notice"', self.html("articles/general"))

    def test_broken_reciprocity_fails(self):
        self.article("general", ["general"], "/articles/technical")
        self.article("technical", ["technical"])
        self.build(success=False)

    def test_same_audience_fails(self):
        self.article("general", ["general"], "/articles/other")
        self.article("other", ["general"], "/articles/general")
        self.build(success=False)

    def test_self_reference_fails(self):
        self.article("self", ["general"], "/articles/self")
        self.build(success=False)

    def test_invalid_audience_fails(self):
        self.article("invalid", ["unknown"])
        self.build(success=False)

    def test_multiple_audiences_fail(self):
        self.article("invalid", ["general", "technical"])
        self.build(success=False)

    def test_external_companion_fails(self):
        self.article("general", ["general"], "https://example.com/")
        self.build(success=False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
