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

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server_debug.log'),
        logging.StreamHandler()  # Also print to console
    ]
)

from code_processor import format_prompt_for_array_comments, format_prompt_for_remove_all_comments, clean_model_output, clean_removed_comments_output

from ollama_client import (
    call_ollama_smart, 
    check_ollama_availability, 
    create_ollama_session,
    get_available_models,
    get_available_models_cli,
    IS_REMOTE,
    OLLAMA_BASE_URL,
    OLLAMA_AVAILABLE
)
from liturgical_processor import renumber_verses_with_ai
from liturgical_processor import (
    parse_verses_from_array, 
    analyze_verse_structure_with_ai,
    adjust_verses_to_count
)

from latin_morphology import analyze_latin_word
from ollama_client import call_ollama_smart, check_ollama_availability

app = Flask(__name__)
CORS(app)

# Configuration
PORT = int(os.getenv('PORT', 5000))
DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'deepseek-coder:6.7b')
logging.info(f"[STARTUP] DEFAULT_MODEL from env: {DEFAULT_MODEL}")
logging.info(f"[STARTUP] PORT from env: {PORT}")
print(f"Using model: {DEFAULT_MODEL}")
print(f"Server port: {PORT}")

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
    is_available = check_ollama_availability()
    ollama_status = "connected" if is_available else "disconnected"
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

# Remove all comments endpoint
@app.route('/api/remove-all-comments', methods=['POST'])
def remove_all_comments():
    """Remove all comments from code using Ollama"""
    try:
        data = request.get_json()

        if not data or 'code' not in data:
            return jsonify({"error": "No code provided"}), 400

        code = data['code'].strip()
        language = data.get('language', 'swift')
        model = data.get('model', DEFAULT_MODEL)
        
        if not code:
            return jsonify({"error": "Empty code provided"}), 400

        prompt = format_prompt_for_remove_all_comments(code, language)
        
        # Use smart caller (HTTP first, CLI fallback)
        result = call_ollama_smart(model, prompt)
        
        # Check if result is an error
        if result.startswith("Error:"):
            return jsonify({"error": result}), 500

        # Use specialized cleaning for comment removal (ensures all comments are gone)
        cleaned_output = clean_removed_comments_output(result, code)
        validated_output = validate_corrected_code(code, cleaned_output)
        
        if validated_output.startswith("Error:"):
            return jsonify({"error": validated_output}), 500

        return jsonify({
            "original_code": code,
            "cleaned_code": cleaned_output,
            "model_used": model,
            "language": language,
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
    print("\n" + "=" * 50)
    print("[REQUEST] REQUEST RECEIVED at /v1/chat/completions")
    print("=" * 50)
    
    import sys
    sys.stdout.flush()
    
    try:
        # Log basic info
        print(f"[INFO] Method: {request.method}")
        print(f"[INFO] Content-Type: {request.headers.get('Content-Type')}")
        print(f"[INFO] User-Agent: {request.headers.get('User-Agent')}")
        
        # Get raw data first
        raw_data = request.get_data(as_text=True)
        print(f"[DATA] Raw data received: {len(raw_data)} characters")
        
        # Try to parse JSON
        if raw_data:
            print(f"[DATA] First 200 chars: {raw_data[:200]}")
            
            data = json.loads(raw_data)
            print(f"[JSON] JSON parsed successfully")
            
            # Log messages
            if 'messages' in data:
                print(f"[CHAT] Found {len(data['messages'])} messages:")
                for i, msg in enumerate(data['messages']):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')[:100]  # First 100 chars
                    print(f"   {i}. {role}: {content}")
        
        sys.stdout.flush()
        
    except Exception as e:
        print(f"[ERROR] Error in logging: {str(e)}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        sys.stdout.flush()
    
    # Now continue with your existing function logic
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        model = data.get('model', DEFAULT_MODEL)
        temperature = data.get('temperature', 0.1)
        stream = data.get('stream', False)
        
        # NEW: Check for optional 'code' field or 'code_file' for direct code operations
        direct_code = data.get('code', None)
        code_file = data.get('code_file', None)
        
        # If code_file is provided, read from file
        if code_file:
            try:
                import os
                # Support both absolute and relative paths
                if not os.path.isabs(code_file):
                    # Relative to current working directory
                    code_file_path = os.path.join(os.getcwd(), code_file)
                else:
                    code_file_path = code_file
                
                with open(code_file_path, 'r', encoding='utf-8') as f:
                    direct_code = f.read()
                logging.info(f"[CODE_FILE] Loaded code from file: {code_file}")
                logging.info(f"[CODE_FILE] Code preview: {direct_code[:100]}...")
            except FileNotFoundError:
                logging.error(f"[CODE_FILE] File not found: {code_file}")
                return jsonify({
                    "error": {
                        "message": f"Code file not found: {code_file}",
                        "type": "invalid_request_error"
                    }
                }), 400
            except Exception as e:
                logging.error(f"[CODE_FILE] Error reading file: {str(e)}")
                return jsonify({
                    "error": {
                        "message": f"Error reading code file: {str(e)}",
                        "type": "invalid_request_error"
                    }
                }), 400
        elif direct_code:
            logging.info(f"[DIRECT_CODE] Using direct 'code' field: {direct_code[:100]}...")
        
        logging.info(f"[STREAM] Stream requested: {stream}")
        print(f"[STREAM] Stream requested: {stream}")

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

        logging.info(f"[PROCESS] Processing user message: {user_message[:100]}...")
        logging.info(f"[PROCESS] Full user message: {user_message}")
        
        # Check if this is a remove-all-comments request (check this FIRST for priority)
        is_remove_comments_request = any(keyword in user_message.lower() for keyword in 
                                        ['@remove-all-comments', '/remove-all-comments', 
                                         'remove-all-comments', 'remove all comment', 
                                         'delete comment', 'strip comment', 'clean comment'])
        
        logging.info(f"[DETECT] Remove comments request: {is_remove_comments_request}")
        
        # Check if this is a renumber verses request (check SECOND for priority)
        is_renumber_verses_request = False
        if not is_remove_comments_request:
            is_renumber_verses_request = any(keyword in user_message.lower() for keyword in 
                                            ['@renumber-verses', '/renumber-verses',
                                             'renumber-verses', 'renumber verses', 
                                             'renumber verse', 'fix verse numbers', 'fix comment'])
        
        logging.info(f"[DETECT] Renumber verses request: {is_renumber_verses_request}")
        
        # Check if this is an array commenting request (but not if remove comments or renumber already matched)
        is_array_request = False
        if not is_remove_comments_request and not is_renumber_verses_request:
            is_array_request = any(keyword in user_message.lower() for keyword in 
                                  ['@fix-array-comments', '/fix-array-comments',
                                   'fix-array-comments', 'add sequential comment', 
                                   'sequential comment', 'number comment'])
        
        logging.info(f"[DETECT] Array request: {is_array_request}")
        
        if is_remove_comments_request:
            logging.info("[REMOVE_COMMENTS] USING REMOVE COMMENTS LOGIC")
            
            # Use direct code if provided, otherwise extract from message
            if direct_code:
                code_to_fix = direct_code.strip()
                logging.info(f"[REMOVE_COMMENTS] Using direct 'code' field")
            else:
                # Extract code - try to get code block or variable assignment
                code_to_fix = user_message
                
                # Try to extract code from markdown blocks first
                code_block_match = re.search(r'```[\w]*\n(.*?)\n```', user_message, re.DOTALL)
                if code_block_match:
                    code_to_fix = code_block_match.group(1).strip()
                    print(f"[OK] Extracted code from markdown block: {code_to_fix[:80]}...")
                else:
                    # Try to extract variable assignment
                    full_code_match = re.search(
                        r'((?:private\s+|public\s+|internal\s+)?(?:let|var|const)\s+\w+\s*=\s*\[.*?\])',
                        user_message,
                        re.DOTALL | re.IGNORECASE
                    )
                    if full_code_match:
                        code_to_fix = full_code_match.group(1).strip()
                        print(f"[OK] Extracted variable assignment: {code_to_fix[:80]}...")
            
            logging.info(f"[REMOVE_COMMENTS] Code to process: {code_to_fix}")
            
            prompt = format_prompt_for_remove_all_comments(code_to_fix, "swift")
        elif is_renumber_verses_request:
            logging.info("[RENUMBER_VERSES] USING RENUMBER VERSES LOGIC")
            
            # Use direct code if provided, otherwise extract from message
            if direct_code:
                code_to_fix = direct_code.strip()
                logging.info(f"[RENUMBER_VERSES] Using direct 'code' field")
            else:
                # Extract code - try to get code block or variable assignment
                code_to_fix = user_message
                
                # Try to extract code from markdown blocks first
                code_block_match = re.search(r'```[\w]*\n(.*?)\n```', user_message, re.DOTALL)
                if code_block_match:
                    code_to_fix = code_block_match.group(1).strip()
                    logging.info(f"[OK] Extracted code from markdown block: {code_to_fix[:80]}...")
                else:
                    # Try to extract variable assignment
                    full_code_match = re.search(
                        r'((?:private\s+|public\s+|internal\s+)?(?:let|var|const)\s+\w+\s*=\s*\[.*?\])',
                        user_message,
                        re.DOTALL | re.IGNORECASE
                    )
                    if full_code_match:
                        code_to_fix = full_code_match.group(1).strip()
                        logging.info(f"[OK] Extracted variable assignment: {code_to_fix[:80]}...")
            
            logging.info(f"[RENUMBER_VERSES] Code to process: {code_to_fix[:200]}...")
            
            # Call renumber_verses_with_ai directly (it handles its own prompt internally)
            response_text = renumber_verses_with_ai(code_to_fix, model=model)
            
            # Don't send to Ollama again - we already have the response
            # Skip the normal prompt processing
            prompt = None
        elif is_array_request:
            logging.info("[ARRAY] USING ARRAY COMMENTING LOGIC")
            
            # Use direct code if provided, otherwise extract from message
            if direct_code:
                code_to_fix = direct_code.strip()
                logging.info(f"[ARRAY] Using direct 'code' field")
            else:
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
                    logging.info(f"[OK] Extracted full code with variable: {code_to_fix[:80]}...")
                else:
                    # Pattern 2: Fall back to just extracting the array
                    array_match = re.search(r'(\[.*\])', user_message, re.DOTALL)
                    if array_match:
                        code_to_fix = array_match.group(1).strip()
                        print(f"[OK] Extracted array only: {code_to_fix[:80]}...")
                    else:
                        # Pattern 3: Use the whole message as last resort
                        code_to_fix = user_message
                        print("[WARNING] Using whole message as code")
            
            prompt = format_prompt_for_array_comments(code_to_fix, "swift")
        else:
            logging.info("[CHAT] USING REGULAR CHAT LOGIC")
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

        # Only call Ollama if we haven't already processed the request
        if prompt is not None:
            print(f"[SEND] Sending prompt to Ollama...")
            response_text = call_ollama_smart(model, prompt)
            print(f"[RESPONSE] Ollama response: {response_text[:200]}...")
        else:
            print(f"[SKIP] Skipping Ollama call - response already generated")
            print(f"[RESPONSE] Pre-generated response: {response_text[:200]}...")
        
        if response_text.startswith("Error:"):
            return jsonify({
                "error": {
                    "message": response_text,
                    "type": "internal_server_error"
                }
            }), 500
        
        # Clean the output for remove comments requests
        if is_remove_comments_request and 'code_to_fix' in locals():
            print("[CLEAN] Cleaning output (remove comments mode)...")
            logging.info("[CLEAN] Cleaning output (remove comments mode)...")
            
            cleaned = clean_removed_comments_output(response_text, code_to_fix)
            
            if not cleaned.startswith("Error:"):
                # Check if comments were actually removed
                has_block_comments = bool(re.search(r'/\*.*?\*/', cleaned))
                has_line_comments = bool(re.search(r'//.*$', cleaned, re.MULTILINE))
                
                if not has_block_comments and not has_line_comments:
                    response_text = cleaned
                    print(f"[OK] Comments successfully removed")
                    logging.info(f"[OK] Comments successfully removed")
                    print(f"[OUTPUT] First 300 chars: {cleaned[:300]}...")
                    logging.info(f"[OUTPUT] Full cleaned code: {cleaned}")
                else:
                    print(f"[WARNING] Some comments may remain (block: {has_block_comments}, line: {has_line_comments})")
                    logging.warning(f"[WARNING] Some comments may remain (block: {has_block_comments}, line: {has_line_comments})")
                    response_text = cleaned  # Use it anyway
                    print(f"[OUTPUT] Output: {cleaned[:300]}...")
                    logging.info(f"[OUTPUT] Full output: {cleaned}")
            else:
                print(f"[WARNING] Cleaning failed: {cleaned}")
                logging.warning(f"[WARNING] Cleaning failed: {cleaned}")
        
        # Clean the output for array requests
        elif is_array_request and 'code_to_fix' in locals():
            print("[CLEAN] Cleaning model output...")
            cleaned = clean_model_output(response_text, code_to_fix)
            
            if not cleaned.startswith("Error:"):
                # Validate the cleaned output
                has_comments = bool(re.search(r'\/\*\s*\d+\s*\*\/', cleaned))
                has_array = '[' in cleaned and ']' in cleaned
                
                if has_comments and has_array:
                    response_text = cleaned
                    # Count comments for logging
                    comment_count = len(re.findall(r'\/\*\s*(\d+)\s*\*\/', cleaned))
                    print(f"[OK] Cleaned output validated: {comment_count} comments added")
                    print(f"[OUTPUT] First 300 chars: {cleaned[:300]}...")
                else:
                    print(f"[WARNING] Cleaned output invalid (comments: {has_comments}, array: {has_array})")
                    print(f"[OUTPUT] Output: {cleaned[:300]}...")
                    # Fall back to original response with a warning message
                    response_text = f"[WARNING] Warning: Output validation failed. Raw response:\n\n{cleaned}"
            else:
                print(f"[WARNING] Cleaning failed: {cleaned}")

        # Convert to OpenAI format
        prompt_tokens = len(prompt.split()) if prompt else 0
        completion_tokens = len(response_text.split())
        
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
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            }
        }

        print("[OK] Request completed successfully")
        print(f"[SEND] Sending response to Continue (content length: {len(response_text)} chars)")
        print(f"[SEND] Response preview: {response_text[:200]}...")
        
        # Handle streaming vs non-streaming response
        if stream:
            logging.info("[STREAM] Sending STREAMING response")
            print("[STREAM] Sending STREAMING response")
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
            print("[OUTPUT] Sending NON-STREAMING response")
            return jsonify(openai_response)

    except Exception as e:
        print(f"[ERROR] Error in chat_completions: {str(e)}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
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


@app.route('/api/adjust-liturgical-verses', methods=['POST'])
def adjust_liturgical_verses():
    """Adjust psalm verses to target count with liturgical awareness"""
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        target_count = data.get('target_verse_count', 18)
        model = data.get('model', DEFAULT_MODEL)

        if not code:
            return jsonify({"error": "No code provided"}), 400

        # Step 1: Parse verses from array
        verses = parse_verses_from_array(code)
        if not verses:
            return jsonify({"error": "No verses found in array"}), 400

        # Step 2: Analyze current structure
        analysis = analyze_verse_structure_with_ai(verses)
        
        # Step 3: Adjust to target count
        adjustment = adjust_verses_to_count(verses, analysis, target_count)
        
        # Step 4: Generate new array
        new_verses = [v["content"] for v in adjustment["new_verses"]]
        new_array = generate_swift_array(new_verses)

        return jsonify({
            "original_verse_count": len(verses),
            "target_verse_count": target_count,
            "new_verse_count": len(new_verses),
            "original_code": code,
            "adjusted_code": new_array,
            "analysis": analysis,
            "adjustment_explanation": adjustment.get("explanation", ""),
            "success": True
        })

    except Exception as e:
        return jsonify({"error": f"Liturgical processing error: {str(e)}"}), 500

def generate_swift_array(verses):
    """Generate Swift array code from verses"""
    lines = ["private let text = ["]
    
    for i, verse in enumerate(verses):
        # Handle multi-line verses by checking length
        if len(verse) > 80:  # Long verse - split intelligently
            parts = split_long_verse(verse)
            lines.append(f'    /* {i+1} */ "{parts[0]}"')
            for part in parts[1:]:
                lines.append(f'            "{part}"')
        else:
            lines.append(f'    /* {i+1} */ "{verse}"')
    
    lines.append("]")
    return "\n".join(lines)

def split_long_verse(verse, max_length=80):
    """Split long verses at natural break points"""
    words = verse.split()
    parts = []
    current_part = ""
    
    for word in words:
        if len(current_part) + len(word) + 1 > max_length and current_part:
            parts.append(current_part.strip())
            current_part = word
        else:
            current_part += " " + word if current_part else word
    
    if current_part:
        parts.append(current_part.strip())
    
    return parts


@app.route('/api/renumber-verses', methods=['POST'])
def renumber_verses_endpoint():
    """Renumber verse comments sequentially using AI"""
    try:
        data = request.get_json()
        
        # Support both 'code' and 'code_file'
        code = data.get('code', None)
        code_file = data.get('code_file', None)
        
        if code_file:
            # Read code from file
            try:
                import os
                if not os.path.isabs(code_file):
                    code_file_path = os.path.join(os.getcwd(), code_file)
                else:
                    code_file_path = code_file
                
                with open(code_file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                logging.info(f"[RENUMBER_VERSES] Loaded code from file: {code_file}")
            except FileNotFoundError:
                return jsonify({"error": f"Code file not found: {code_file}"}), 400
            except Exception as e:
                return jsonify({"error": f"Error reading code file: {str(e)}"}), 400
        
        if not code:
            return jsonify({"error": "No code provided (use 'code' or 'code_file' parameter)"}), 400

        code = code.strip()
        
        if not code:
            return jsonify({"error": "Empty code provided"}), 400
        
        model = data.get('model', DEFAULT_MODEL) 

        # Call the renumber function from liturgical_processor
        result = renumber_verses_with_ai(code, model=model)
        
        if result.startswith("Error:"):
            return jsonify({"error": result}), 500

        return jsonify({
            "original_code": code,
            "renumbered_code": result,
            "success": True
        })

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    print(f"[START] Starting Enhanced Python coding server on port {PORT}")
    print(f"[INFO] Default model: {DEFAULT_MODEL}")
    print(f"[INFO] Ollama server: {OLLAMA_BASE_URL}")
    print(f"[INFO] Health check: http://localhost:{PORT}/health")
    print(f"[INFO] Fix array comments: http://localhost:{PORT}/api/fix-array-comments")
    print(f"[INFO] Latin analysis: http://localhost:{PORT}/api/analyze-latin-word")
    print(f"[INFO] OpenAI API: http://localhost:{PORT}/v1/chat/completions")
    
    # Initial Ollama check
    if check_ollama_availability():
        if IS_REMOTE:
            print("[OK] Connected to REMOTE Ollama server")
        else:
            print("[OK] Connected to LOCAL Ollama server")
    else:
        if IS_REMOTE:
            print("[ERROR] Cannot connect to REMOTE Ollama server")
        else:
            print("[ERROR] Cannot connect to LOCAL Ollama server - will use CLI fallback")
    
    app.run(host='0.0.0.0', port=PORT, debug=True)