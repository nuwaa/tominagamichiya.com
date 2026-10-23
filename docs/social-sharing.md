# OGP・Xカードの設定

記事ごとの画像制作は必須ではありません。共通画像は `config.toml` の `params.og_default_image`、説明は `params.og_default_image_alt` で管理します。

## 現在の共通画像

- `/media/tominaga.jpg`：既存の本人写真。JPEG、480×480px、25,370バイト。
- `static/media/og-default.jpg` は0バイトで、画像の寸法も内容も確認できませんでした。空ファイルは削除しました。
- 正方形の本人写真に合わせ、Xは `summary` カードにします。横長の画像を個別指定した場合は、寸法の比率に応じて `summary_large_image` に切り替わります。
- 本人写真はサイトの識別用として利用できますが、横長カードのためのデザイン画像ではありません。1200×630px程度の共通画像の新規制作は別作業です。画像は今回作り直していません。

## 優先順位と指定例

1. ページの `image`。
2. ページの `images` 配列の先頭から利用できる画像。
3. サイト共通の `og_default_image`。

ローカルの画像が存在しない、空、または読み取れない場合は次の候補へ進みます。共通画像まで利用できなければビルドを失敗させ、画像なしの公開を防ぎます。

```yaml
image: "/media/article-image.jpg"
image_alt: "画像に写っている内容"
```

ページバンドル内の画像は `image: "cover.jpg"` と指定できます。既存の絶対URL指定も利用できます。外部画像はビルド時にダウンロードせず、到達性・サイズ・利用条件は指定する側で確認します。外部画像は寸法が不明なためXの大きなカードを指定します。指定を省略すれば共通画像になります。

タイトル・説明・URLはページの情報を使用します。説明はページの `description`、本文要約、サイト説明の順で補完します。トップの説明は `content/_index.md` に既に設定された文を利用します。個別画像のalt省略時はページタイトルを使うため、可能なら内容を表す `image_alt` を指定してください。

## 読み込み関係と確認

有効な `layouts/_default/baseof.html` から `layouts/partials/seo/opengraph.html` を呼び、OGPとXの情報を統一しています。画像解決は `seo/image.html`、ページ情報は `seo/metadata.html` です。構造化データの画像も同じ解決結果を使います。テーマの旧実装はプロジェクト側のpartialで上書きします。`.BAK` は有効なテンプレートではありません。

```sh
npm ci --include=dev
npm run build
python3 scripts/test_social.py
```

生成HTMLの `og:image` と `twitter:image` が一致し、画像URLがHTTP 200と正しいContent-Typeを返し、画像として読み取れることを確認します。Cloudflareプレビューでは同じ画像パスをプレビューのホストでも確認します。canonical・OGPのURLには本番URLを維持します。

SNS側の表示はキャッシュやクローラーの判断にも左右されるため、タグとHTTPの検証だけで実際の投稿表示まで保証しません。マージ後に代表記事とトップを共有して確認してください。
