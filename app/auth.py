import os
from fastapi import Header, HTTPException, status
from dotenv import load_dotenv

load_dotenv()

# Read the expected API key from the .env file
# If API_KEY is not set in .env, default to "secret" as a fallback
API_KEY = os.getenv("API_KEY", "secret")


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        # 401 Unauthorized — key is missing or wrong
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )