"""
FastAPI app. HTTP concerns only — Range parsing, status codes, headers.
All Telegram work is delegated to the telegram module.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware

import telegram
from config import BACKEND_PORT, FRONTEND_ORIGIN


@asynccontextmanager
async def lifespan(app: FastAPI):
    await telegram.connect()
    yield
    await telegram.disconnect()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/api/videos")
async def videos(limit: int = 50):
    return await telegram.list_videos(limit)


@app.get("/stream/{msg_id}")
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


@app.get("/thumb/{msg_id}")
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