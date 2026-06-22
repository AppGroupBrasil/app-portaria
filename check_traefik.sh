#!/bin/bash
echo "=== TRAEFIK ROUTERS ==="
curl -s http://127.0.0.1:8080/api/http/routers | python3 -c "
import sys, json
data = json.load(sys.stdin)
for r in data:
    name = r.get('name','')
    rule = r.get('rule','')
    service = r.get('service','')
    status = r.get('status','')
    print(f'{name} | {rule} | {service} | {status}')
" 2>/dev/null

echo ""
echo "=== TRAEFIK SERVICES ==="
curl -s http://127.0.0.1:8080/api/http/services | python3 -c "
import sys, json
data = json.load(sys.stdin)
for s in data:
    name = s.get('name','')
    stype = s.get('type','')
    urls = ''
    if 'loadBalancer' in s:
        servers = s['loadBalancer'].get('servers',[])
        urls = ', '.join([sv.get('url','') for sv in servers])
    print(f'{name} | {stype} | {urls}')
" 2>/dev/null | grep -i 'portaria\|8001'
