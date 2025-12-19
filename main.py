from fastapi import FastAPI, Form
from fastapi.responses import StreamingResponse, HTMLResponse
from telethon import TelegramClient
import io
import os
import asyncio

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <html>
        <body>
            <h2>Start Telegram Bot</h2>
            /start
                API_ID: <input type="text" name="api_id"><br>
                API_HASH: <input type="text" name="api_hash"><br>
                BOT_TOKEN: <input type="text" name="bot_token"><br>
                <input type="submit" value="Start Bot">
            </form>
        </body>
    </html>
    """

@app.post("/start")
async def start_bot(api_id: str = Form(...), api_hash: str = Form(...), bot_token: str = Form(...)):
    session_name = "bot_session"
    client = TelegramClient(session_name, int(api_id), api_hash)

    await client.start(bot_token=bot_token)
    await client.disconnect()

    # Read session files
    session_file = f"{session_name}.session"
    journal_file = f"{session_name}.journal"

    # Prepare download links
    html = "<h3>Bot Started Successfully!</h3>"
    if os.path.exists(session_file):
        html += f'/download?file={session_file}Download {session_file}</a><br>'
    if os.path.exists(journal_file):
        html += f'/download?file={journal_file}Download {journal_file}</a><br>'
    return HTMLResponse(content=html)

@app.get("/download")
async def download_file(file: str):
    if not os.path.exists(file):
        return {"error": "File not found"}
    with open(file, "rb") as f:
        data = io.BytesIO(f.read())
    return StreamingResponse(data, media_type="application/octet-stream", headers={"Content-Disposition": f"attachment; filename={file}"})
