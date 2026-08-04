import asyncio
import uuid

from datastar_py import ServerSentEventGenerator as SSE
from datastar_py.attributes import SignalValue
from datastar_py.sse import DatastarEvent
from fastapi import Request
from fastapi.responses import StreamingResponse
from fastapi.routing import APIRouter

from ..event_system import NotifType
from ..event_system import event_system as ES
from ..shared import EVENT_SUBSCRIPTION_ID

router = APIRouter(prefix="/event-listener")

def process_notification(notif: tuple[NotifType, dict[str, dict[str, str | SignalValue]]] = (NotifType.EMPTY, {})) -> DatastarEvent:
    content = notif[1].get("content", {})
    match notif[0]:
        case NotifType.MESSAGE:
            return SSE.patch_signals(content)
        case NotifType.RESPONSE:
            response = SSE.execute_script("window.location='/'")
            # response = construct_cookie_response(response, SESSION_TOKEN_STR, content.get(SESSION_TOKEN_STR, ""))
            # response = construct_cookie_response(response, SESSION_USER_UUID_STR, content.get(SESSION_USER_UUID_STR, ""))
            return response
        case _:
            return DatastarEvent()
            # return DatastarResponse()

@router.get("/", response_class=StreamingResponse)
async def open_notification_pipeline(request: Request):
    """
    Normally, an HTTP response is one blob: FastAPI builds the whole body in memory,
    then sends it in one shot. `StreamingResponse` is different - instead of body string/bytes,
    we give it something iterable, and it sends each item as separate chunk over the wire as they
    become available, keeping the HTTP connection open in between.

    Under the hood, `StreamingResponse.__call__` (this is what Satarlette/ASGI actually invokes to handle
    connection) does roughly:
    ```
    async for chunk in self.body_iterator:
        await send({"type": "http.response.body", "body": chunk, "more_body": True})
    ```

    So it just keeps pullling values out of whatever we gave it, forwarding each one to the client, until the
    iterable is exhausted (or the connection dies) => that's why we have to send heartbeat every `timeout` seconds
    to keep the connection alive - we give iterable something to iterate over to prevent it from terminating.

    A route handler like `open_notification_pipeline` is a normal coroutine - it runs once, computes a result and 
    returns. It can only produce one value (we need to send many values over time, potentionally indefinitely - 
    notifications as they arrive, heartbeats every `timeout` seconds).

    The tool for 'a function that can produce many values over time, pausing between each' is a generator - here,
    an async generator, because we need to `await` things (`asyncio.wait_for`, `request.is_disconnected()`) between each value.

    `StreamingResponse` needs excatly that: an (async) iterable. So `pipeline` function is written as an async generator function 
    purely so we have something to hand to `StreamingResponse` as its `body_iterator`. It's not optional plumbing - it's the actual 
    mechanism that lets us emit multiple SSE events on the one open connection.

    Why the outer function (`open_notification_pipeline`) isn't terminating? - it already has
    1. `open_notification_pipeline(request)` - the route handler - runs to completion almost immediately:
        - generates uuid
        - defines `pipeline` (defines, doesn't run it)
        - calls `pipeline()` - since `pipeline` is async generator function, calling it doesn't execute any code inside it yet.
        It just creates and returns an async generator object, paused before the first line
        - wraps that generator object in `StreamingResponse(...)`
        - sets a cookie
        - `return response`
    
    That's it. The coroutine for `open_notification_pipeline` returns here and is popped off the stack.

    2. FastAPI/Starlette makes the `StreamingResponse` object we returned and calls it as an ASGI app: `await response(scope, receive, send)`.
    This is a separate, later step, driven by the ASGI server (uvicorn), not by your route function. This is what does `async for chunk in 
    pipeline_generator`, which is what actually starts executing the code inside `pipeline()` - including our `while True` loop - for the first time.

    So the infinite loop isn't running "inside" `open_notification_pipeline` at all by the time it executes. Route handler's job was only ever to 
    construct the response (including the not-yet-run generator) and hand it off. The generator's execution is then driven by the ASGI layer, and its 
    lifetim is tied to the HTTP connection itself, not to the route handler's call stack, That's why it can loop essentially forever without the route 
    handler "hanging" - the route handler already finished; the connection is being kept alive by the streaming machinery consuming our generator. 

    Each time `yield` is hit, execution of `pipeline()` pauses right there, the chunk gets flushed to the client, and Starlette asks for the next
    value whenever it's ready - resuming the generator right after the `yield` - until the generator itself returns (the loop breaks) or the client disconnects.
    
    """
    e_subs_id = str(uuid.uuid4()) if not request.cookies.get(EVENT_SUBSCRIPTION_ID, "") else request.cookies.get(EVENT_SUBSCRIPTION_ID, "")
    async def pipeline():
        print(f"Listening pipe opened for session: {e_subs_id}...")
        # ES.subscribe_session(e_subs_id, [])
        try:
            while True:
                # print("LOOP IS TRUE")
                if await request.is_disconnected() or ES.should_shutdown():
                    break
                try:
                    # session_notifications = await asyncio.wait_for(ES.get_session_notifications(e_subs_id), timeout=15)
                    notification = await asyncio.wait_for(ES.consume_notification(e_subs_id), timeout=15)
                    # print(f"[LOOP NOTIFICATION]: {notification}")
                    if notification[0] != NotifType.EMPTY:
                        # signals = ES.combine_signals(session_notifications)
                        # yield SSE.patch_signals(signals)
                        yield process_notification(notification)
                        # ES.consume_notifications(e_subs_id, session_notifications)
                except asyncio.TimeoutError:
                    yield SSE.patch_signals({}) # heartbeat / keep-alive, prevents idle timeouts
        finally:
            print(f"Finished listening for session: {e_subs_id}")
            ES.unsubscribe_session(e_subs_id)
    response = StreamingResponse(
        pipeline(),
        media_type="text/event-stream"
    )

    if not request.cookies.get(EVENT_SUBSCRIPTION_ID, ""):
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