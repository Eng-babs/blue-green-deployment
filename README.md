# Blue/Green Deployment with Nginx

## Setup

1. Clone this repo
2. Copy `.env.example` to `.env`
3. Run: `docker-compose up -d`

## Testing

### Normal operation (Blue active):
```bash
curl http://localhost:8080/version
```

### Trigger chaos on Blue:
```bash
curl -X POST http://localhost:8081/chaos/start?mode=error
```

### Verify Green takes over:
```bash
curl http://localhost:8080/version
# Should show X-App-Pool: green
```

### Stop chaos:
```bash
curl -X POST http://localhost:8081/chaos/stop
```

## Ports
- 8080: Nginx (main entrance)
- 8081: Blue direct
- 8082: Green direct
