# webapp/go — Go (Gin) バックエンド

掃除当番アプリの **Go 実装**。Web フレームワークは [Gin](https://github.com/gin-gonic/gin)、DB は `database/sql` + `go-sql-driver/mysql` で生 SQL を叩く構成。

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
    │   └── db.go                 # MySQL 接続 + 起動待ちリトライ
    ├── domain/
    │   └── model.go              # Employee / Area / Duty 構造体
    ├── repository/
    │   ├── employee.go           # 社員クエリ
    │   ├── area.go               # エリアクエリ
    │   └── duty.go               # 当番クエリ + バッチ挿入
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
| GET    | `/api/employees`         | `Handler.ListEmployees`          |
| GET    | `/api/areas`             | `Handler.ListAreas`              |
| GET    | `/api/duties`            | `Handler.ListDuties`             |
| POST   | `/api/duties/generate`   | `Handler.GenerateDuties`         |

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
| 新しいテーブル                       | `domain/model.go` + 新しい `repository/*.go` |
| 当番割当ロジックの差し替え           | `service/duty_generator.go`                 |
| DB 接続プールの調整                  | `db/db.go`                                  |
| バリデーション導入                   | `go-playground/validator` を `handler` に追加 |
| OpenAPI ドキュメント                 | `swaggo/swag` の導入を検討                  |
| 構造化ログ                           | `slog` (stdlib) or `zerolog` に差し替え     |

## ローカルでのテスト (Docker 無し)

```bash
cd webapp/go
DB_HOST=127.0.0.1 go run ./cmd/server
```

別途 MySQL を起動しておくこと。
