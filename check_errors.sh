#!/bin/bash
echo "=== ERROS 500 (24h) ==="
journalctl -u gunicorn --since '24 hours ago' --no-pager | grep ' 500 ' | grep -v 'get-server-time' | wc -l

echo "=== TRACEBACKS UNICOS (24h) ==="
journalctl -u gunicorn --since '24 hours ago' --no-pager | grep -A3 'Internal Server Error' | grep -v 'get-server-time' 

echo "=== ERROS DJANGO (24h) ==="
journalctl -u gunicorn --since '24 hours ago' --no-pager | grep -E 'TypeError|ValueError|AttributeError|KeyError|IntegrityError|OperationalError|DoesNotExist' | sort -u

echo "=== DATABASE LOCKED (7 dias) ==="
journalctl -u gunicorn --since '7 days ago' --no-pager | grep -c 'database is locked'

echo "=== ERROS NGINX (24h) ==="
tail -100 /var/log/nginx/error.log | grep -v 'static_cdn/img' | tail -20
