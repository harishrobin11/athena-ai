from app.auth.security import (
    hash_password,
    verify_password
)

password = "password123"

hashed = hash_password(password)

print("Original:", password)
print("Hashed:", hashed)

print(
    "Verification:",
    verify_password(password, hashed)
)