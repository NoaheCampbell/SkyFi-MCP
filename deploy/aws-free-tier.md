# AWS Free Tier Setup (12 months free)

## Option 1: AWS EC2

### 1. Launch EC2 Instance
1. Go to [AWS Console](https://console.aws.amazon.com)
2. EC2 → Launch Instance
3. Choose:
   - AMI: Ubuntu Server 22.04 LTS (Free tier eligible)
   - Instance Type: t2.micro (Free tier)
   - Configure Security Group:
     - SSH (22) from your IP
     - Custom TCP (5456) from anywhere

### 2. Connect and Install
```bash
ssh ubuntu@YOUR_INSTANCE_IP

# One-line install
curl -sSL https://raw.githubusercontent.com/YOUR_REPO/mcp-skyfi/main/deploy/setup-server.sh | sudo bash
```

### 3. Configure Claude Desktop
```json
{
  "mcpServers": {
    "skyfi-remote": {
      "command": "nc",
      "args": ["YOUR_INSTANCE_IP", "5456"],
      "env": {
        "SKYFI_API_KEY": "your-api-key"
      }
    }
  }
}
```

## Option 2: Google Cloud Free Tier

### 1. Create VM
```bash
gcloud compute instances create mcp-skyfi \
  --machine-type=e2-micro \
  --zone=us-central1-a \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --tags=mcp-server

# Create firewall rule
gcloud compute firewall-rules create allow-mcp \
  --allow tcp:5456 \
  --source-ranges 0.0.0.0/0 \
  --target-tags mcp-server
```

### 2. Install (same as AWS)

## Option 3: Azure Free Tier
- B1s instance (750 hours/month free for 12 months)
- Similar setup process

## Free Forever Options:

### 1. Oracle Cloud (Best Free Option)
- 2 VMs forever free
- See oracle-cloud-setup.md

### 2. Google Cloud Run (Serverless)
Would need HTTP adapter, but scales to zero when not in use:
```dockerfile
FROM python:3.10-slim
RUN pip install socat
COPY . /app
WORKDIR /app
RUN pip install -e .
CMD ["socat", "TCP-LISTEN:$PORT,fork,reuseaddr", "EXEC:python3 -m mcp_skyfi"]
```

### 3. Fly.io (Free tier)
- 3 shared-cpu-1x VMs
- 160GB outbound transfer
```bash
fly launch
fly deploy
```