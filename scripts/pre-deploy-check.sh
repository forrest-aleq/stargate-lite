#!/bin/bash
# Pre-deployment checklist
# Run this before any production deployment

set -e

echo "🔍 Running pre-deployment checks..."

# 1. Mypy
echo "1/5 Type checking..."
mypy app/ --no-error-summary || { echo "❌ Mypy failed"; exit 1; }
echo "✅ Type check passed"

# 2. Ruff lint
echo "2/5 Linting..."
ruff check app/ || { echo "❌ Ruff failed"; exit 1; }
echo "✅ Lint passed"

# 3. Tests
echo "3/5 Running tests..."
pytest tests/ -q || { echo "❌ Tests failed"; exit 1; }
echo "✅ Tests passed"

# 4. Version check
echo "4/5 Version check..."
python scripts/release_check.py || { echo "❌ Version check failed"; exit 1; }
echo "✅ Version matches changelog"

# 5. Import check
echo "5/5 Import check..."
python -c "from app.main import app; print(f'Version: {app.version}')" || { echo "❌ Import failed"; exit 1; }
echo "✅ App imports correctly"

echo ""
echo "✅ All pre-deployment checks passed!"
echo "Safe to deploy."
