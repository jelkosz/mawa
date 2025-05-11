from fastapi import FastAPI, Request
from google import genai
from starlette.responses import HTMLResponse

from mawa.adk_bridge import call_adk

app = FastAPI()
client = genai.Client()

@app.post("/api", response_class=HTMLResponse)
async def api(request: Request):
    body = await request.body()
    return await call_adk("hardcoded_username", body.decode("utf-8"))


@app.get("/{root_prompt}", response_class=HTMLResponse)
async def root(root_prompt: str):
    return await call_adk("hardcoded_username", root_prompt)
