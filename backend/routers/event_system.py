import asyncio
from fastapi import Request
from fastapi.routing import APIRouter
from fastapi.responses import StreamingResponse
from datastar_py import ServerSentEventGenerator as SSE

from ..notifications import EventSystem
from ..shared import SESSION_TOKEN_STR, SESSION_USER_UUID_STR, templates

router = APIRouter(prefix="/event-system")

@router.get("/", response_class=StreamingResponse)
async def open_notification_pipeline(request: Request):
    session_id = request.cookies.get(SESSION_TOKEN_STR)
    if not session_id:
        return
    event_system = EventSystem()
    event_system.subscribe_session(session_id, [])
    try:
        while True:
            if await request.is_disconnected():
                break
            try:
                kind, msg = await asyncio.wait_for(event_system.get_session_notifications(session_id), timeout=15)
                yield SSE.patch_signals({f"{kind}Msg": msg})
            except asyncio.TimeoutError:
                yield SSE.patch_signals({}) # heartbeat / keep-alive, prevents idle timeouts
    finally:
        event_system.unsubscribe_session(session_id)
    return