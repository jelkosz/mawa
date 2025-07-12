import asyncio
import threading

from adk_web_initialization.adk_web_agent_definitions import create_adk_web_root_agent

# This file prepares the root_agent for adk web which expects it to be synchronously loaded even though it is async

root_agent = None
_agent_ready = threading.Event()

def init_agent_sync():
    global root_agent
    root_agent = asyncio.run(create_adk_web_root_agent())
    _agent_ready.set()

threading.Thread(target=init_agent_sync, daemon=True).start()

def get_root_agent():
    _agent_ready.wait()
    return root_agent

try:
    _agent_ready.wait(timeout=5)
    if root_agent is None:
        raise RuntimeError("root_agent initialization failed")
except Exception as e:
    print(f"Agent not ready: {e}")
