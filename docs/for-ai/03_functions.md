# 4. 機能設計

### 4.1 機能一覧

| ID | 機能 | 利用者 | 概要 | 主なテーブル |
|----|------|--------|------|------|
| F1 | 回の自動作成 | システム | 毎週、設定(W9)の曜日・時刻に、エリアごとに回を作り、出欠 DM を送る(4.6) | cleaning_events, attendances, notifications |
| F2 | 臨時の回の作成 | 管理者 | エリア・掃除日・開始時刻・各時刻を指定して回を作り、出欠 DM を送る(W3) | 同上 (source='manual') |
| F3 | 回の中止 | 管理者 | 祝日などで掃除しない回を中止する。未送信の通知も送らない(W4) | cleaning_events.status, notifications |
| F4 | 出欠 DM | システム | 回のエリアの有効な社員へ、出席/欠席リンク付きの DM を送る (kind=invite) | attendances.token, notifications |
| F5 | 出欠回答 | 社員 | DM のリンクをクリックするだけで記録。締切まで何度でも変更可(W2) | attendances |
| F6 | 未回答者リマインド | システム | `remind_at` に未回答者へ DM (kind=remind) | attendances, notifications |
| F7 | 抽選 | システム | `draw_at` に自動で抽選する(4.2) | attendances, duties, tools |
| F8 | 結果投稿 | システム | 抽選後、回ごとに当選結果画面(W10)の URL を Teams のチャネルに投稿 (kind=result) | notifications |
| F9 | 当選結果画面 | 誰でも | 回(東京の回 / 大阪の回)ごとに、当番(道具・在庫・ポイント)を表示。ログイン不要(W10) | duties, tools, employees |
| F10 | 当番履歴 | 管理者 | 前回の当選者(次回の除外対象)と過去の当番を表示(W6) | duties |
| F11 | 社員管理 | 管理者 | 社員の登録・編集・休止(W7) | employees |
| F12 | 掃除道具管理 | 管理者 | 道具・ポイント・必要人数・在庫数の登録・更新(W8)。在庫 0 は赤で表示 | tools |
| F13 | 自動作成の設定 | 管理者 | 掃除の曜日・開始時刻・各時刻(W9) | schedule_settings |

### 4.2 抽選アルゴリズム(F7)

```
draw(event):
  BEGIN; SELECT ... FROM cleaning_events WHERE id=? FOR UPDATE      -- 二重実行防止
  status が 'open' でなければ中断 (冪等。中止・抽選済みの回は何もしない)

  area      = event.area_id
  attendees = この回の attendances(response='attend') の社員 ∩ employees.active=1
  prev      = 同じエリアの前回 (area_id が同じ, status='drawn', (event_date, id) がこの回より前で最新)
  last_won  = prev の duties の社員                       -- 前回が無ければ空
  tools     = area の掃除道具のうち stock > 0 のもの      -- 在庫 0 の道具は使えないので割り当てない
  need      = Σ tools.required_people                     -- 当番人数
  eligible  = attendees − last_won

  if len(eligible) >= need:  winners = sample(eligible, need)
  else:                                                   -- 対象不足 → 前回当選者から補充 (連続当番)
      winners = eligible 全員 + sample(attendees ∩ last_won, need − len(eligible))
  -- 出席者そのものが need より少なければ、出席者全員が当番 (不足は W4 に表示)

  winners をシャッフルし、各道具に required_people 人ずつ割り当てる
  duties INSERT (event_id, employee_id, tool_id)
  cleaning_events.status = 'drawn'
  notifications INSERT (kind='result', employee_id=0, scheduled_at=now)
  COMMIT
```

- **公平性**: 一様乱数。除外は「前回当選者」のみ。前回当選者は1回休むだけで、次の回からは他の人と同じ確率に戻る。
- **連続当番の判定**: 列には持たない。当番の社員が `prev` の `duties` にいれば連続当番(W4・W6 で表示)。
- **出席者 0 人**: 当番は 0 人のまま `drawn` にし、W4 と W10 に「出席者なし」と表示する。

### 4.3 リマインド(F6)
- 対象 = その回の `attendances` で `response IS NULL` の人
- 各人の DM に、その人の個人別リンクを送る。全員回答済みなら送らない
- 通知は `notifications` の `scheduled_at <= now AND status='pending'` を1分間隔で送る。`UNIQUE(event_id, kind, employee_id)` で二重送信を防ぐ
- 中止(`cancelled`)の回の未送信の通知は送らない

### 4.5 本人確認(個人別リンク)
- 回答リンクは社員ごとに異なる(`/a/{token}?r=attend|absent`)。token から `(回, 社員)` が一意に決まるので、**ログイン不要で本人を特定**できる
- 回の作成時に、回のエリアに所属する有効な社員分の `attendances` 行(token つき)を作る
- token は推測不能(128bit 乱数)。締切後は回答を記録しない

### 4.6 回の自動作成(F1)
アプリ内スケジューラが1分間隔で判定する。

```
autoCreate(now):
  s          = schedule_settings
  event_date = 開始時刻 (s.cleaning_start_time) がまだ来ていない直近の s.cleaning_weekday の日付
  if now < event_date の s.publish_time:  return
  for area in areas:                                      -- エリアごとに1回ずつ作る
    if cleaning_events に (area, event_date, 'auto') が既にある:  continue   -- 冪等
    BEGIN
      cleaning_events INSERT (area_id=area, event_date, source='auto', start_time=s.cleaning_start_time,
          attendance_deadline / remind_at / draw_at = event_date + s.deadline_time / s.remind_time / s.draw_time,
          status='open')
      attendances INSERT: そのエリアの有効な社員分 (token 発行)
      notifications INSERT: invite (社員ごと, scheduled_at=now), remind (社員ごと, scheduled_at=remind_at)
    COMMIT
  -- remind は送信時に response IS NULL の人だけに送る。抽選は draw_at にスケジューラが draw() を呼ぶ
```
- 祝日などで掃除しない週は、管理者が回を **中止**(`cancelled`)する(F3)。
- 臨時の回(W3)は `source='manual'`。同じエリア・同じ日に自動の回と臨時の回が共存できる。

### 4.7 当番人数の決め方
- 必要人数は **掃除道具ごと**に持つ(`tools.required_people`。既定値なし、W8 で登録)。
- 回の当番人数 = 回のエリアの、在庫がある(`stock > 0`)道具の `required_people` の合計。**回・エリアの単位では人数を持たない**(合計のコピーを持つと二重管理になるため)。
- 過去の回の人数は `duties` を数えれば分かる。道具の人数を後で変えても、過去の記録は変わらない。

### 4.9 エッジケース
| ケース | 扱い |
|--------|------|
| 出席者 < 当番人数 | 出席者全員を当番にし、W4 に不足を表示 |
| 対象(出席者 − 前回当選者) < 当番人数 | 前回当選者から不足分を補充(連続当番)。W4・W6 に表示 |
| 締切後の回答 | 記録しない(W2 に「締め切られました」) |
| 抽選の二重実行 | 行ロック + status チェックで防止 |
| UPN 未登録の社員 | 出欠の行は作るが DM は送れない(`notifications.status='failed'`)。W7 に未登録を表示 |
