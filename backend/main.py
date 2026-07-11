"""
FastAPI app. HTTP concerns only — Range parsing, status codes, headers.
All Telegram work is delegated to the telegram module.
"""

from contextlib import asynccontextmanager

import bcrypt
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

import telegram
from config import BACKEND_PORT, FRONTEND_ORIGIN, PW_HASH, SESSION_SECRET


@asynccontextmanager
async def lifespan(app: FastAPI):
    await telegram.connect()
    yield
    await telegram.disconnect()


app = FastAPI(lifespan=lifespan)

# Signed session cookie; the login route sets "authenticated" in it.
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    max_age=24 * 60 * 60,  # 24 hours
    same_site="strict",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- auth ---


class AuthBody(BaseModel):
    pw: str


def check_password(pw: str) -> bool:
    """Compare a submitted password against the bcrypt hash from config."""
    try:
        return bcrypt.checkpw(pw.encode(), PW_HASH.encode())
    except ValueError as e:
        print(f"BCRYPT ERROR (is PW_HASH a valid bcrypt hash?): {e}")
        return False


def require_auth(request: Request) -> None:
    """Route dependency: reject requests whose session isn't authenticated."""
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.post("/api/auth")
async def login(body: AuthBody, request: Request):
    if not check_password(body.pw):
        return {"success": False, "message": "Wrong password"}

    request.session["authenticated"] = True
    return {"success": True, "message": "Authenticated"}


# --- videos ---


def parse_range(range_header: str, file_size: int):
    """
    Parse a single-range 'bytes=START-END' header.
    Returns (start, end) inclusive, or None if unsatisfiable.
    """
    if not range_header or not range_header.startswith("bytes="):
        return 0, file_size - 1

    spec = range_header[len("bytes="):].split(",")[0].strip()
    start_str, _, end_str = spec.partition("-")

    try:
        if start_str == "":
            # suffix range: bytes=-N -> last N bytes
            length = int(end_str)
            if length <= 0:
                return None
            start = max(0, file_size - length)
            end = file_size - 1
        else:
            start = int(start_str)
            end = int(end_str) if end_str else file_size - 1
    except ValueError:
        return None

    if start < 0 or start >= file_size or end < start:
        return None
    end = min(end, file_size - 1)
    return start, end


@app.get("/api/videos", dependencies=[Depends(require_auth)])
async def videos(limit: int = 50):
    result = await telegram.list_videos(limit)
    if result is None:
        raise HTTPException(status_code=502, detail="Telegram request failed")
    return result


@app.get("/stream/{msg_id}", dependencies=[Depends(require_auth)])
async def stream(msg_id: int, request: Request):
    msg = await telegram.get_message(msg_id)
    if not msg or not msg.file:
        raise HTTPException(status_code=404, detail="Message not found")

    file_size = msg.file.size
    mime = msg.file.mime_type or "video/mp4"
    range_header = request.headers.get("Range")

    parsed = parse_range(range_header, file_size)
    if parsed is None:
        return Response(
            status_code=416,
            headers={"Content-Range": f"bytes */{file_size}"},
        )
    start, end = parsed
    content_length = end - start + 1

    status = 206 if range_header else 200
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
    }
    if range_header:
        headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"

    return StreamingResponse(
        telegram.stream_range(msg, start, end),
        status_code=status,
        media_type=mime,
        headers=headers,
    )


@app.get("/thumb/{msg_id}", dependencies=[Depends(require_auth)])
async def thumb(msg_id: int):
    msg = await telegram.get_message(msg_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    data = await telegram.get_thumbnail(msg)
    if not data:
        raise HTTPException(status_code=404, detail="No thumbnail available")

    return Response(content=data, media_type="image/jpeg")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", port=BACKEND_PORT, reload=True)