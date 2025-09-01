import ast

def _maybe_extract_component_id_from_prompt(prompt: str):
    try:
        data = ast.literal_eval(prompt)

        if isinstance(data, dict) and 'id' in data and 'prompt' in data:
            return data['id']
        else:
            return prompt
    except (ValueError, SyntaxError, TypeError):
        return prompt