from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import json
import re
import requests
import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
OLLAMA_BASE_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
PORT = int(os.getenv('PORT', 5000))
DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'deepseek-coder:6.7b')

# Track Ollama availability
OLLAMA_AVAILABLE = False
LAST_OLLAMA_CHECK = 0

def check_ollama_availability():
    """Check if Ollama is available and update global status"""
    global OLLAMA_AVAILABLE, LAST_OLLAMA_CHECK
    
    # Cache check for 30 seconds
    if time.time() - LAST_OLLAMA_CHECK < 30:
        return OLLAMA_AVAILABLE
    
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        OLLAMA_AVAILABLE = response.status_code == 200
    except:
        OLLAMA_AVAILABLE = False
    
    LAST_OLLAMA_CHECK = time.time()
    return OLLAMA_AVAILABLE

def format_prompt_for_array_comments(code, language="swift"):
    """Enhanced prompt for better comment correction"""
    prompt = f"""You are a code formatting assistant. Add or fix sequential comments in this {language} array.

CRITICAL REQUIREMENTS:
1. Add /* number */ comments before EVERY array element
2. Number sequentially from 1 to the total number of elements
3. If comments already exist but numbering is wrong, RENUMBER them correctly
4. If elements are missing comments, ADD them
5. Maintain the original code structure, indentation, and formatting exactly
6. Preserve all original strings and content unchanged
7. Output ONLY the corrected code, no explanations

EXAMPLES:

Input (no comments):
private let text = [
    "First line",
    "Second line", 
    "Third line"
]

Output:
private let text = [
    /* 1 */ "First line",
    /* 2 */ "Second line",
    /* 3 */ "Third line"
]

Input (mixed/wrong comments):
private let text = [
    /* 1 */ "First line",
    "Second line",
    /* 5 */ "Third line",
    /* 4 */ "Fourth line"
]

Output:
private let text = [
    /* 1 */ "First line",
    /* 2 */ "Second line",
    /* 3 */ "Third line",
    /* 4 */ "Fourth line"
]

Input (multiple on one line):
let arr = ["a", "b", "c"]

Output:
let arr = [
    /* 1 */ "a",
    /* 2 */ "b", 
    /* 3 */ "c"
]

Now process this code:
{code}

Corrected code:"""
    return prompt

def call_ollama_http(model_name, prompt):
    """Call Ollama using HTTP API with better error handling"""
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "top_k": 40
                }
            },
            timeout=45  # Increased timeout for larger arrays
        )
        
        if response.status_code == 200:
            return response.json().get("response", "").strip()
        else:
            return f"Error: HTTP {response.status_code} - {response.text}"
            
    except requests.exceptions.Timeout:
        return "Error: Request timeout - Ollama took too long to respond"
    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to Ollama - make sure it's running"
    except Exception as e:
        return f"Error: {str(e)}"

def call_ollama_cli(model_name, prompt):
    """Call Ollama using CLI with better error handling"""
    try:
        result = subprocess.run(
            ['ollama', 'run', model_name],
            input=prompt,
            text=True,
            capture_output=True,
            timeout=45
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            error_msg = result.stderr.strip()
            if "file does not exist" in error_msg:
                return f"Error: Model '{model_name}' not found. Available models: {get_available_models_cli()}"
            return f"Error: {error_msg}"
            
    except subprocess.TimeoutExpired:
        return "Error: Request timeout - Ollama took too long to respond"
    except FileNotFoundError:
        return "Error: Ollama not installed or not in PATH"
    except Exception as e:
        return f"Error: {str(e)}"

def get_available_models_cli():
    """Get available models via CLI fallback"""
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]
            models = [line.split()[0] for line in lines if line.strip()]
            return models
    except:
        pass
    return []

def call_ollama_smart(model_name, prompt):
    """
    Smart Ollama caller that tries HTTP first, then CLI fallback
    """
    # Try HTTP first if available
    if check_ollama_availability():
        result = call_ollama_http(model_name, prompt)
        if not result.startswith("Error:"):
            return result
        # If HTTP fails, try CLI
        return call_ollama_cli(model_name, prompt)
    else:
        # Ollama not available via HTTP, try CLI
        return call_ollama_cli(model_name, prompt)

def clean_model_output(output, original_code):
    """Enhanced cleaning with better array detection"""
    if output.startswith("Error:"):
        return output
    
    # Remove markdown code blocks
    cleaned = re.sub(r'```[\w]*\n?', '', output)
    cleaned = re.sub(r'\n?```', '', cleaned)
    cleaned = cleaned.strip()
    
    # Remove any introductory text before the code
    lines = cleaned.split('\n')
    
    # Find the start of the array (looking for lines with [ or the first comment)
    start_index = 0
    for i, line in enumerate(lines):
        if '[' in line or '/*' in line:
            start_index = i
            break
    
    # Find the end of the array
    end_index = len(lines)
    for i, line in enumerate(lines[start_index:], start_index):
        if ']' in line and not line.strip().startswith('//'):
            end_index = i + 1
            break
    
    code_lines = lines[start_index:end_index]
    
    if code_lines:
        result = '\n'.join(code_lines).strip()
        # Ensure we have the complete array structure
        if '[' in result and ']' in result:
            return result
    
    # Fallback: return the original cleaned output
    return cleaned

def count_array_elements(code):
    """Count elements and validate sequential numbering"""
    if code.startswith("Error:"):
        return 0
    
    # Find all comment numbers
    matches = re.findall(r'\/\*\s*(\d+)\s*\*\/', code)
    numbers = [int(match) for match in matches]
    
    if not numbers:
        return 0
    
    # Check if numbering is sequential from 1
    expected = list(range(1, len(numbers) + 1))
    if numbers != expected:
        return f"{len(numbers)} (non-sequential: {numbers})"
    
    return len(numbers)

def validate_corrected_code(original, corrected):
    """Basic validation that the corrected code is reasonable"""
    if corrected.startswith("Error:"):
        return corrected
    
    # Check if we have roughly the same number of lines
    orig_lines = len(original.split('\n'))
    corr_lines = len(corrected.split('\n'))
    
    # Allow for some variation due to added comments
    if corr_lines < orig_lines * 0.5:
        return "Error: Corrected code seems incomplete"
    
    return corrected

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    ollama_status = "connected" if check_ollama_availability() else "disconnected"
    
    return jsonify({
        "status": "healthy",
        "message": "Coding server is running",
        "ollama": ollama_status,
        "timestamp": datetime.now().isoformat(),
        "default_model": DEFAULT_MODEL
    })

# List available models
@app.route('/api/models', methods=['GET'])
def list_models():
    try:
        if check_ollama_availability():
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
            models_data = response.json()
            models = [model["name"] for model in models_data.get("models", [])]
        else:
            # Fallback to CLI
            models = get_available_models_cli()
        
        return jsonify({
            "available_models": models,
            "method": "http" if check_ollama_availability() else "cli"
        })

    except Exception as e:
        return jsonify({"error": f"Failed to get models: {str(e)}"}), 500

# Enhanced fix array comments endpoint
@app.route('/api/fix-array-comments', methods=['POST'])
def fix_array_comments():
    """Add or fix sequential comments in arrays with smart Ollama calling"""
    try:
        data = request.get_json()

        if not data or 'code' not in data:
            return jsonify({"error": "No code provided"}), 400

        code = data['code'].strip()
        language = data.get('language', 'swift')
        model = data.get('model', DEFAULT_MODEL)
        
        if not code:
            return jsonify({"error": "Empty code provided"}), 400

        prompt = format_prompt_for_array_comments(code, language)
        
        # Use smart caller (HTTP first, CLI fallback)
        result = call_ollama_smart(model, prompt)
        
        # Check if result is an error
        if result.startswith("Error:"):
            return jsonify({"error": result}), 500

        cleaned_output = clean_model_output(result, code)
        validated_output = validate_corrected_code(code, cleaned_output)
        
        if validated_output.startswith("Error:"):
            return jsonify({"error": validated_output}), 500
            
        elements_count = count_array_elements(cleaned_output)

        return jsonify({
            "original_code": code,
            "corrected_code": cleaned_output,
            "model_used": model,
            "language": language,
            "elements_count": elements_count,
            "success": True
        })

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# Keep your existing OpenAI-compatible endpoints (they're fine)
@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """OpenAI-compatible endpoint for VS Code Continue extension"""
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        model = data.get('model', DEFAULT_MODEL)
        temperature = data.get('temperature', 0.1)

        if not messages:
            return jsonify({
                "error": {
                    "message": "Messages array is required",
                    "type": "invalid_request_error"
                }
            }), 400

        # Convert messages to prompt
        prompt = ""
        for message in messages:
            role = message.get('role', '')
            content = message.get('content', '')

            if role == 'system':
                prompt += f"System: {content}\n\n"
            elif role == 'user':
                prompt += f"User: {content}\n\n"
            elif role == 'assistant':
                prompt += f"Assistant: {content}\n\n"
            else:
                prompt += f"{content}\n\n"

        prompt += "Assistant:"

        # Use smart caller
        response_text = call_ollama_smart(model, prompt)
        
        if response_text.startswith("Error:"):
            return jsonify({
                "error": {
                    "message": response_text,
                    "type": "internal_server_error"
                }
            }), 500

        # Convert to OpenAI format
        openai_response = {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(prompt.split()) + len(response_text.split())
            }
        }

        return jsonify(openai_response)

    except Exception as e:
        return jsonify({
            "error": {
                "message": str(e),
                "type": "internal_server_error"
            }
        }), 500

@app.route('/v1/models', methods=['GET'])
def list_models_openai():
    """OpenAI-compatible models endpoint"""
    try:
        models = []
        if check_ollama_availability():
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
            models_data = response.json()
            models = [model["name"] for model in models_data.get("models", [])]
        else:
            models = get_available_models_cli()
        
        models_list = [{
            "id": model_name,
            "object": "model",
            "created": int(time.time()),
            "owned_by": "ollama"
        } for model_name in models]

        return jsonify({
            "object": "list",
            "data": models_list
        })

    except Exception as e:
        return jsonify({
            "error": {
                "message": f"Failed to get models: {str(e)}",
                "type": "internal_server_error"
            }
        }), 500

if __name__ == '__main__':
    print(f"🚀 Starting Enhanced Python coding server on port {PORT}")
    print(f"📍 Default model: {DEFAULT_MODEL}")
    print(f"📍 Health check: http://localhost:{PORT}/health")
    print(f"📍 Fix array comments: http://localhost:{PORT}/api/fix-array-comments")
    print(f"📍 OpenAI API: http://localhost:{PORT}/v1/chat/completions")
    
    # Initial Ollama check
    if check_ollama_availability():
        print("✅ Ollama is available")
    else:
        print("⚠️  Ollama is not available - will use CLI fallback")
    
    app.run(host='0.0.0.0', port=PORT, debug=True)