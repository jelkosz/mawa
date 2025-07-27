import json
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from google.genai.types import Content, Part
from mawa.cache import is_cached, get_from_cache
from mawa.constants import ROOT_PROMPT

def load_from_cache(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    cache_decision_agent_output = callback_context.state.get('cache_decision_agent_output')
    if cache_decision_agent_output:
        cache_decision_agent_output = cache_decision_agent_output.strip('\n')
    else:
        return None

    if cache_decision_agent_output == 'CACHE':
        root_prompt = get_from_cache(ROOT_PROMPT)
        key = root_prompt + callback_context.user_content.parts[0].text
        if is_cached(key):
            cache_response = LlmResponse(
                content=Content(
                    role="model",
                    parts=[Part(text=get_from_cache(key))],
                )
            )
            cache_response.custom_metadata = {'cache_response': True}
            return cache_response
    return None

def clear_technical_response(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> Optional[LlmResponse]:
    cleaned_response = llm_response.model_copy(deep=True)
    return clean_response_parts(cleaned_response)


def clean_response_parts(cleaned_response):
    """
    Cleans the text content of each part in a response by:
    1. Stripping leading/trailing whitespace.
    2. Removing common code block delimiters (```html, ```json, ```).

    Args:
        cleaned_response: An object with a 'content' attribute, which in turn
                          has a 'parts' attribute (an iterable of objects
                          each having a 'text' attribute).

    Returns:
        The modified cleaned_response object with cleaned text parts.
    """
    if cleaned_response is None or cleaned_response.content is None or cleaned_response.content.parts is None:
        return cleaned_response

    for part in cleaned_response.content.parts:
        if part.text is None:
            continue

        # Strip whitespace from the text
        processed_text = part.text.strip()

        # Remove known code block prefixes
        if processed_text.startswith("```html"):
            processed_text = processed_text.removeprefix("```html")
        elif processed_text.startswith("```json"):
            processed_text = processed_text.removeprefix("```json")

        # Remove the common code block suffix
        processed_text = processed_text.removesuffix("```")

        # Update the part's text with the cleaned version
        part.text = processed_text

    return cleaned_response


def inject_stored_component_ids(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    original_instruction = llm_request.config.system_instruction or Content(role="system", parts=[])
    if not isinstance(original_instruction, Content):
        # Handle case where it might be a string (though config expects Content)
        original_instruction = Content(role="system", parts=[Part(text=str(original_instruction))])
    if not original_instruction.parts:
        original_instruction.parts.append(Part(text=""))  # Add an empty part if none exist

    # Modify the text of the first part
    custom_component_prompts = filter_component_keys(callback_context.state.to_dict())
    prefix = "# Instructions Provided by Users Per Component" + custom_component_prompts

    modified_text = prefix + (original_instruction.parts[0].text or "")

    if custom_component_prompts != "":
        original_instruction.parts[0].text = modified_text

    return None

def filter_component_keys(data_dict):
    """
    Filters keys starting with 'user:component' from a dictionary and formats them into a JSON string.

    Args:
        data_dict (dict): Dictionary containing keys and values

    Returns:
        str: JSON string with componentId and bodyValue for each component
    """

    components = []

    for key, value in data_dict.items():
        if key.startswith('user:component'):
            component_name = key.replace('user:', '')
            components.append({
                'componentId': component_name,
                'bodyValue': value
            })

    result = json.dumps(components)

    return result