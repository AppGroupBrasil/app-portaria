import sqlite3
import os

src = r'C:\Projetos\appportaria\db.sqlite3'
dst = r'C:\Projetos\appportaria\db_recovered.sqlite3'

if os.path.exists(dst):
    os.remove(dst)

src_conn = sqlite3.connect(src)
dst_conn = sqlite3.connect(dst)
dst_conn.execute("PRAGMA journal_mode=WAL")
dst_conn.execute("PRAGMA synchronous=OFF")

tables = src_conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL").fetchall()
print(f"Copying {len(tables)} tables...")

for name, create_sql in tables:
    if name.startswith('sqlite_'):
        print(f"  {name}... skipped (internal)")
        continue
    
    # Create table in destination
    dst_conn.execute(create_sql)
    
    # Get rowid range for batch processing
    try:
        max_rowid = src_conn.execute(f'SELECT MAX(rowid) FROM [{name}]').fetchone()[0]
    except Exception:
        max_rowid = None
    
    if max_rowid is None or max_rowid == 0:
        print(f"  {name}... 0 rows")
        continue
    
    total = 0
    errors = 0
    batch_size = 10000
    
    for start in range(0, max_rowid + 1, batch_size):
        end = start + batch_size
        try:
            rows = src_conn.execute(f'SELECT * FROM [{name}] WHERE rowid >= ? AND rowid < ?', (start, end)).fetchall()
            if rows:
                placeholders = ','.join(['?' for _ in rows[0]])
                dst_conn.executemany(f'INSERT INTO [{name}] VALUES ({placeholders})', rows)
                total += len(rows)
        except sqlite3.DatabaseError as e:
            # Try row by row for this batch
            for rowid in range(start, end):
                try:
                    row = src_conn.execute(f'SELECT * FROM [{name}] WHERE rowid = ?', (rowid,)).fetchone()
                    if row:
                        placeholders = ','.join(['?' for _ in row])
                        dst_conn.execute(f'INSERT INTO [{name}] VALUES ({placeholders})', row)
                        total += 1
                except sqlite3.DatabaseError:
                    errors += 1
    
    dst_conn.commit()
    status = f"{total} rows"
    if errors:
        status += f" ({errors} lost)"
    print(f"  {name}... {status}")

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
