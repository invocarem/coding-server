# Coding Server with Ollama Integration

A local coding assistant server that uses Ollama models to provide code formatting and commenting features.

## Features

- ✅ Add sequential comments to arrays
- ✅ Remove all comments from code
- ✅ Renumber verse comments sequentially (liturgical text support)
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

2. **Setup virtual invironment**:

```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Start server**:

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
```

### Remove All Comments

```bash
$ curl -X POST http://localhost:5000/api/remove-all-comments \
  -H "Content-Type: application/json" \
  -d '{
    "code": "let text = [\n    /* 1 */ \"First\",\n    /* 2 */ \"Second\", /* note */\n]",
    "language": "swift"
  }'
```

Response:

```json
{
  "cleaned_code": "let text = [\n    \"First\",\n    \"Second\",\n]",
  "language": "swift",
  "model_used": "deepseek-coder:6.7b",
  "original_code": "let text = [\n    /* 1 */ \"First\",\n    /* 2 */ \"Second\", /* note */\n]",
  "success": true
}
```

# Chat completions

The chat completions endpoint supports special keywords for triggering specific functionality:

## Keywords:

- **@fix-array-comments** or `/fix-array-comments` - Add sequential comments to array elements
- **@remove-all-comments** or `/remove-all-comments` - Remove all comments from code
- **@renumber-verses** or `/renumber-verses` - Renumber verse comments sequentially

## Examples:

### Fix Array Comments

```bash
$ curl -X POST http://127.0.0.1:5000/v1/chat/completions   -H "Content-Type: application/json"   -d '{
    "model": "deepseek-coder:6.7b",
    "messages": [
      {"role": "user", "content": "@fix-array-comments [\"apple\", \"banana\"]"}
    ]
  }'
```

### Renumber Verses

```bash
$ curl -X POST http://127.0.0.1:5000/v1/chat/completions   -H "Content-Type: application/json"   -d '{
    "model": "mixtral:8x7b",
    "messages": [
      {"role": "user", "content": "@renumber-verses private let text = [\n  /* 1 */ \"First verse\",\n  \"continuation\",\n  /* 2 */ \"Second verse\"\n]"}
    ]
  }' -o output.log
```

# VS Code Continue Extension Setup

This server works seamlessly with VS Code's Continue extension! **No changes needed** - Continue automatically sends code in the `messages.content` field, which the server handles perfectly.

## Quick Setup

Add this to your Continue configuration (`.continue/config.json`):

```yaml
name: Local Agent
version: 1.0.0
schema: v1
models:
  - name: local-coding-assistant
    provider: "openai"
    model: "mixtral:8x7b" # or "deepseek-coder:6.7b"
    apiBase: "http://127.0.0.1:5000/v1"
    apiKey: "not-needed"
    temperature: 0.1
    default: true
    contextLength: 4096
customCommands:
  - name: "renumber-verses"
    prompt: "@renumber-verses"
    description: "Renumber verse comments sequentially"
  - name: "fix-array-comments"
    prompt: "@fix-array-comments"
    description: "Fix array comments with sequential numbering"
  - name: "remove-all-comments"
    prompt: "@remove-all-comments"
    description: "Remove all comments from code"

contextProviders:
  - name: file
  - name: code
  - name: terminal
  - name: diff
```

## Usage in VS Code

1. **Select your Swift array code**
2. **Open Continue** (`Cmd+L` or `Ctrl+L`)
3. **Type**: `/renumber-verses` or `/fix-array-comments` or `/remove-all-comments`
4. **Press Enter**

📖 **See [CONTINUE_SETUP.md](CONTINUE_SETUP.md) for detailed usage guide, examples, and troubleshooting.**

## How It Works

Continue sends your selected code in the standard OpenAI format:

```json
{
  "messages": [{ "role": "user", "content": "@renumber-verses <your-code>" }]
}
```

The server automatically detects the keyword and extracts your code - no special configuration needed!

a test json:

````json
{
  "code": "private let text = [\n    /* 1 */ \"Benedictus Dominus die quotidie; prosperum iter faciet nobis Deus salutarium nostrorum.\",\n    /* 2 */ \"Deus noster, Deus salvos faciendi; et Domini Domini exitus mortis.\",\n    /* 3 */ \"Verumtamen Deus confringet capita inimicorum suorum, verticem capilli perambulantium in delictis suis.\",\n    /* 4 */ \"Dixit Dominus: Ex Basan convertam, convertam in profundum maris.\",\n    /* 5 */ \"Ut intingatur pes tuus in sanguine; lingua canum tuorum ex inimicis ab ipso.\",\n    /* 6 */ \"Viderunt ingressus tuos, Deus, ingressus Dei mei, regis mei, qui est in sancto.\",\n    /* 7 */ \"Praevenerunt principes conjuncti psallentibus, in medio juvencularum tympanistriarum.\",\n    /* 8 */ \"In ecclesiis benedicite Deo Domino, de fontibus Israel.\",\n    /* 9 */ \"Ibi Benjamin adolescentulus, in mentis excessu; \", \n            \"principes Juda, duces eorum; principes Zabulon, principes Nephthali.\",\n    /* 10 */ \"Manda, Deus, virtuti tuae; confirma hoc, Deus, quod operatus es in nobis.\",\n    /* 11 */ \"A templo tuo in Ierusalem, tibi offerent reges munera.\",\n    /* 12 */ \"Increpa feras arundinis; congregatio taurorum in vaccis populorum, ut excludantur qui probati sunt argento;\",\n            \" Dissipa gentes quae bella volunt. Venient legati ex Aegypto; Aethiopia praeveniet manus eius Deo.\",\n    /* 14 */ \"Regna terrae, cantate Deo; psallite Domino.\",\n    /* 15 */ \"Psallite Deo, qui ascendit super caelum caeli ad orientem; \",\n            \"ecce dabit voci suae vocem virtutis. Date gloriam Deo super Israel; magnificentia eius et virtus eius in nubibus.\",\n    /* 17 */ \"Mirabilis Deus in sanctis suis; Deus Israel, ipse dabit virtutem et fortitudinem plebi suae; benedictus Deus.\"\n]",
  "model": "deepseek-coder:6.7b",
  "target_verse_count": 18
}


# Usage

## 🎉 New! File-Based Code Loading (No JSON Escaping!)

The easiest way - reference plain Swift files directly:

**Step 1:** Create `psalm68.swift` (plain Swift, no escaping):
```swift
private let text = [
    /* 1 */ "Benedictus Dominus...",
    /* 14 */ "Regna terrae...",
    /* 17 */ "Mirabilis Deus..."
]
```

**Step 2:** Create `request.json`:
```json
{
  "model": "mixtral:8x7b",
  "messages": [{"role": "user", "content": "renumber verses"}],
  "code_file": "psalm68.swift"
}
```

**Step 3:** Run:
```bash
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d @request.json \
  -o output.log
```

✅ **No `\n` or `\"` escaping needed!**

📖 **See [FILE_BASED_USAGE.md](FILE_BASED_USAGE.md) for complete guide.**

## Traditional Usage (Still Works)

```bash
curl -X POST http://localhost:5000/api/renumber-verses \
  -H "Content-Type: application/json" \
  -d @psalm_request.json \
  -o output.log
```

```bash
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d @psalm_request.json \
  -o output.log
```
````
