# src/ollama_client.py
import requests
import subprocess
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_AVAILABLE = False
LAST_OLLAMA_CHECK = 0

def check_ollama_availability():
    """Check if Ollama is available"""
    global OLLAMA_AVAILABLE, LAST_OLLAMA_CHECK
    
    # Cache check for 30 seconds
    import time
    if time.time() - LAST_OLLAMA_CHECK < 30:
        return OLLAMA_AVAILABLE
    
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        OLLAMA_AVAILABLE = response.status_code == 200
    except:
        OLLAMA_AVAILABLE = False
    
    LAST_OLLAMA_CHECK = time.time()
    return OLLAMA_AVAILABLE

def call_ollama_http(model_name, prompt):
    """Call Ollama using HTTP API"""
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
            timeout=45
        )
        
        if response.status_code == 200:
            return response.json().get("response", "").strip()
        else:
            return f"Error: HTTP {response.status_code} - {response.text}"
            
    except requests.exceptions.Timeout:
        return "Error: Request timeout"
    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to Ollama"
    except Exception as e:
        return f"Error: {str(e)}"

def call_ollama_smart(model_name, prompt):
    """
    Smart Ollama caller that tries HTTP first, then CLI fallback
    """
    # Try HTTP first
    if check_ollama_availability():
        result = call_ollama_http(model_name, prompt)
        if not result.startswith("Error:"):
            return result
    
    # Fallback to CLI (for local Ollama only)
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
            return f"Error: {result.stderr}"
            
    except Exception as e:
        return f"Error: {str(e)}"