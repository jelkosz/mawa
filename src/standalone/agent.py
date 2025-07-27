from mawa.agent import create_main_agent

root_agent = create_main_agent({
    "{current_prompt_hash}": "mock_root_prompt_hash",
    "{styling_instructions}": "mock_styling_instructions"
})
