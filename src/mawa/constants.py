# This file contains constants which can be considered a form of an API - a way how agents or callbacks can access data added to state by the orchestrator code.

# The prompt which is in the URL. For example, in "localhost:8000/a page in calming style" it would be "a page in calming style".
ROOT_PROMPT = "root_prompt"

# Will be stored in the session and contain instructions for components on how to style themselves.
STYLING_INSTRUCTIONS = "styling_instructions"

# Will be stored in the session and contain the hash of the prompt which is now being handled.
# It can be used for cache invalidation.
CURRENT_PROMPT_HASH = "current_prompt_hash"