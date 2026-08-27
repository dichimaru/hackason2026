# 社内掃除当番アプリ — 開発用 Makefile
#
# 使い方:
#   make up                           # 既定 (BACKEND=go FRONTEND=next)
#   make up BACKEND=python FRONTEND=nuxt
#   make up BACKEND=ruby   FRONTEND=svelte
#   make down
#   make logs
#   make seed                         # DBを再初期化 (volume削除 → 再up)
#   make ps
#   make docs                         # 設計ドキュメント (docs/*.md → xlsx) を再生成
#
# 起動後:
#   http://localhost:8080         アプリ (Nginx → frontend/api)
#   http://localhost:8081         Adminer (DB管理UI, server=db user=cleaning pass=cleaning)

BACKEND  ?= go
FRONTEND ?= next
# Windows など python3 が無い環境では: make docs PYTHON=python
PYTHON   ?= python3

DEV_DIR := development
COMPOSE := docker compose \
  -f $(DEV_DIR)/compose-base.yml \
  -f $(DEV_DIR)/compose-backend-$(BACKEND).yml \
  -f $(DEV_DIR)/compose-frontend-$(FRONTEND).yml \
  -p cleaning

.PHONY: up down restart build logs ps seed nuke check-stack docs docs-xlsx docs-figures help

help:
	@echo "Targets: up / down / restart / build / logs / ps / seed / nuke / docs"
	@echo "Vars:    BACKEND={go|python|ruby}  FRONTEND={next|nuxt|svelte}"
	@echo "Current: BACKEND=$(BACKEND)  FRONTEND=$(FRONTEND)"

check-stack:
	@case "$(BACKEND)"  in go|python|ruby) ;;     *) echo "Invalid BACKEND=$(BACKEND)";  exit 1 ;; esac
	@case "$(FRONTEND)" in next|nuxt|svelte) ;;   *) echo "Invalid FRONTEND=$(FRONTEND)"; exit 1 ;; esac

up: check-stack
	$(COMPOSE) up -d --build

build: check-stack
	$(COMPOSE) build

down:
	$(COMPOSE) down --remove-orphans

restart: down up

logs:
	$(COMPOSE) logs -f --tail=200

ps:
	$(COMPOSE) ps

# seed = DBボリュームを消して、init SQLを再投入 (= 0_schema.sql + 1_seed.sql)
seed:
	$(COMPOSE) down -v
	$(COMPOSE) up -d

# 全イメージ・ボリューム・コンテナを破棄 (注意: 不可逆)
nuke:
	$(COMPOSE) down -v --rmi local --remove-orphans

# --- 設計ドキュメント ---------------------------------------------------
# docs/*.md が正。xlsx と docs/images/*.png は生成物なので直接編集しない。
docs: docs-figures docs-xlsx

# md → xlsx (Python 標準ライブラリのみ。Node.js 不要)
docs-xlsx:
	$(PYTHON) docs/tools/md2xlsx.py

# md 内の mermaid → PNG (Node.js 必要。初回のみ mermaid-cli を取得)
docs-figures:
	$(PYTHON) docs/tools/render_mermaid.py
