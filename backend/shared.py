from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


SESSION_TOKEN_STR = "s_token"
SESSION_USER_UUID_STR = "s_user_uuid"
templates = Jinja2Templates(directory="frontend")