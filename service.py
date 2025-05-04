import json
import zipfile

from io import BytesIO
from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.dokken import DokkenAPI
from src.steam_service import get_encrypted_ticket

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class LoginRequest(BaseModel):
    username: str
    password: Optional[str] = None
    auth_code: Optional[str] = None
    two_factor_code: Optional[str] = None
    login_key: Optional[str] = None

class DataRequest(BaseModel):
    ticket: str

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/healthcheck")
async def healthcheck():
    return "ok"

@app.post("/get_ticket")
async def get_ticket(data: LoginRequest):
    try:
        result = await get_encrypted_ticket(
            username=data.username,
            password=data.password,
            auth_code=data.auth_code,
            two_factor_code=data.two_factor_code,
            login_key=data.login_key,
            app_id=1818750,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown Steam error"))

    return result


@app.get("/data")
async def get_data(ticket: str = Query(..., description="EncryptedAppTicket for MVS")):
    dokken_api = DokkenAPI(ticket)

    (access_info, profile_info), account_id = dokken_api.get_user_mvs_data()
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        # Save access_info as access.json
        zip_file.writestr("access.json", json.dumps(access_info, ensure_ascii=False, indent=4))

        # Save profile_info as individual JSON files
        for key, data in profile_info.items():
            zip_file.writestr(f"{key}.json", json.dumps(data, ensure_ascii=False, indent=4))

    # Prepare the zip for download (seek to the start of the buffer)
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={account_id}.zip"},
    )
