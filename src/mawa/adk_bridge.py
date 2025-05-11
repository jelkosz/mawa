
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from .agent import root_agent
import uuid

session_service = InMemorySessionService()
APP_NAME = "Fotbalek App"

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service
)

async def call_adk(user_id, prompt):
    # todo: pass session from outside
    session_id = str(uuid.uuid4())
    session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id
    )
    content = types.Content(role='user', parts=[types.Part(text=prompt)])
    final_response_text = "Agent did not produce a final response."
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        print(
            f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Branch: {event.branch}, Content: {event.content}")

        # todo remove the hardcoded list of returning agents
        if event.is_final_response() and event.author in ["component_page_merger_agent", "main_page_agent", "data_saver_agent"]:
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate:
                final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
            break

    print(f"<<< Agent Response: {final_response_text}")
    print(f"Runner created for agent '{runner.agent.name}'.")
    return final_response_text
