echo "=== Complete Blue/Green Failover Test ==="
echo ""

echo "1️⃣  Initial State (should be Blue):"
curl -si http://localhost:8080/version | grep "X-App-Pool"
echo ""

echo "2️⃣  Triggering chaos on Blue..."
curl -X POST "http://localhost:8081/chaos/start?mode=error"
echo ""
sleep 2

echo "3️⃣  Testing automatic failover (should ALL be Green with 200 OK):"
for i in {1..10}; do 
  response=$(curl -si http://localhost:8080/version 2>&1)
  status=$(echo "$response" | grep "HTTP" | head -1 | awk '{print $2}')
  pool=$(echo "$response" | grep "X-App-Pool" | awk '{print $2}' | tr -d '\r')
  
  if [ "$status" = "200" ]; then
    echo "  ✅ Request $i: HTTP $status → Pool: $pool"
  else
    echo "  ❌ Request $i: HTTP $status → Pool: $pool"
  fi
done
echo ""

echo "4️⃣  Stopping chaos..."
curl -X POST "http://localhost:8081/chaos/stop"
echo ""

echo "5️⃣  Waiting 10 seconds for Blue to recover..."
sleep 10

echo "6️⃣  Testing recovery (should switch back to Blue):"
for i in {1..5}; do 
  pool=$(curl -si http://localhost:8080/version | grep "X-App-Pool" | awk '{print $2}' | tr -d '\r')
  echo "  Request $i: Pool: $pool"
  sleep 1
done

echo ""
echo "✅ Failover test complete!"
