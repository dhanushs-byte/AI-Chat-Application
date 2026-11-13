
import os
import secrets

from dotenv import load_dotenv
from fastapi import Header, HTTPException, status

load_dotenv()


def verify_api_key(
    x_api_key: str | None = Header(default=None)
):

    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key is missing"
        )

    valid_keys = [
        key.strip()
        for key in os.getenv("API_KEYS", "").split(",")
        if key.strip()
    ]

    if not any(
        secrets.compare_digest(x_api_key, key)
        for key in valid_keys
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )

    return x_api_key
