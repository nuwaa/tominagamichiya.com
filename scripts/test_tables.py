#!/usr/bin/env python3
"""Build real articles and temporary Markdown fixtures to check table rendering."""
from html.parser import HTMLParser
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Element:
    def __init__(self, tag, attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []

    def all(self, tag):
        matches = []
        for child in self.children:
            if isinstance(child, Element):
                if child.tag == tag:
                    matches.append(child)
                matches.extend(child.all(tag))
        return matches

    def text(self):
        return ''.join(child.text() if isinstance(child, Element) else child for child in self.children)


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.root = Element('document')
        self.stack = [self.root]
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        element = Element(tag, attrs)
        self.stack[-1].children.append(element)
        if tag not in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}:
            self.stack.append(element)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


class TableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='hugo-tables-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.site = Path(cls.temp.name)
        for folder in ('content', 'layouts', 'static'):
            shutil.copytree(ROOT / folder, cls.site / folder)
        shutil.copy2(ROOT / 'config.toml', cls.site / 'config.toml')
        fixture = cls.site / 'content/articles/table-fixture/index.md'
        fixture.parent.mkdir()
        fixture.write_text('''---
title: Table fixture
date: 2000-01-01T00:00:00+09:00
draft: false
---

| Left | Center | Right |
| :--- | :---: | ---: |
| **太字** | [参照リンク](https://example.com/) | `npm run build` |
| 長い日本語の文章を単語ごとの空白がなくても読みやすく表示するための検証 | ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 | 1234567890 |

| 見出しA | 見出しB |
| --- | --- |
| 二つ目の表 | 内容 |
''')
        # Rendering checks include saved drafts only in this temporary test site.
        result = subprocess.run(['hugo', '--buildDrafts', '--source', str(cls.site), '--cacheDir', str(cls.site / 'cache')], text=True, capture_output=True)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    def document(self, slug):
        return Document((self.site / f'public/articles/{slug}/index.html').read_text()).root

    def markdown_table(self, slug):
        doc = self.document(slug)
        tables = [table for table in doc.all('table') if table.attrs.get('class') == 'markdown-table']
        self.assertTrue(tables)
        for table in tables:
            self.assertEqual(len(table.all('thead')), 1)
            self.assertEqual(len(table.all('tbody')), 1)
            self.assertTrue(all(cell.attrs.get('scope') == 'col' for cell in table.all('th')))
            columns = len(table.all('th'))
            for row in table.all('tbody')[0].all('tr'):
                self.assertEqual(len(row.all('td')), columns)
        return tables

    def test_real_hugo_article_preserves_cells_and_code(self):
        table = self.markdown_table('claude-code-to-codex-cloud-hugo-site')[0]
        self.assertEqual([h.text() for h in table.all('th')], ['役割', '採用していたもの'])
        self.assertEqual(len(table.all('td')), 14)
        self.assertEqual([c.text() for c in table.all('code')], ['npm run build', 'main'])
        self.assertEqual([c.text() for c in table.all('td')[:2]], ['静的サイト生成', 'Hugo'])

    def test_other_markdown_article(self):
        table = self.markdown_table('suica-2025')[0]
        self.assertEqual(len(table.all('th')), 3)
        self.assertEqual(len(table.all('td')), 15)

    def test_alignment_and_inline_markdown(self):
        table = self.markdown_table('table-fixture')[0]
        for row in table.all('tr'):
            cells = row.all('th') or row.all('td')
            self.assertEqual([cell.attrs.get('style') for cell in cells],
                             ['text-align: left', 'text-align: center', 'text-align: right'])
        self.assertEqual(table.all('strong')[0].text(), '太字')
        self.assertEqual(table.all('a')[0].attrs['href'], 'https://example.com/')
        self.assertEqual(table.all('code')[0].text(), 'npm run build')

    def test_scroll_regions_are_named_and_keyboard_focusable(self):
        doc = self.document('table-fixture')
        regions = [node for node in doc.all('div') if node.attrs.get('class') == 'table-scroll']
        self.assertEqual(len(regions), 2)
        for number, region in enumerate(regions, 1):
            self.assertEqual(region.attrs.get('role'), 'region')
            self.assertEqual(region.attrs.get('tabindex'), '0')
            self.assertIn(f'表{number}：', region.attrs.get('aria-label', ''))
            self.assertIn('横スクロール可能', region.attrs['aria-label'])
            self.assertEqual(len(region.all('table')), 1)

    def test_raw_html_table_is_not_rewritten(self):
        doc = self.document('misinfo-5sec-check')
        table = doc.all('table')[0]
        self.assertNotIn('class', table.attrs)
        self.assertIn('border-collapse: collapse', table.attrs.get('style', ''))
        self.assertEqual(len(table.all('th')), 4)
        self.assertEqual(len(table.all('td')), 20)
        self.assertFalse([node for node in doc.all('div') if node.attrs.get('class') == 'table-scroll'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
