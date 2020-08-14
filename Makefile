
# https://tech.davis-hansson.com/p/make/
SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eux -o pipefail -c
.DELETE_ON_ERROR:
.SILENT:
.DEFAULT_GOAL := all
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

.PHONY: all
all: lint test ## Run lint and test (default goal)

.PHONY: lint
lint: ## Lint all source code
	poetry run yapf -q -r bme280
	poetry run pylint --ignore=snapshots bme280 tests

.PHONY: test
test: ## Run all tests
	poetry run pytest

.PHONY: rebase-three-branch
rebase-three-branch: ## Rebase the py3 branch with master contents
	git stash
	git checkout master
	git pull
	git checkout three
	git rebase -i origin/master
	git push --force-with-lease
	git checkout master
	git stash pop

.PHONY: help
help: ## Print this help text
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
