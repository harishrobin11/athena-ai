from app.db.database import SessionLocal
from app.db.models import User

db = SessionLocal()
try:
    users = db.query(User).all()
    for u in users:
        print(u.id, u.username)
finally:
    db.close()