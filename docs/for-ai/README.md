# 設計書(AI・実装者向け)

実装時に参照する **仕様の正本**。DDL・アルゴリズム・API・制約を厳密に書く。人間向けの概要は [../for-human/](../for-human/README.md)。
**設計のみ。実装は含まない。** 仕様を変えるときは、まずこのフォルダを直し、人間向けの要約も合わせる。

| # | ファイル | 内容 |
|---|---|---|
| 1 | [01_requirements.md](01_requirements.md) | 要件、全体フロー、回のステータス遷移 |
| 2 | [02_tables.md](02_tables.md) | テーブル定義(DDL) |
| 3 | [03_functions.md](03_functions.md) | 機能一覧、抽選アルゴリズム、リマインド、本人確認、自動作成、当番人数、エッジケース |
| 4 | [04_api.md](04_api.md) | API(案) |
| 5 | [05_screens.md](05_screens.md) | 画面 W0〜W10(ASCII)と、各項目とテーブル列の対応。見た目は ../wireframes/index.html |
| 6 | [06_teams.md](06_teams.md) | Teams 連携(Workflows Webhook)、通知文面 |
| 7 | [07_decisions.md](07_decisions.md) | 決定事項と要確認事項 |
| 8 | [08_security.md](08_security.md) | セキュリティ(管理者認証・セッション・公開ページ・操作ログ) |

※本文中の「4.x」「W◯」は旧通し番号。4.1〜4.7・4.9 = 03、4.4 = 06、4.8 = 04、W◯ = 05 を参照。
