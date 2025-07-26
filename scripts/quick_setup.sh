#!/bin/bash
# Quick setup script for SkyFi MCP Server

echo "🚀 SkyFi MCP Server Quick Setup"
echo "==============================="
echo ""

# Check if .env exists
if [ -f .env ]; then
    echo "✅ .env file found"
else
    echo "Creating .env file..."
    cp config/.env.example .env
    
    echo ""
    echo "⚠️  Please edit .env file with your settings:"
    echo ""
    echo "1. Set NGROK_DOMAIN to your reserved domain"
    echo "2. Set NGROK_AUTHTOKEN from ngrok dashboard"
    echo ""
    read -p "Press Enter after editing .env file..."
fi

# Load environment
source .env

# Verify required settings
if [ -z "$NGROK_DOMAIN" ] || [ "$NGROK_DOMAIN" = "your-reserved-domain.ngrok-free.app" ]; then
    echo "❌ Error: Please set NGROK_DOMAIN in .env file"
    exit 1
fi

if [ -z "$NGROK_AUTHTOKEN" ] || [ "$NGROK_AUTHTOKEN" = "your_ngrok_auth_token_here" ]; then
    echo "❌ Error: Please set NGROK_AUTHTOKEN in .env file"
    exit 1
fi

# Setup virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -e . --quiet

# Configure ngrok
echo "Configuring ngrok..."
ngrok config add-authtoken $NGROK_AUTHTOKEN

# Make scripts executable
chmod +x scripts/*.sh

echo ""
echo "✅ Setup complete!"
echo ""
echo "Your server URL will be: https://$NGROK_DOMAIN"
echo ""
echo "To start the server:"
echo "  ./scripts/start_production_server.sh"
echo ""
echo "To install as a service:"
echo "  sudo ./scripts/install_service.sh"
echo ""