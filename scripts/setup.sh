#!/bin/bash

echo "🚀 Setting up Coding Server..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create .env from example if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Install Ollama from https://ollama.ai/"
echo "2. Pull some models:"
echo "   ollama pull deepseek-coder:6.7b"
echo "3. Start the server:"
echo "   source venv/bin/activate"
echo "   python src/coding_server.py"
echo ""
echo "Or use the run script:"
echo "   chmod +x scripts/run_server.sh"
echo "   ./scripts/run_server.sh"