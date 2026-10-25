.PHONY: help install generate migrate push studio start test bench

# ── Configuration ──────────────────────────────────────────────────────────────
PYTHON     := python
UVICORN    := uvicorn
PYTEST     := pytest
PRISMA     := prisma

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ── Dependency Management ──────────────────────────────────────────────────────
install:  ## Install all Python dependencies
	pip install -r requirements.txt

# ── Prisma Commands ────────────────────────────────────────────────────────────
generate:  ## Generate the Prisma Python client from schema.prisma
	$(PRISMA) generate

migrate:  ## Create a new tracked migration and apply it (set NAME= for description)
	$(PRISMA) migrate dev --name $(or $(NAME),auto)

push:  ## Push schema changes to the DB without creating a migration file (dev only)
	$(PRISMA) db push

pull:  ## Introspect the database and update schema.prisma
	$(PRISMA) db pull

studio:  ## Open Prisma Studio (browser-based DB GUI)
	$(PRISMA) studio

reset:  ## Drop and recreate the database (DANGER: deletes all data)
	$(PRISMA) migrate reset --force

# ── Docker ─────────────────────────────────────────────────────────────────────
up:  ## Start all services (postgres, pgadmin, api, prometheus, grafana)
	docker compose up -d --build

down:  ## Stop all services
	docker compose down

logs:  ## Tail API logs
	docker compose logs -f api

db-shell:  ## Open psql shell inside the postgres container
	docker compose exec postgres psql -U sign0 -d sign0db

pgadmin:  ## Open pgAdmin URL in browser
	@echo "pgAdmin available at http://localhost:5050"
	@echo "  Email   : admin@sign0.ai"
	@echo "  Password: (see PGADMIN_PASSWORD in .env)"

# ── Local Development ──────────────────────────────────────────────────────────
start:  ## Start the FastAPI dev server with hot-reload
	$(UVICORN) app:app --host 0.0.0.0 --port 8000 --reload

# ── Testing ────────────────────────────────────────────────────────────────────
test:  ## Run the full test suite
	$(PYTEST) tests/ -v

test-cov:  ## Run tests with coverage report
	$(PYTEST) tests/ -v --cov=backend --cov-report=term-missing

# ── Benchmarks ─────────────────────────────────────────────────────────────────
bench:  ## Run the SignCodec 48-byte latency benchmark
	$(PYTHON) ml/benchmarks/run_codec_demo.py

bench-latency:  ## Run ONNX inference P50/P99 latency profiler
	$(PYTHON) ml/benchmarks/benchmark_latency.py
