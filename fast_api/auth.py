from fastapi import HTTPException, Header
import os

# JWT tokens removed. Replace admin check with a simple header-based secret.
# Set the environment variable `ADMIN_SECRET` to enable admin protection.

ADMIN_SECRET = os.getenv("ADMIN_SECRET")


def get_current_user() -> dict:
    # No token-based authentication in this simplified setup.
    return {}


def require_admin(x_admin_secret: str | None = Header(None)) -> dict:
    if ADMIN_SECRET:
        if x_admin_secret != ADMIN_SECRET:
            raise HTTPException(status_code=403, detail="Admin access required")
    # When no ADMIN_SECRET is configured, allow for local/dev usage.
    return {"role": "admin"}