import asyncio
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Literal

from datastar_py import ServerSentEventGenerator as SSE
from datastar_py.fastapi import DatastarResponse
from datastar_py.sse import DatastarEvent
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRouter

from backend.event_system import event_system as ES

from ..shared import templates

router = APIRouter(prefix="/counter")

INTERVAL = 1

def construct_cookie_response(
        response: HTMLResponse | DatastarResponse | None,
        key: str, value: str, is_secure: bool = True, 
        http_only: bool = True, samesite: Literal['lax', 'strict', 'none'] | None = 'lax', max_age: int = 3600
    ) -> HTMLResponse | DatastarResponse:

    print(f"[CONSTRUCTING COOKIE] for key: {key}")
    if not response:
        response = HTMLResponse()
    response.set_cookie(
        key=key,
        value=value,
        httponly=http_only,
        secure=is_secure,
        samesite=samesite,
        max_age=max_age
    )
    return response

@router.get("", response_class=HTMLResponse)
def get_counter_page(request: Request):
    print("Returning counter page")
    html = templates.get_template("counter/counter.html").render({"request": request})
    # return templates.TemplateResponse(
    #     request=request, name="counter/counter.html"
    # )
    response = HTMLResponse(html)
    response = construct_cookie_response(response, "id", str(uuid.uuid4()))
    return response

@router.get("/stream", response_class=DatastarResponse)
async def update_message_stream(request: Request) -> AsyncGenerator[DatastarEvent, None]:
    print("COUNTER STREAM INITIALIZED")
    response = DatastarResponse()
    response = construct_cookie_response(response, str(uuid.uuid4()), str(uuid.uuid4()))
    counter = 1
    while True:
        if ES.should_shutdown():
            break
        if await request.is_disconnected():
            print("DISCONNECTED")
            break
        now = datetime.now(timezone.utc)
        date_str = f"{now:%I:%M:%S}.{now.microsecond // 10000:02d} {now:%p}"

        # yield SSE.patch_signals({"counter": counter})
        yield SSE.patch_signals({"counter": date_str})
        # print(f"{counter=}")
        await asyncio.sleep(INTERVAL)
        counter += 1
    yield SSE.patch_signals({"infoMsg": "Stream has been stopped"})

@router.post("")
def update_message(request: Request) -> DatastarResponse:
    print("CLICKED ON BUTTON")
    return DatastarResponse(
        SSE.patch_signals({"message": request.cookies.get("id")})
    )