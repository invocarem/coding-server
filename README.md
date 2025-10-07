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


2. Setup virtual invironment
```bash
   python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate



3. Install dependences
```bash
pip install -r requirements.txt

pip install flask flask-cors requests python-dotenv


start server
python src/coding_server.py