import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
import google.generativeai as genai
from concurrent.futures import TimeoutError
from functools import partial
import logging
from datetime import datetime
import traceback

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

# Global variables
last_response = None
iteration = 0
iteration_response = []

# System prompt template (to be formatted with tools_description)
SYSTEM_PROMPT_TEMPLATE = """You are a helpful assistant that can perform various tasks including math calculations, PowerPoint operations, and sending emails.

Available tools:
{tools_description}

You must respond with EXACTLY ONE line in one of these formats (no additional text):
1. For function calls:
   FUNCTION_CALL: function_name|param1|param2|...
   
2. For final answers:
   FINAL_ANSWER: [your final answer here]

Important Rules:
1. ONLY perform the exact operations requested by the user.
2. DO NOT perform any PowerPoint operations unless explicitly asked (e.g., 'create a PowerPoint', 'make a presentation', 'show in PPT').
3. For email operations, ONLY use 'send_gmail' when explicitly asked (e.g., 'send email', 'email me', 'mail the result').
4. For math operations, just return the FINAL_ANSWER unless additional operations are explicitly requested.
5. When a function returns multiple values, you need to process all of them.
6. Only give FINAL_ANSWER when you have completed all necessary operations.
7. Do not repeat function calls with the same parameters.

Special Instructions for Email Operations:
- If the user asks to solve a math problem and send the result by email, you must:
  a) First, compute the result using the appropriate math tool(s).
  b) Only after obtaining the result, call 'send_gmail' ONCE with both the original query and the computed result in the email content.
  c) Never call 'send_gmail' before the result is available, and never call it more than once per user request.

PowerPoint Operations (ONLY use when explicitly requested):
- Use 'open_powerpoint' to open PowerPoint with a blank presentation
- Use 'draw_rectangle' to draw a rectangle on the slide (default coordinates: x1=1, y1=1, x2=8, y2=6)
- Use 'add_text_in_powerpoint' to add text to the slide
- Use 'close_powerpoint' when done with PowerPoint operations
- Follow this sequence: open_powerpoint -> draw_rectangle -> add_text_in_powerpoint -> close_powerpoint

Email Operations (ONLY use when explicitly requested):
- Use 'send_gmail' to send an email with the results
- Format: send_gmail|Your message here

Examples:
User: What is 2 + 3?
FINAL_ANSWER: [Query: What is 2 + 3? Result: 5]

User: Add 2 and 3 and show in PowerPoint
FUNCTION_CALL: open_powerpoint|
FUNCTION_CALL: draw_rectangle|1|1|8|6
FUNCTION_CALL: add_text_in_powerpoint|Query: Add 2 and 3 and show in PowerPoint\nResult: 2 + 3 = 5|2|2|24|True
FUNCTION_CALL: close_powerpoint|
FINAL_ANSWER: [Query: Add 2 and 3 and show in PowerPoint. Result: 5. The result has been added to PowerPoint.]

User: Add 2 and 3 and email me the result
FUNCTION_CALL: number_list_to_sum|[2,3]
FUNCTION_CALL: send_gmail|Query: Add 2 and 3 and email me the result\n\nResult: 2 + 3 = 5
FINAL_ANSWER: [Query: Add 2 and 3 and email me the result. Result: 5. The result has been sent via email.]

User: Add 2 and 3
FINAL_ANSWER: [Query: Add 2 and 3. Result: 5]"""

async def generate_with_timeout(model, prompt, timeout=10):
    """Generate content with a timeout"""
    logger.info("Starting LLM generation...")
    try:
        # Convert the synchronous generate_content call to run in a thread
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: model.generate_content(prompt)
            ),
            timeout=timeout
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
    global last_response, iteration, iteration_response
    last_response = None
    iteration = 0
    iteration_response = []
    logger.debug("Reset global state")

async def create_tools_description(tools):
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

async def main(query: str):
    reset_state()  # Reset at the start of main
    logger.info(f"Starting main execution with query: {query}")
    try:
        # Create a single MCP server connection
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
                
                # Get available tools
                logger.info("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                logger.info(f"Successfully retrieved {len(tools)} tools")

                # Create tools description
                tools_description = await create_tools_description(tools)
                
                # Format system prompt with tools description
                system_prompt = SYSTEM_PROMPT_TEMPLATE.format(tools_description=tools_description)
                logger.info("Created system prompt...")
                
                logger.info("Starting iteration loop...")
                
                # Use global iteration variables
                global iteration, last_response
                
                while iteration < MAX_ITERATIONS:
                    logger.info(f"--- Iteration {iteration + 1} ---")
                    if last_response is None:
                        current_query = query
                    else:
                        current_query = query + "\n\n" + " ".join(iteration_response) + " What should I do next?"

                    # Get model's response with timeout
                    logger.info("Preparing to generate LLM response...")
                    prompt = f"{system_prompt}\n\nQuery: {current_query}"
                    try:
                        response_text = await generate_with_timeout(model, prompt)
                        response_text = response_text.strip()
                        logger.info(f"LLM Response: {response_text}")
                        
                        # Find the FUNCTION_CALL line in the response
                        for line in response_text.split('\n'):
                            line = line.strip()
                            if line.startswith("FUNCTION_CALL:"):
                                response_text = line
                                break
                        
                    except Exception as e:
                        logger.error(f"Failed to get LLM response: {e}")
                        break

                    if response_text.startswith("FUNCTION_CALL:"):
                        _, function_info = response_text.split(":", 1)
                        parts = [p.strip() for p in function_info.split("|")]
                        func_name, params = parts[0], parts[1:]
                        
                        logger.debug(f"Raw function info: {function_info}")
                        logger.debug(f"Split parts: {parts}")
                        logger.debug(f"Function name: {func_name}")
                        logger.debug(f"Raw parameters: {params}")
                        
                        try:
                            # Find the matching tool to get its input schema
                            tool = next((t for t in tools if t.name == func_name), None)
                            if not tool:
                                logger.debug(f"Available tools: {[t.name for t in tools]}")
                                raise ValueError(f"Unknown tool: {func_name}")

                            logger.debug(f"Found tool: {tool.name}")
                            logger.debug(f"Tool schema: {tool.inputSchema}")

                            # Prepare arguments according to the tool's input schema
                            arguments = {}
                            schema_properties = tool.inputSchema.get('properties', {})
                            logger.debug(f"Schema properties: {schema_properties}")

                            for param_name, param_info in schema_properties.items():
                                if not params:  # Check if we have enough parameters
                                    raise ValueError(f"Not enough parameters provided for {func_name}")
                                    
                                value = params.pop(0)  # Get and remove the first parameter
                                param_type = param_info.get('type', 'string')
                                
                                logger.debug(f"Converting parameter {param_name} with value {value} to type {param_type}")
                                
                                # Convert the value to the correct type based on the schema
                                if param_type == 'integer':
                                    arguments[param_name] = int(value)
                                elif param_type == 'number':
                                    arguments[param_name] = float(value)
                                elif param_type == 'array':
                                    # Handle array input
                                    if isinstance(value, str):
                                        value = value.strip('[]').split(',')
                                    arguments[param_name] = [int(x.strip()) for x in value]
                                else:
                                    arguments[param_name] = str(value)

                            logger.debug(f"Final arguments: {arguments}")
                            logger.debug(f"Calling tool {func_name}")
                            
                            result = await session.call_tool(func_name, arguments=arguments)
                            logger.debug(f"Raw result: {result}")
                            
                            # Get the full result content
                            if hasattr(result, 'content'):
                                logger.debug("Result has content attribute")
                                # Handle multiple content items
                                if isinstance(result.content, list):
                                    iteration_result = [
                                        item.text if hasattr(item, 'text') else str(item)
                                        for item in result.content
                                    ]
                                else:
                                    iteration_result = str(result.content)
                            else:
                                logger.debug("Result has no content attribute")
                                iteration_result = str(result)
                                
                            logger.debug(f"Final iteration result: {iteration_result}")
                            
                            # Format the response based on result type
                            if isinstance(iteration_result, list):
                                result_str = f"[{', '.join(iteration_result)}]"
                            else:
                                result_str = str(iteration_result)
                            
                            iteration_response.append(
                                f"In the {iteration + 1} iteration you called {func_name} with {arguments} parameters, "
                                f"and the function returned {result_str}."
                            )
                            last_response = iteration_result

                        except Exception as e:
                            logger.error(f"Error details: {str(e)}")
                            logger.error(f"Error type: {type(e)}")
                            logger.error(traceback.format_exc())
                            iteration_response.append(f"Error in iteration {iteration + 1}: {str(e)}")
                            break

                    elif response_text.startswith("FINAL_ANSWER:"):
                        logger.info("=== Agent Execution Complete ===")
                        # Extract just the answer part
                        final_answer = response_text.split(":", 1)[1].strip()
                        logger.info(f"Final answer: {final_answer}")
                        
                        # Clean up the final answer by removing any existing Query/Result prefixes and brackets
                        clean_answer = final_answer.strip('[]')
                        if clean_answer.startswith('Query:'):
                            clean_answer = clean_answer.split('Result:')[-1].strip()
                        
                        # Format the response for the Chrome extension
                        response_data = {
                            'result': clean_answer,  # Just the clean answer for the extension
                            'success': True,
                            'query': query,
                            'answer': clean_answer,
                            'full_response': f"Query: {query}\nResult: {clean_answer}"  # Keep full format for other uses
                        }
                        
                        # Convert to JSON string for the response
                        import json
                        return json.dumps(response_data, indent=2)

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