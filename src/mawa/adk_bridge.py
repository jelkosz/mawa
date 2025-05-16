import ast
import time

from google.adk.events import Event, EventActions
from google.adk.sessions import InMemorySessionService, Session, State
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


def maybe_store_user_prompt(prompt: str, session: Session):
    """
       Processes an input string. If the string is a JSON object with an 'id' and 'prompt'
       property, stores the prompt under the user:id in the state.
       The id in this case refers to the id of the UI component this prompt is used to generate.

        If the input string is not a json, it just returns it as is and does not store anything.
       Args:
           prompt: The string to be processed.
           session: The session to which the event should be added to
       """
    try:
        data = ast.literal_eval(prompt)

        if isinstance(data, dict) and 'id' in data and 'prompt' in data:
            current_time = time.time()
            state_changes = {
                f"{State.USER_PREFIX}{data['id']}": data['prompt']
            }
            actions_with_update = EventActions(state_delta=state_changes)
            system_event = Event(
                invocation_id="component_prompt_update",
                author="system",
                actions=actions_with_update,
                timestamp=current_time
            )
            session_service.append_event(session, system_event)
            return data['prompt']
        else:
            return prompt
    except (ValueError, SyntaxError, TypeError):
        return prompt


async def call_adk(user_id, prompt):
    session_id = str(uuid.uuid4())
    session = session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id
    )

    maybe_store_user_prompt(prompt, session)

    content = types.Content(role='user', parts=[types.Part(text=prompt)])

    final_response_text = "Agent did not produce a final response."
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        print(
            f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Branch: {event.branch}, Content: {event.content}")

        # todo remove the hardcoded list of returning agents
        if event.is_final_response() and event.author in ["component_page_merger_agent", "main_page_agent",
                                                          "data_saver_agent"]:
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate:
                final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
            break

    print(f"<<< Agent Response: {final_response_text}")
    print(f"Runner created for agent '{runner.agent.name}'.")
    return final_response_text
