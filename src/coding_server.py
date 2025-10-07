from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import json
import re
import requests
import os
import time
import logging
from urllib.parse import urlparse

from datetime import datetime
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server_debug.log'),
        logging.StreamHandler()  # Also print to console
    ]
)

from code_processor import format_prompt_for_array_comments, clean_model_output
from ollama_client import call_ollama_smart, check_ollama_availability
from latin_morphology import analyze_latin_word

load_dotenv()
from ollama_client import call_ollama_smart, check_ollama_availability

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
OLLAMA_BASE_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_USERNAME = os.getenv('OLLAMA_USERNAME')
OLLAMA_PASSWORD = os.getenv('OLLAMA_PASSWORD')
PORT = int(os.getenv('PORT', 5000))
DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'deepseek-coder:6.7b')

# Track Ollama availability
OLLAMA_AVAILABLE = False
LAST_OLLAMA_CHECK = 0
IS_REMOTE = False

def is_remote_url(url):
    """Check if the Ollama URL is remote"""
    parsed = urlparse(url)
    local_hosts = ['localhost', '127.0.0.1', '0.0.0.0']
    return parsed.hostname not in local_hosts

def create_ollama_session():
    """Create requests session with authentication if needed"""
    session = requests.Session()
    
    # Add basic auth if credentials provided
    if OLLAMA_USERNAME and OLLAMA_PASSWORD:
        session.auth = (OLLAMA_USERNAME, OLLAMA_PASSWORD)
    
    # Add timeout and retry configuration
    session.timeout = 30
    
    return session

def check_ollama_availability():
    """Check if Ollama is available (local or remote)"""
    global OLLAMA_AVAILABLE, LAST_OLLAMA_CHECK, IS_REMOTE
    
    # Cache check for 30 seconds
    if time.time() - LAST_OLLAMA_CHECK < 30:
        return OLLAMA_AVAILABLE
    
    IS_REMOTE = is_remote_url(OLLAMA_BASE_URL)
    
    try:
        session = create_ollama_session()
        response = session.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        OLLAMA_AVAILABLE = response.status_code == 200
        
        if OLLAMA_AVAILABLE and IS_REMOTE:
            print(f"✅ Connected to remote Ollama server: {OLLAMA_BASE_URL}")
        elif OLLAMA_AVAILABLE:
            print("✅ Connected to local Ollama server")
        else:
            print(f"❌ Ollama server not responding: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        OLLAMA_AVAILABLE = False
        if IS_REMOTE:
            print(f"❌ Cannot connect to remote Ollama server: {OLLAMA_BASE_URL}")
        else:
            print("❌ Cannot connect to local Ollama server - is it running?")
    except requests.exceptions.Timeout:
        OLLAMA_AVAILABLE = False
        print("❌ Ollama server timeout")
    except Exception as e:
        OLLAMA_AVAILABLE = False
        print(f"❌ Error connecting to Ollama: {e}")
    
    LAST_OLLAMA_CHECK = time.time()
    return OLLAMA_AVAILABLE

def call_ollama_http(model_name, prompt):
    """Call Ollama using HTTP API with remote support"""
    try:
        session = create_ollama_session()
        
        response = session.post(
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
            timeout=45
        )
        
        if response.status_code == 200:
            return response.json().get("response", "").strip()
        elif response.status_code == 401:
            return "Error: Authentication failed - check OLLAMA_USERNAME and OLLAMA_PASSWORD"
        elif response.status_code == 404:
            return f"Error: Model '{model_name}' not found on remote server"
        else:
            return f"Error: HTTP {response.status_code} - {response.text}"
            
    except requests.exceptions.Timeout:
        return "Error: Request timeout - remote server took too long to respond"
    except requests.exceptions.ConnectionError:
        return f"Error: Cannot connect to Ollama server at {OLLAMA_BASE_URL}"
    except Exception as e:
        return f"Error: {str(e)}"

def call_ollama_cli(model_name, prompt):
    """Call Ollama using CLI - only for local Ollama"""
    if IS_REMOTE:
        return "Error: CLI mode not available for remote Ollama servers"
    
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
    Smart Ollama caller that handles both local and remote servers
    """
    # For remote servers, only use HTTP
    if IS_REMOTE:
        return call_ollama_http(model_name, prompt)
    
    # For local servers, try HTTP first, then CLI fallback
    if check_ollama_availability():
        result = call_ollama_http(model_name, prompt)
        if not result.startswith("Error:"):
            return result
        # If HTTP fails, try CLI
        return call_ollama_cli(model_name, prompt)
    else:
        # Ollama not available via HTTP, try CLI
        return call_ollama_cli(model_name, prompt)

def count_array_elements(code):
    """Count the number of array elements with comments"""
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
    server_type = "remote" if IS_REMOTE else "local"
    
    return jsonify({
        "status": "healthy",
        "message": "Coding server is running",
        "ollama": {
            "status": ollama_status,
            "type": server_type,
            "url": OLLAMA_BASE_URL,
            "available": OLLAMA_AVAILABLE
        },
        "timestamp": datetime.now().isoformat(),
        "default_model": DEFAULT_MODEL
    })

# List available models
@app.route('/api/models', methods=['GET'])
def list_models():
    try:
        if check_ollama_availability():
            session = create_ollama_session()
            response = session.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
            models_data = response.json()
            models = [model["name"] for model in models_data.get("models", [])]
            method = "http"
        else:
            models = get_available_models_cli() if not IS_REMOTE else []
            method = "cli" if not IS_REMOTE else "none"
        
        return jsonify({
            "available_models": models,
            "method": method,
            "server_type": "remote" if IS_REMOTE else "local"
        })

    except Exception as e:
        return jsonify({"error": f"Failed to get models: {str(e)}"}), 500

# Fix array comments endpoint
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

# Latin word analysis endpoint
@app.route('/api/analyze-latin-word', methods=['POST'])
def analyze_latin_word_endpoint():
    """Analyze Latin word and return structured morphological data"""
    try:
        data = request.get_json()
        word = data.get('word', '')
        
        if not word:
            return jsonify({"error": "No word provided"}), 400
        
        # Analyze the word
        analysis = analyze_latin_word(word)
        
        return jsonify(analysis)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Latin text analysis endpoint
@app.route('/api/analyze-latin-text', methods=['POST'])
def analyze_latin_text_endpoint():
    """Analyze multiple Latin words in a text"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        # Split into words and analyze each
        words = re.findall(r'\b[a-zA-ZāēīōūĀĒĪŌŪ]+\b', text)
        analyses = []
        
        for word in words:
            if len(word) > 2:  # Ignore very short words
                analysis = analyze_latin_word(word)
                analyses.append(analysis)
        
        return jsonify({
            "original_text": text,
            "word_count": len(analyses),
            "analyses": analyses
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Latin linguistic analysis endpoint
@app.route('/api/analyze-latin', methods=['POST'])
def analyze_latin():
    """Analyze Latin/Greek words for form, lemma, and translation using Ollama"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        language = data.get('language', 'latin')
        model = data.get('model', 'mistral:7b')

        if not text:
            return jsonify({"error": "No text provided"}), 400

        prompt = f"""Analyze this {language} text linguistically: "{text}"

For each word, provide:
1. Dictionary form (lemma)
2. Grammatical form (case, number, gender, tense, mood, etc.)
3. English translation
4. Brief grammatical explanation

Format as a structured analysis.

Text: "{text}"
Analysis:"""

        result = call_ollama_smart(model, prompt)
        
        if result.startswith("Error:"):
            return jsonify({"error": result}), 500

        return jsonify({
            "original_text": text,
            "language": language,
            "analysis": result,
            "model_used": model
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Classical language translation endpoint
@app.route('/api/translate-classical', methods=['POST'])
def translate_classical():
    """Translate Latin/Greek with grammatical analysis"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        source_lang = data.get('source_language', 'latin')
        target_lang = data.get('target_language', 'english')
        model = data.get('model', 'mixtral:8x7b')

        if not text:
            return jsonify({"error": "No text provided"}), 400

        prompt = f"""Translate this {source_lang} text to {target_lang} and provide grammatical analysis:

Text: "{text}"

Provide:
1. Literal translation
2. Fluent translation  
3. Word-by-word analysis (lemma, form, grammar)
4. Overall grammatical structure

Translation and Analysis:"""

        result = call_ollama_smart(model, prompt)
        
        if result.startswith("Error:"):
            return jsonify({"error": result}), 500

        return jsonify({
            "original_text": text,
            "source_language": source_lang,
            "target_language": target_lang,
            "translation": result,
            "model_used": model
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# OpenAI-compatible endpoint for Continue extension
@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """OpenAI-compatible endpoint for VS Code Continue extension"""
    print("\n" + "🎯" * 50)
    print("📨 REQUEST RECEIVED at /v1/chat/completions")
    print("🎯" * 50)
    
    import sys
    sys.stdout.flush()
    
    try:
        # Log basic info
        print(f"📧 Method: {request.method}")
        print(f"🌐 Content-Type: {request.headers.get('Content-Type')}")
        print(f"🌐 User-Agent: {request.headers.get('User-Agent')}")
        
        # Get raw data first
        raw_data = request.get_data(as_text=True)
        print(f"📦 Raw data received: {len(raw_data)} characters")
        
        # Try to parse JSON
        if raw_data:
            print(f"📦 First 200 chars: {raw_data[:200]}")
            
            data = json.loads(raw_data)
            print(f"📋 JSON parsed successfully")
            
            # Log messages
            if 'messages' in data:
                print(f"💬 Found {len(data['messages'])} messages:")
                for i, msg in enumerate(data['messages']):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')[:100]  # First 100 chars
                    print(f"   {i}. {role}: {content}")
        
        sys.stdout.flush()
        
    except Exception as e:
        print(f"❌ Error in logging: {str(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        sys.stdout.flush()
    
    # Now continue with your existing function logic
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        model = data.get('model', DEFAULT_MODEL)
        temperature = data.get('temperature', 0.1)
        stream = data.get('stream', False)
        
        logging.info(f"🌊 Stream requested: {stream}")
        print(f"🌊 Stream requested: {stream}")

        if not messages:
            return jsonify({
                "error": {
                    "message": "Messages array is required",
                    "type": "invalid_request_error"
                }
            }), 400

        # Extract user message for array detection
        user_message = ""
        for message in messages:
            if message.get('role') == 'user':
                user_message = message.get('content', '')
                break

        logging.info(f"🔍 Processing user message: {user_message[:100]}...")
        print(f"🔍 Processing user message: {user_message[:100]}...")
        
        # Check if this is an array commenting request
        is_array_request = any(keyword in user_message.lower() for keyword in 
                              ['array', 'comment', 'sequential', 'number', 'fix array', 'add comment', '/fix-array-comments'])
        
        if is_array_request:
            logging.info("🎯 USING ARRAY COMMENTING LOGIC")
            print("🎯 USING ARRAY COMMENTING LOGIC")
            
            # Extract code properly - handle Continue's format with file paths
            # Pattern 1: Try to extract full code with variable assignment
            # Matches: private let text = [...] or let text = [...] or var x = [...]
            full_code_match = re.search(
                r'((?:private\s+|public\s+|internal\s+)?(?:let|var|const)\s+\w+\s*=\s*\[.*\])',
                user_message,
                re.DOTALL | re.IGNORECASE
            )
            
            if full_code_match:
                code_to_fix = full_code_match.group(1).strip()
                print(f"✅ Extracted full code with variable: {code_to_fix[:80]}...")
            else:
                # Pattern 2: Fall back to just extracting the array
                array_match = re.search(r'(\[.*\])', user_message, re.DOTALL)
                if array_match:
                    code_to_fix = array_match.group(1).strip()
                    print(f"✅ Extracted array only: {code_to_fix[:80]}...")
                else:
                    # Pattern 3: Use the whole message as last resort
                    code_to_fix = user_message
                    print("⚠️ Using whole message as code")
            
            prompt = format_prompt_for_array_comments(code_to_fix, "swift")
        else:
            print("💬 USING REGULAR CHAT LOGIC")
            # Use normal conversation
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

        print(f"📝 Sending prompt to Ollama...")
        response_text = call_ollama_smart(model, prompt)
        
        print(f"📨 Ollama response: {response_text[:200]}...")
        
        if response_text.startswith("Error:"):
            return jsonify({
                "error": {
                    "message": response_text,
                    "type": "internal_server_error"
                }
            }), 500
        
        # Clean the output for array requests
        if is_array_request and 'code_to_fix' in locals():
            print("🧹 Cleaning model output...")
            cleaned = clean_model_output(response_text, code_to_fix)
            
            if not cleaned.startswith("Error:"):
                # Validate the cleaned output
                has_comments = bool(re.search(r'\/\*\s*\d+\s*\*\/', cleaned))
                has_array = '[' in cleaned and ']' in cleaned
                
                if has_comments and has_array:
                    response_text = cleaned
                    # Count comments for logging
                    comment_count = len(re.findall(r'\/\*\s*(\d+)\s*\*\/', cleaned))
                    print(f"✅ Cleaned output validated: {comment_count} comments added")
                    print(f"📄 First 300 chars: {cleaned[:300]}...")
                else:
                    print(f"⚠️ Cleaned output invalid (comments: {has_comments}, array: {has_array})")
                    print(f"📄 Output: {cleaned[:300]}...")
                    # Fall back to original response with a warning message
                    response_text = f"⚠️ Warning: Output validation failed. Raw response:\n\n{cleaned}"
            else:
                print(f"⚠️ Cleaning failed: {cleaned}")

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

        print("✅ Request completed successfully")
        print(f"📤 Sending response to Continue (content length: {len(response_text)} chars)")
        print(f"📤 Response preview: {response_text[:200]}...")
        
        # Handle streaming vs non-streaming response
        if stream:
            logging.info("🌊 Sending STREAMING response")
            print("🌊 Sending STREAMING response")
            def generate():
                response_id = f"chatcmpl-{int(time.time())}"
                
                # Split response into chunks for streaming
                chunks = [response_text[i:i+50] for i in range(0, len(response_text), 50)]
                
                for chunk in chunks:
                    chunk_data = {
                        "id": response_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": chunk},
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                
                # Send final chunk
                final_chunk = {
                    "id": response_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": model,
                    "choices": [{
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }]
                }
                yield f"data: {json.dumps(final_chunk)}\n\n"
                yield "data: [DONE]\n\n"
            
            return app.response_class(generate(), mimetype='text/event-stream')
        else:
            print("📄 Sending NON-STREAMING response")
            return jsonify(openai_response)

    except Exception as e:
        print(f"❌ Error in chat_completions: {str(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": {
                "message": str(e),
                "type": "internal_server_error"
            }
        }), 500

# Models endpoint for OpenAI compatibility
@app.route('/v1/models', methods=['GET'])
def list_models_openai():
    """OpenAI-compatible models endpoint"""
    try:
        models = []
        if check_ollama_availability():
            session = create_ollama_session()
            response = session.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
            models_data = response.json()
            models = [model["name"] for model in models_data.get("models", [])]
        else:
            models = get_available_models_cli() if not IS_REMOTE else []
        
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
    print(f"📍 Ollama server: {OLLAMA_BASE_URL}")
    print(f"📍 Health check: http://localhost:{PORT}/health")
    print(f"📍 Fix array comments: http://localhost:{PORT}/api/fix-array-comments")
    print(f"📍 Latin analysis: http://localhost:{PORT}/api/analyze-latin-word")
    print(f"📍 OpenAI API: http://localhost:{PORT}/v1/chat/completions")
    
    # Initial Ollama check
    if check_ollama_availability():
        if IS_REMOTE:
            print("✅ Connected to REMOTE Ollama server")
        else:
            print("✅ Connected to LOCAL Ollama server")
    else:
        if IS_REMOTE:
            print("❌ Cannot connect to REMOTE Ollama server")
        else:
            print("❌ Cannot connect to LOCAL Ollama server - will use CLI fallback")
    
    app.run(host='0.0.0.0', port=PORT, debug=True)