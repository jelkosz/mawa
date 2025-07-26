import ast
import time
from google.adk.events import Event, EventActions
from google.adk.sessions import InMemorySessionService, Session, State
from google.adk.runners import Runner
from google.genai import types
import uuid
from .agent import _create_style_extraction_agent, create_main_agent
from .cache import store_to_cache, key_to_hash, clear_from_cache, get_from_cache, is_cached
from .constants import ROOT_PROMPT

APP_NAME = "Table Football App"

main_agent_session_service = InMemorySessionService()

style_extraction_service = InMemorySessionService()


async def _store_styling_info_to_state(instructions: str, session: Session):
    """
       Stores the detailed styling instructions extracted from user description to the state.

       Args:
           instructions: The instructions extracted by a different agent
           session: The session to which the event should be added to
       """

    current_time = time.time()
    state_changes = {
        f"styling_instructions": instructions
    }
    actions_with_update = EventActions(state_delta=state_changes)
    system_event = Event(
        invocation_id="styling_instructions_update",
        author="system",
        actions=actions_with_update,
        timestamp=current_time
    )
    await main_agent_session_service.append_event(session, system_event)


async def _store_hashed_prompt_to_state(prompt: str, session: Session):
    """
       Stores the hash of the prompt to session state so that the agents can access it.
       It is meant to be used for cache invalidation

       Args:
           prompt: The string to be processed and stored.
           session: The session to which the event should be added to
       """

    current_time = time.time()
    state_changes = {
        f"current_prompt_hash": key_to_hash(prompt)
    }
    actions_with_update = EventActions(state_delta=state_changes)
    system_event = Event(
        invocation_id="prompt_hash_update",
        author="system",
        actions=actions_with_update,
        timestamp=current_time
    )
    await main_agent_session_service.append_event(session, system_event)


async def _maybe_store_custom_component_prompt(prompt: str, session: Session):
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
            await main_agent_session_service.append_event(session, system_event)
            return data['prompt']
        else:
            return prompt
    except (ValueError, SyntaxError, TypeError):
        return prompt


def _maybe_invalidate_cache(prompt: str):
    try:
        data = ast.literal_eval(prompt)
        if isinstance(data, dict) and 'invalidate_cache_key' in data:
            clear_from_cache(data['invalidate_cache_key'])
    except (ValueError, SyntaxError, TypeError):
        # it is an OK state if the prompt can not be parsed
        pass


def _is_cache_hit(event: Event) -> bool:
    return isinstance(event.custom_metadata, dict) and 'cache_response' in event.custom_metadata and \
        event.custom_metadata['cache_response'] == True


async def run_root_agent(user_id, prompt, styling_instructions):
    session_id = str(uuid.uuid4())
    session = await main_agent_session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id
    )

    main_agent_runner = Runner(
        agent=create_main_agent(),
        app_name=APP_NAME,
        session_service=main_agent_session_service
    )

    await _maybe_store_custom_component_prompt(prompt, session)
    await _store_hashed_prompt_to_state(prompt, session)
    await _store_styling_info_to_state(styling_instructions, session)

    _maybe_invalidate_cache(prompt)

    content = types.Content(role='user', parts=[types.Part(text=prompt)])

    final_response_text = "Agent did not produce a final response."
    async for event in main_agent_runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        print(
            f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Branch: {event.branch}, Content: {event.content}")

        # todo remove the hardcoded list of returning agents
        if event.is_final_response() and (
                _is_cache_hit(event) or event.author in ["component_page_merger_agent", "main_page_agent",
                                                         "data_saver_agent", "data_loader_agent"]):
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate:
                final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
            break

    print(f"<<< Agent Response: {final_response_text}")
    print(f"Runner created for agent '{main_agent_runner.agent.name}'.")

    # todo null checks
    reloaded_session = await main_agent_session_service.get_session(app_name=APP_NAME, user_id=user_id,
                                                                         session_id=session_id)
    cache_decision_agent_output = reloaded_session.state.get(
        'cache_decision_agent_output').strip('\n')
    if cache_decision_agent_output == 'CACHE':
        root_prompt = get_from_cache(ROOT_PROMPT)
        # this combination is used to make sure that different styling of the component will be cached separately
        cache_key = root_prompt + prompt
        store_to_cache(cache_key, final_response_text)
    return final_response_text


async def run_style_extraction_agent(user_id, prompt):
    session_id = str(uuid.uuid4())
    await style_extraction_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id
    )
    style_extraction_agent_runner = Runner(
        agent=await _create_style_extraction_agent(),
        app_name=APP_NAME,
        session_service=style_extraction_service
    )

    cache_key = f"styling_instructions {prompt}"
    if is_cached(cache_key):
        return get_from_cache(cache_key)

    content = types.Content(role='user', parts=[types.Part(text=prompt)])

    final_response_text = "No specific styling provided by the user."
    async for event in style_extraction_agent_runner.run_async(user_id=user_id, session_id=session_id,
                                                               new_message=content):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate:
                final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
            break

    store_to_cache(cache_key, final_response_text)
    return final_response_text
