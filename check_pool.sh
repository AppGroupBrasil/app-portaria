#!/bin/bash
echo "=== WAL/SHM FILES ==="
ls -lh /root/projetos/condominio_info/db.sqlite3* 2>/dev/null

echo "=== GUNICORN WORKERS DETAIL ==="
for pid in $(pgrep -f 'gunicorn.*wsgi'); do
    threads=$(ls /proc/$pid/task 2>/dev/null | wc -l)
    fds=$(ls /proc/$pid/fd 2>/dev/null | wc -l)
    mem=$(ps -o rss= -p $pid 2>/dev/null)
    echo "  PID=$pid threads=$threads fds=$fds mem_kb=$mem"
done

echo "=== PENDING UNIX SOCKET CONNECTIONS ==="
ss -x | grep gunicorn | wc -l

echo "=== GUNICORN SOCKET QUEUE ==="
ss -xlnp | grep gunicorn

echo "=== DJANGO DB SETTINGS ==="
cd /root/projetos/condominio_info
source venv/bin/activate
python -c "
import os, django
os.environ['DJANGO_SETTINGS_MODULE']='condominio_info.settings'
django.setup()
from django.conf import settings
db = settings.DATABASES['default']
print('ENGINE:', db.get('ENGINE'))
print('NAME:', db.get('NAME'))
print('OPTIONS:', db.get('OPTIONS', {}))
print('CONN_MAX_AGE:', db.get('CONN_MAX_AGE', 0))
"

echo "=== SQLITE WAL CHECK ==="
python -c "
import sqlite3
conn = sqlite3.connect('/root/projetos/condominio_info/db.sqlite3')
c = conn.cursor()
print('journal_mode:', c.execute('PRAGMA journal_mode;').fetchone())
print('busy_timeout:', c.execute('PRAGMA busy_timeout;').fetchone())
print('wal_checkpoint:', c.execute('PRAGMA wal_checkpoint;').fetchone())
conn.close()
"

echo "=== LOAD AVERAGE ==="
uptime

echo "=== TOP CPU PROCESSES ==="
ps aux --sort=-%cpu | head -8
