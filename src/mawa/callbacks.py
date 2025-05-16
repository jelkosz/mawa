from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from google.genai.types import Content, Part


# todo add clear ```json too
def clean_html_after_model_callback(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> Optional[LlmResponse]:
    cleaned_response = llm_response.model_copy(deep=True)
    if cleaned_response.content is None:
        return None

    for part in cleaned_response.content.parts:
        cleaned_text = part.text
        if cleaned_text is None:
            continue
        cleaned_text = cleaned_text.strip()
        if cleaned_text.startswith("```html"):
            cleaned_text = cleaned_text[len("```html"):]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-len("```")]
        part.text = cleaned_text
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

    llm_request.config.system_instruction = original_instruction
    return None

# todo taken from claude without reviewing it, needs to be reviewed and cleaned up
def filter_component_keys(data_dict):
    """
    Filters keys starting with 'user:component' from a dictionary and formats them into a JSON string.

    Args:
        data_dict (dict): Dictionary containing keys and values

    Returns:
        str: JSON string with componentId and bodyValue for each component
    """
    import json

    # Initialize an empty list to store the component entries
    components = []

    # Iterate through the dictionary
    for key, value in data_dict.items():
        # Check if key starts with 'user:component'
        if key.startswith('user:component'):
            # Extract the component name (remove 'user:' prefix)
            component_name = key.replace('user:', '')

            # Add entry to the components list
            components.append({
                'componentId': component_name,
                'bodyValue': value
            })

    # Convert the list to a JSON string
    result = json.dumps(components)

    return result