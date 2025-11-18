#!/bin/bash
# Fix installation script - removes old venv and reinstalls with compatible versions

echo "🔧 Fixing installation..."

# Remove old virtual environment
if [ -d "venv" ]; then
    echo "🗑️  Removing old virtual environment..."
    rm -rf venv
fi

# Create new virtual environment with Python 3.11 or 3.12 if available
echo "📦 Creating new virtual environment..."
if command -v python3.11 &> /dev/null; then
    echo "   Using Python 3.11"
    python3.11 -m venv venv
elif command -v python3.12 &> /dev/null; then
    echo "   Using Python 3.12"
    python3.12 -m venv venv
else
    echo "   Using default Python 3"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Initialize database
echo "🗄️  Initializing database..."
python -c "from database import init_db; init_db(); print('✅ Database initialized!')"

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Create admin account: python3 setup_admin.py"
echo "2. Start server: ./start.sh"
echo "   Or: uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

