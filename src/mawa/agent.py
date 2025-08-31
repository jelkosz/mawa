import os
from typing import Optional

from google.adk.agents import Agent, ParallelAgent, SequentialAgent
from google.adk.planners import BuiltInPlanner
from google.adk.tools.mcp_tool import MCPToolset
from google.genai.types import GenerateContentConfig, ThinkingConfig
from mcp import StdioServerParameters

from mawa.callbacks import clear_technical_response, inject_stored_component_ids, load_from_cache
from mawa.constants import STYLING_INSTRUCTIONS, CURRENT_PROMPT_HASH

STYLING_INSTRUCTIONS_SECTION = f"""
            ## Styling Instructions
                - Never come up with your own colors/fonts or styles in general
                - Always follow the following styling instructions: {{{STYLING_INSTRUCTIONS}}}
"""

STRICT_AGENT_TEMPERATURE = 0.0
CREATIVE_AGENT_TEMPERATURE = 1.5
MODEL_FULL = "gemini-2.5-flash"
MODEL_LITE = "gemini-2.0-flash-lite"
NOT_THINKING_MODEL = "gemini-1.5-flash"

_data_provider_mcp_toolset = MCPToolset(
    connection_params=StdioServerParameters(
        command='poetry',
        args=[
            "run",
            "mcp",
            "run",
            os.path.abspath("/home/jelene/work/mawa/src/mawa_mcp_server/data_provider.py")
        ],
    ),
)


def _create_style_extraction_agent():
    return Agent(
        name="style_extraction_agent",
        model=MODEL_FULL,
        generate_content_config=GenerateContentConfig(
            temperature=CREATIVE_AGENT_TEMPERATURE,
        ),
        description=(
            "Agent to generate clear styling instructions from vague user description."
        ),
        instruction=(
            """
                You are an agent which generates clear instructions for other LLM agents to style their components.
                Your input is a vague description by the human user about the expected style.
                Your output is an un-ambiguous set of LLM processable instructions on how to style its HTML components.
                
                ## Follow the following rules:
                    - While generating the instructions, dont generate actual HTML.
                    - Never recommend using external styling. 
                    - Always add specific un-ambiguous instructions about colors, fonts, border styles and background colors.
                    - Make the instructions one paragraphs long.
                    - Never use terms like: "such as", "or similar" etc since they introduce ambiguity.
                    - Add instructions for how to behave in case of this instructions dont contain the description explicitely. 
            """
        ),
    )

def _create_main_page_agent(default_session_variables: Optional[dict[str, str]]):
    instructions = f"""
            You are an agent which generates a simple HTML page. Always generate a HTML page with head and body.
            Your output will be directly interpreted by a browser so don't include any explanation or any additional text around the HTML content.
            Do add additional components based on the user prompt.
            
            # The Layout of the Page:
                - the page has a masthead containing a logout button (doing nothing) and a text saying "Dynamic Table Football"
                - main section has as many components as the user asks for. If the user does not specify the main section layout in any way, refer to the "Default Main Section Layout" section.
                - for details on how to generate components, refer to the "Generating Components" section.
                - if the user does specify the layout, interpret it as an attempt to either override or to extend the Default Main Section Layout and incorporate this ask.
            
            # Generating Components
                - for each component, generate a header and a content_part.
                - for each component generate a unique id based on the position in the page. Examples:
                   - first row, first column: id=component_1_1
                   - second row, third column: id=component_2_3
                - the ONLY part, which can be modified as per user request is the "body->prompt" from the content_part. Nothing else.
            
                ## Header
                    - the header is a <div> having only one clickable "Edit" icon in the top right corner, nothing else. If the mouse hovers over it, the mouse pointer will change to a hand icon.
                    - the header never has a title. Never add anything like "Component 1" as the title of the header or anything similar. 
                    - if the edit icon is clicked, an edit component will be opened.
                    - an example of to how react to onclick on the edit button: "onclick="document.getElementById('editDialog_5789').style.display='block';"
                    - on load, the edit dialog is always closed.
            
                ## Edit Component
                    - the edit component is a dialog with a text editor, a save button and cancel button.
                    - generate a unique ID for this dialog to avoid clash with an another instance of it.
                    - the content of the text editor will be the content of the body->prompt from the content_part.
                    - when the cancel button is clicked, the dialog is closed and no additional action is performed
                    - when the save button is clicked, then:
                       - the content of the editor will replace the content of the body->prompt from the content_part.
                       - make sure you add the actual text of editor to the content_part->body, not a javascript able to provide it.
                       - make sure you always add 'invalidate_cache_key': '{{{CURRENT_PROMPT_HASH}}}' part to the body.
                       - make sure the body of the POST is always a valid json. For example: "{{'id': 'component_1_1', 'prompt': 'Generate me a fun fact about cats.', 'invalidate_cache_key': '{{current_prompt_hash}}'}}".
                       - the script will re-fetch the content if the content_part changed
                       - the dialog will be closed
                    - while the component is loading, replace the content of detail-component-id by something which will tell the user the component is being re-loaded..
            
                ## content_part
                    - the body will be a <div> with an id field and a <script> which will load the content of the div.
                    - An example:
                        <div id="detail-component-id-1" class="loading-message">Loading Component...</div>
                        <script>
                           function loadHTMLWithScripts(html, targetId) {{
                                const targetElement = document.getElementById(targetId);
                                const parser = new DOMParser();
                                const doc = parser.parseFromString(html, 'text/html');
                                const scripts = Array.from(doc.querySelectorAll('script'));
                                scripts.forEach(script => script.remove());
                                targetElement.innerHTML = doc.body.innerHTML;
                                scripts.forEach(oldScript => {{
                                    const newScript = document.createElement('script');
                                    Array.from(oldScript.attributes).forEach(attr => {{
                                        newScript.setAttribute(attr.name, attr.value);
                                    }});
                                    newScript.textContent = oldScript.textContent;
                                    document.body.appendChild(newScript);
                                }});
                            }}
                          function updateComponent(componentId, newPrompt, targetDivId) {{
                            document.getElementById(targetDivId).innerHTML = '<div class="loading-message">Reloading component...</div>';
                            fetch('/api', {{
                                method: 'POST',
                                headers: {{
                                    'Content-Type': 'application/json'
                                }},
                                body: JSON.stringify({{'id': componentId, 'prompt': newPrompt, 'invalidate_cache_key': '{{{CURRENT_PROMPT_HASH}}}'}})
                            }})
                            .then(res => res.text())
                            .then(html => {{
                                loadHTMLWithScripts(html, targetDivId);
                            }})
                            .catch(error => {{
                                document.getElementById(targetDivId).innerHTML = '<div style="color: red;">Error loading component.</div>';
                                console.error('Error:', error);
                            }});
                        }}
                        // Initial load
                          fetch('/api', {{
                                method: 'POST',
                                headers: {{
                                    'Content-Type': 'application/json'
                                }},
                                body: JSON.stringify({{'id': 'component_1_1', 'prompt': 'Generate me a fun fact about cats.'}})
                            }})
                            .then(res => res.text())
                            .then(html => {{
                                loadHTMLWithScripts(html, 'detail-component-id-1');
                            }})
                            .catch(error => {{
                                document.getElementById('detail-component-id-1').innerHTML = '<div style="color: red;">Error loading component.</div>';
                                console.error('Error:', error);
                            }});
                        </script>
                    - if the body is not specified, add the following text to it: "{{'id': the generated id for this component, 'prompt': 'Generate a simple div containing Hello from a div text inside', 'invalidate_cache_key': '{{{CURRENT_PROMPT_HASH}}}'}}."
            
                ## Default Main Section Layout
                    - Refer to the "Instructions Provided by Users Per Component" section, to get the default body values per component ID. If this section is not present, use the following defaults:
                    - The main section has a single stack of 1 component
                        - the first component has a body: "Generate me a component with a table of matches from the brno league containing the name of both players and their scores. First two columns are the player names, last two the scores. Make sure to add an add new match component."

{STYLING_INSTRUCTIONS_SECTION}
        """

    # injects mock values for tests/adk web case
    if default_session_variables is not None:
        for key, value in default_session_variables.items():
            instructions = instructions.replace(key, value)

    return Agent(
        name="main_page_agent",
        model="gemini-2.0-flash",
        generate_content_config=GenerateContentConfig(
            temperature=STRICT_AGENT_TEMPERATURE,
        ),
        description=(
            "Agent to generate the main html page of the document."
        ),
        instruction=(
            instructions
        ),
        before_model_callback=inject_stored_component_ids,
        after_model_callback=clear_technical_response,
    )


def _create_data_loader_agent():
    # tools = await load_mcp_tools()

    return Agent(
        name="data_loader_agent",
        model=NOT_THINKING_MODEL,
        generate_content_config=GenerateContentConfig(
            temperature=STRICT_AGENT_TEMPERATURE,
        ),
        description=(
            "Agent loading data from a datasource."
        ),
        instruction=(
            """
                You are a specialized agent designed to load data using available tools.

                ## Available Tools:
                    - For loading the data, you have to call one of the following tools: [get_matches].            

                ## Input Format:
                    - Your input will always be a JSON object with the following structure:

                    {
                        "request": "load data",
                        "source": "matches_database",
                        "format": "JSON", 
                        "output_format": [
                            {
                                "name": "userName1",
                                "age": "userAge1"
                            },
                            {
                                "name": "userName2",
                                "age": "userAge2"
                            },
                        ]
                    }

                ## Output Format:
                    - Your output will always be a JSON array with the structure following the output_format from the input.
                    - Convert the output from the get_matches tool to conform to the output_format requested.
            """
        ),
        after_model_callback=clear_technical_response,

        tools=[_data_provider_mcp_toolset]
    )


def _create_tabular_data_visualization_agent():
    return Agent(
        name="tabular_data_visualization_agent",
        model=MODEL_FULL,
        generate_content_config=GenerateContentConfig(
            temperature=STRICT_AGENT_TEMPERATURE,
        ),
        description=(
            "Agent to generate an HTML table with data."
        ),
        instruction=(
            f"""
            You are a specialized agent designed to generate nicely formatted HTML tables.

            ## Output Format:
                - Your output MUST be raw HTML, directly renderable by a web browser.
                - DO NOT include any conversational text, explanations, or extraneous characters outside the HTML structure.
                - If no table generation is requested, return the literal string `NO_CONTENT`.
            
            ## Table Generation Rules:
                ### Data Loading:
                    - Data MUST be loaded asynchronously via a `POST` request to the `/api` endpoint. 
                    - Generate a <script> tag which uses XHR to load the data.
                    - Make sure this script will call the server right after this component is done rendering.
                    - Never add an ADD button to the component. 
                    - Add a reload button. If clicked, the same server call will be executed loading the data again.
                    - The `POST` request body MUST be a JSON object specifying:
                        - `request`: "load data",
                        - `source`: (string) The origin or identifier of the data.
                        - `format`: (string) The desired data format (e.g., 'JSON', 'CSV').
                        - `output_format`: (object) The output structure the table generated by you can process. For instance, to get a list of users, the structure would be `[{{'name': 'userName', 'age': 'userAge'}}]`.
                    - While data is loading, display a prominent loading indicator within the table structure.
                
                ### Example Request Body for Data Loading:
                {{
                    "request": "load data",
                    "source": "users_database",
                    "format": "JSON",
                    "output_format": [
                        {{
                            "name": "userName1",
                            "age": "userAge1"
                        }},
                        {{
                            "name": "userName2",
                            "age": "userAge2"
                        }},
                    ]
                }}
            
{STYLING_INSTRUCTIONS_SECTION}
        """
        ),
        after_model_callback=clear_technical_response,
        output_key="tabular_data_visualization_agent_output"
    )


def _create_chart_data_visualization_agent():
    return Agent(
        name="chart_data_visualization_agent",
        model=MODEL_FULL,
        generate_content_config=GenerateContentConfig(
            temperature=STRICT_AGENT_TEMPERATURE,
        ),
        description=(
            "Agent to generate an HTML chart with data."
        ),
        instruction=(
            f"""
            You are a specialized agent designed to generate visually nice charts.

            ## Output Format:
                - Your output MUST be raw HTML, directly renderable by a web browser.
                - DO NOT include any conversational text, explanations, or extraneous characters outside the HTML structure.
                - If no chart generation is requested, return the literal string `NO_CONTENT`.
            
            ## Chart Generation Rules:
                ### Data Loading:
                    - Data MUST be loaded asynchronously via a `POST` request to the `/api` endpoint. 
                    - Generate a <script> tag which uses XHR to load the data.
                    - Make sure this script will call the server right after this component is done rendering.
                    - Never add an ADD button to the component. 
                    - Add a reload button. If clicked, the same server call will be executed loading the data again.
                    - The `POST` request body MUST be a JSON object specifying:
                        - `request`: "load data",
                        - `source`: (string) The origin or identifier of the data.
                        - `format`: (string) The desired data format (e.g., 'JSON', 'CSV').
                        - `output_format`: (object) The output structure the chart generated by you can process. For instance, to get a list of users, the structure would be `[{{'name': 'userName', 'age': 'userAge'}}]`.
                    - While data is loading, display a prominent loading indicator within the chart structure.
                    - Once the data is loaded, show the chart visualizing the date returned from the server. 
            
                ### Example Request Body for Data Loading:
                {{
                    "request": "load data",
                    "source": "users_database",
                    "format": "JSON",
                    "output_format": [
                        {{
                            "name": "userName1",
                            "age": "userAge1"
                        }},
                        {{
                            "name": "userName2",
                            "age": "userAge2"
                        }},
                    ]
                }}
            
{STYLING_INSTRUCTIONS_SECTION}
        """
        ),
        after_model_callback=clear_technical_response,
        output_key="chart_data_visualization_agent_output"
    )


def _create_add_data_to_table_agent():
    return Agent(
        name="add_data_agent",
        model=MODEL_FULL,
        generate_content_config=GenerateContentConfig(
            temperature=STRICT_AGENT_TEMPERATURE,
        ),
        planner=BuiltInPlanner(
            thinking_config=ThinkingConfig(
                include_thoughts=False,
                thinking_budget=0
            )
        ),
        description=(
            "Agent to generate an HTML form to add new data."
        ),
        instruction=(
            """
                You are an agent which generates an html form to add a match to the list.
                
                If there is no request to generate an add new match component or form, return NO_CONTENT.
                
                If there is a request to generate an add new match component or form, follow the instructions below.
                # Basic Behavior
                    - Do not generate the <html> <body> etc. Only generate a <div>, since this output will be embedded into a different component.
                    - Make sure this <div> can be embedded into other <div>s in the page.
                    - Inside of the <div> generate a <form> which contains data the user can fill.  
    
                # The content and behavior of the form
                    - the content of the form is:
                        - the league as a listbox containing Brno and Hradec.
                        - Name of player 1
                        - Score of player 1
                        - Name of player 2
                        - Score of player 2  
                        - one buttons: save 
                    - give the save button an id with a prefix save_button and a random suffix to make it unique. For example: save_button_123
                    - add a javascript event listener to listen on click event of this save button. For example: document.getElementById("save_button_123").addEventListener("click", function() {});
                    - in the listener, call the /api endpoint with a body described in the "The body of the POST request". Use XHR to call the /api.
                    - while the server call is ongoing, display a prominent loading indicator in the form. Hide the loading indicator once the server call returns.
                    - once the server call returns, hide the loading indicator. Do not do any other action afterwards.
                
                # The body of the POST request
                    - The body will always begin with the text describing what the content of the request will be. For example: create a new match. 
                    - After this, a json will continue with the data. The json will encode all the data from the dialog form.
            """
        ),
        after_model_callback=clear_technical_response,
        output_key="add_data_agent_output"
    )


def _create_component_page_merger_agent():
    return Agent(
        name="component_page_merger_agent",
        model=MODEL_FULL,
        generate_content_config=GenerateContentConfig(
            temperature=STRICT_AGENT_TEMPERATURE,
        ),
        description=(
            "Agent to generate the component html."
        ),
        instruction=(
            f"""
            You are an agent which generates an HTML div with content.
            
            ## Follow the following rules:
                - Your output will be directly interpreted by a browser so dont include any explanation or any additional text around the HTML content.
                - Do add additional content based on the user prompt.
                - If the input contains a request to generate tabular data, add the {{tabular_data_visualization_agent_output}} to your output.
                - If the input contains a request to generate a chart, add the {{chart_data_visualization_agent_output}} to your output.
                - If the input contains a request to add a new match component or form, add the {{add_data_agent_output}} to your output.         
                - If the request did not contain any of the two above requests, ignore the output from the previous agents and generate your output directly.
                - Never add the string "NO_CONTENT" directly to the output
            
{STYLING_INSTRUCTIONS_SECTION}
        """
        ),
        after_model_callback=clear_technical_response,
    )


def _create_component_parallel_sub_agents():
    return ParallelAgent(
        name="component_parallel_sub_agents",
        sub_agents=[
            _create_tabular_data_visualization_agent(),
            _create_chart_data_visualization_agent(),
            _create_add_data_to_table_agent(),
        ],
        description="Gets the user input and calls all sub agents in parallel to generate their portion of the output."
    )

def _create_component_page_agent():
    return SequentialAgent(
        name="component_page_agent",
        sub_agents=[
            _create_component_parallel_sub_agents(),
            _create_component_page_merger_agent()
        ],
        description="Coordinates parallel research and synthesizes the results."
    )


def _create_data_saver_agent():
    return Agent(
        name="data_saver_agent",
        model=NOT_THINKING_MODEL,
        generate_content_config=GenerateContentConfig(
            temperature=STRICT_AGENT_TEMPERATURE,
        ),
        description=(
            "An agent which can store data to the server."
        ),
        instruction=(
            """
            You are an agent storing data to server.
            For storing data, you have to call one of the following tools: [add_match].
            The input provided to you will be a prefix like "create a new match" and a json encoded string. Always convert the json encoded string to the input parameters of the tool you will be using.
            Your output will be a json containing a status and an optional message. The status will either be "success" or "error".
            Example input:
            - create a new match: {
                    "id": "match_id3",
                    "player1": "Pecene",
                    "player1_score": "10",
                    "player2": "Kure",
                    "player2_score": "4",
                }
            Expected output:
            - {"status": "success"}
            - {"status": "error", "message": "the provided parameters can not be translated to the tool add_match I need to be calling"}
            
            
            If you wont know how to convert the input json into parameters of the tool, return an error describing the issue.
            If the tool will end with an error, return an error and pass the message from the tool to your output json.
            The only success case is, if the tool has been successfully called. Never return success without attempting to call a tool.
            """
        ),
        after_model_callback=clear_technical_response,
        tools=[_data_provider_mcp_toolset],
    )


def _create_root_agent(default_session_variables: Optional[dict[str, str]]):
    return Agent(
        name="generic_webpage_root_agent",
        model="gemini-2.0-flash",
        generate_content_config=GenerateContentConfig(
            temperature=STRICT_AGENT_TEMPERATURE,
        ),
        description=(
            "Root agent delegating to appropriate agents."
        ),
        instruction=(
            """
            You are router agent delegating work to different agents. In case the answer is an HTML, do not interpret it further and just return it as-is.
            Always delegate the request to the appropriate agent. For example:
             - if the request asks for a component, delegate to component_page_agent
             - if the request asks for creating, storing or saving data, delegate to data_saver_agent
             - in other cases, delegate to the main_page_agent
            """
        ),
        sub_agents=[
            _create_main_page_agent(default_session_variables),
            _create_component_page_agent(),
            _create_data_loader_agent(),
            _create_data_saver_agent(),
        ],
        before_model_callback=load_from_cache,
    )


def _create_cache_decision_agent():
    return Agent(
        name="cache_decision_agent",
        model=MODEL_LITE,
        generate_content_config=GenerateContentConfig(
            temperature=STRICT_AGENT_TEMPERATURE,
        ),
        description=(
            "Agent deciding, if the result should be stored to cache / loaded from cache or calculated live"
        ),
        instruction=(
            """
            You are an agent determining if a user's request requires live calculation or can be served from cache.
    
            * **LIVE** if the request involves **loading, storing, or editing data**.
            * **CACHE** if the request involves **rendering a page or component**.
            * If the user explicitly states "always calculate" or similar, output **LIVE**.
            * If the user explicitly states "cache" or similar, output **CACHE**.
    
            Return only 'LIVE' or 'CACHE'.
            """
        ),
        output_key="cache_decision_agent_output"
    )

def create_main_agent(default_session_variables: Optional[dict[str, str]] = None):
    return SequentialAgent(
        name="main_agent",
        sub_agents=[
            _create_cache_decision_agent(),
            _create_root_agent(default_session_variables)
        ],
        description="Decides if to return the result from cache or live. Than proceeds to load or calculate the result."
    )
