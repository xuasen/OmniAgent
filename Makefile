.PHONY: dev test lint format migrate clean docker-up docker-down

dev:
	uvicorn omniagent.app:create_app --factory --host 0.0.0.0 --port 8000 --reload

test:
	pytest tests/ -v --tb=short

test-unit:
	pytest tests/unit/ -v --tb=short -m unit

test-integration:
	pytest tests/integration/ -v --tb=short -m integration

test-cov:
	pytest tests/ --cov=src/omniagent --cov-report=html --cov-report=term

lint:
	ruff check src/ tests/
	mypy src/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

migrate:
	alembic upgrade head

migrate-create:
	alembic revision --autogenerate -m "$(msg)"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache .ruff_cache .pytest_cache htmlcov dist build *.egg-info

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-test:
	docker compose run --rm test

install:
	pip install -e ".[dev]"
