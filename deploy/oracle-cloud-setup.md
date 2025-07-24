# Free Hosting on Oracle Cloud (Always Free Tier)

Oracle Cloud offers a generous always-free tier with:
- 2 AMD-based VMs (1/8 OCPU, 1GB RAM each)
- 200GB storage
- 10TB outbound data/month

## Step 1: Sign Up
1. Go to [cloud.oracle.com](https://cloud.oracle.com)
2. Sign up for free account (credit card required but won't be charged)

## Step 2: Create VM Instance
1. Navigate to Compute → Instances
2. Click "Create Instance"
3. Choose:
   - Image: Ubuntu 22.04
   - Shape: VM.Standard.E2.1.Micro (Always Free)
   - Add your SSH key

## Step 3: Configure Networking
1. Go to your VCN (Virtual Cloud Network)
2. Security Lists → Add Ingress Rule:
   - Source: 0.0.0.0/0 (or your IP for better security)
   - Destination Port: 5456
   - Protocol: TCP

## Step 4: Install MCP Server
SSH into your instance:
```bash
ssh ubuntu@YOUR_INSTANCE_IP

# Quick install
curl -sSL https://raw.githubusercontent.com/YOUR_REPO/mcp-skyfi/main/deploy/oracle-setup.sh | sudo bash
```

## Step 5: Configure Claude Desktop
```json
{
  "mcpServers": {
    "skyfi-remote": {
      "command": "nc",
      "args": [
        "YOUR_INSTANCE_IP",
        "5456"
      ],
      "env": {
        "SKYFI_API_KEY": "YOUR_SKYFI_API_KEY_HERE",
        "SKYFI_COST_LIMIT": "40.0",
        "SKYFI_FORCE_LOWEST_COST": "true",
        "SKYFI_ENABLE_ORDERING": "true",
        "SKYFI_REQUIRE_CONFIRMATION": "true",
        "SKYFI_REQUIRE_HUMAN_APPROVAL": "true",
        "SKYFI_MAX_ORDER_COST": "20.0",
        "SKYFI_DAILY_LIMIT": "40.0"
      }
    }
  }
}
```

That's it! No socat needed on client.