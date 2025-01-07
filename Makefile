SHELL := /usr/bin/env -S bash -O globstar # makes work globs like **/*.py
.DEFAULT_GOAL := deploy

outdated:
	uv tree -d 1 --outdated | grep -E '──.*latest:'

deploy: linter
	uv sync
	ansible-playbook deploy.yml --skip-tags=full

full-deploy:
	uv sync
	ansible-playbook deploy.yml

init: clean
	uv venv -q
	uv sync

clean:
	rm -rf .venv db.sqlite3

githooks:
	git config --local core.hooksPath .githooks

linter: githooks
	python -m py_compile **/*.py
	uvx ruff format
	uvx ruff check --fix

safety:
	uv tool run safety scan -o bare
