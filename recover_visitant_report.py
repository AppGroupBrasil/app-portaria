import sqlite3

src = r'C:\Projetos\appportaria\db.sqlite3'
dst = r'C:\Projetos\appportaria\db_recovered.sqlite3'

# Check what we can get from visitantreport using different approaches
src_conn = sqlite3.connect(src)

# Try with LIMIT/OFFSET
print("Trying LIMIT/OFFSET approach...")
total = 0
batch = 50000
offset = 0
all_rows = []

while True:
    try:
        rows = src_conn.execute(f'SELECT * FROM info_visitantreport LIMIT {batch} OFFSET {offset}').fetchall()
        if not rows:
            break
        all_rows.extend(rows)
        total += len(rows)
        offset += batch
        print(f"  Retrieved {total} rows so far...")
    except sqlite3.DatabaseError as e:
        print(f"  Error at offset {offset}: {e}")
        # Try smaller batches
        for small_offset in range(offset, offset + batch, 1000):
            try:
                rows = src_conn.execute(f'SELECT * FROM info_visitantreport LIMIT 1000 OFFSET {small_offset}').fetchall()
                all_rows.extend(rows)
                total += len(rows)
            except sqlite3.DatabaseError:
                pass
        offset += batch

print(f"\nTotal recovered from visitantreport: {total}")

if all_rows:
    # Insert into recovered db
    dst_conn = sqlite3.connect(dst)
    placeholders = ','.join(['?' for _ in all_rows[0]])
    # Delete existing (empty) rows first
    dst_conn.execute('DELETE FROM info_visitantreport')
    for i in range(0, len(all_rows), 10000):
        batch_rows = all_rows[i:i+10000]
        dst_conn.executemany(f'INSERT INTO info_visitantreport VALUES ({placeholders})', batch_rows)
    dst_conn.commit()
    
    count = dst_conn.execute('SELECT COUNT(*) FROM info_visitantreport').fetchone()[0]
    print(f"Inserted {count} rows into recovered database")
    dst_conn.close()

src_conn.close()
