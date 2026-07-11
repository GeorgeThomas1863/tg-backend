"""Configuration: environment variables and Telegram download constants."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Repo-root .env, shared with the frontend. Already-set env vars win.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

def parse_channel(raw: str) -> int | str:
    """Telethon needs numeric channel IDs as int; usernames stay strings."""
    stripped = raw.strip()
    if stripped.lstrip("-").isdigit():
        return int(stripped)
    return stripped


# From https://my.telegram.org -> "API development tools"
API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
CHANNEL = parse_channel(os.environ["TELEGRAM_CHANNEL"])  # "mychannel" or -1001234567890

# Site auth. PW_HASH is a bcrypt hash of the site password (single-quote it in
# .env — the $ signs must stay literal). SESSION_SECRET signs the session
# cookie. Both required — the app must not start unprotected.
PW_HASH = os.environ["PW_HASH"]
SESSION_SECRET = os.environ["SESSION_SECRET"]

# Telegram download constraints (verified against Telegram's files API and
# Telethon source):
#   - request_size must be a multiple of 4096 bytes.
#   - offset passed to iter_download must be a multiple of 4096.
# Telethon handles the internal 1 MiB-boundary chunking; we only need to give
# it a 4096-aligned offset.
ALIGN = 4096                  # offset alignment requirement
REQUEST_SIZE = 512 * 1024     # 512 KiB; multiple of 4096, valid request_size

# Dev server ports; the frontend reads the same .env keys in vite.config.js.
BACKEND_PORT = int(os.environ.get("BACKEND_PORT", "8000"))
FRONTEND_PORT = int(os.environ.get("FRONTEND_PORT", "5173"))

# Where the React dev server runs, for CORS during development.
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", f"http://localhost:{FRONTEND_PORT}")