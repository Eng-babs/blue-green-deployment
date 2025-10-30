#!/usr/bin/env python3
import os
import re
import time
import json
import subprocess
from collections import deque
from datetime import datetime
import requests

# Environment variables
SLACK_WEBHOOK = os.getenv('SLACK_WEBHOOK_URL', '')
ERROR_THRESHOLD = float(os.getenv('ERROR_RATE_THRESHOLD', 2.0))
WINDOW_SIZE = int(os.getenv('WINDOW_SIZE', 200))
COOLDOWN = int(os.getenv('ALERT_COOLDOWN_SEC', 300))

# State tracking
request_window = deque(maxlen=WINDOW_SIZE)
last_pool = None
last_failover_alert = 0
last_error_alert = 0

# Regex to parse Nginx logs
LOG_PATTERN = re.compile(
    r'pool=(?P<pool>\w+) '
    r'release=(?P<release>[\w\-\.]+) '
    r'upstream_status=(?P<upstream_status>\d+)'
)

def send_slack_alert(message, alert_type="info"):
    """Send alert to Slack"""
    if not SLACK_WEBHOOK:
        print(f"[ALERT] {message}")
        return
    
    colors = {
        "error": "#ff0000",
        "warning": "#ffa500", 
        "info": "#00ff00",
        "failover": "#ffff00"
    }
    
    payload = {
        "attachments": [{
            "color": colors.get(alert_type, "#808080"),
            "title": f"🚨 {alert_type.upper()} Alert",
            "text": message,
            "footer": "Blue/Green Monitoring",
            "ts": int(time.time())
        }]
    }
    
    try:
        response = requests.post(SLACK_WEBHOOK, json=payload, timeout=5)
        response.raise_for_status()
        print(f"[✓] Slack alert sent: {message}")
    except Exception as e:
        print(f"[✗] Failed to send Slack alert: {e}")

def check_failover(current_pool):
    """Detect pool changes (failover)"""
    global last_pool, last_failover_alert
    
    if last_pool is None:
        last_pool = current_pool
        return
    
    if current_pool != last_pool:
        now = time.time()
        if now - last_failover_alert > COOLDOWN:
            message = f"⚠️ Failover Detected: {last_pool} → {current_pool}\n" \
                     f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" \
                     f"Action: Check health of {last_pool} container"
            send_slack_alert(message, "failover")
            last_failover_alert = now
        
        last_pool = current_pool

def check_error_rate():
    """Calculate error rate over sliding window"""
    global last_error_alert
    
    if len(request_window) < WINDOW_SIZE:
        return
    
    error_count = sum(1 for status in request_window if status >= 500)
    error_rate = (error_count / len(request_window)) * 100
    
    if error_rate > ERROR_THRESHOLD:
        now = time.time()
        if now - last_error_alert > COOLDOWN:
            message = f"🔥 High Error Rate Detected!\n" \
                     f"Error Rate: {error_rate:.2f}% (threshold: {ERROR_THRESHOLD}%)\n" \
                     f"Errors: {error_count}/{len(request_window)} requests\n" \
                     f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" \
                     f"Action: Investigate upstream services"
            send_slack_alert(message, "error")
            last_error_alert = now

def tail_logs(log_file):
    """Tail nginx access logs and parse in real-time"""
    print(f"[*] Watching logs: {log_file}")
    print(f"[*] Slack webhook configured: {bool(SLACK_WEBHOOK)}")
    print(f"[*] Error threshold: {ERROR_THRESHOLD}%, Window: {WINDOW_SIZE}, Cooldown: {COOLDOWN}s")
    
    # Use tail command to follow the file
    process = subprocess.Popen(
        ['tail', '-F', '-n', '0', log_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    print("[✓] Started tailing logs...")
    
    try:
        for line in iter(process.stdout.readline, ''):
            if not line:
                continue
            
            # Parse log line
            match = LOG_PATTERN.search(line)
            if not match:
                continue
            
            pool = match.group('pool')
            release = match.group('release')
            upstream_status = int(match.group('upstream_status'))
            
            # Track request
            request_window.append(upstream_status)
            
            # Check for alerts
            check_failover(pool)
            check_error_rate()
            
            # Debug output
            print(f"[LOG] pool={pool} release={release} status={upstream_status}")
    
    except KeyboardInterrupt:
        print("\n[*] Stopping watcher...")
        process.terminate()
        raise

if __name__ == '__main__':
    log_file = '/var/log/nginx/access.log'
    
    # Wait for log file to exist
    while not os.path.exists(log_file):
        print(f"[*] Waiting for {log_file}...")
        time.sleep(2)
    
    print("[✓] Log file found, starting watcher...")
    
    try:
        tail_logs(log_file)
    except KeyboardInterrupt:
        print("\n[*] Watcher stopped")
