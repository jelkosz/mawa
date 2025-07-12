from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from google import genai
from starlette.responses import HTMLResponse

from mawa.adk_bridge import run_root_agent, run_style_extraction_agent
from mawa.cache import store_to_cache, get_from_cache
from mawa.constants import ROOT_PROMPT
from mawa.mcp_tools_utils import close_mcp_connection

FOOTBALL_FAVICON_SVG = """<svg xmlns="[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)" viewBox="0 0 100 100">
  <circle cx="50" cy="50" r="48" fill="#FFFFFF"/> <polygon points="50,25 70,40 60,70 40,70 30,40" fill="#000000"/> </svg>"""

USER_NAME = "hardcoded_username"

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_mcp_connection()

app = FastAPI(lifespan=lifespan)
client = genai.Client()

@app.post("/api", response_class=HTMLResponse)
async def api(request: Request):
    body = await request.body()

    return await _run_mawa(USER_NAME, body.decode("utf-8"))


@app.get("/{root_prompt}", response_class=HTMLResponse)
async def root(root_prompt: str):
    if root_prompt == "favicon.ico":
        return Response(content=FOOTBALL_FAVICON_SVG, media_type="image/svg+xml")

    store_to_cache(ROOT_PROMPT, root_prompt)
    return await _run_mawa(USER_NAME, root_prompt)

async def _run_mawa(username, prompt):
    styling_instructions = await run_style_extraction_agent(username, get_from_cache(ROOT_PROMPT))
    return HTMLResponse(await run_root_agent(username, prompt, styling_instructions))
