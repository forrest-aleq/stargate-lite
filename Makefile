.PHONY: help setup run test docker-up docker-down clean

help:
	@echo "Stargate Lite - Available Commands"
	@echo "===================================="
	@echo "  make setup       - Run initial setup"
	@echo "  make run         - Start the server (development)"
	@echo "  make test        - Run test suite"
	@echo "  make docker-up   - Start with Docker Compose"
	@echo "  make docker-down - Stop Docker containers"
	@echo "  make clean       - Clean temporary files"
	@echo ""

setup:
	@echo "Setting up Stargate Lite..."
	chmod +x setup.sh
	./setup.sh

run:
	@echo "Starting Stargate Lite..."
	@. venv/bin/activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

test:
	@echo "Running tests..."
	@. venv/bin/activate && python test.py

docker-up:
	@echo "Starting Docker containers..."
	docker-compose up -d
	@echo "✅ Stargate Lite is running at http://localhost:8001"

docker-down:
	@echo "Stopping Docker containers..."
	docker-compose down

docker-logs:
	docker-compose logs -f stargate-lite

clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	rm -rf .pytest_cache
	@echo "✅ Cleanup complete!"
