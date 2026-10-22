# tominagamichiya.com

富永道也の個人サイト。HugoとMarkdownで管理し、Cloudflare Pagesで公開する。

## 構成

- `content/articles/<slug>/index.md`：記事
- `content/`内のその他のページ：トップ、Topics、Media Kit、Contact、Search
- `config.toml`：サイト設定
- `layouts/`：優先して使うテンプレート
- `themes/simple-news/`：同梱テーマ
- `static/`：そのまま配信するCSS・画像
- `assets/`：Hugoで加工する素材
- `public/`：生成物（コミットしない）

## 開発・ビルド

Hugo extended **0.152.2**とNode.js/npmを用意する。現行Cloudflare本番はNode **18**、移行検証先は**22**。

```bash
npm ci --include=dev
npm run dev
# http://localhost:1313/ （下書きを含む）
```

```bash
npm run build
# HugoとPagefindを実行しpublic/へ出力
```

## 更新と公開

作業ブランチで編集し、PRで内容とビルドを確認する。本人がマージして`main`を更新すると、Cloudflare Pagesが`npm run build`を実行し`public`を本番公開する。

- [Codex Cloud・複数端末での日本語運用手順](docs/operations.md)
- [旧定期処理の廃止案・Node 22移行計画](docs/maintenance-plan.md)
- [Codexの編集ルール](AGENTS.md)

GitHub ActionsはPRビルド検証を担当する。GitHub Pagesは使わない。PRプレビューの有効状態はCloudflare側で確認する。本番環境変数は移行計画に従い本人の承認後に変更する。

`draft: true`や未来日時の記事は本番ビルドに含まれない。予約日時の到来だけでは再ビルドされない。検索UI・OGP等の既存課題はビルド検証とは分けて扱う。
