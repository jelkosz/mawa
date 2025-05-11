from google.adk.agents import Agent, ParallelAgent, SequentialAgent
from google.genai.types import GenerateContentConfig

from mawa.callbacks import clean_html_after_model_callback
from mawa.tools import get_users, add_game

# TODOs:
# - create a naming convention for agents generating visual output and technical agents
# - make sure to pass the COMMON_HTML_AGENT_PROMPT everywhere
# - add caching
# - extract GenerateContentConfig
# - add chantting component
# - make the user inputs stored in state
# - add support for reloading dependent components

COMMON_HTML_AGENT_PROMPT = """
    Follow the following rules:
        - your output will be directly interpreted by a browser so dont include any explanation or any additional text around the HTML content.
        - do add additional details like styling and additional contents based on the user prompt.
        - by default, respect the styling of the page this component is embedded in.
        - never add any <script> tags into the component. If you need additional data, always use tools to load them.
"""

main_page_agent = Agent(
    name="main_page_agent",
    model="gemini-2.0-flash",
    generate_content_config=GenerateContentConfig(
        temperature=0,
    ),
    description=(
        "Agent to generate the main html page of the document."
    ),
    instruction=(
        """
            You are an agent which generates a simple HTML page. Always generate a HTML page with head and body.
            Your output will be directly interpreted by a browser so dont include any explanation or any additional text around the HTML content.
            Do add additional details like styling and additional components based on the user prompt.
            
            # The Layout of the Page:
                - the page has a masthead containing a logout button (doing nothing) and a text saying "Dynamic Table Football"
                - main section has as many components as the user asks for. If the user does not specify the main section layout in any way, refer to the "Default Main Section Layout" section.
                - for details on how to generate components, refer to the "Generating Components" section.
                - if the user does specify the layout, interpret it as an attempt to either override or to extend the Default Main Section Layout and incorporate this ask.
            
            # Generating Components
                - for each component, generate a header and a content_part.
                - the ONLY part, which can be modified as per user request is the "body" from the content_part. Nothing else.
                
                # Header
                    - the header is a <div> having only one clickable "Edit" icon in the top right corner, nothing else. If the mouse hovers over it, the mouse pointer will change to a hand icon.
                    - if the edit icon is clicked, an edit component will be opened.
                    - an example of to how react to onclick on the edit button: "onclick="document.getElementById('editDialog_5789').style.display='block';"
                    - on load, the edit dialog is always closed.
                
                # Edit Component
                    - the edit component is a dialog with a text editor, a save button and cancel button. 
                    - generate a unique ID for this dialog to avoid clash with an another instance of it.
                    - the content of the text editor will be the content of the body from the content_part.
                    - when the cancel button is clicked, the dialog is closed and no additional action is performed
                    - when the save button is clicked, then:
                       - the content of the editor will replace the content of the body from the content_part. Always add the string "Use the component_page_agent for generating this content" to the end of the content_part->body.
                       - the script will re-fetch the content if the content_part
                       - the header will be changed to reflect the new content of the body from the content_part
                       - the dialog will be closed
                    - while the component is loading, replace the content of detail-component-id by something which will tell the user the component is being re-loaded. Respect the styling of the overall component.
                    
                # content_part    
                    - the body will be a <div> with an id field and a <script> which will load the content of the div.
                    - And example:
                        <div id="detail-component-id-1">Loading Component...</div>
                        <script>
                           function loadHTMLWithScripts(html, targetId) {
                                const targetElement = document.getElementById(targetId);
                                const parser = new DOMParser();
                                const doc = parser.parseFromString(html, 'text/html');
                                const scripts = Array.from(doc.querySelectorAll('script'));
                                scripts.forEach(script => script.remove());
                                targetElement.innerHTML = doc.body.innerHTML;
                                scripts.forEach(oldScript => {
                                    const newScript = document.createElement('script');
                                    Array.from(oldScript.attributes).forEach(attr => {
                                        newScript.setAttribute(attr.name, attr.value);
                                    });
                                    newScript.textContent = oldScript.textContent;
                                    document.body.appendChild(newScript);
                                });
                            }
                          fetch('/api', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'text/plain'
                                },
                                body: 'Generate me a component telling me a fun fact.'
                            })
                            .then(res => res.text())
                            .then(html => {
                                loadHTMLWithScripts(html, 'detail-component-id-1');
                            });
                        </script>
                    - if the body is not specified, add the following text to it: "Generate a simple div containing Hello from a div text inside."
                            
                # Default Main Section Layout
                    The main section has a single stack of 2 components
                        - the first component has a body: "Generate me a component with a table of all users from the brno league and their scores. To the bottom left corner of this component, add an add button."
                        - the second component has a body: "Generate me a component with a fun fact about cats."
        """
    ),
    after_model_callback=clean_html_after_model_callback,
)

tabular_data_visualization_agent = Agent(
    name="tabular_data_visualization_agent",
    model="gemini-2.5-flash-preview-04-17",
    generate_content_config=GenerateContentConfig(
        temperature=0,
    ),
    description=(
        "Agent to generate an HTML table with data."
    ),
    instruction=(
        f"""
            You are an agent which generates an HTML table with content loaded using tools. The list of tools available to you are [get_users].
            If there is no request to generate a table, return NO_TABULAR_DATA.
            {COMMON_HTML_AGENT_PROMPT}
                - always use the a tool to load data. Use this data directly in your output, never try to generate anything which will be calling an API endpoint to load them.
                - if the tool returns an error, inform the user politely.
                - if the information you need is not available using any tools, inform the user politely that the information is not available.
        """
    ),
    after_model_callback=clean_html_after_model_callback,
    tools=[get_users],
    output_key="tabular_data_visualization_agent_output"
)

add_data_agent = Agent(
    name="add_data_agent",
    model="gemini-2.5-flash-preview-04-17",
    generate_content_config=GenerateContentConfig(
        temperature=0,
    ),
    description=(
        "Agent to generate an HTML form to add new data."
    ),
    instruction=(
        """
            You are an agent which generates an "add" button and an HTML form in a dialog opened by the add button. 
            
            If there is no request to generate an add button, return NO_ADD_BUTTON.
            
            If there is a request to generate an add button, follow the instructions below.
            # Basic Behavior
                - Create a dialog and generate it a unique id. For example addDialog_156.
                - The dialog is not visible on load.
                - Create an "add" button which listens to the onclick event. Once the button is clicked, change the display of the dialog to be visible. For example "onclick="document.getElementById('addDialog_156').style.display='block';" 

            # The content and behavior of the dialog content 
                - the content of the dialog is:
                    - a form with two fields: the score as an int and the league as a listbox containing Brno and Hradec.
                    - two buttons: save and cancel.
                - if the cancel is clicked, close the dialog.
                - give the save button an id with a prefix save_button and a random suffix to make it unique. For example: save_button_123
                - add a javascript event listener to listen on click event of this save button. For example: document.getElementById("save_button_123").addEventListener("click", function() {});
                - in the listener, call the /api endpoint with a body described in the "The body of the POST request". Use XHR to call the /api.
            
            # The body of the POST request
                - The body will always begin with the text describing what the content of the request will be. For example: create a new game. 
                - After this, a json will continue with the data. The json will encode all the data from the dialog form.
        """
    ),
    after_model_callback=clean_html_after_model_callback,
    output_key="add_data_agent_output"
)

component_page_merger_agent = Agent(
    name="component_page_merger_agent",
    model="gemini-2.5-flash-preview-04-17",
    generate_content_config=GenerateContentConfig(
        temperature=0,
    ),
    description=(
        "Agent to generate the component html."
    ),
    instruction=(
        """
            You are an agent which generates an HTML div with content.
            
            Follow the following rules:
                - your output will be directly interpreted by a browser so dont include any explanation or any additional text around the HTML content.
                - do add additional details like styling and additional contents based on the user prompt.
                - by default, respect the styling of the page this component is embedded in.
                - never add any <script> tags into the component. If you need additional data, always use tools to load them.
                - If the input contains a request to generate tabular data, add the {tabular_data_visualization_agent_output} to your output.
                - If the input contains a request to generate an add button, add the {add_data_agent_output} to your output.                 
                - If the request did not contain any of the two above requests, ignore the output from the previous agents and generate your output directly.
        """
    ),
    after_model_callback=clean_html_after_model_callback,
)

component_parallel_sub_agents = ParallelAgent(
    name="component_parallel_sub_agents",
    sub_agents=[
        tabular_data_visualization_agent,
        add_data_agent
    ],
    description="Gets the user input and calls all sub agents in parallel to generate their portion of the output."
)

component_page_agent = SequentialAgent(
    name="component_page_agent",
    sub_agents=[component_parallel_sub_agents, component_page_merger_agent],
    description="Coordinates parallel research and synthesizes the results."
)

# todo add clear callback
data_saver_agent = Agent(
    name="data_saver_agent",
    model="gemini-2.5-flash-preview-04-17",
    generate_content_config=GenerateContentConfig(
        temperature=0,
    ),
    description=(
        "An agent which can store data to the server."
    ),
    instruction=(
        """
        You are an agent storing data to server.
        For storing data, you have to call one of the following tools: [add_game].
        The input provided to you will be a prefix like "create a new game" and a json encoded string. Always convert the json encoded strong to the input parameters of the tool you will be using.
        Your output will be a json containing a status and an optional message. The status will either be "success" or "error".
        Example input:
        - create a new game: {"score":2,"league":"Brno"}
        Examples output:
        - {"status": "success", "message": "data saved successfully"}
        - {"status": "error", "message": "the provided parameters can not be translated to the tool add_game I need to be calling"}
        
        
        If you wont know how to convert the input json into parameters of the tool, return an error describing the issue.
        If the tool will end with an error, return an error and pass the message from the tool to your output json.
        The only success case is, if the tool has been successfully called. Never return success without attempting to call a tool.
        """
    ),
    tools=[add_game],
)

root_agent = Agent(
    name="generic_webpage_root_agent",
    model="gemini-2.0-flash-lite",
    generate_content_config=GenerateContentConfig(
        temperature=0,
    ),
    description=(
        "Root agent delegating to appropriate agents."
    ),
    instruction=(
        """
        You are router agent delegating work to different agents. In case the answer is an HTML, do not interpret it further and just return it as-is.
        Always delegate the request to the appropriate agent. For example:
         - if the request asks for a component, delegate to component_page_agent
         - if the request asks for a generic/main etc or does not specify further, delegate to the main_page_agent
         - if the request asks for creating, storing or saving data, delegate to data_saver_agent
        """
    ),
    sub_agents=[
        main_page_agent,
        component_page_agent,
        data_saver_agent,
    ],
)
