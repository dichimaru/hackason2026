# webapp/go — Go (Gin) バックエンド

掃除当番アプリの **Go 実装**。Web フレームワークは [Gin](https://github.com/gin-gonic/gin)、DB アクセスは [GORM](https://gorm.io/ja_JP/docs/) (`gorm.io/driver/mysql`) を使う。

テーブル定義は `webapp/sql/0_schema.sql` を正とするため、`AutoMigrate` は呼ばない。

## フォルダ構成

```
webapp/go/
├── Dockerfile                    # 2段ビルド (golang:1.22 → distroless static)
├── .dockerignore
├── go.mod
├── cmd/
│   └── server/
│       └── main.go               # エントリポイント (依存組み立て + 起動)
└── internal/
    ├── config/
    │   └── config.go             # 環境変数の読み込み
    ├── db/
    │   └── db.go                 # GORM 初期化 (MySQL) + 起動待ちリトライ
    ├── domain/
    │   └── model.go              # GORM モデル (Employee / Area / Duty) + DutyView
    ├── repository/
    │   ├── employee.go           # 社員クエリ (GORM)
    │   ├── area.go               # エリアクエリ (GORM)
    │   └── duty.go               # 当番クエリ (Preload) + バッチ挿入
    ├── service/
    │   └── duty_generator.go     # 当番自動割当ロジック
    ├── handler/
    │   └── handler.go            # Gin ハンドラ (*gin.Context)
    └── router/
        └── router.go             # ルーティング登録
```

### 依存方向

```
cmd/server  →  router  →  handler  →  service / repository  →  domain / db
                                                       ↑
                                                    config
```

下のレイヤは上を知らない。Gin に依存するのは `handler` / `router` のみで、`service` / `repository` / `domain` は他のフレームワークに乗り換えても流用可能。

## エンドポイント

| Method | Path                     | ハンドラ                         |
|--------|--------------------------|----------------------------------|
| GET    | `/api/health`            | `Handler.Health`                 |
| GET    | `/api/people`                 | `Handler.ListEmployees`          |
| GET    | `/api/tasks`                  | `Handler.ListAreas`              |
| GET    | `/api/lottery-results`        | `Handler.ListDuties`             |
| POST   | `/api/lottery-results/generate` | `Handler.GenerateDuties`         |

## 環境変数

| 変数      | 既定値     | 用途                |
|-----------|------------|---------------------|
| `DB_HOST` | `db`       | MySQL ホスト        |
| `DB_PORT` | `3306`     | MySQL ポート        |
| `DB_USER` | `cleaning` | DB ユーザ           |
| `DB_PASS` | `cleaning` | DB パスワード       |
| `DB_NAME` | `cleaning` | DB 名               |
| `PORT`    | `8080`     | リッスンポート      |

`compose-base.yml` から自動注入されるのでローカルでは設定不要。

## 起動 (リポジトリルートから)

```bash
make up BACKEND=go          # 既定なので make up でもOK
make logs                   # ログ追跡
make down                   # 停止
```

## 拡張ポイント

| やりたいこと                         | 触る場所                                    |
|--------------------------------------|---------------------------------------------|
| 新しいエンドポイント追加             | `handler/handler.go` + `router/router.go`   |
| 新しいテーブル                       | `webapp/sql/0_schema.sql` + `domain/model.go` + 新しい `repository/*.go` |
| 当番割当ロジックの差し替え           | `service/duty_generator.go`                 |
| DB 接続プールの調整                  | `db/db.go` (`gdb.DB()` で `*sql.DB` を取得して設定) |
| 発行される SQL の確認                | `db/db.go` の Logger を `logger.Info` にする |
| バリデーション導入                   | `go-playground/validator` を `handler` に追加 |
| OpenAPI ドキュメント                 | `swaggo/swag` の導入を検討                  |
| 構造化ログ                           | `slog` (stdlib) or `zerolog` に差し替え     |

## ローカルでのテスト (Docker 無し)

```bash
cd webapp/go
DB_HOST=127.0.0.1 PORT=8888 go run ./cmd/server
```

DB は `make up` で起動している MySQL (ホストの `3306`) をそのまま使える。
`PORT` を変えているのは、`8080` が Nginx、`8081` が Adminer で埋まっているため。
この場合フロントからは繋がらないので、`curl http://localhost:8888/api/lottery-results` で直接叩いて確認する。

なお Go をローカルに入れていない場合は、Docker 経由でビルドと静的解析ができる。

```bash
docker run --rm -v "$PWD":/src -w /src golang:1.22-alpine \
  sh -c "gofmt -l . && go vet ./... && go build ./..."
```
