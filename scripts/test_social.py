#!/usr/bin/env python3
"""Build temporary fixtures and check rendered social metadata, not source strings."""
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://tominagamichiya.com'


class Metadata(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.meta = {}
        self.canonical = None
        self.jsonld = []
        self.script = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            key = attrs.get('property', attrs.get('name'))
            self.meta.setdefault(key, []).append(attrs.get('content'))
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonical = attrs['href']
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.script = ''

    def handle_data(self, text):
        if self.script is not None:
            self.script += text

    def handle_endtag(self, tag):
        if tag == 'script' and self.script is not None:
            self.jsonld.append(json.loads(self.script))
            self.script = None

    def one(self, key):
        values = self.meta[key]
        if len(values) != 1:
            raise AssertionError(f'Duplicate {key}: {values}')
        return values[0]


class SocialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='hugo-social-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.site = Path(cls.temp.name)
        for name in ('content', 'layouts', 'static'):
            shutil.copytree(ROOT / name, cls.site / name)
        shutil.copy2(ROOT / 'config.toml', cls.site / 'config.toml')
        fixtures = {
            'social-default': 'description: \'説明に「引用」と & 記号\'\n',
            'social-missing': 'image: "/media/missing.jpg"\n',
            'social-empty': 'image: "/media/empty.jpg"\n',
            'social-corrupt': 'image: "/media/corrupt.jpg"\n',
            'social-bundle': 'image: "cover.jpg"\nimage_alt: "個別写真"\nimages: ["https://example.com/ignored.jpg"]\n',
            'social-images': 'images: ["/missing.jpg", "/media/tominaga.jpg"]\n',
            'social-remote': 'image: "https://example.com/cover.jpg"\nimage_alt: "外部の個別画像"\n',
        }
        for slug, params in fixtures.items():
            p = cls.site / f'content/articles/{slug}/index.md'
            p.parent.mkdir()
            p.write_text('---\ntitle: \'見出し「写真」 & 説明\'\ndate: 2000-01-01T00:00:00+09:00\ndraft: false\n' + params + '---\n\n本文の要約です。\n', encoding='utf-8')
        shutil.copy2(ROOT / 'static/media/tominaga.jpg', cls.site / 'content/articles/social-bundle/cover.jpg')
        (cls.site / 'static/media/empty.jpg').write_bytes(b'')
        (cls.site / 'static/media/corrupt.jpg').write_text('This is not a JPEG.')
        result = cls.build()
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    @classmethod
    def build(cls):
        return subprocess.run(['hugo', '--source', str(cls.site), '--cacheDir', str(cls.site / 'cache')], text=True, capture_output=True)

    def page(self, path):
        return Metadata((self.site / 'public' / path / 'index.html').read_text())

    def test_home_and_profile(self):
        home = self.page('')
        self.assertIn('技術の「難しい」を、社会の言葉へ。', home.one('description'))
        self.assertEqual(home.one('description'), home.one('og:description'))
        self.assertEqual(home.one('og:type'), 'website')
        self.assertIn('富永道也', home.one('og:title'))
        self.assertEqual(self.page('about').one('og:type'), 'website')

    def test_all_public_pages_have_consistent_unique_tags(self):
        for path in (self.site / 'public').rglob('index.html'):
            with self.subTest(path=str(path)):
                m = Metadata(path.read_text())
                self.assertEqual(m.one('og:image'), m.one('twitter:image'))
                self.assertEqual(m.one('og:title'), m.one('twitter:title'))
                self.assertEqual(m.one('og:description'), m.one('twitter:description'))
                self.assertEqual(m.one('og:url'), m.canonical)
                self.assertTrue(m.one('og:image').startswith('https://'))
                self.assertTrue(m.one('description'))
                for obj in m.jsonld:
                    if 'image' in obj:
                        self.assertEqual(obj['image'], m.one('og:image'))

    def test_shared_portrait_and_square_card(self):
        m = self.page('articles/social-default')
        self.assertEqual(m.one('og:image'), BASE + '/media/tominaga.jpg')
        self.assertEqual(m.one('og:image:width'), '480')
        self.assertEqual(m.one('og:image:height'), '480')
        self.assertEqual(m.one('og:image:alt'), '富永道也のプロフィール写真')
        self.assertEqual(m.one('twitter:card'), 'summary')
        self.assertEqual(m.one('og:type'), 'article')

    def test_missing_empty_corrupt_and_array_fallbacks(self):
        for slug in ('social-missing', 'social-empty', 'social-corrupt', 'social-images'):
            with self.subTest(slug=slug):
                self.assertEqual(self.page('articles/' + slug).one('og:image'), BASE + '/media/tominaga.jpg')

    def test_page_bundle_overrides_array_and_shared_image(self):
        m = self.page('articles/social-bundle')
        self.assertEqual(m.one('og:image'), BASE + '/articles/social-bundle/cover.jpg')
        self.assertEqual(m.one('og:image:alt'), '個別写真')
        self.assertTrue((self.site / 'public/articles/social-bundle/cover.jpg').is_file())

    def test_remote_image_and_escaped_page_metadata(self):
        m = self.page('articles/social-remote')
        self.assertEqual(m.one('og:image'), 'https://example.com/cover.jpg')
        self.assertEqual(m.one('twitter:card'), 'summary_large_image')
        self.assertEqual(m.one('twitter:image:alt'), '外部の個別画像')
        self.assertEqual(m.one('og:title'), '見出し「写真」 & 説明')
        self.assertIn('本文の要約', m.one('og:description'))
        self.assertEqual(self.page('articles/social-default').one('description'), '説明に「引用」と & 記号')

    def test_unusable_common_image_stops_build(self):
        config = self.site / 'config.toml'
        original = config.read_text()
        try:
            config.write_text(original.replace('og_default_image = "/media/tominaga.jpg"', 'og_default_image = "/media/empty.jpg"'))
            result = self.build()
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('No usable social image', result.stdout + result.stderr)
        finally:
            config.write_text(original)


if __name__ == '__main__':
    unittest.main(verbosity=2)
