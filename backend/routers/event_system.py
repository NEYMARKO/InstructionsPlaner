import asyncio
import uuid

from datastar_py import ServerSentEventGenerator as SSE
from fastapi import Request
from fastapi.responses import StreamingResponse
from fastapi.routing import APIRouter

from ..notifications import event_system as ES
from ..shared import EVENT_SUBSCRIPTION_ID

router = APIRouter(prefix="/event-system")

@router.get("/", response_class=StreamingResponse)
async def open_notification_pipeline(request: Request):
    e_subs_id = str(uuid.uuid4())
    async def pipeline():
        print(f"Listening pipe opened for session: {e_subs_id}...")
        ES.subscribe_session(e_subs_id, [])
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    session_notifications = await asyncio.wait_for(ES.get_session_notifications(e_subs_id), timeout=15)
                    if session_notifications:
                        signals = ES.combine_signals(session_notifications)
                        yield SSE.patch_signals(signals)
                        ES.consume_notifications(e_subs_id, session_notifications)
                except asyncio.TimeoutError:
                    yield SSE.patch_signals({}) # heartbeat / keep-alive, prevents idle timeouts
        finally:
            print(f"Finished listening for session: {e_subs_id}")
            ES.unsubscribe_session(e_subs_id)
    response = StreamingResponse(
        pipeline(),
        media_type="text/event-stream"
    )
    response.set_cookie(
        key=EVENT_SUBSCRIPTION_ID,
        # value=service_response.token,
        value=e_subs_id,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600
    )
    
    return response