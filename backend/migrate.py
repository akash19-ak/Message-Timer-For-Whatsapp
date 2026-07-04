import sqlite3, os

db_path = 'birthday.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('PRAGMA table_info(schedules)')
    cols = [row[1] for row in cur.fetchall()]
    print('Existing columns:', cols)
    if 'send_method' not in cols:
        cur.execute("ALTER TABLE schedules ADD COLUMN send_method TEXT NOT NULL DEFAULT 'app'")
        conn.commit()
        print('send_method column added successfully.')
    else:
        print('send_method column already exists — no migration needed.')
    conn.close()
else:
    print('No DB file found — will be created fresh when app starts.')
