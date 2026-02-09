#!/bin/bash

echo "========================================="
echo "Stargate Lite Setup Script"
echo "========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7+ first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Generate encryption key
echo ""
echo "🔐 Generating encryption key..."
python3 << 'EOF'
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(f"\nYour encryption key (add this to .env as ENCRYPTION_KEY):")
print(key.decode())
EOF

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API credentials!"
else
    echo ""
    echo "ℹ️  .env file already exists, skipping..."
fi

# Run database migrations
echo ""
echo "🗄️  Running database migrations..."
alembic upgrade head

echo ""
echo "========================================="
echo "✅ Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your API credentials"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001"
echo ""
