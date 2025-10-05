import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
import google.generativeai as genai
from concurrent.futures import TimeoutError
import logging
from datetime import datetime
import traceback
import json

# Configure logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"math_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Access your API key and initialize Gemini client correctly
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logger.error("GEMINI_API_KEY not found in .env file")
    raise ValueError("GEMINI_API_KEY not found in .env file")

# Configure the Gemini API
genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-2.5-flash')

# Constants
MAX_ITERATIONS = 5
FUNCTION_CALL_PREFIX = "FUNCTION_CALL:"

# Global variables
last_response = None
iteration = 0
iteration_response = []
conversation_history = []

# System prompt template (to be formatted with tools_description)
SYSTEM_PROMPT_TEMPLATE = """
You are a helpful assistant that can perform various tasks including math calculations, PowerPoint operations, and sending emails.

Available tools:
{tools_description}

You must respond with EXACTLY ONE line in one of these formats (no additional text):

1. For function calls:
   FUNCTION_CALL: {{"name": "<function_name>", "args": <args>, "reasoning_type": "<type>", "step": "<step description>"}}
   - <args> is a JSON array or object matching the tool's schema.
   - <reasoning_type> is one of: "Arithmetic", "Logical", "Entity Lookup", etc.
   - <step> is a short description of what this step is doing.

2. For self-checks:
   SELF_CHECK: Is the result reasonable? -> Yes/No

3. For fallbacks:
   FUNCTION_CALL: {{"name": "fallback_reasoning", "description": "<step description>"}}

4. For final answers:
   FINAL_ANSWER: [your final answer here]

Important Rules:
- Reason step by step.
- Use function calls to split reasoning, calculation, and verification.
- Tag each step with the reasoning type.
- Always do a SELF_CHECK after calculation or verification.
- If a tool fails or you are uncertain, use a fallback_reasoning call.
- Maintain conversation_history and update it each round.
- ONLY perform the exact operations requested by the user.
- Do not repeat function calls with the same parameters.
- Only give FINAL_ANSWER when you have completed all necessary operations.

Examples:
User: What is 2 + 3?
FUNCTION_CALL: {{"name": "number_list_to_sum", "args": [2,3], "reasoning_type": "Arithmetic", "step": "Add 2 and 3"}}
SELF_CHECK: Is the result reasonable? -> Yes
FINAL_ANSWER: [Query: What is 2 + 3? Result: 5]

User: Add 2 and 3 and show in PowerPoint
FUNCTION_CALL: {{"name": "open_powerpoint", "args": [], "reasoning_type": "Entity Lookup", "step": "Open PowerPoint"}}
FUNCTION_CALL: {{"name": "draw_rectangle", "args": [1,1,8,6], "reasoning_type": "Entity Lookup", "step": "Draw rectangle"}}
FUNCTION_CALL: {{"name": "add_text_in_powerpoint", "args": ["Query: Add 2 and 3 and show in PowerPoint\\nResult: 2 + 3 = 5",2,2,24,True], "reasoning_type": "Entity Lookup", "step": "Add text"}}
FUNCTION_CALL: {{"name": "close_powerpoint", "args": [], "reasoning_type": "Entity Lookup", "step": "Close PowerPoint"}}
SELF_CHECK: Is the result reasonable? -> Yes
FINAL_ANSWER: [Query: Add 2 and 3 and show in PowerPoint. Result: 5. The result has been added to PowerPoint.]

User: Add 2 and 3 and email me the result
FUNCTION_CALL: {{"name": "number_list_to_sum", "args": [2,3], "reasoning_type": "Arithmetic", "step": "Add 2 and 3"}}
SELF_CHECK: Is the result reasonable? -> Yes
FUNCTION_CALL: {{"name": "send_gmail", "args": ["Query: Add 2 and 3 and email me the result\\n\\nResult: 2 + 3 = 5"], "reasoning_type": "Entity Lookup", "step": "Send result by email"}}
SELF_CHECK: Is the result reasonable? -> Yes
FINAL_ANSWER: [Query: Add 2 and 3 and email me the result. Result: 5. The result has been sent via email.]

User: Add 2 and 3
FUNCTION_CALL: {{"name": "number_list_to_sum", "args": [2,3], "reasoning_type": "Arithmetic", "step": "Add 2 and 3"}}
SELF_CHECK: Is the result reasonable? -> Yes
FINAL_ANSWER: [Query: Add 2 and 3. Result: 5]
"""

async def generate_with_timeout(model, prompt):
    """Generate content with a timeout"""
    logger.info("Starting LLM generation...")
    try:
        # Convert the synchronous generate_content call to run in a thread
        loop = asyncio.get_event_loop()
        async with asyncio.timeout(10):
            response = await loop.run_in_executor(
                None, 
                lambda: model.generate_content(prompt)
            )
        logger.info("LLM generation completed")
        return response.text
    except TimeoutError:
        logger.error("LLM generation timed out!")
        raise
    except Exception as e:
        logger.error(f"Error in LLM generation: {e}")
        raise

def reset_state():
    """Reset all global variables to their initial state"""
    global last_response, iteration, iteration_response, conversation_history
    last_response = None
    iteration = 0
    iteration_response = []
    conversation_history = []
    logger.debug("Reset global state")

def create_tools_description(tools):
    """Create a formatted description of available tools."""
    logger.info("Creating tools description...")
    logger.debug(f"Number of tools: {len(tools)}")
    
    try:
        tools_description = []
        for i, tool in enumerate(tools):
            try:
                # Get tool properties
                params = tool.inputSchema
                desc = getattr(tool, 'description', 'No description available')
                name = getattr(tool, 'name', f'tool_{i}')
                
                # Format the input schema in a more readable way
                if 'properties' in params:
                    param_details = []
                    for param_name, param_info in params['properties'].items():
                        param_type = param_info.get('type', 'unknown')
                        param_details.append(f"{param_name}: {param_type}")
                    params_str = ', '.join(param_details)
                else:
                    params_str = 'no parameters'

                tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
                tools_description.append(tool_desc)
                logger.debug(f"Added description for tool: {tool_desc}")
            except Exception as e:
                logger.error(f"Error processing tool {i}: {e}")
                tools_description.append(f"{i+1}. Error processing tool")
        
        tools_description = "\n".join(tools_description)
        logger.info("Successfully created tools description")
        return tools_description
    except Exception as e:
        logger.error(f"Error creating tools description: {e}")
        return "Error loading tools"

def find_tool_by_name(tools, func_name):
    """Helper to find a tool by name."""
    return next((t for t in tools if t.name == func_name), None)

def parse_arguments(args, schema_properties):
    """Helper to parse arguments according to schema."""
    arguments = {}
    if isinstance(args, dict):
        return args
    elif isinstance(args, list):
        for (param_name, param_info), value in zip(schema_properties.items(), args):
            param_type = param_info.get('type', 'string')
            if param_type == 'integer':
                arguments[param_name] = int(value)
            elif param_type == 'number':
                arguments[param_name] = float(value)
            elif param_type == 'array':
                arguments[param_name] = value
            else:
                arguments[param_name] = str(value)
        return arguments
    else:
        return args

async def execute_tool(session, tools, call, iteration_response, conversation_history):
    func_name = call.get("name")
    args = call.get("args", [])
    reasoning_type = call.get("reasoning_type", "")
    step_desc = call.get("step", "")
    logger.debug(f"Parsed function call: {call}")

    tool = find_tool_by_name(tools, func_name)
    if not tool:
        logger.debug(f"Available tools: {[t.name for t in tools]}")
        iteration_response.append(f"Unknown tool: {func_name}")
        conversation_history.append({
            "type": "function_call",
            "name": func_name,
            "args": args,
            "reasoning_type": reasoning_type,
            "step": step_desc,
            "result": "Unknown tool"
        })
        return None, iteration_response, conversation_history

    schema_properties = tool.inputSchema.get('properties', {})
    arguments = parse_arguments(args, schema_properties)

    logger.debug(f"Final arguments: {arguments}")
    result = await session.call_tool(func_name, arguments=arguments)
    iteration_result = None
    if hasattr(result, 'content'):
        if isinstance(result.content, list):
            iteration_result = [
                item.text if hasattr(item, 'text') else str(item)
                for item in result.content
            ]
        else:
            iteration_result = str(result.content)
    else:
        iteration_result = str(result)

    result_str = (
        f"[{', '.join(iteration_result)}]" if isinstance(iteration_result, list)
        else str(iteration_result)
    )
    iteration_response.append(
        f"Step: {step_desc} | Reasoning: {reasoning_type} | Called {func_name} with {arguments} -> {result_str}"
    )
    conversation_history.append({
        "type": "function_call",
        "name": func_name,
        "args": arguments,
        "reasoning_type": reasoning_type,
        "step": step_desc,
        "result": result_str
    })
    return iteration_result, iteration_response, conversation_history

def build_prompt(system_prompt, conversation_history, query, last_response, iteration_response):
    if last_response is None:
        current_query = query
    else:
        current_query = query + "\n\n" + " ".join(iteration_response) + " What should I do next?"
    prompt = (
        f"{system_prompt}\n\n"
        f"Conversation history:\n{json.dumps(conversation_history, indent=2)}\n\n"
        f"Query: {current_query}"
    )
    return prompt

def handle_final_answer(first_line, query):
    logger.info("=== Agent Execution Complete ===")
    final_answer = first_line.split(":", 1)[1].strip()
    clean_answer = final_answer.strip('[]')
    if clean_answer.startswith('Query:'):
        clean_answer = clean_answer.split('Result:')[-1].strip()
    response_data = {
        'result': clean_answer,
        'success': True,
        'query': query,
        'answer': clean_answer,
        'full_response': f"Query: {query}\nResult: {clean_answer}"
    }
    return json.dumps(response_data, indent=2)

async def process_llm_response(
    response_text, tools, session, iteration_response, conversation_history, query
):
    global last_response
    first_line = response_text.splitlines()[0].strip()
    if first_line.startswith(FUNCTION_CALL_PREFIX):
        json_str = first_line[len(FUNCTION_CALL_PREFIX):].strip()
        try:
            call = json.loads(json_str)
        except Exception as e:
            logger.error(f"Failed to parse FUNCTION_CALL JSON: {e}")
            iteration_response.append(f"Error parsing FUNCTION_CALL JSON: {str(e)}")
            return None, True  # End iteration
        iteration_result, iteration_response, conversation_history = await execute_tool(
            session, tools, call, iteration_response, conversation_history
        )
        last_response = iteration_result
        return None, False
    elif first_line.startswith("SELF_CHECK:"):
        conversation_history.append({
            "type": "self_check",
            "content": first_line
        })
        iteration_response.append(first_line)
        return None, False
    elif first_line.startswith("FINAL_ANSWER:"):
        return handle_final_answer(first_line, query), True
    elif first_line.startswith(FUNCTION_CALL_PREFIX) and "fallback_reasoning" in first_line:
        conversation_history.append({
            "type": "fallback",
            "content": first_line
        })
        iteration_response.append(first_line)
        iteration_response.append(first_line)
        return None, False
    else:
        logger.warning(f"Unrecognized response: {first_line}")
        iteration_response.append(f"Unrecognized response: {first_line}")
        return None, False

async def main(query: str):
    reset_state()  # Reset at the start of main
    logger.info(f"Starting main execution with query: {query}")
    try:
        logger.info("Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=["mcp-server.py", "dev"]
        )

        async with stdio_client(server_params) as (read, write):
            logger.info("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                logger.info("Session created, initializing...")
                await session.initialize()
                logger.info("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                logger.info(f"Successfully retrieved {len(tools)} tools")
                tools_description = create_tools_description(tools)
                system_prompt = SYSTEM_PROMPT_TEMPLATE.format(tools_description=tools_description)
                logger.info("Created system prompt...")
                logger.info("Starting iteration loop...")
                global iteration, last_response, conversation_history
                while iteration < MAX_ITERATIONS:
                    logger.info(f"--- Iteration {iteration + 1} ---")
                    prompt = build_prompt(system_prompt, conversation_history, query, last_response, iteration_response)
                    try:
                        response_text = await generate_with_timeout(model, prompt)
                        response_text = response_text.strip()
                        logger.info(f"LLM Response: {response_text}")
                        result, should_break = await process_llm_response(
                            response_text, tools, session, iteration_response, conversation_history, query
                        )
                        if result is not None:
                            return result
                        if should_break:
                            break
                    except Exception as e:
                        logger.error(f"Failed to get LLM response: {e}")
                        break
                    iteration += 1
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        logger.error(traceback.format_exc())
    finally:
        reset_state()  # Reset at the end of main

if __name__ == "__main__":
    query = input("Enter your math query: ").strip()
    if not query:
        logger.error("No query provided by user")
        print("Error: Please provide a valid math query")
    else:
        logger.info(f"User provided query: {query}")
        asyncio.run(main(query))
