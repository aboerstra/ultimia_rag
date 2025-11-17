#!/bin/bash
# Restart API server with fresh Python module cache

echo "🔄 Restarting API server..."
pkill -9 -f "uvicorn api.main:app"
sleep 2

# Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null

# Start fresh
cd /Users/adrianboerstra/projects/maximQBR
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload > api.log 2>&1 &

sleep 3
echo "✅ API server restarted!"
echo ""
echo "Testing persona deduplication..."
curl -s http://localhost:8000/api/personas/participants | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'\n Found {len(data)} unique people:\n')
for p in sorted(data, key=lambda x: x['transcript_count'], reverse=True)[:8]:
    print(f'  {p[\"name\"]}: {p[\"transcript_count\"]} transcripts')
"
