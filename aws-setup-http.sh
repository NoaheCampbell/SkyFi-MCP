#!/bin/bash
# Setup script for AWS instance with HTTP server and ngrok

echo "Setting up SkyFi MCP HTTP server..."

# Update package manager
sudo yum update -y

# Install Python 3.11
sudo yum install -y python3.11 python3.11-pip git

# Install ngrok
echo "Installing ngrok..."
curl -O https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/
rm ngrok-v3-stable-linux-amd64.tgz

# Clone repository
cd ~
git clone https://github.com/NoaheCampbell/SkyFi-MCP.git
cd SkyFi-MCP

# Install Python dependencies
python3.11 -m pip install -e .

# Create systemd service for HTTP server
sudo tee /etc/systemd/system/skyfi-mcp-http.service << 'EOF'
[Unit]
Description=SkyFi MCP HTTP Server
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/SkyFi-MCP
ExecStart=/usr/bin/python3.11 -m src.mcp_skyfi --transport http --port 8000
Restart=always
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable skyfi-mcp-http
sudo systemctl start skyfi-mcp-http

echo "HTTP server started on port 8000"
echo ""
echo "Next steps:"
echo "1. Add your ngrok authtoken: ngrok authtoken YOUR_TOKEN"
echo "2. Start ngrok tunnel: ngrok http 8000"
echo "3. Copy the HTTPS URL from ngrok"
echo "4. Update claude-config-http-ngrok.json with:"
echo "   - Your ngrok URL"
echo "   - Your SkyFi API key"
echo ""
echo "Test the server locally first:"
echo "curl http://localhost:8000/"
echo "curl http://localhost:8000/health"