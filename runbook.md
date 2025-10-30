# DevOps Runbook - Blue/Green Alerts

## Alert Types

### 1. ⚠️ Failover Detected

**What it means:**
Traffic has switched from one pool to another (e.g., Blue → Green).

**Possible causes:**
- Primary pool became unhealthy
- Manual chaos testing
- Container crash or restart

**Actions:**
1. Check the health of the previous pool:
```bash
   docker-compose logs app_blue
   docker-compose logs app_green
```

2. Verify container status:
```bash
   docker-compose ps
```

3. If unintentional:
   - Check application logs for errors
   - Restart the failed container: `docker-compose restart app_blue`
   - Monitor for recovery

4. If during chaos testing:
   - This is expected behavior ✅
   - Stop chaos: `curl -X POST http://localhost:8081/chaos/stop`

---

### 2. 🔥 High Error Rate Detected

**What it means:**
More than ERROR_RATE_THRESHOLD% of requests are returning 5xx errors.

**Possible causes:**
- Application bugs
- Database connection issues
- Resource exhaustion
- Downstream service failures

**Actions:**
1. Check which pool is serving traffic:
```bash
   curl -i http://localhost:8080/version
```

2. Check container logs for errors:
```bash
   docker-compose logs --tail=50 app_blue
   docker-compose logs --tail=50 app_green
```

3. Check resource usage:
```bash
   docker stats
```

4. If error rate is critical:
   - Consider manually switching pools
   - Restart affected containers
   - Check database connectivity

---

## Maintenance Mode

To suppress alerts during planned maintenance:

1. Stop the watcher temporarily:
```bash
   docker-compose stop alert_watcher
```

2. Perform maintenance

3. Restart the watcher:
```bash
   docker-compose start alert_watcher
```

---

## Testing Alerts

### Test Failover Alert
```bash
# Trigger chaos on Blue
curl -X POST "http://localhost:8081/chaos/start?mode=error"

# Generate traffic
for i in {1..10}; do curl http://localhost:8080/version; done

# Check Slack for failover alert
```

### Test Error Rate Alert
```bash
# Start chaos on active pool
curl -X POST "http://localhost:8081/chaos/start?mode=error"

# Generate 200+ requests to fill the window
for i in {1..250}; do 
  curl -s http://localhost:8080/version > /dev/null
  sleep 0.1
done

# Check Slack for error rate alert
```

---

## Configuration

Edit `.env` to adjust thresholds:
```env
ERROR_RATE_THRESHOLD=2     # Alert if >2% errors
WINDOW_SIZE=200            # Check last 200 requests
ALERT_COOLDOWN_SEC=300     # Wait 5min between similar alerts
```

After changing `.env`:
```bash
docker-compose down
docker-compose up -d
```

---

## Troubleshooting

### Alerts not appearing in Slack

1. Verify webhook URL is correct in `.env`
2. Check watcher logs:
```bash
   docker-compose logs alert_watcher
```
3. Test webhook manually:
```bash
   curl -X POST $SLACK_WEBHOOK_URL \
     -H 'Content-Type: application/json' \
     -d '{"text":"Test alert"}'
```

### Watcher not starting

1. Check logs:
```bash
   docker-compose logs alert_watcher
```

2. Verify Python script syntax:
```bash
   python3 watcher.py
```

3. Check file permissions:
```bash
   ls -l watcher.py
```
