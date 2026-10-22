# 公開処理の整理とNode 22移行計画

## 旧gh-pages定期処理の廃止案

旧`.github/workflows/hugo-cron.yml`は毎日18:00 JSTと手動実行でHugo 0.152.2を起動し、`public/`を`gh-pages`へpushする。`npm run build`を使わずPagefindも生成しない。Cloudflare本番は`main`を直接ビルドするので、この処理は本番公開に必要ない。

このPRは旧ワークフローの削除を提案する。削除が有効になるのは本人がマージした後であり、それまでは`main`の定期処理は残る。管理画面での停止、`gh-pages`ブランチ削除、履歴削除は行わない。GitHub Pagesへの移行もしない。

旧処理は`main`を更新せず、Cloudflare本番の毎日再ビルドを保証する仕組みでもなかった。予約公開にはCloudflareのビルド起動を含む別設計が必要。旧cronを残すだけでは解決しない。

## PRビルド検証

新しい`.github/workflows/hugo-pr.yml`は`main`向けPRの作成・更新・再オープン・レビュー準備完了と手動実行が対象。Hugo extended 0.152.2、Node 18/22の両方で`npm ci --include=dev`と本番と同じ`npm run build`を実行する。

権限は`contents: read`。デプロイ、リポジトリへの書き込み、秘密情報の使用、成果物アップロードは行わない。同じPRの古い実行はキャンセルする。`pull_request_target`は使わない。

今後GitHub側で検討する設定（今回は変更しない）：

- `main`をPR経由に限定し、force push・削除を禁止する。
- 実際のチェック名を確認して`Build (Node 18)`、`Build (Node 22)`をマージ必須にする。移行完了後は18側のCIと必須条件を合わせて整理する。
- 一人運用では自分のPRを自分でApproveできないため、別の承認者がいない状態で承認レビュー件数を必須にしない。本人のマージを公開承認にする。

必須チェック設定前は、CI追加だけでマージが強制的に阻止されるわけではない。

## Node 22への移行

本人確認済みの本番はNode 18、Hugo 0.152.2、Cloudflareビルドシステムv3。Node 18はサポート終了済みのため移行を推奨するが、今回は本番環境変数を変更しない。

1. 同じlockfile・Hugo 0.152.2でNode 18と22のクリーンビルドを比較する。実際の版・結果・警告をPRに記録する。
2. 本人の承認後、CloudflareのPreview環境だけ`NODE_VERSION=22`へ変更する。`HUGO_VERSION=0.152.2`、`npm run build`、`public`、v3は維持する。
3. 新しいPreviewデプロイのログでNode版、依存導入、Hugo、Pagefindを確認する。ローカル検証とCloudflare実環境の検証は区別する。
4. プレビューとPRのNode 22チェックが成功し本人が承認したら、別作業でProductionの`NODE_VERSION`を22にして承認済みコミットを再デプロイする。本番公開を伴うため今回は実施しない。
5. 移行後にNode 18のCIと必須チェックを整理する。問題時は本人の承認のもとで以前の環境変数・成功デプロイに戻す。

今回は切替を引き起こす`.nvmrc`・`.node-version`やNode 22必須の`engines`を追加しない。本番Node 18互換性を保ったまま検証する。依存ライブラリの更新も混ぜない。

## 検証範囲

このPRのローカル検証では、Hugo extended 0.152.2と既存lockfileを使い、Node 18.20.8（npm 10.8.2）／Node 22.23.4（npm 10.9.9）の独立したディレクトリでクリーン導入・ビルドに成功した。両方で42記事、Pagefindの86ページを生成し、出力234ファイルのパスとSHA-256がすべて一致した。`package.json`とlockfileは変更していない。

Pagefindは`data-pagefind-body`がないためbody全体を索引化する旨と、日本語の語幹処理非対応の通知を出す。いずれも両Node版で共通の既存通知で、今回の対象外。Cloudflareの実環境でのNode 22検証は別途必要。

ビルド成功はHTMLと検索インデックスを生成できることを意味し、検索画面・OGP・スマートフォン表示・記事内容の正しさを保証しない。これらとプロフィール本文の修正は今回の対象外。

CloudflareのPRプレビュー設定と表示はダッシュボードとプレビューURLで確認する必要がある。PR作成だけで利用可能とは断定しない。
