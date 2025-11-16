.PHONY: help install test lint format run dev docker-build docker-run k8s-deploy clean

ifneq (,$(wildcard ./.env))
include .env
export
endif

install: ## Install dependencies
	uv sync

test:
	uv run pytest

test-cov:
	uv run pytest --cov=app --cov-report=term-missing

lint:
	uv run ruff check .
	uv run mypy domain application infrastructure main.py

format:
	uv run black .
	uv run ruff check --fix .

run:
	PYTHONPATH=app uv run python src/main.py

docker-build:
	docker build -t sqs-worker:latest .

docker-run: ## Run Docker container locally
	docker run --rm \
		--env-file .env \
		-p 8080:8080 \
		sqs-worker:latest

clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf htmlcov .coverage