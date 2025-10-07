# Coding Server with Ollama Integration

A local coding assistant server that uses Ollama models to provide code formatting and commenting features.

## Features

- ✅ Fix array comments with sequential numbering
- ✅ OpenAI-compatible API for VS Code Continue extension
- ✅ Support for multiple Ollama models (DeepSeek Coder, CodeLlama, etc.)
- ✅ Both HTTP and CLI communication with Ollama
- ✅ Automatic fallback between HTTP and CLI methods

## Quick Start

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed
- At least one coding model (e.g., `deepseek-coder:6.7b`)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/coding-server.git
   cd coding-server
   ```


2. Setup virtual invironment
```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Start server
```bash
export PYTHONIOENCODING=utf-8
python src/coding_server.py
```

4. Test
```bash
$ curl -X POST http://localhost:5000/api/fix-array-comments \
  -H "Content-Type: application/json" \
  -d '{
    "code": "let test = [ \"a\", \"b\"]",
    "language": "swift"
  }'
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   305  100   234  100    71     21      6  0:00:11  0:00:10  0:00:01    49{
  "corrected_code": "let test = [\n    /* 1 */ \"a\",\n    /* 2 */ \"b\"\n]",
  "elements_count": 2,
  "language": "swift",
  "model_used": "deepseek-coder:6.7b",
  "original_code": "let test = [ \"a\", \"b\"]",
  "success": true
```


```bash
$ curl -X POST http://127.0.0.1:5000/v1/chat/completions   -H "Content-Type: application/json"   -d '{
    "model": "deepseek-coder:6.7b",
    "messages": [
      {"role": "user", "content": "Add sequential comments to this array: [\"apple\", \"banana\"]"}
    ]
  }'


# my config setting of vscode

```
name: Local Agent
version: 1.0.0
schema: v1
models:
  - name: local-coding-assistant
    provider: "openai"
    model: "deepseek-coder:6.7b"
    apiBase: "http://127.0.0.1:5000/v1"
    apiKey: "not-needed"
    temperature: 0.1
    default: true
    contextLength: 2048 
customCommands:
  - name: "fix-array-comments"
    prompt: "Add sequential /* number */ comments to every element in the selected array. Number from 1 to the total count. Maintain original formatting."
    description: "Fix array comments with sequential numbering"
  - name: "analyze-latin"
    prompt: "Analyze Latin text for lemmas and grammar"
    description: "Latin linguistic analysis"

contextProviders:
  - name: file
  - name: terminal
  - name: diff
  - name: problems

experimental:
  debug: true
```