# 社内掃除当番アプリ — ハッカソン2026

「30名規模オフィス向け掃除当番管理システム」のプロトタイプ雛形です。
ISUCON14 風に **Docker Compose で一発起動** できるよう構成しており、
**バックエンド3 (Go / Python / Ruby) × フロントエンド3 (Next.js / Nuxt / SvelteKit) = 9通り** を
ビルド時オプションで切り替えられます。

## デザイン / ワイヤーフレーム

- Figma: [掃除当番抽選アプリ](https://www.figma.com/design/e32i2DHHXEFeU8X15bmHbX/%E6%8E%83%E9%99%A4%E5%BD%93%E7%95%AA%E6%8A%BD%E9%81%B8%E3%82%A2%E3%83%97%E3%83%AA?node-id=0-1&m=dev&t=FIzCNAGSJpc7yaOB-1)

## 構成

### トップレベル

```
hackason2026/
├── README.md
├── Makefile / Taskfile.yml           # 起動ショートカット
├── .env.example
├── .claude/                          # Claude Code 設定
├── development/                      # 起動側 (compose / nginx 設定)
└── webapp/                           # アプリ側 (バックエンド3 + フロント3 + DB)
```

### development/ — 起動・プロキシ層

```
development/
├── compose-base.yml                  # 共通: db (MySQL) + nginx + adminer
├── compose-backend-go.yml            # webapp サービスに Go を差し込む
├── compose-backend-python.yml        # 〃 Python
├── compose-backend-ruby.yml          # 〃 Ruby
├── compose-frontend-next.yml         # frontend サービスに Next.js を差し込む
├── compose-frontend-nuxt.yml         # 〃 Nuxt
├── compose-frontend-svelte.yml       # 〃 SvelteKit
└── nginx/
    └── default.conf                  # /api/* → webapp:8080, / → frontend:3000
```

`compose-base.yml` + `compose-backend-X.yml` + `compose-frontend-Y.yml` の3枚を重ねて起動する仕組み。

### webapp/ — アプリ層

#### 共通 (DB初期化SQL)

```
webapp/sql/
├── 0_schema.sql                      # cleaning DB スキーマ
└── 1_seed.sql                        # 30名 + 5エリア + 25当番
```

MySQL コンテナの `/docker-entrypoint-initdb.d` にマウントされ初回起動時に自動投入。

#### バックエンド (3言語)

すべて `/api/health` `/api/employees` `/api/areas` `/api/duties` `/api/duties/generate` を公開。各言語でWeb フレームワークを採用し、それぞれの**標準的なフォルダ構成**に合わせています。詳細は各 README を参照。

```
webapp/go/                            # Gin + database/sql  → webapp/go/README.md
├── Dockerfile
├── go.mod
├── cmd/server/main.go                # エントリポイント
└── internal/
    ├── config/                       # 環境変数
    ├── db/                           # MySQL 接続
    ├── domain/                       # Employee / Area / Duty
    ├── repository/                   # DB アクセス
    ├── service/                      # ビジネスロジック
    ├── handler/                      # Gin ハンドラ
    └── router/                       # ルーティング

webapp/python/                        # FastAPI + SQLAlchemy → webapp/python/README.md
├── Dockerfile
├── requirements.txt
└── app/
    ├── main.py                       # FastAPI() + ルータ登録
    ├── core/                         # config / db
    ├── api/                          # routes + deps
    │   └── routes/                   # health, employees, areas, duties
    ├── schemas/                      # Pydantic モデル
    └── services/                     # ビジネスロジック

webapp/ruby/                          # Rails 7 API mode → webapp/ruby/README.md
├── Dockerfile
├── Gemfile
├── Rakefile
├── config.ru
├── config/                           # application / database / routes / puma / environments
└── app/
    ├── controllers/                  # ActionController::API
    ├── models/                       # ActiveRecord
    └── services/                     # ビジネスロジック
```

> **設計方針**: 3言語で「handler/controller → service → repository/model → db」の共通レイヤ構造を保ちつつ、各フレームワークの慣習に従う。フレームワーク依存コードは `handler`/`controllers`/`routes` などの薄い層に閉じ込め、`service`/`models` 層は乗り換え可能に。

#### フロントエンド (3フレームワーク)

すべて `/api/*` を相対パスで叩く。Nginx 経由で同一オリジンなので CORS 不要。

```
webapp/frontend/next/                 # Next.js (React, Pages Router)
├── Dockerfile
├── package.json
├── next.config.js
├── tsconfig.json
└── pages/
    ├── _app.tsx
    └── index.tsx                     # 当番一覧 + 生成ボタン

webapp/frontend/nuxt/                 # Nuxt 3 (Vue)
├── Dockerfile
├── package.json
├── nuxt.config.ts
├── tsconfig.json
├── app.vue
└── pages/
    └── index.vue

webapp/frontend/svelte/               # SvelteKit
├── Dockerfile
├── package.json
├── svelte.config.js
├── vite.config.js
└── src/
    ├── app.html
    └── routes/
        └── +page.svelte
```

### 起動時のサービス構成 (どの組み合わせでも同じ)

```
[ browser ]
    │ :8080
    ▼
┌───────────┐    /api/*   ┌────────────────┐    ┌──────────┐
│  nginx    │────────────▶│     webapp     │───▶│    db    │
│ (1.27)    │             │ (go|py|ruby)   │    │ (MySQL 8)│
│           │     /       └────────────────┘    └──────────┘
│           │─────────┐                                ▲
└───────────┘         │                                │ :8081
                      ▼                          ┌──────────┐
            ┌────────────────────┐               │ adminer  │
            │      frontend      │               └──────────┘
            │ (next|nuxt|svelte) │
            └────────────────────┘
```

選んだ `BACKEND=` / `FRONTEND=` に応じて `webapp` と `frontend` の中身だけが入れ替わる。

### 共通 API

すべてのバックエンドが同じ API を公開します:

| Method | Path                     | 説明                          |
|--------|--------------------------|-------------------------------|
| GET    | `/api/health`            | ヘルスチェック                |
| GET    | `/api/employees`         | 社員一覧                      |
| GET    | `/api/areas`             | 掃除エリア一覧                |
| GET    | `/api/duties`            | 当番一覧 (社員名・エリア名込み) |
| POST   | `/api/duties/generate`   | 翌週5日分の当番をランダム生成 |

## セットアップ

### 必要なもの

| ツール | 用途 | 備考 |
|--------|------|------|
| **Docker Desktop** (Compose v2 同梱) | コンテナ起動 | Windows / Mac 共通 |
| **GNU Make** | 起動ショートカット | 無くても docker compose 直叩きでOK ([後述](#make-が無い環境でも動かす)) |
| Git | リポジトリ取得 | |

ポート `8080` / `8081` / `3306` をローカルで使うので、空けておくこと。

### 1. Docker Desktop をインストール

- **Windows**: <https://www.docker.com/products/docker-desktop/> から DL → インストール → 起動
  - WSL2 バックエンドを推奨 (インストーラの既定)
- **Mac**: 同上 URL から Apple Silicon / Intel 用を選んで DL
  - もしくは `brew install --cask docker`

インストール後に Docker Desktop を起動し、タスクトレイのクジラアイコンが「Running」になることを確認。

```bash
docker --version          # 例: Docker version 29.x
docker compose version    # 例: Docker Compose version v2.x  (← v2 であること)
```

### 2. GNU Make をインストール

#### Windows

いずれか1つでOK (Scoop 推奨: 管理者権限不要)。

```powershell
# Scoop (推奨)
# https://scoop.sh/ の手順で Scoop 自体をまずインストール、その後:
scoop install main/make

# または winget (Windows 10/11 標準)
winget install GnuWin32.Make
# winget の場合、PATH 追加が必要なことがある: C:\Program Files (x86)\GnuWin32\bin

# または Chocolatey
choco install make
```

確認:
```powershell
make --version    # GNU Make 4.x
```

> PowerShell から `make` を実行します。Git Bash でも動きます。

#### Mac

Xcode Command Line Tools に含まれています。

```bash
xcode-select --install   # 未インストールならこれだけ
make --version           # GNU Make 3.x が入る (今回の Makefile は 3/4 どちらでも動く)
```

GNU Make 4 を使いたければ `brew install make` (コマンド名は `gmake`)。

#### Linux

```bash
sudo apt install make    # Debian / Ubuntu
sudo dnf install make    # Fedora
```

### 3. リポジトリ取得 → 起動

```bash
git clone <このリポジトリのURL> hackason2026
cd hackason2026

make up                  # 既定: Go + Next.js
```

初回はイメージビルドに数分かかります。完了したら以下で起動確認:

```bash
make ps                  # 5サービス (db / webapp / frontend / nginx / adminer) が Up
```

ブラウザで:
- アプリ: <http://localhost:8080>
- DB管理UI (Adminer): <http://localhost:8081>
  - System: `MySQL`, Server: `db`, Username: `cleaning`, Password: `cleaning`, Database: `cleaning`

API も直接叩けます (PowerShell では `curl` の代わりに `Invoke-RestMethod` を使用):

```bash
curl http://localhost:8080/api/health
curl http://localhost:8080/api/employees
curl -X POST http://localhost:8080/api/duties/generate
```

### 4. 日常操作

```bash
make up BACKEND=python FRONTEND=nuxt   # 組み合わせを変えて起動
make up BACKEND=ruby   FRONTEND=svelte

make down                # 停止 (DBデータは残る)
make restart             # down → up
make logs                # 全サービスのログを追跡 (Ctrl+C で抜ける)
make ps                  # 状態確認
make seed                # DBを再初期化 (volume削除 → init SQL 再投入)
make nuke                # 完全リセット (volume + ローカルビルドイメージ破棄)
```

Taskfile 派なら同じことが `task up BACKEND=python FRONTEND=nuxt` でできます (Taskfile を使う場合は <https://taskfile.dev/installation/> から `task` をインストール)。

### make が無い環境でも動かす

`make up` の実体は `docker compose` の長いコマンドです。Makefile を見れば等価コマンドが分かりますが、よく使うものを抜粋:

```bash
# 起動 (Go + Next.js)
docker compose \
  -f development/compose-base.yml \
  -f development/compose-backend-go.yml \
  -f development/compose-frontend-next.yml \
  -p cleaning up -d --build

# 停止
docker compose -f development/compose-base.yml \
  -f development/compose-backend-go.yml \
  -f development/compose-frontend-next.yml \
  -p cleaning down
```

### トラブルシューティング

| 症状 | 対処 |
|------|------|
| `make: command not found` | 上記「2. GNU Make をインストール」を参照 |
| `docker: command not found` | Docker Desktop が起動していない / PATH が通っていない |
| `port is already allocated` (8080等) | 既存プロセスがポートを使用中。`make down` で停止、または該当プロセスを終了 |
| ビルドが途中で固まる | Docker Desktop の Settings → Resources でメモリを 4GB 以上に |
| DBが壊れた / シードが古い | `make seed` で再初期化 |
| `Invalid BACKEND=xxx` | `BACKEND={go|python|ruby}` / `FRONTEND={next|nuxt|svelte}` のいずれかを指定 |

## 9通りの組み合わせ

| BACKEND \\ FRONTEND | `next`           | `nuxt`           | `svelte`           |
|---------------------|------------------|------------------|--------------------|
| `go`                | Go + Next.js     | Go + Nuxt        | Go + SvelteKit     |
| `python`            | Python + Next.js | Python + Nuxt    | Python + SvelteKit |
| `ruby`              | Ruby + Next.js   | Ruby + Nuxt      | Ruby + SvelteKit   |

すべて同じ Nginx 設定・同じ DB スキーマ・同じ API 仕様で動きます。
チームで好きな組み合わせを試して、開発体験や性能を比較できます。

## 設計上のポイント

- **共通I/F**: フロントは全実装で `/api/*` を相対パスで叩くだけ。CORS不要。
- **Nginx前段**: `/api/*` を `webapp:8080` に、それ以外を `frontend:3000` にプロキシ。
  各 compose ファイルで `webapp` / `frontend` という名前のサービスを差し込む構造。
- **DB初期化**: MySQL公式イメージの `/docker-entrypoint-initdb.d` に `webapp/sql/*.sql` を
  マウントしているので、`make seed` (volume削除 → 再up) で簡単に初期化できる。
- **生成ロジック**: `/api/duties/generate` は社員リストをシャッフルしてから
  5営業日 × 全エリアに割り当てるシンプルなラウンドロビン。
  公平性の強化やスケジュール連携はここを起点に拡張。

## 次のステップ (実装の伸ばし方)
- [ ] 当番状態 (`pending` → `done`) を更新するAPI
- [ ] 通知 (メール/Slack) 連携
- [ ] レポート/ダッシュボード集計 (完了率、社員別頻度)
- [ ] 認証 (社内SSO / OIDC) の組み込み
- [ ] フロントの状態管理ライブラリ (TanStack Query 等) 導入
## 参考資料
- [機能一覧](https://docs.google.com/spreadsheets/d/1-29wuKeMmVg6Gu3cdoodapO5eMVD_kYcFn3enIEWSuU/edit?gid=0#gid=0)
