## Stage 3: Observability & Alerts

### Additional Setup

1. Create a Slack webhook (see runbook.md)
2. Update `.env` with your `SLACK_WEBHOOK_URL`

### Testing Alerts

#### Test Failover Alert
```bash
# Start chaos on Blue
curl -X POST "http://localhost:8081/chaos/start?mode=error"

# Generate traffic
for i in {1..10}; do curl http://localhost:8080/version; sleep 0.5; done

# Check Slack for "Failover Detected" alert
```

#### Test Error Rate Alert
```bash
# Ensure chaos is running
curl -X POST "http://localhost:8081/chaos/start?mode=error"

# Generate 250 requests
for i in {1..250}; do 
  curl -s http://localhost:8080/version > /dev/null
done

# Check Slack for "High Error Rate" alert
```

#### Stop Chaos
```bash
curl -X POST "http://localhost:8081/chaos/stop"
```

### Viewing Logs

**Watcher logs:**
```bash
docker-compose logs -f alert_watcher
```

**Nginx logs:**
```bash
docker-compose exec nginx cat /var/log/nginx/access.log
```

### Screenshots Required

For submission, capture:
1. Slack alert showing failover event
2. Slack alert showing high error rate
3. Container logs showing structured Nginx log format
