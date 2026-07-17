from app.memory.database import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
SELECT id, username
FROM users
""")

for row in cursor.fetchall():
    print(row)

conn.close()