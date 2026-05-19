#!/bin/bash

set -euo pipefail

REQUIRED_PYTHON="3.12"
PYTHON_BIN="${PYTHON_BIN:-python3.12}"
VENV_DIR=".venv"

echo "========================================="
echo "Stargate Lite Setup Script"
echo "========================================="
echo ""

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "❌ ${PYTHON_BIN} is not installed. Install Python ${REQUIRED_PYTHON} first."
    exit 1
fi

PYTHON_VERSION="$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [ "$PYTHON_VERSION" != "$REQUIRED_PYTHON" ]; then
    echo "❌ ${PYTHON_BIN} resolved to Python ${PYTHON_VERSION}. Expected ${REQUIRED_PYTHON}."
    exit 1
fi

echo "✅ Python found: $("$PYTHON_BIN" --version)"
echo ""

if [ -x "${VENV_DIR}/bin/python" ]; then
    EXISTING_VERSION="$("${VENV_DIR}/bin/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    if [ "$EXISTING_VERSION" != "$REQUIRED_PYTHON" ]; then
        echo "♻️  Replacing stale ${VENV_DIR} (found Python ${EXISTING_VERSION})..."
        rm -rf "${VENV_DIR}"
    fi
fi

echo "📦 Creating virtual environment..."
"$PYTHON_BIN" -m venv "$VENV_DIR"

echo "🔌 Activating virtual environment..."
source "${VENV_DIR}/bin/activate"

echo "⬆️  Upgrading pip..."
python -m pip install --upgrade pip

echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "🔐 Generating encryption key..."
python <<'EOF'
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print("\nYour encryption key (add this to .env as ENCRYPTION_KEY):")
print(key.decode())
EOF

if [ ! -f ".env" ]; then
    echo ""
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Edit .env before starting the app."
else
    echo ""
    echo "ℹ️  .env file already exists, skipping..."
fi

echo ""
echo "🪝 Installing pre-commit hooks..."
pip install pre-commit
pre-commit install
pre-commit install --hook-type pre-push

echo ""
echo "========================================="
echo "✅ Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Review .env and add required credentials"
echo "2. Run: source ${VENV_DIR}/bin/activate"
echo "3. Run: alembic upgrade head"
echo "4. Run: python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001"
