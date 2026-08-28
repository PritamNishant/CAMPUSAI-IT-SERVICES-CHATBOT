#!/bin/bash

# CampusFix AI Backend Setup Script

echo "=========================================="
echo "   CampusFix AI - Backend Setup"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3."
    exit 1
fi

echo "✓ pip3 found"
echo ""

# Check if .env file exists
if [ ! -f "../.env" ]; then
    echo "❌ .env file not found in project root!"
    echo "Please create a .env file with your MONGO_URI"
    exit 1
fi

echo "✓ .env file found"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✓ Dependencies installed successfully"
echo ""

# Initialize database
echo "🗄️  Initializing database..."
python3 init_db.py

if [ $? -ne 0 ]; then
    echo "❌ Failed to initialize database"
    echo "Please check your MONGO_URI in .env file"
    exit 1
fi

echo ""
echo "=========================================="
echo "   ✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Run the backend: python3 app.py"
echo "2. Test the API: curl http://localhost:5001/api/health"
echo "3. Update frontend to use backend API"
echo ""
echo "Backend will run at: http://localhost:5001"
echo ""
