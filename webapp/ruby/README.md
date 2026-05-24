# webapp/ruby — Ruby (Rails 7 API mode) バックエンド

掃除当番アプリの **Ruby 実装**。Web フレームワークは [Ruby on Rails 7.2 API mode](https://guides.rubyonrails.org/api_app.html)、ORM は [ActiveRecord](https://guides.rubyonrails.org/active_record_basics.html)、Web サーバは Puma の構成。

## Rails standard layout (`config.api_only = true`)

```
webapp/ruby/
├── Dockerfile                       # ruby:3.3.5-slim + mysql client
├── .dockerignore
├── Gemfile                          # rails / mysql2 / puma / bootsnap
├── Rakefile                         # rake タスク (rails db: 等)
├── config.ru                        # Rack エントリポイント
├── config/
│   ├── boot.rb                      # Bundler + bootsnap セットアップ
│   ├── application.rb               # CleaningApi::Application 定義
│   ├── environment.rb               # initialize! 呼び出し
│   ├── database.yml                 # DB 接続 (ENV 経由)
│   ├── puma.rb                      # Puma 設定 (bind/threads)
│   ├── routes.rb                    # ルーティング DSL
│   └── environments/
│       ├── development.rb
│       └── production.rb
└── app/
    ├── controllers/
    │   ├── application_controller.rb    # ActionController::API 基底
    │   ├── health_controller.rb
    │   ├── employees_controller.rb
    │   ├── areas_controller.rb
    │   └── duties_controller.rb
    ├── models/
    │   ├── application_record.rb        # ActiveRecord::Base 基底
    │   ├── employee.rb
    │   ├── area.rb
    │   └── duty.rb
    └── services/
        └── duty_generator.rb            # 当番自動割当 (autoload pathに追加済)
```

> Rails の標準構成にほぼ準拠。`api_only = true` なので `views/` `helpers/` `assets/` `javascript/` は不要、`ActionController::API` ベースで JSON 専用。
>
> マイグレーションは使っていません (`db/migrate/` 無し)。DB スキーマは `webapp/sql/0_schema.sql` で MySQL コンテナ初回起動時に投入され、ActiveRecord はそのテーブルに「マップするだけ」。Rails 流儀でやり直すなら `bin/rails g model` でマイグレーションを生成し、`webapp/sql/` を捨てる方向に切り替え。

## エンドポイント

| Method | Path                     | コントローラ                          |
|--------|--------------------------|---------------------------------------|
| GET    | `/api/health`            | `HealthController#show`               |
| GET    | `/api/employees`         | `EmployeesController#index`           |
| GET    | `/api/areas`             | `AreasController#index`               |
| GET    | `/api/duties`            | `DutiesController#index`              |
| POST   | `/api/duties/generate`   | `DutiesController#generate`           |

ルーティングは `config/routes.rb` を参照。

## 環境変数

| 変数               | 既定値     | 用途                                    |
|--------------------|------------|-----------------------------------------|
| `DB_HOST`          | `db`       | MySQL ホスト                            |
| `DB_PORT`          | `3306`     | MySQL ポート                            |
| `DB_USER`          | `cleaning` | DB ユーザ                               |
| `DB_PASS`          | `cleaning` | DB パスワード                           |
| `DB_NAME`          | `cleaning` | DB 名                                   |
| `PORT`             | `8080`     | Puma バインドポート                     |
| `RAILS_ENV`        | `production` | Rails 環境 (Dockerfile で設定)        |
| `RAILS_MAX_THREADS`| `5`        | Puma スレッド数                         |
| `SECRET_KEY_BASE`  | (Dockerfile に dummy 設定) | 本番運用時は必ず差し替え |

## 起動 (リポジトリルートから)

```bash
make up BACKEND=ruby
make logs
make down
```

初回ビルドは Gem インストール (Rails + 依存一式) のため数分かかります。

## 拡張ポイント

| やりたいこと                         | 触る場所                                          |
|--------------------------------------|---------------------------------------------------|
| 新しいエンドポイント追加             | `config/routes.rb` + `app/controllers/<name>_controller.rb` |
| 新しいテーブル / モデル              | `app/models/<name>.rb` (テーブルは `webapp/sql/0_schema.sql` に追加) |
| ビジネスロジック                     | `app/services/`                                   |
| バリデーション                       | モデルに `validates :xxx, presence: true` を追加 |
| シリアライザ                         | `gem "active_model_serializers"` or `gem "jbuilder"` の導入 |
| 認証                                 | `gem "devise"` / `gem "devise-jwt"` の導入        |
| Sidekiq などの非同期処理             | `gem "sidekiq"` + Redis サービスを compose に追加 |
| マイグレーション運用に切り替え       | `bin/rails db:create db:migrate` 運用へ。`webapp/sql/` をリプレース |

## ローカルでのテスト (Docker 無し)

```bash
cd webapp/ruby
bundle install
DB_HOST=127.0.0.1 RAILS_ENV=development bin/rails server -p 8080
```

別途 MySQL を起動しておくこと。`bin/rails` が無い場合は `bundle exec rails ...` で代用できます。

## メモ: Sinatra 版からの移行

旧バージョン (`webapp/ruby/app.rb` 単一ファイルの Sinatra 実装) からの主な変更点:

- フレームワーク: Sinatra 4 → Rails 7 API mode
- DB: Sequel raw SQL → ActiveRecord (`.pluck`/`.joins`)
- ルーティング: `get "/path"` ブロック → `routes.rb` + Controller#action
- 起動: `bundle exec puma config.ru` → `bundle exec puma -C config/puma.rb` (Rails が `config.ru` 経由でロード)
- ファイル数: 4 → 20+ (Rails 流の規約が増えた分)
