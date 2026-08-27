# 基本設計書 — 社内掃除当番アプリ

| 項目 | 内容 |
|------|------|
| システム名 | 社内掃除当番アプリ (hackason2026) |
| 目的 | 30名規模のオフィスにおける掃除当番の割当・可視化 |
| 位置づけ | ハッカソン用プロトタイプ雛形。Docker Compose で一発起動できる開発環境を提供する |
| 採用技術スタック | **バックエンド: Go (Gin + GORM) / フロントエンド: Next.js (React)** — 2026-08-27 決定 |
| 関連ドキュメント | [実装手順書](./implementation-guide.md) / [Go の書き方入門](./go-guide.md) / [テーブル定義書](./table-definition.md) / [README](../README.md) |
| デザイン | [Figma: 掃除当番抽選アプリ](https://www.figma.com/design/e32i2DHHXEFeU8X15bmHbX/%E6%8E%83%E9%99%A4%E5%BD%93%E7%95%AA%E6%8A%BD%E9%81%B8%E3%82%A2%E3%83%97%E3%83%AA?node-id=0-1&m=dev&t=FIzCNAGSJpc7yaOB-1) |

---

## 1. システム概要

社員マスタと掃除エリアマスタをもとに、翌週5日分の掃除当番をランダムに抽選・登録し、一覧表示する Web アプリケーション。

技術スタックは **バックエンド Go (Gin + GORM) + フロントエンド Next.js (React)** を採用する (2026-08-27 決定)。以降の設計はこの組み合わせを前提に記述する。

本リポジトリは元々、同一の API 仕様・同一の DB スキーマに対してバックエンド3言語 × フロントエンド3フレームワークの計9通りを差し替えて起動できる雛形として作られており、採用しなかった実装 (Python / Ruby / Nuxt / SvelteKit) もコードとして残っている。これらは技術比較のための参考実装として扱い、本設計書の対象外とする。

### 1.1 スコープ

| 区分 | 内容 |
|------|------|
| 対象 | 社員一覧の参照、掃除エリア一覧の参照、当番一覧の参照、翌週当番の自動生成、ヘルスチェック |
| 対象外 | 認証・認可、当番の状態更新 (完了報告)、当番の交代申請、通知連携、集計レポート |

対象外の項目は「6. 制約事項」「7. 拡張の方針」に整理する。

### 1.2 想定利用者

| 利用者 | 用途 |
|--------|------|
| 総務担当 | 翌週の当番を生成し、割当結果を確認する |
| 一般社員 | 自分および他メンバーの当番予定を閲覧する |
| 開発者 | Adminer から DB を直接参照・編集する |

---

## 2. システム構成

### 2.1 全体構成

```
[ ブラウザ ]
     │ http://localhost:8080
     ▼
┌──────────────┐  /api/*  ┌────────────────────┐      ┌────────────────┐
│    nginx     │─────────▶│       webapp       │─────▶│       db       │
│ (1.27-alpine)│          │     (Go + Gin)     │      │  (MySQL 8.0)   │
│              │   /      └────────────────────┘      └────────────────┘
│              │─────┐                                         ▲
└──────────────┘     ▼                                         │ :8081
            ┌────────────────────┐                    ┌────────────────┐
            │      frontend      │                    │    adminer     │
            │     (Next.js)      │                    │    (4.x)       │
            └────────────────────┘                    └────────────────┘
```

すべてのリクエストは nginx (ホスト `:8080`) を経由し、同一オリジンで配信されるため **CORS 設定は不要**。

### 2.2 サービス一覧

| サービス | イメージ / ビルド元 | 公開ポート | 役割 |
|----------|--------------------|-----------|------|
| `nginx` | `nginx:1.27-alpine` | `8080:80` | リバースプロキシ。`/api/` をバックエンド、それ以外をフロントへ振り分ける |
| `webapp` | `webapp/go` | 内部 `8080` (expose) | API サーバ (Go + Gin + GORM) |
| `frontend` | `webapp/frontend/next` | 内部 `3000` (expose) | 画面 (Next.js) |
| `db` | `mysql:8.0` | `3306:3306` | データストア。初回起動時に `webapp/sql/*.sql` を自動投入 |
| `adminer` | `adminer:4` | `8081:8080` | DB 管理 UI (開発用) |

`webapp` / `frontend` はホストにポートを公開せず `expose` のみ。外部からの入口は nginx と adminer に限定する。

### 2.3 ルーティング (`development/nginx/default.conf`)

| パス | プロキシ先 | 備考 |
|------|-----------|------|
| `/api/` 配下 | `webapp:8080` | `proxy_read_timeout 30s`、`X-Real-IP` / `X-Forwarded-For` / `X-Forwarded-Proto` を付与 |
| 上記以外 (`/`) | `frontend:3000` | `Upgrade` / `Connection: upgrade` を付与し、開発サーバの HMR (WebSocket) を通す |

リクエストボディ上限は `client_max_body_size 10m`。

### 2.4 起動方式 (Compose ファイルの重ね合わせ)

`compose-base.yml` (db / nginx / adminer) に、バックエンド用・フロントエンド用の compose ファイルを重ねて `webapp` / `frontend` サービスを注入する。採用スタックでは以下の3枚を重ねる。

```bash
docker compose \
  -f development/compose-base.yml \
  -f development/compose-backend-go.yml \
  -f development/compose-frontend-next.yml \
  -p cleaning up -d --build
```

`Makefile` / `Taskfile.yml` がこのコマンドのショートカットを提供する。

| コマンド | 内容 |
|----------|------|
| `make up` | ビルドして起動。既定値が `BACKEND=go` / `FRONTEND=next` なので、採用スタックでは引数の指定は不要 |
| `make down` | 停止 (DB ボリュームは保持) |
| `make restart` | `down` → `up` |
| `make build` | ビルドのみ |
| `make logs` | 全サービスのログ追跡 |
| `make ps` | 状態確認 |
| `make seed` | DB ボリュームを削除して初期化 SQL を再投入 |
| `make nuke` | ボリューム・ローカルビルドイメージまで破棄 (不可逆) |

`BACKEND` / `FRONTEND` を明示指定すれば参考実装にも切り替えられる (`check-stack` ターゲットで値を検証し、想定外の値は起動前にエラーとなる)。

### 2.5 技術スタック

| 層 | 採用 | 備考 |
|----|------|------|
| バックエンド | **Go 1.22 + Gin v1.10 + GORM v1.31** (`webapp/go`) | ドライバは `gorm.io/driver/mysql` |
| フロントエンド | **Next.js (React, Pages Router, TypeScript)** (`webapp/frontend/next`) | `/api/*` を相対パスで呼ぶ |
| データストア | MySQL 8.0 | |
| リバースプロキシ | Nginx 1.27 | |
| 実行環境 | Docker Compose | |
| DB 管理 UI | Adminer 4 (開発用) | |

参考実装として Python (FastAPI + SQLAlchemy) / Ruby (Rails 7 API mode) / Nuxt 3 / SvelteKit がリポジトリに残っており、`make up BACKEND=.. FRONTEND=..` で起動できる。nginx 設定・DB スキーマ・API 仕様はどの組み合わせでも共通のため、比較検証にはそのまま使える。

### 2.6 バックエンドのレイヤ構成

「ハンドラ → サービス → リポジトリ → DB」の4層構成。Gin 依存のコードは `handler` / `router` の薄い層に閉じ込め、`service` 層はフレームワークに依存させない。

| レイヤ | ディレクトリ | 役割 |
|--------|-------------|------|
| エントリポイント | `cmd/server/main.go` | 設定読み込み → DB 接続 → ルータ起動 |
| ルーティング | `internal/router/` | `/api` 配下のパスとハンドラの対応付け |
| ハンドラ | `internal/handler/` | リクエスト受け取りと JSON 応答、HTTP ステータスの決定 |
| サービス | `internal/service/` | 当番生成などのビジネスロジック |
| リポジトリ | `internal/repository/` | GORM を使った DB アクセス。`employee` / `area` / `duty` の3つ |
| モデル / 型定義 | `internal/domain/model.go` | GORM モデル (`Employee` / `Area` / `Duty`) と API 応答用の `DutyView` |
| 接続・設定 | `internal/db/`, `internal/config/` | MySQL 接続 (リトライ付き)、環境変数の読み込み |

---

## 3. 機能設計

### 3.1 機能一覧

| ID | 機能名 | 概要 | 対応 API |
|----|--------|------|----------|
| F-01 | ヘルスチェック | DB 接続を含む死活確認 | `GET /api/health` |
| F-02 | 社員一覧参照 | 全社員を ID 順に取得 | `GET /api/employees` |
| F-03 | エリア一覧参照 | 全掃除エリアを ID 順に取得 | `GET /api/areas` |
| F-04 | 当番一覧参照 | 当番を社員名・エリア名込みで日付順に取得 | `GET /api/duties` |
| F-05 | 当番生成 | 翌週5日分 × 全エリアの当番をランダム抽選で登録 | `POST /api/duties/generate` |

### 3.2 当番生成ロジック (F-05)

`internal/service/duty_generator.go` に実装する (参考実装の Python / Ruby も同一アルゴリズム)。

1. `employees` から `active = 1` の社員 ID を全件取得する。
2. `areas` から全エリア ID を取得する。
3. いずれかが空の場合はエラー (`employees or areas is empty`) とし、HTTP 400 を返す。
4. 社員 ID リストをシャッフルする (乱数シードは実行時刻ベース)。
5. 実行日の **7日後から11日後まで** の5日間について、日ごとに全エリアを走査し、シャッフル済みリストの先頭から順に (剰余でラップしながら) 社員を割り当てる。
6. 生成した当番を `status = 'pending'` で**1トランザクションにまとめて INSERT** する。
7. 登録件数を `{"created": <件数>}` として返す。

```
生成件数 = 5日 × エリア件数   (初期データでは 5 × 5 = 25件)
対象期間 = 実行日 + 7日 〜 実行日 + 11日
```

**設計上の留意点**

- 「翌週5営業日」を意図しているが、実装は**単純な連続5日**であり、土日祝の除外は行っていない。実行する曜日によって期間が週内に収まらない。
- 既存の当番を削除しないため、同じ期間に対して複数回実行すると当番が重複して登録される。
- 公平性は「シャッフル + ラウンドロビン」のみで担保しており、過去の担当回数は考慮していない。社員数がエリア件数×5 を上回る場合、1回の生成で当番が回ってこない社員が出る。

### 3.3 画面設計

フロントエンドは単一画面 (`/` = `pages/index.tsx`) で、以下の要素を持つ。

| 要素 | 内容 |
|------|------|
| 見出し | アプリ名 (実装フレームワーク名を併記) |
| 生成ボタン | 押下で `POST /api/duties/generate` を実行。処理中は disabled、完了時に生成件数をダイアログ表示し一覧を再取得 |
| 社員一覧 | 氏名と部署を件数付きで列挙 |
| 当番一覧 | 「日付 / エリア / 担当 / 状態」の4列テーブル |

初期表示時に `GET /api/employees` と `GET /api/duties` を並列で呼び出す。API は相対パス (`/api/...`) で呼ぶため、環境ごとのエンドポイント設定を持たない。

---

## 4. API 設計

- ベース URL: `http://localhost:8080/api`
- リクエスト / レスポンスとも `application/json` (UTF-8)
- 認証: なし
- 日付は `YYYY-MM-DD` 形式の文字列

### 4.1 `GET /api/health`

死活確認。DB への `Ping` / `SELECT 1` を実行する。

| ステータス | ボディ |
|-----------|--------|
| 200 | `{"status": "ok"}` |
| 500 | `{"status": "ng", "error": "<エラーメッセージ>"}` |

### 4.2 `GET /api/employees`

社員一覧を `id` 昇順で返す (`active` による絞り込みは行わない)。

```json
[
  { "id": 1, "name": "佐藤 一郎", "email": "sato.ichiro@example.com", "department": "営業部", "active": true }
]
```

| フィールド | 型 | 説明 |
|-----------|----|------|
| `id` | number | 社員ID |
| `name` | string | 氏名 |
| `email` | string | メールアドレス |
| `department` | string | 部署名 |
| `active` | boolean | 在籍フラグ |

エラー時は 500 / `{"error": "..."}`。

### 4.3 `GET /api/areas`

掃除エリア一覧を `id` 昇順で返す。

```json
[
  { "id": 1, "name": "会議室A", "description": "机・椅子の整頓、ホワイトボード消去" }
]
```

| フィールド | 型 | 説明 |
|-----------|----|------|
| `id` | number | エリアID |
| `name` | string | エリア名 |
| `description` | string | 作業内容 |

エラー時は 500 / `{"error": "..."}`。

### 4.4 `GET /api/duties`

当番一覧を `scheduled_date` 昇順 → `areas.id` 昇順で返す。社員名・エリア名を JOIN 済みで含むため、フロントは追加の問い合わせを行わない。期間絞り込みのパラメータは持たず、常に全件を返す。

```json
[
  {
    "id": 1,
    "employee_id": 1,
    "employee_name": "佐藤 一郎",
    "area_id": 1,
    "area_name": "会議室A",
    "scheduled_date": "2026-08-27",
    "status": "pending"
  }
]
```

| フィールド | 型 | 説明 |
|-----------|----|------|
| `id` | number | 当番ID |
| `employee_id` | number | 担当社員ID |
| `employee_name` | string | 担当社員の氏名 |
| `area_id` | number | エリアID |
| `area_name` | string | エリア名 |
| `scheduled_date` | string | 実施予定日 (`YYYY-MM-DD`) |
| `status` | string | `pending` / `done` / `swapped` |

エラー時は 500 / `{"error": "..."}`。

### 4.5 `POST /api/duties/generate`

翌週分の当番を生成する。リクエストボディなし。

| ステータス | ボディ | 発生条件 |
|-----------|--------|----------|
| 200 | `{"created": 25}` | 正常終了。`created` は登録件数 |
| 400 | `{"error": "employees or areas is empty"}` | 有効な社員またはエリアが0件 |
| 500 | `{"error": "..."}` | DB エラー等 |

参考実装の FastAPI (Python) では、400 のボディが FastAPI の既定形式 `{"detail": "..."}` になる。参考実装に切り替えて動作確認する場合は注意する。

---

## 5. 非機能設計

### 5.1 環境変数 (webapp コンテナ)

| 変数 | 既定値 | 説明 |
|------|--------|------|
| `DB_HOST` | `db` | 接続先ホスト |
| `DB_PORT` | `3306` | 接続先ポート |
| `DB_USER` | `cleaning` | DB ユーザ |
| `DB_PASS` | `cleaning` | DB パスワード |
| `DB_NAME` | `cleaning` | データベース名 |
| `PORT` | `8080` | 待ち受けポート |

採用スタックは `Makefile` 変数の既定値 (`BACKEND=go` / `FRONTEND=next`) と一致しているため、通常は指定不要。参考実装を起動する場合のみ上書きする (`.env.example` に例を記載)。

### 5.2 起動順序制御

- `db` は `mysqladmin ping` によるヘルスチェックを持つ (5秒間隔・最大20回・起動猶予30秒)。
- `webapp` は `depends_on: db (service_healthy)` により、DB が healthy になるまで起動しない。
- さらに `internal/db` が **2秒間隔で最大30回 (最長60秒) の接続リトライ**を行い、初回起動時の DB 初期化待ちを吸収する
  (`gorm.Open` 後に `*sql.DB` を取り出して `Ping` している)。
- `nginx` は `webapp` / `frontend` に依存する (起動順のみ、healthy 待ちはしない)。

### 5.3 文字コード

DB・接続文字列とも `utf8mb4` に統一する。日本語データの文字化けを防ぐため、以下をすべて揃えている。

- MySQL サーバ起動オプション: `--character-set-server=utf8mb4` / `--collation-server=utf8mb4_unicode_ci` / `--skip-character-set-client-handshake`
- 初期化 SQL 冒頭: `SET NAMES utf8mb4;`
- 接続 DSN: `charset=utf8mb4&parseTime=true&loc=Local` (GORM の `gorm.io/driver/mysql` に渡す)

### 5.4 性能・可用性

プロトタイプのため冗長化・スケールアウトは考慮しない。データ量は社員30名・当番が週25件増加する規模を想定し、`duties` には `scheduled_date` と `employee_id` のインデックスを用意している。

### 5.5 セキュリティ

| 項目 | 現状 |
|------|------|
| 認証・認可 | なし。API・画面とも誰でもアクセスできる |
| 通信の暗号化 | なし (HTTP)。ローカル開発前提 |
| 資格情報 | DB のユーザ/パスワードは compose ファイルに平文で記述 |
| DB ポート | `3306` をホストに公開している |
| SQL インジェクション | GORM のパラメータバインドを使用。`Where("id = ?", id)` のように値は必ず `?` で渡す |

**本番運用にはそのまま適さない**。社内公開する場合は認証の追加、資格情報の外部化、`3306` / `8081` の非公開化が前提となる。

---

## 6. 制約事項

| # | 制約 | 影響 |
|---|------|------|
| 1 | 当番生成は連続5日を対象とし、土日祝を除外しない | 実行曜日によって週をまたぐ割当になる |
| 2 | 当番生成は追記のみで、既存当番を削除・置換しない | 複数回実行すると同一日・同一エリアの当番が重複する |
| 3 | `duties.status` を更新する API がない | 完了報告・交代の反映ができず、常に `pending` のまま |
| 4 | `swap_requests` テーブルは未使用 | 交代申請機能は未実装 |
| 5 | 社員・エリアの登録/更新 API がない | マスタ整備は seed SQL または Adminer 経由 |
| 6 | 認証・認可がない | 利用者の識別ができず「自分の当番」を出せない |
| 7 | 自動テストがない | API の互換性・回帰は手動確認に依存 |
| 8 | 採用しなかった実装 (Python / Ruby / Nuxt / SvelteKit) がリポジトリに残っている | 変更時に追随しないため、参考実装として次第に古くなる |

## 7. 拡張の方針

以下は README の「次のステップ」を、本設計書の構造に沿って整理したもの。

| 優先度 | 項目 | 設計上の起点 |
|--------|------|-------------|
| 高 | 当番状態の更新 API (`pending` → `done`) | `duties.status`。`PATCH /api/duties/:id` を追加 |
| 高 | 当番生成ロジックの改善 (営業日判定・重複防止・担当回数の平準化) | `internal/service/duty_generator.go` |
| 中 | 交代申請機能 | `swap_requests` テーブル。`from_employee_id` / `to_employee_id` への FK 追加も併せて検討 |
| 中 | 通知連携 (メール / Slack) | 当番生成後のフックとしてサービス層に追加 |
| 中 | レポート / ダッシュボード (完了率・社員別頻度) | `duties` の集計クエリ |
| 低 | 認証 (社内 SSO / OIDC) | nginx またはバックエンドの入口層 |
| 低 | フロントの状態管理ライブラリ導入 (TanStack Query 等) | `pages/index.tsx` の一覧取得部分 |
