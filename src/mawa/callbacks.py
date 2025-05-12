from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest


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
    # todo add the instructions to use the data prompts from the state
    # instructions here:
    # https://google.github.io/adk-docs/callbacks/types-of-callbacks/#before-model-callback
    return None