from google.adk import Agent
from google.genai.types import GenerateContentConfig

from mawa.agent_definitions import STRICT_AGENT_TEMPERATURE, _create_component_page_agent, _create_data_loader_agent, \
    _create_data_saver_agent
from mawa.callbacks import load_from_cache


async def create_adk_web_root_agent():
    return Agent(
        name="generic_webpage_root_agent",
        model="gemini-2.0-flash",
        generate_content_config=GenerateContentConfig(
            temperature=STRICT_AGENT_TEMPERATURE,
        ),
        description=(
            "Root agent delegating to appropriate agents."
        ),
        instruction=(
            """
            You are router agent delegating work to different agents. In case the answer is an HTML, do not interpret it further and just return it as-is.
            Always delegate the request to the appropriate agent. For example:
             - if the request asks for a component, delegate to component_page_agent
             - if the request asks for creating, storing or saving data, delegate to data_saver_agent
             - in other cases, delegate to the main_page_agent
            """
        ),
        sub_agents=[
            await _create_component_page_agent(),
            await _create_data_loader_agent(),
            await _create_data_saver_agent(),
        ],
        before_model_callback=load_from_cache,
    )