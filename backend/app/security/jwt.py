import os
from datetime import datetime, timedelta, timezone

from jose import jwt

SECRET_KEY = os.getenv("SECRET_KEY", "oucoGQm_NimkJ66gl9CB4jNdESWuG3iV50z_kyP_aSs")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(user_id: int, role_id: int) -> str:
    expire = datetime.now(timezone.utc)+timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub" : str(user_id),
        "role_id" : str(role_id),
        "exp" : expire
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)