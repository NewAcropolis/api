.DEFAULT_GOAL := help
SHELL := /bin/bash

.PHONY: help
help:
	@cat $(MAKEFILE_LIST) | grep -E '^[a-zA-Z_-]+:.*?## .*$$' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: current
current: ## Current db
	python app_start.py db current

.PHONY: migrate
migrate: ## Migrate
	python app_start.py db migrate

.PHONY: upgrade
upgrade: ## Upgrade
	python app_start.py db upgrade

.PHONY: downgrade
downgrade: ## Downgrade
	python app_start.py db downgrade

.PHONY: test
test: ## Run all tests
	./scripts/run_tests.sh

.PHONY: test-one
test-one: ## Test one, make test-one test=<test function name>
	pytest -k ${test}

.PHONY: test-dir
test-dir: ## Test directory under tests/app, make test-dir dir=<directory of tests>
	pytest tests/app/${dir}

.PHONY: run
run: ## Run app
	./scripts/run_app.sh

.PHONY: integration-test
integration-test: ## Run integration tests
	./scripts/integration_test.sh -a
