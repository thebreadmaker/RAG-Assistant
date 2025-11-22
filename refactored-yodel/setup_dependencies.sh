#!/bin/bash

# Refactored YodeL - Dependency Installation Script
# Run this from the project root: bash setup_dependencies.sh

set -e

echo "🚀 Setting up Refactored YodeL dependencies..."
echo ""

# Navigate to backend directory
cd "$(dirname "$0")/refactored-yodel/backend"

echo "📦 Step 1: Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

echo ""
echo "📦 Step 2: Activating virtual environment..."
source venv/bin/activate

echo ""
echo "📦 Step 3: Upgrading pip..."
pip install --upgrade pip

echo ""
echo "📦 Step 4: Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "📦 Step 5: Downloading embedding model..."
python3 << EOF
from sentence_transformers import SentenceTransformer
print("Downloading all-MiniLM-L6-v2 model...")
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print("✅ Model downloaded successfully")
EOF

echo ""
echo "✅ All dependencies installed!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source refactored-yodel/backend/venv/bin/activate"
echo "2. Start services: cd refactored-yodel/scripts && ./boot.sh"
echo ""
echo "Or use VS Code's Python interpreter selector to choose: ./refactored-yodel/backend/venv/bin/python"
