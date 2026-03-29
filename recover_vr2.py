import sqlite3

src = r'C:\Projetos\appportaria\db.sqlite3'
dst = r'C:\Projetos\appportaria\db_recovered.sqlite3'

src_conn = sqlite3.connect(src)
dst_conn = sqlite3.connect(dst)
dst_conn.execute("PRAGMA synchronous=OFF")
dst_conn.execute("PRAGMA journal_mode=WAL")

# Clear existing empty table
dst_conn.execute('DELETE FROM info_visitantreport')
dst_conn.commit()

batch = 50000
offset = 0
total = 0
placeholders = None

while True:
    try:
        rows = src_conn.execute(f'SELECT * FROM info_visitantreport LIMIT {batch} OFFSET {offset}').fetchall()
        if not rows:
            break
        if placeholders is None:
            placeholders = ','.join(['?' for _ in rows[0]])
        dst_conn.executemany(f'INSERT INTO info_visitantreport VALUES ({placeholders})', rows)
        dst_conn.commit()
        total += len(rows)
        offset += batch
        if total % 200000 == 0:
            print(f"  {total} rows written...")
    except sqlite3.DatabaseError:
        print(f"  Corruption hit at offset {offset}, stopping.")
        break

print(f"\nTotal visitantreport rows recovered: {total}")
count = dst_conn.execute('SELECT COUNT(*) FROM info_visitantreport').fetchone()[0]
print(f"Verified in recovered DB: {count} rows")

src_conn.close()
dst_conn.close()
