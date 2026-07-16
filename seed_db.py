from app.memory.database import init_db, create_user
from app.auth.security import hash_password

print("Initializing SQLite database...")
init_db()

try:
    print("Creating admin user...")
    create_user(
        username="admin",
        email="admin@athena.local",
        hashed_password=hash_password("password"),
        department="ADMIN"
    )
    print("Admin user created successfully.")
except Exception as e:
    print(f"User may already exist or error occurred: {e}")
