"""
Telegram layer.

Owns the shared Telethon client and everything that talks to Telegram, so the
route handlers in main.py stay purely about HTTP. The byte-range streaming
logic (including Telegram's 4096-offset-alignment requirement) lives here.
"""

from typing import AsyncGenerator, Optional

from telethon import TelegramClient
from telethon.tl.types import InputMessagesFilterVideo

from config import API_ID, API_HASH, CHANNEL, ALIGN, REQUEST_SIZE

# Single shared client. One session, one event loop — fine for 1-2 users.
client = TelegramClient("session", API_ID, API_HASH)


async def connect() -> None:
    """Start the client (interactive login on first run, reuses session after)."""
    await client.start()


async def disconnect() -> None:
    await client.disconnect()


def media_to_dict(msg) -> dict:
    """Normalise a Telethon message with media into a plain dict."""
    f = msg.file
    return {
        "id": msg.id,
        "date": msg.date.isoformat(),
        "name": f.name or f"video_{msg.id}",
        "size": f.size,
        "mime": f.mime_type or "video/mp4",
        "width": getattr(f, "width", None),
        "height": getattr(f, "height", None),
        "duration": getattr(f, "duration", None),
    }


async def list_videos(limit: int = 50) -> list[dict]:
    msgs = await client.get_messages(
        CHANNEL, limit=limit, filter=InputMessagesFilterVideo
    )
    return [media_to_dict(m) for m in msgs if m.file]


async def get_message(msg_id: int):
    """Re-resolve a message fresh, sidestepping file_reference expiration."""
    return await client.get_messages(CHANNEL, ids=msg_id)


async def get_thumbnail(msg) -> Optional[bytes]:
    return await client.download_media(msg, bytes, thumb=-1)


async def stream_range(msg, start: int, end: int) -> AsyncGenerator[bytes, None]:
    """
    Yield bytes [start, end] inclusive of the message's media.

    Telegram requires the download offset to be a multiple of 4096, so we floor
    start to a 4096 boundary, then discard the leading remainder before
    emitting. We also trim the tail so we never emit past `end`.
    """
    content_length = end - start + 1
    aligned_start = (start // ALIGN) * ALIGN
    to_skip = start - aligned_start
    sent = 0

    async for chunk in client.iter_download(
        msg.media,
        offset=aligned_start,
        request_size=REQUEST_SIZE,
    ):
        # Drop bytes introduced by aligning the offset downward.
        if to_skip:
            if len(chunk) <= to_skip:
                to_skip -= len(chunk)
                continue
            chunk = chunk[to_skip:]
            to_skip = 0

        remaining = content_length - sent
        if remaining <= 0:
            break
        if len(chunk) > remaining:
            chunk = chunk[:remaining]

        sent += len(chunk)   # count what we yield, not what we received
        yield chunk

        if sent >= content_length:
            break