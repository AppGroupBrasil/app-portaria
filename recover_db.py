import sqlite3
import os

src = r'C:\Projetos\appportaria\db.sqlite3'
dst = r'C:\Projetos\appportaria\db_recovered.sqlite3'

if os.path.exists(dst):
    os.remove(dst)

src_conn = sqlite3.connect(src)
dst_conn = sqlite3.connect(dst)

# Get all table creation SQL
tables = src_conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL").fetchall()
print(f"Copying {len(tables)} tables...")

for name, create_sql in tables:
    if name.startswith('sqlite_'):
        print(f"  {name}... skipped (internal)")
        continue
    print(f"  {name}...", end=" ", flush=True)
    # Create table in destination
    dst_conn.execute(create_sql)
    
    # Copy all rows
    rows = src_conn.execute(f'SELECT * FROM [{name}]').fetchall()
    if rows:
        placeholders = ','.join(['?' for _ in rows[0]])
        dst_conn.executemany(f'INSERT INTO [{name}] VALUES ({placeholders})', rows)
    print(f"{len(rows)} rows")

# Copy indexes
indexes = src_conn.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL").fetchall()
print(f"\nRecreating {len(indexes)} indexes...")
for (idx_sql,) in indexes:
    try:
        dst_conn.execute(idx_sql)
    except Exception as e:
        print(f"  Warning: {e}")

dst_conn.commit()

# Verify
result = dst_conn.execute('PRAGMA integrity_check').fetchone()
print(f"\nIntegrity check: {result[0]}")

src_size = os.path.getsize(src) / 1024 / 1024
dst_size = os.path.getsize(dst) / 1024 / 1024
print(f"Original: {src_size:.1f} MB, Recovered: {dst_size:.1f} MB")

src_conn.close()
dst_conn.close()
