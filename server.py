import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from ai_agent import main as ai_main

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/api/query', methods=['POST'])
async def handle_query():
    try:
        data = request.get_json()
        query = data.get('query')
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        logger.info(f"Received query: {query}")
        
        # Run the AI agent with the query
        result = await ai_main(query)
        
        # Parse the JSON response from the AI agent
        try:
            if isinstance(result, str):
                import json
                result_data = json.loads(result)
                if 'result' in result_data:
                    # Return the clean result for the Chrome extension
                    return jsonify({
                        'status': 'success',
                        'result': result_data.get('answer', result_data['result']),
                        'query': result_data.get('query', '')
                    })
        except json.JSONDecodeError:
            logger.warning("Failed to parse AI agent response as JSON, falling back to string extraction")
            # Fallback to string extraction if JSON parsing fails
            if 'FINAL_ANSWER:' in result:
                final_answer = result.split('FINAL_ANSWER:')[-1].strip('[] \'"')
                # Clean up any Query/Result prefixes
                if 'Query:' in final_answer:
                    final_answer = final_answer.split('Result:')[-1].strip()
                return jsonify({
                    'status': 'success',
                    'result': final_answer,
                    'query': ''
                })
        
        # If we get here, we couldn't extract a proper result
        return jsonify({
            'status': 'success',
            'result': result if isinstance(result, str) else str(result)
        })
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    # Make sure the server is accessible from other devices on the network
    app.run(host='0.0.0.0', port=5000, debug=True)
