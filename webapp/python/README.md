# webapp/python — Python (FastAPI) バックエンド

掃除当番アプリの **Python 実装**。Web フレームワークは [FastAPI](https://fastapi.tiangolo.com/)、DB は [SQLAlchemy 2.0](https://docs.sqlalchemy.org/) の Core API (`text(...)` でSQL文字列)、ASGI サーバは [uvicorn](https://www.uvicorn.org/) の構成。

## フォルダ構成

```
webapp/python/
├── Dockerfile                       # python:3.12-slim 単段
├── .dockerignore
├── requirements.txt                 # 依存ピン留め
└── app/
    ├── __init__.py
    ├── main.py                      # FastAPI() + ルータ登録だけ
    ├── core/
    │   ├── config.py                # 環境変数 → Settings dataclass
    │   └── db.py                    # SQLAlchemy engine (起動待ちリトライ)
    ├── api/
    │   ├── deps.py                  # FastAPI Depends() で engine を注入
    │   └── routes/
    │       ├── health.py
    │       ├── employees.py
    │       ├── areas.py
    │       └── duties.py
    ├── schemas/                     # Pydantic モデル (入出力スキーマ)
    │   ├── employee.py
    │   ├── area.py
    │   └── duty.py
    └── services/
        └── duty_generator.py        # 当番自動割当ロジック
```

### 依存方向

```
main.py  →  api/routes/*  →  schemas / services / api/deps
                                              ↓
                                       core/{config, db}
```

`api/routes/*` だけが FastAPI に依存。`services` / `schemas` / `core` は FastAPI から独立。

## エンドポイント

| Method | Path                     | ルート                                   |
|--------|--------------------------|------------------------------------------|
| GET    | `/api/health`            | `app.api.routes.health.health`           |
| GET    | `/api/people`                  | `app.api.routes.employees.list_employees`|
| GET    | `/api/tasks`                   | `app.api.routes.areas.list_areas`        |
| GET    | `/api/lottery-results`         | `app.api.routes.duties.list_duties`      |
| POST   | `/api/lottery-results/generate`| `app.api.routes.duties.post_generate`    |

レスポンスはすべて Pydantic モデルでバリデーション済み。

## OpenAPI / Swagger UI

FastAPI が自動生成します:
- スキーマ: `/openapi.json`
- Swagger UI: `/docs`
- ReDoc: `/redoc`

ただし本プロジェクトは Nginx が `/api/*` のみを webapp に流すので、コンテナ内から直接当てる必要があります:

```bash
docker exec cleaning-webapp curl -s http://localhost:8080/openapi.json | head -30
```

Nginx 設定 (`development/nginx/default.conf`) に `/docs` `/openapi.json` も流すよう加えれば、ブラウザからアクセス可能になります。

## 環境変数

| 変数      | 既定値     | 用途                |
|-----------|------------|---------------------|
| `DB_HOST` | `db`       | MySQL ホスト        |
| `DB_PORT` | `3306`     | MySQL ポート        |
| `DB_USER` | `cleaning` | DB ユーザ           |
| `DB_PASS` | `cleaning` | DB パスワード       |
| `DB_NAME` | `cleaning` | DB 名               |

`compose-base.yml` から自動注入。

## 起動 (リポジトリルートから)

```bash
make up BACKEND=python
make logs
make down
```

## 拡張ポイント

| やりたいこと                         | 触る場所                                              |
|--------------------------------------|-------------------------------------------------------|
| 新しいエンドポイント追加             | `app/api/routes/<name>.py` 追加 + `app/main.py` で登録 |
| 新しい入出力スキーマ                 | `app/schemas/<name>.py`                               |
| ビジネスロジック                     | `app/services/`                                       |
| 設定を `.env` 経由にしたい           | `pydantic-settings` を導入、`core/config.py` を移行   |
| ORM を本格採用                       | SQLAlchemy 2.0 の Declarative + `app/models/` 追加    |
| 非同期化                             | `create_async_engine` + asyncpg/aiomysql、ルートも async |
| 認証                                 | `fastapi.security` + `Depends(get_current_user)`      |

## ローカルでのテスト (Docker 無し)

```bash
cd webapp/python
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
DB_HOST=127.0.0.1 uvicorn app.main:app --reload --port 8080
```

別途 MySQL を起動しておくこと。
