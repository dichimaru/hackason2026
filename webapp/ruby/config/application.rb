require_relative "boot"

require "rails"
require "active_model/railtie"
require "active_record/railtie"
require "action_controller/railtie"

Bundler.require(*Rails.groups)

module CleaningApi
  class Application < Rails::Application
    config.load_defaults 7.2

    # API mode
    config.api_only = true

    # 既存スキーマ(webapp/sql)で構造管理。Railsのマイグレーションは使わない。
    config.active_record.dump_schema_after_migration = false

    # autoload
    config.autoload_paths += %W[#{config.root}/app/services]

    config.eager_load = ENV.fetch("RAILS_ENV", "development") == "production"
  end
end
