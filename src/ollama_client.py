# src/ollama_client.py
from tkinter import W
import requests
import subprocess
import os
import time
import logging
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

# Configuration
OLLAMA_BASE_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_USERNAME = os.getenv('OLLAMA_USERNAME')
OLLAMA_PASSWORD = os.getenv('OLLAMA_PASSWORD')

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
            logging.info(f"[OK] Connected to remote Ollama server: {OLLAMA_BASE_URL}")
        elif OLLAMA_AVAILABLE:
            logging.info("[OK] Connected to local Ollama server")
        else:
            logging.info(f"[ERROR] Ollama server not responding: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        OLLAMA_AVAILABLE = False
        if IS_REMOTE:
            logging.info(f"[ERROR] Cannot connect to remote Ollama server: {OLLAMA_BASE_URL}")
        else:
            logging.info("[ERROR] Cannot connect to local Ollama server - is it running?")
    except requests.exceptions.Timeout:
        OLLAMA_AVAILABLE = False
        logging.info("[ERROR] Ollama server timeout")
    except Exception as e:
        OLLAMA_AVAILABLE = False
        logging.info(f"[ERROR] Error connecting to Ollama: {e}")
    
    LAST_OLLAMA_CHECK = time.time()
    return OLLAMA_AVAILABLE

def call_ollama_http(model_name, prompt, timeout=45):
    """Call Ollama using HTTP API with remote support"""
    try:
        session = create_ollama_session()
        logging.info(f"[INFO] Ollama model name: {model_name}")
        logging.info(f"[INFO] prompt: {prompt}")
        
        response = session.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "top_k": 40,
                    "num_predict": 4096
                }
            },
            timeout=timeout
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

def call_ollama_smart(model_name, prompt, timeout=240):
    """
    Smart Ollama caller that handles both local and remote servers
    """
    # For remote servers, only use HTTP
    if IS_REMOTE:
        return call_ollama_http(model_name, prompt)
    
    # For local servers, try HTTP first, then CLI fallback
    if check_ollama_availability():

        result = call_ollama_http(model_name, prompt, timeout)
        if not result.startswith("Error:"):
            return result
        # If HTTP fails, try CLI
        return call_ollama_cli(model_name, prompt)
    else:
        # Ollama not available via HTTP, try CLI
        return call_ollama_cli(model_name, prompt)

def get_available_models():
    """Get available models from Ollama server"""
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
        
        return {
            "available_models": models,
            "method": method,
            "server_type": "remote" if IS_REMOTE else "local"
        }

    except Exception as e:
        return {"error": f"Failed to get models: {str(e)}"}