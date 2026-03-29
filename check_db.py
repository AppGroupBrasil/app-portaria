import sqlite3

conn = sqlite3.connect(r'C:\Projetos\appportaria\db.sqlite3')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print(f'Total tables: {len(tables)}')
for t in tables:
    try:
        count = conn.execute(f'SELECT COUNT(*) FROM [{t[0]}]').fetchone()[0]
        print(f'  OK  {t[0]}: {count} rows')
    except Exception as e:
        print(f'  ERR {t[0]}: {e}')
conn.close()
