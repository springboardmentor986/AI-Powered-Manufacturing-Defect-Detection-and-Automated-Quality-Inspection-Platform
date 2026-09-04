from backend.app.core.security import (
    hash_password,
    verify_password
)

password = "VisionInspect123"

hashed_password = hash_password(password)

print("Original Password:", password)
print("Hashed Password:", hashed_password)

is_valid = verify_password(
    password,
    hashed_password
)

print("Password Verified:", is_valid)