#!/bin/bash
# Setup script for DevNavigator

set -e

echo "🚀 Setting up DevNavigator..."

# Create directories
mkdir -p database data logs

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Node dependencies
echo "📦 Installing Node dependencies..."
npm install

# Initialize database
echo "🗄️  Initializing database..."
python3 devnavigator.py init-db

# Create sample templates
echo "📝 Creating sample templates..."
python3 python_engine/template_manager.py

# Build C++ crawler
echo "🔧 Building C++ email sender..."
npm run build:cpp

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure .env file with your SMTP credentials"
echo "2. Extract emails: python3 devnavigator.py extract-emails --file emails.txt --store"
echo "3. Send emails: npm run send:emails"
echo "4. Check stats: python3 devnavigator.py stats"
