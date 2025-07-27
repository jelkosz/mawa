from mawa.agent import create_main_agent
from mawa.constants import STYLING_INSTRUCTIONS, CURRENT_PROMPT_HASH

root_agent = create_main_agent({
    f"{{{CURRENT_PROMPT_HASH}}}": "mock_root_prompt_hash",
    f"""{{{STYLING_INSTRUCTIONS}}}""": "mock_styling_instructions"
})
