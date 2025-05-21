from click import prompt
from fastapi import FastAPI, Request, Response
from google import genai
from starlette.responses import HTMLResponse

from mawa.adk_bridge import call_adk

FOOTBALL_FAVICON_SVG = """<svg xmlns="[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)" viewBox="0 0 100 100">
  <circle cx="50" cy="50" r="48" fill="#FFFFFF"/> <polygon points="50,25 70,40 60,70 40,70 30,40" fill="#000000"/> </svg>"""

app = FastAPI()
client = genai.Client()

@app.post("/api", response_class=HTMLResponse)
async def api(request: Request):
    body = await request.body()
    return await call_adk("hardcoded_username", body.decode("utf-8"))


@app.get("/{root_prompt}", response_class=HTMLResponse)
async def root(root_prompt: str):
    if root_prompt == "favicon.ico":
        return Response(content=FOOTBALL_FAVICON_SVG, media_type="image/svg+xml")

    return await call_adk("hardcoded_username", root_prompt)
