# 3. テーブル定義

**エリア(areas)は大阪・東京の固定2件**。社員は1つのエリアに所属する。**回(cleaning_events)はエリアごと**(「大阪の回」「東京の回」)で、抽選も回ごとに行う。
**当番の必要人数は掃除道具ごとに持つ**(`tools.required_people`)。道具の**在庫数**(`tools.stock`)も道具ごとに持ち、**在庫 0 の道具には当番を割り当てない**(使えない道具の判定に別のフラグを持たない)。エリアの人数はその合計で、別の列には持たない。実際に誰を割り当てたかは `duties` に残る。
**担当の単位は掃除道具**(場所という単位はない)。当選者は、回のエリアの掃除道具のどれかを担当する。

**計算で出せる値は列に持たない**(正規化)。抽選の締切後は出欠が変わらず、当番も決まった後に変わらない(辞退なし)ため、次の値はいつでも同じ結果で計算できる。
- 出席者数・対象数(出席者 − 前回当選者) … `attendances` と前回の回の `duties` から計算
- 連続当番かどうか … 前回の回の `duties` にその社員がいるかで判定
- 回の「締切済み」 … `attendance_deadline` と現在時刻で判定(状態として持たない)

```
areas 1─N employees 1─N attendances N─1 cleaning_events N─1 areas
areas 1─N tools 1─N duties N─1 cleaning_events
          employees 1─N duties
cleaning_events 1─N notifications
employees 1─0..1 admin_accounts 1─N admin_sessions
admin_accounts 1─N audit_logs
```

```sql
-- エリア (大阪・東京の固定。seed で2件のみ投入)
CREATE TABLE areas (
  id    INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name  VARCHAR(64)  NOT NULL,                       -- '大阪' / '東京'
  PRIMARY KEY (id),
  UNIQUE KEY uq_areas_name (name)
);

-- 社員
CREATE TABLE employees (
  id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name        VARCHAR(64)  NOT NULL,                 -- W7・W10 に表示
  department  VARCHAR(64)  NOT NULL,                 -- W7 に表示 (同姓同名の見分け)
  area_id     INT UNSIGNED NOT NULL,                 -- 所属エリア。この社員はこのエリアの回にだけ出欠・抽選の対象になる
  teams_upn   VARCHAR(255) NULL,                     -- Teams の UPN。DM の宛先。NULL=未登録 (DM を送れない)
  active      TINYINT(1)   NOT NULL DEFAULT 1,       -- 0=休止 (出欠 DM・抽選の対象外)。過去の記録が参照するので行は消さない
  created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_employees_upn (teams_upn),           -- 同じ UPN の社員を二重に登録しない
  CONSTRAINT fk_emp_area FOREIGN KEY (area_id) REFERENCES areas(id)
);

-- 掃除道具 (エリアに属する。担当の単位。場所は持たない)
CREATE TABLE tools (
  id           INT UNSIGNED NOT NULL AUTO_INCREMENT,
  area_id      INT UNSIGNED NOT NULL,                -- 属するエリア
  name         VARCHAR(64)  NOT NULL,                -- 掃除道具名
  description  VARCHAR(255) NOT NULL DEFAULT '',     -- 掃除のポイント (W8 で登録、W10 に表示)
  required_people TINYINT UNSIGNED NOT NULL,         -- この道具の当番の必要人数 (既定値なし。管理者が登録)
  stock        SMALLINT UNSIGNED NOT NULL,           -- 在庫数 (W8 で登録・更新)。0=使えない → 当番を割り当てない。W8・W10 に表示
                                                    -- 過去の当番が参照するので行は消さない (使わなくなった道具は在庫 0 にする)
  PRIMARY KEY (id),
  UNIQUE KEY uq_tools_area_name (area_id, name),
  CONSTRAINT fk_tool_area FOREIGN KEY (area_id) REFERENCES areas(id)
);

-- 回 (エリアごと)
CREATE TABLE cleaning_events (
  id                   INT UNSIGNED NOT NULL AUTO_INCREMENT,
  area_id              INT UNSIGNED NOT NULL,        -- この回のエリア (大阪の回 / 東京の回)
  event_date           DATE         NOT NULL,        -- 掃除日
  start_time           TIME         NOT NULL,        -- 掃除開始時刻
  source               ENUM('auto','manual') NOT NULL,  -- 自動作成 / 臨時の回(手動作成)
  attendance_deadline  DATETIME     NOT NULL,        -- 出欠締切
  remind_at            DATETIME     NOT NULL,        -- 未回答者リマインド
  draw_at              DATETIME     NOT NULL,        -- 抽選日時 (この時刻に自動で抽選し、結果を投稿する)
  public_token         CHAR(32)     NOT NULL,        -- 当選結果画面 W10 の URL 用の乱数 (128bit を hex)。連番の id を公開しない (08 参照)
  status               ENUM('open','drawn','cancelled') NOT NULL DEFAULT 'open',
                       -- open=出欠受付〜抽選前 / drawn=抽選済み / cancelled=中止
  created_at           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_event_area_date_source (area_id, event_date, source),  -- 自動作成の二重作成を防ぐ
  UNIQUE KEY uq_event_public_token (public_token),
  KEY idx_event_area_date (area_id, event_date),     -- 「同じエリアの前回」を引く
  CONSTRAINT fk_event_area FOREIGN KEY (area_id) REFERENCES areas(id)
);

-- 自動作成の設定 (1行のみ。W9 で編集)。時刻はすべて掃除当日
-- 例: 金曜 09:00 作成+出欠 DM → 11:00 リマインド → 13:00 締切 → 13:05 抽選+結果投稿 → 16:00 掃除開始
CREATE TABLE schedule_settings (
  id                   TINYINT UNSIGNED NOT NULL DEFAULT 1,
  cleaning_weekday     TINYINT     NOT NULL,         -- 掃除の曜日 (1=月 … 5=金)
  cleaning_start_time  TIME        NOT NULL,
  publish_time         TIME        NOT NULL,         -- 回の自動作成 + 出欠 DM
  remind_time          TIME        NOT NULL,         -- 未回答者リマインド
  deadline_time        TIME        NOT NULL,         -- 出欠締切
  draw_time            TIME        NOT NULL,         -- 抽選 + 結果投稿
  PRIMARY KEY (id)
);

-- 出欠 (回の作成時に、回のエリアに所属する有効な社員分の行を作る。response が NULL = 未回答)
-- token が「個人別リンク」そのもの。token から (回, 社員) が一意に決まる = 本人確認
CREATE TABLE attendances (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  event_id      INT UNSIGNED NOT NULL,
  employee_id   INT UNSIGNED NOT NULL,
  token         CHAR(32)     NOT NULL,               -- 推測不能な乱数 (128bit を hex)
  response      ENUM('attend','absent') NULL,        -- NULL=未回答。締切までは上書き可、締切後は変更しない
  responded_at  DATETIME     NULL,                   -- W2 に表示
  PRIMARY KEY (id),
  UNIQUE KEY uq_att (event_id, employee_id),
  UNIQUE KEY uq_att_token (token),
  CONSTRAINT fk_att_event FOREIGN KEY (event_id)    REFERENCES cleaning_events(id),
  CONSTRAINT fk_att_emp   FOREIGN KEY (employee_id) REFERENCES employees(id)
);

-- 当番 (抽選結果)。決まった後は変更しない
CREATE TABLE duties (
  id           INT UNSIGNED NOT NULL AUTO_INCREMENT,
  event_id     INT UNSIGNED NOT NULL,
  employee_id  INT UNSIGNED NOT NULL,
  tool_id      INT UNSIGNED NOT NULL,                -- 担当する掃除道具 (回のエリアの道具)
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_duty_event_emp (event_id, employee_id),  -- 1回の中で二重当選しない
  KEY idx_duty_emp (employee_id),
  CONSTRAINT fk_duty_event FOREIGN KEY (event_id)    REFERENCES cleaning_events(id),
  CONSTRAINT fk_duty_emp   FOREIGN KEY (employee_id) REFERENCES employees(id),
  CONSTRAINT fk_duty_tool  FOREIGN KEY (tool_id)     REFERENCES tools(id)
);

-- Teams 通知 (送信予約・二重送信防止・失敗の記録)
CREATE TABLE notifications (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  event_id      INT UNSIGNED NOT NULL,
  employee_id   INT UNSIGNED NOT NULL DEFAULT 0,     -- DM の宛先。result (チャネル投稿) は宛先がないので 0
  kind          ENUM('invite','remind','result') NOT NULL,
                -- invite=出欠のお願い(DM) / remind=未回答リマインド(DM) / result=結果 URL のチャネル投稿
                -- 送り先 (DM 用 / チャネル用の Webhook) は kind で決まるので列に持たない
  status        ENUM('pending','sent','failed') NOT NULL DEFAULT 'pending',
  error         VARCHAR(512) NULL,                   -- failed の理由
  scheduled_at  DATETIME     NOT NULL,
  sent_at       DATETIME     NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_notif_once (event_id, kind, employee_id),  -- 同じ相手に同じ種類を二重送信しない
  CONSTRAINT fk_notif_event FOREIGN KEY (event_id) REFERENCES cleaning_events(id)
);

-- 管理者のログイン情報 (行がある社員 = 管理者)。一般の社員の情報と分けて持つ (08 参照)
CREATE TABLE admin_accounts (
  employee_id           INT UNSIGNED NOT NULL,          -- 管理者である社員
  login_id              VARCHAR(64)  NOT NULL,          -- ログイン ID
  password_hash         VARCHAR(255) NOT NULL,          -- Argon2id (または bcrypt) のハッシュ。平文は持たない
  must_change_password  TINYINT(1)   NOT NULL DEFAULT 1, -- 1=次のログインでパスワード変更が必須 (一時パスワード)
  failed_login_count    TINYINT UNSIGNED NOT NULL DEFAULT 0,  -- 連続失敗回数。成功で 0 に戻す
  locked_until          DATETIME     NULL,              -- この時刻までログイン不可 (5回失敗で15分)
  password_changed_at   DATETIME     NOT NULL,
  PRIMARY KEY (employee_id),
  UNIQUE KEY uq_admin_login_id (login_id),
  CONSTRAINT fk_admin_emp FOREIGN KEY (employee_id) REFERENCES employees(id)
);

-- 管理者のログインセッション。Cookie のセッション ID は保存せず、ハッシュだけを持つ
CREATE TABLE admin_sessions (
  session_hash   CHAR(64)     NOT NULL,                 -- セッション ID (256bit 乱数) の SHA-256
  employee_id    INT UNSIGNED NOT NULL,
  csrf_token     CHAR(64)     NOT NULL,                 -- 更新操作で照合する
  created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_seen_at   DATETIME     NOT NULL,                 -- 30分操作がなければ失効
  expires_at     DATETIME     NOT NULL,                 -- ログインから最長8時間
  PRIMARY KEY (session_hash),
  KEY idx_session_emp (employee_id),
  CONSTRAINT fk_session_admin FOREIGN KEY (employee_id) REFERENCES admin_accounts(employee_id) ON DELETE CASCADE
);

-- 管理操作のログ (誰が・いつ・何をしたか)。個人情報の中身は書かず、対象の id だけを書く
CREATE TABLE audit_logs (
  id           INT UNSIGNED NOT NULL AUTO_INCREMENT,
  employee_id  INT UNSIGNED NOT NULL,                   -- 操作した管理者
  action       VARCHAR(64)  NOT NULL,                   -- 例: login / login_failed / event_create / event_cancel / employee_update / tool_update / admin_grant
  target_type  VARCHAR(32)  NULL,                       -- 例: event / employee / tool
  target_id    INT UNSIGNED NULL,
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_audit_created (created_at),
  CONSTRAINT fk_audit_admin FOREIGN KEY (employee_id) REFERENCES employees(id)
);
```

### テーブルで守れない制約(処理で守る)
- `duties.tool_id` の道具のエリアは、回のエリア(`cleaning_events.area_id`)と同じであること。
- `attendances` の社員の所属エリアは、回のエリアと同じであること。
- `notifications.employee_id = 0` は「宛先なし(チャネル投稿)」。外部キーは張らない。NULL にすると MySQL では一意制約が効かず、二重送信を防げないため。

### テーブルに持たない設定(環境変数)
DM 用 / チャネル用の Webhook URL(秘密情報)、アプリの URL。管理者が画面から変えるものではないため、テーブルを作らない。
