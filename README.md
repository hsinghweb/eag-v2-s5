# AI Agent with Chrome Extension

A versatile AI assistant that can perform mathematical calculations, create PowerPoint presentations, and send emails through a user-friendly Chrome extension interface.

## ✨ Features

- **Natural Language Processing**: Ask questions in plain English
- **Mathematical Calculations**: Solve complex equations and word problems
- **PowerPoint Integration**: Automatically generate and populate slides with results
- **Email Notifications**: Send results directly to your email
- **Clean Interface**: Modern, responsive design with clear query/result separation
- **Real-time Processing**: Get instant responses to your queries

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js (for development)
- Google Chrome browser
- Google Gemini API key

### 1. Server Setup

1. Clone the repository:
   ```bash
   git clone [your-repository-url]
   cd eag-v2-s4
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

5. Start the server:
   ```bash
   python server.py
   ```
   The server will start on `http://localhost:5000`

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

## 🛠 Development

### Project Structure
- `ai_agent.py`: Core AI agent logic and tool integration
- `server.py`: Flask server for handling requests
- `mcp-server.py`: MCP server for tool execution
- `chrome-extension/`: Frontend Chrome extension code

### Dependencies
- Backend:
  - Flask
  - python-dotenv
  - google-generativeai
  - mcp (custom tool server)

- Frontend:
  - Vanilla JavaScript
  - Modern CSS with Flexbox

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

### Viewing Logs
- Server logs are output to the terminal where `server.py` is running
- Chrome extension logs can be viewed in the browser's developer console

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Gemini for the AI capabilities
- Flask for the lightweight server
- The open-source community for various utilities and libraries
