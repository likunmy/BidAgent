.PHONY: install run lint test migrate frontend-install frontend-dev install-dev

# ─── Backend ───────────────────────────────────────────────

install:
	cd backend && pip install -e .

install-dev:
	cd backend && pip install -e ".[dev]"

run:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lint:
	cd backend && ruff check . --fix

lint-check:
	cd backend && ruff check .

migrate:
	cd backend && alembic upgrade head

migrate-new:
	cd backend && alembic revision --autogenerate -m "$(name)"

test:
	cd backend && pytest -v

# ─── Frontend ──────────────────────────────────────────────

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

# ─── Database ──────────────────────────────────────────────

db-init:
	mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS bidagent DEFAULT CHARACTER SET utf8mb4;"

# ─── All-in-one ────────────────────────────────────────────

setup: install frontend-install migrate
	@echo "Setup complete. Run 'make run' and 'make frontend-dev' in separate terminals."
