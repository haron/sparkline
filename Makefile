SHELL := /usr/bin/env -S bash -O globstar # makes work globs like **/*.py
.DEFAULT_GOAL := deploy
# the host stays out of this public repo: one line in the gitignored `hosts`
HOST ?= $(or $(shell cat hosts 2>/dev/null),$(error put the deploy host in ./hosts))
SLUG := sparkline-prod
PREFIX := /var/www/$(SLUG)

outdated:
	uv tree -d 1 --outdated | grep -E '──.*latest:'

# Code, .env (0600, the sandboxed unit reads it as a credential), then ansible-pets' app-deploy
# (uv sync, restart; FRESH=--fresh rebuilds the venv). No CI deploy: public repo, no runner.
deploy: linter
	rsync -a -F ./ deploy@$(HOST):$(PREFIX)/
	ssh deploy@$(HOST) 'umask 077 && cat > $(PREFIX)/.env' < env-prod
	ssh deploy@$(HOST) app-deploy $(SLUG) $(FRESH)

full-deploy:
	$(MAKE) deploy FRESH=--fresh

logs:
	ssh -t deploy@$(HOST) journalctl -eu app@$(SLUG)

restart:
	ssh deploy@$(HOST) systemctl restart app@$(SLUG)

init: clean
	uv venv -q
	uv sync

clean:
	rm -rf .venv db.sqlite3

githooks:
	git config --local core.hooksPath .githooks

linter: githooks
	uv run python -m py_compile **/*.py
	uvx ruff format
	uvx ruff check --fix

safety:
	uv tool run safety scan -o bare
