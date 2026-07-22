import uuid
import asyncio
from typing import AsyncGenerator
from fastapi.requests import Request
from fastapi.routing import APIRouter
from datetime import datetime, timezone
from datastar_py.sse import DatastarEvent
from fastapi.responses import HTMLResponse
from datastar_py.fastapi import DatastarResponse
from datastar_py import ServerSentEventGenerator as SSE

from ..shared import templates

router = APIRouter(prefix="/counter")

INTERVAL = 1

@router.get("", response_class=HTMLResponse)
def get_counter_page(request: Request):
    print("Returning counter page")
    return templates.TemplateResponse(
        request=request, name="counter/counter.html"
    )

@router.get("/stream", response_class=DatastarResponse)
async def update_message_stream(request: Request) -> AsyncGenerator[DatastarEvent, None]:
    print("COUNTER STREAM INITIALIZED")
    counter = 1
    while True:
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
def update_message() -> DatastarResponse:
    print("CLICKED ON BUTTON")
    return DatastarResponse(
        SSE.patch_signals({"message": str(uuid.uuid4())})
    )