#!/bin/bash
# Quick setup script for AI Provider Configuration

umask 077

echo "=========================================="
echo "AI Provider Configuration Setup"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from template..."
    while IFS= read -r line; do
        case "$line" in
            GEMINI_API_KEY=*|OPENAI_API_KEY=*|ANTHROPIC_API_KEY=*|MISTRAL_API_KEY=*|GROQ_API_KEY=*|COHERE_API_KEY=*|HF_TOKEN=*|OPENROUTER_API_KEY=*|KILO_API_KEY=*|TOGETHER_API_KEY=*|REPLICATE_API_TOKEN=*)
                echo "${line%%=*}="
                ;;
            *)
                echo "$line"
                ;;
        esac
    done < .env.example > .env
    chmod 600 .env
    echo "✓ .env created"
    echo "⚠️  You need to add your API keys to .env"
else
    chmod 600 .env
    echo "✓ .env already exists"
fi

# Create a locked secrets store for API keys
if [ ! -d secrets ]; then
    mkdir -p secrets
fi
chmod 700 secrets
echo "✓ Secure secrets directory ready"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 not found"
    exit 1
fi

echo "✓ Python 3 found"

# Create virtual environment
if [ ! -d venv ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate
echo "✓ Virtual environment activated"

# Install requirements
echo ""
echo "Installing requirements..."
pip install -q -r requirements.txt
echo "✓ Requirements installed"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env or use: python providers.py store <provider>"
echo "2. Run: python providers.py all"
echo "3. Run: python client.py list"
echo "4. Try: python client.py chat gemini 'Hello!'"
echo ""
