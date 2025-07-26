# AWS Amazon Linux Setup Guide for SkyFi MCP Server

## Quick Setup for Amazon Linux

### 1. Install Dependencies

```bash
# Update system
sudo yum update -y

# Install Python 3 and Git
sudo yum install -y python3 python3-pip git

# Install development tools (needed for some Python packages)
sudo yum groupinstall -y "Development Tools"
sudo yum install -y python3-devel

# Install ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
sudo tar xvzf ngrok-v3-stable-linux-amd64.tgz -C /usr/local/bin
rm ngrok-v3-stable-linux-amd64.tgz
```

### 2. Clone and Setup the Server

```bash
# Clone the repository
git clone https://github.com/NoaheCampbell/SkyFi-MCP.git
cd SkyFi-MCP

# Install Python dependencies
pip3 install -e .

# Set up configuration
cp config/.env.example .env
nano .env
```

Edit `.env` with your details:
```
NGROK_DOMAIN=your-reserved-domain.ngrok-free.app
NGROK_AUTHTOKEN=your_ngrok_auth_token_here
MCP_PORT=8080
AUTH_PORT=8081
```

### 3. Configure Ngrok

```bash
# Add your ngrok auth token
ngrok config add-authtoken YOUR_NGROK_AUTH_TOKEN
```

### 4. Start the Server

```bash
# Make the script executable
chmod +x scripts/start_production_server.sh

# Start the server
./scripts/start_production_server.sh
```

## Running as a Service with systemd

```bash
# Copy and edit the service file
sudo cp scripts/skyfi-mcp.service /etc/systemd/system/
sudo sed -i 's/ubuntu/ec2-user/g' /etc/systemd/system/skyfi-mcp.service

# Enable and start the service
sudo systemctl enable skyfi-mcp
sudo systemctl start skyfi-mcp

# Check status
sudo systemctl status skyfi-mcp
```

## Firewall Configuration

```bash
# Open ports if needed (usually not required with ngrok)
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --permanent --add-port=8081/tcp
sudo firewall-cmd --reload
```