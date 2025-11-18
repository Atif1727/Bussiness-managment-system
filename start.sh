#!/bin/bash
# Startup script for Fahran Business System

echo "🚀 Starting Fahran Business Investment System..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    # Try Python 3.11 first (most compatible), fallback to python3
    if command -v python3.11 &> /dev/null; then
        python3.11 -m venv venv
    elif command -v python3.12 &> /dev/null; then
        python3.12 -m venv venv
    else
        python3 -m venv venv
    fi
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Initialize database
echo "🗄️  Initializing database..."
python3 -c "from database import init_db; init_db(); print('Database initialized!')"

# Check if admin exists
echo "👤 Checking for admin account..."
python3 -c "from database import SessionLocal, Member; db = SessionLocal(); admins = db.query(Member).filter(Member.is_top_member == True).count(); db.close(); exit(0 if admins > 0 else 1)" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "⚠️  No admin account found. Please run: python3 setup_admin.py"
    echo "   Or continue and create admin via API/DB"
fi

# Start server
echo "🌐 Starting server on http://localhost:8000"
echo "   Press Ctrl+C to stop"
echo ""
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

