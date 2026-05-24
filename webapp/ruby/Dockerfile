FROM ruby:3.3.5-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential default-libmysqlclient-dev pkg-config \
 && rm -rf /var/lib/apt/lists/*

COPY Gemfile ./
RUN bundle install

COPY Rakefile config.ru ./
COPY config ./config
COPY app ./app

ENV RAILS_ENV=production \
    RAILS_LOG_TO_STDOUT=1 \
    SECRET_KEY_BASE=dummy_for_local_dev_only_replace_in_real_production

RUN mkdir -p tmp log

EXPOSE 8080
CMD ["bundle", "exec", "puma", "-C", "config/puma.rb"]
