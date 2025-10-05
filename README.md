# AI Agent with Chrome Extension

A versatile AI assistant that can perform mathematical calculations, create PowerPoint presentations, and send emails through a user-friendly Chrome extension interface.

## ✨ Features

- **Natural Language Processing**: Ask questions in plain English
- **Mathematical Calculations**: Solve complex equations and word problems
- **PowerPoint Integration**: Automatically generate and populate slides with results
- **Email Notifications**: Send results directly to your email
- **Structured Reasoning**: Step-by-step, tagged, and self-checked reasoning with explicit function calls
- **Fallback Handling**: Robust fallback reasoning for error recovery
- **Conversation Memory**: Maintains context and reasoning history for multi-step tasks
- **Clean Interface**: Modern, responsive design with clear query/result separation
- **Real-time Processing**: Get instant responses to your queries

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js (for development)
- Google Chrome browser
- Google Gemini API key

### 1. Server Setup

1. Clone the repository:
   ```bash
   git clone [your-repository-url]
   cd eag-v2-s5
   ```

2. (Recommended) Use [uv](https://github.com/astral-sh/uv) for fast, reproducible Python environments:
   ```bash
   uv venv
   uv pip install -r requirements.txt
   ```

   Or, use venv:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your API key and email settings:
   ```
   GEMINI_API_KEY=your_api_key_here
   GMAIL_ADDRESS=your_gmail_address@gmail.com
   GMAIL_APP_PASSWORD=your_gmail_app_password
   RECIPIENT_EMAIL=recipient@example.com
   ```

4. Start the MCP tool server (in one terminal):
   ```bash
   python mcp-server.py dev
   ```

5. Start the AI agent (in another terminal):
   ```bash
   python ai_agent.py
   ```

   The agent will prompt for your query in the terminal.

### 2. Chrome Extension Setup

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in the top-right corner)
3. Click "Load unpacked" and select the `chrome-extension` directory
4. The AI Agent extension should now appear in your extensions bar

## 💡 Usage

### Basic Usage
1. Click on the AI Agent extension icon in your browser
2. Enter your query in the input field (e.g., "What is 15% of 200?")
3. Click "Ask" or press Enter
4. View the formatted result in the popup

### Advanced Features
- **PowerPoint Integration**: 
  - Ask to "Show [result] in PowerPoint"
  - The agent will create a slide with your query and result

- **Email Results**:
  - Request to "Email me the result"
  - The agent will send the query and result to your configured email

- **Step-by-step Reasoning**:
  - The agent reasons step by step, tags each reasoning type, and performs self-checks for correctness.
  - All function calls are made in strict JSON format for reliability and traceability.

- **Fallback Handling**:
  - If a tool fails or the agent is uncertain, it will call a fallback reasoning tool and log the step.

## 🛠 Development

### Project Structure
- `ai_agent.py`: Core AI agent logic, conversation memory, and tool integration
- `mcp-server.py`: MCP server for tool execution, including fallback reasoning
- `chrome-extension/`: Frontend Chrome extension code
- `requirements.txt` / `pyproject.toml`: Python dependencies and project metadata

### Dependencies
- Backend:
  - mcp
  - python-dotenv
  - google-generativeai
  - Pillow
  - pywinauto
  - pywin32
  - python-pptx
  - typer
  - anyio
  - httpx
  - flask[async]
  - flask-cors
  - pydantic

- Frontend:
  - Vanilla JavaScript
  - Modern CSS with Flexbox

- Tooling:
  - [uv](https://github.com/astral-sh/uv) for fast Python environments
  - [ruff](https://github.com/astral-sh/ruff) for linting (configured in `pyproject.toml`)

## 🐛 Troubleshooting

### Common Issues
1. **Server not starting**:
   - Check if port 5000 is available
   - Verify all dependencies are installed
   - Check the logs in the terminal

2. **Extension not loading**:
   - Ensure Developer mode is enabled in Chrome
   - Check for errors in Chrome's extension console
   - Reload the extension after making changes

3. **API Errors**:
   - Verify your Gemini API key is correctly set in `.env`
   - Check your internet connection
   - Ensure you have sufficient API quota

4. **Email Sending Fails**:
   - Ensure you have set up an App Password for Gmail
   - Double-check your `.env` values

### Viewing Logs
- Server logs are output to the `logs/` directory and the terminal
- Chrome extension logs can be viewed in the browser's developer console

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Gemini for the AI capabilities
- Flask for the lightweight server
- The open-source community for various utilities and libraries
