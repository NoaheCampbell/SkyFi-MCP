# Deploying SkyFi MCP Server on AWS

This guide explains how to deploy the SkyFi MCP server on AWS for use with Claude Desktop or Cursor.

## Overview

When running on AWS, you cannot use environment variables to store API keys since the MCP client (Claude Desktop/Cursor) starts the server fresh each time. Instead, we provide multiple secure authentication methods.

## Authentication Methods

### 1. Runtime Configuration (Recommended)

The simplest method for cloud deployment:

```bash
# First, check authentication status
skyfi_check_auth

# Then set your API key
skyfi_set_api_key api_key="your-skyfi-api-key-here"
```

The key is stored temporarily and persists across tool calls within the same session.

### 2. AWS Secrets Manager

Store your API key in AWS Secrets Manager:

```bash
# Create secret
aws secretsmanager create-secret \
  --name skyfi/api-key \
  --secret-string '{"api_key":"your-skyfi-api-key-here"}'

# Grant your EC2 instance access via IAM role
```

### 3. AWS Systems Manager Parameter Store

Store your API key in Parameter Store:

```bash
# Create parameter
aws ssm put-parameter \
  --name /skyfi/api-key \
  --value "your-skyfi-api-key-here" \
  --type SecureString

# Grant your EC2 instance access via IAM role
```

### 4. Configuration File

Create a config file on the instance:

```bash
mkdir -p ~/.skyfi
echo '{"api_key":"your-skyfi-api-key-here"}' > ~/.skyfi/config.json
chmod 600 ~/.skyfi/config.json
```

## AWS EC2 Setup

### 1. Launch EC2 Instance

```bash
# Recommended instance type: t3.small or larger
# AMI: Amazon Linux 2 or Ubuntu 22.04
```

### 2. Install Dependencies

```bash
# Update system
sudo yum update -y  # For Amazon Linux
# or
sudo apt update && sudo apt upgrade -y  # For Ubuntu

# Install Python 3.11+
sudo yum install python3.11 -y
# or
sudo apt install python3.11 python3.11-venv -y

# Install git
sudo yum install git -y
# or
sudo apt install git -y
```

### 3. Clone and Install MCP Server

```bash
# Clone repository
git clone https://github.com/yourusername/mcp-skyfi.git
cd mcp-skyfi

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .
```

### 4. Configure MCP Server

Create the MCP server configuration:

```bash
# For Claude Desktop (on your local machine)
# Edit: ~/Library/Application Support/Claude/claude_desktop_config.json

{
  "mcpServers": {
    "skyfi": {
      "command": "ssh",
      "args": [
        "-i", "/path/to/your-key.pem",
        "ec2-user@your-instance-ip",
        "cd /home/ec2-user/mcp-skyfi && source venv/bin/activate && python -m mcp_skyfi"
      ]
    }
  }
}
```

### 5. Set Up IAM Role (for AWS auth methods)

Create an IAM role with these policies:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:skyfi/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/skyfi/*"
    }
  ]
}
```

## Security Considerations

1. **Network Security**
   - Use SSH tunneling or VPN for MCP connections
   - Restrict EC2 security group to your IP only
   - Enable SSH key-based authentication only

2. **API Key Security**
   - Never commit API keys to git
   - Use IAM roles for AWS-based auth
   - Rotate keys regularly
   - Set budget limits in SkyFi

3. **Instance Security**
   - Keep system updated
   - Use minimal IAM permissions
   - Enable CloudWatch logging
   - Set up automated backups

## Usage Workflow

1. Start Claude Desktop or Cursor
2. The MCP server connects via SSH
3. First time setup:
   ```
   # Check auth status
   skyfi_check_auth
   
   # Set API key
   skyfi_set_api_key api_key="sk-..."
   ```
4. Use SkyFi tools normally

## Troubleshooting

### Connection Issues
- Check SSH key permissions: `chmod 600 your-key.pem`
- Verify security group allows SSH from your IP
- Test SSH connection manually first

### Authentication Issues
- Run `skyfi_check_auth` to see current status
- Check IAM role permissions if using AWS auth
- Verify API key is valid at app.skyfi.com

### Performance Issues
- Use larger instance type for heavy workloads
- Consider using EBS optimized instances
- Monitor CloudWatch metrics

## Cost Optimization

1. **Auto-shutdown**: Set up Lambda to stop instance when idle
2. **Spot Instances**: Use for development/testing
3. **Reserved Instances**: For production workloads
4. **S3 Storage**: Store downloaded images in S3 instead of EBS

## Alternative: Lambda Deployment

For serverless deployment, you can package the MCP server as a Lambda function with API Gateway. Contact support for Lambda deployment guide.