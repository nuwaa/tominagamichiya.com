
# tominagamichiya.com — Hugo Starter (静的サイト＋Pagefind＋JSON-LD)

このスターターは、**ITジャーナリスト（サイバー・偽情報）**としての公式サイト向けに最適化しています。

- **Hugo（静的）** + **Pagefind**（静的検索）
- **JSON-LD**（Person / WebSite / Article） + **OG/Twitterカード**
- **Cloudflare Pages** でのCDN配信を想定
- 必須ページ: Top / Topics / Media Kit / Contact / Articles

## 1) ローカル実行（初回）

```bash
# 必要: hugo-extended, node (18+)
npm install
npm run dev
# -> http://localhost:1313
```

## 2) 本番ビルド

```bash
npm run build
# public/ にビルド。Pagefindで検索インデックスを生成
```

## 3) Cloudflare Pages セットアップ

1. このリポジトリを GitHub にアップロード
2. Cloudflare Pages で New Project → GitHub を接続
3. **Build command**: `npm run build`
4. **Build output directory**: `public`
5. **Environment**: Node 18+ / HUGO_VERSION = 最新の extended
6. `tominagamichiya.com` を Cloudflare DNS で管理し、Pages に接続

## 4) 主要ファイル

- `config.toml` … サイト設定（タイトル/メニュー/構造化データの切り替え）
- `layouts/partials/seo/` … JSON-LD と OG/Twitter メタ
- `content/` … コンテンツ（代表記事は `content/articles/`）
- `content/search/` … Pagefind UI（`npm run build` で `public/pagefind/` を生成）
- `assets/css/site.css` … 追加スタイル
- `themes/simple-news/` … 最小テーマ（ベーステンプレート）

## 5) 編集フロー（TV連動）

1. 速報は `content/articles/yyyymmdd-topic/index.md` を追加（600字）
2. 24h以内に本文を追記（テンプレ: 状況/原因/問題定義/予測/対策/生活への影響）
3. X（新アカ）に 30秒要約＋URL を投稿
4. メディアキットは `content/media-kit/` を更新

## 6) 検索（Pagefind）

- `npm run build` で `npx pagefind --site public` を実行 → `public/pagefind/` 生成
- `content/search/_index.md` の UI から検索可能

## 7) 注意

- OG画像の**自動画像生成**は未搭載（将来、GitHub Actions＋Playwright 等で拡張可能）。
- いったんは**テキストOG**（タイトル/説明/サムネ固定）で運用。

---

© 2025 Michiya Tominaga
