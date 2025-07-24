# AWS Cost Protection Guide

## 1. Set Up Billing Alerts (CRITICAL - Do This First!)

### A. Enable Billing Alerts
1. Go to AWS Account → Billing → Billing preferences
2. Check "Receive Billing Alerts"
3. Save preferences

### B. Create CloudWatch Alarms
```bash
# Set alarm for $5
aws cloudwatch put-metric-alarm \
  --alarm-name "billing-alarm-5-dollars" \
  --alarm-description "Alerts when bill exceeds $5" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 86400 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=Currency,Value=USD \
  --evaluation-periods 1
```

Or via Console:
1. CloudWatch → Alarms → Create Alarm
2. Select metric → Billing → Total Estimated Charge
3. Set threshold to $5, $10, and $20

## 2. AWS Budgets (Better than CloudWatch)
1. AWS Budgets → Create budget
2. Budget type: Cost budget
3. Set amount: $10/month
4. Configure alerts at 50%, 80%, 100%
5. Add email notifications

## 3. Free Tier Dashboard
- Check daily: AWS Console → Billing → Free Tier
- Shows what you've used vs. free limits

## 4. Common Cost Traps to Avoid

### ❌ DON'T:
- Leave instances running 24/7 (use t2.micro only)
- Use Elastic IPs without attaching to running instance ($0.005/hour)
- Transfer lots of data OUT (first 100GB/month free)
- Create snapshots and forget them
- Use services outside free tier

### ✅ DO:
- Stop (not terminate) instances when not using
- Use only services marked "Free tier eligible"
- Delete old snapshots/volumes
- Set up auto-shutdown

## 5. Auto-Shutdown Script
Add to your EC2 instance:
```bash
# /home/ubuntu/auto-shutdown.sh
#!/bin/bash
# Shutdown if no SSH connections for 30 minutes
if [ $(who | wc -l) -eq 0 ]; then
    if [ -f /tmp/no_ssh_counter ]; then
        COUNTER=$(cat /tmp/no_ssh_counter)
        COUNTER=$((COUNTER + 1))
        if [ $COUNTER -ge 6 ]; then  # 6 * 5min = 30min
            sudo shutdown -h now
        else
            echo $COUNTER > /tmp/no_ssh_counter
        fi
    else
        echo 1 > /tmp/no_ssh_counter
    fi
else
    rm -f /tmp/no_ssh_counter
fi

# Add to crontab
*/5 * * * * /home/ubuntu/auto-shutdown.sh
```

## 6. Cost Control Instance Setup
```bash
# Use this UserData script when launching
#!/bin/bash
# Auto-stop instance after 4 hours
echo "sudo shutdown -h +240" | at now

# Or use AWS Instance Scheduler
```

## 7. Billing Protection Commands
```bash
# Check current costs
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics "UnblendedCost"

# List all running resources
aws resourcegroupstaggingapi get-resources
```

## 8. Nuclear Option - Spending Limit
AWS doesn't have hard spending limits, but you can:
1. Use prepaid AWS credits
2. Set up AWS Organizations with SCPs to restrict services
3. Use only specific regions (disable others)

## 9. MCP-Specific Cost Savers
For our MCP server:
- t2.micro is sufficient (1GB RAM)
- Stop instance when not using MCP
- No need for Elastic IP (use dynamic IP)
- Data transfer for MCP is minimal

## 10. Daily Checklist
- [ ] Check Free Tier dashboard
- [ ] Stop unused instances
- [ ] Delete old snapshots
- [ ] Review billing alerts

## Emergency: If You Get a Big Bill
1. Stop all resources immediately
2. Contact AWS Support (they often forgive first mistakes)
3. Check for compromised credentials

## Safe Instance Launch Command
```bash
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t2.micro \
  --key-name your-key \
  --security-groups your-sg \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=mcp-server},{Key=AutoStop,Value=true}]' \
  --instance-initiated-shutdown-behavior stop \
  --count 1
```

Remember: The MCP server uses almost no resources, so if you:
- Use t2.micro
- Stop when not using
- Stay within free tier limits

You should pay $0.00!