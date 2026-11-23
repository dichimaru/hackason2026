# 4.8 API(案)

管理者 API は、ログインした管理者のセッション(Cookie)でだけ使える。更新操作は CSRF トークンが必須。社員用・誰でも用のページはログイン不要(08 参照)。

| Method | Path | 利用者 | 説明 | 画面 |
|--------|------|------|------|------|
| GET | `/a/{token}?r=attend\|absent` | 社員 | 出欠を記録して回答完了ページを返す(締切後は記録しない) | W2 |
| GET | `/results/{public_token}` | 誰でも | その回(東京の回 / 大阪の回)の当番を表示 | W10 |
| POST | `/admin/login` | 管理者 | ID/パスワードでログイン(5回失敗で15分ロック) | W0-1 |
| POST | `/admin/logout` | 管理者 | ログアウト(セッション削除) | 全管理画面 |
| POST | `/admin/password` | 管理者 | 自分のパスワード変更(初回は必須) | W0-2 |
| PUT/DELETE | `/api/employees/{id}/admin` | 管理者 | 管理者にする(ID と一時パスワードを設定)/ 外す。最後の1人は外せない | W7-2 |
| GET | `/api/events` | 管理者 | 回の一覧(エリア・掃除日・作成元・状態・出席/全員・締切) | W1 |
| POST | `/api/events` | 管理者 | 臨時の回の作成 → 出欠行と token の発行 → 出欠 DM・リマインドの予約 | W3 |
| GET | `/api/events/{id}` | 管理者 | 回の詳細(出欠一覧・前回当選者・抽選の対象数・抽選後は当番) | W4 |
| POST | `/api/events/{id}/cancel` | 管理者 | 中止(未送信の通知は送らない) | W4 |
| GET | `/api/duties` | 管理者 | 当番履歴・前回の当選者 | W6 |
| GET/POST/PUT | `/api/employees` | 管理者 | 社員の一覧・登録・編集・休止 | W7 |
| GET/POST/PUT | `/api/tools` | 管理者 | 掃除道具の一覧・登録・編集(必要人数・在庫数の更新を含む) | W8 |
| GET/PUT | `/api/schedule-settings` | 管理者 | 自動作成の設定 | W9 |

抽選(F7)・結果投稿(F8)・リマインド(F6)・自動作成(F1)はスケジューラが行うので、API は持たない。
