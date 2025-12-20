from fastapi import FastAPI, Form, Query
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from telethon import TelegramClient
import os
import io

app = FastAPI(title="Telethon Bot Session Generator (Vercel Zero-Config)")

HTML_FORM = """
<html>
  <head><title>Telethon Bot Session Generator</title></head>
  <body style="font-family: sans-serif; padding: 2rem;">
    <h2>Create Telethon Bot Session</h2>
    /api/start
      <label>API_ID:</label><br>
      <input type="text" name="api_id" required><br><br>

      <label>API_HASH:</label><br>
      <input type="text" name="api_hash" required><br><br>

      <label>BOT_TOKEN:</label><br>
      <input type="text" name="bot_token" required><br><br>

      <button type="submit">Start Bot & Generate Session</button>
    </form>
    <p style="margin-top:1rem; color:#666">
      Files are generated in the serverless temp folder (<code>/tmp</code>) and offered immediately for download.
    </p>
  </body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML_FORM

@app.post("/start", response_class=HTMLResponse)
async def start_bot(
    api_id: str = Form(...),
    api_hash: str = Form(...),
    bot_token: str = Form(...)
):
    # Always write to the ephemeral temp directory in serverless environments
    base = os.path.join("/tmp", "bot_session")  # Telethon will add ".session" if no extension
    client = TelegramClient(base, int(api_id), api_hash)

    # Start and immediately disconnect to flush session data to disk
    await client.start(bot_token=bot_token)
    await client.disconnect()

    primary = f"{base}.session"
    journal1 = f"{base}.session-journal"  # common SQLite journal filename
    journal2 = f"{base}.journal"          # rare/legacy alternative

    html = ["<h3>Bot Started Successfully!</h3>"]

    if os.path.exists(primary):
        html.append(
            f'<p>/api/download?file={primary}Download {os.path.basename(primary)}</a></p>'
        )
    else:
        html.append("<p style='color:red'>Primary session file not found.</p>")

    if os.path.exists(journal1):
        html.append(
            f'<p>/api/download?file={journal1}Download {os.path.basename(journal1)}</a></p>'
        )
    elif os.path.exists(journal2):
        html.append(
            f'<p>/api/download?file={journal2}Download {os.path.basename(journal2)}</a></p>'
        )
    else:
        html.append("<p>No SQLite journal file detected (it may be unnecessary).</p>")

    html.append('<p>/api/Back</a></p>')
    return HTMLResponse(content="\n".join(html))

@app.get("/download")
async def download_file(
    file: str = Query(..., description="Absolute path under /tmp, e.g., /tmp/bot_session.session")
):
    # Restrict to temp dir for safety
    if not file.startswith("/tmp/"):
        return JSONResponse(status_code=400, content={"error": "Invalid file path."})

    if not os.path.exists(file):
        return JSONResponse(status_code=404, content={"error": "File not found."})

    with open(file, "rb") as f:
        buf = io.BytesIO(f.read())

    return StreamingResponse(
        buf,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{os.path.basename(file)}"'}
    )
  
