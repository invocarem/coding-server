# Renumber Verses Integration with Chat Completions

## Summary

Successfully integrated the `renumber_verses_with_ai` function from `liturgical_processor.py` into the chat completions endpoint (`/v1/chat/completions`) in `coding_server.py`.

## Changes Made

### 1. Detection Logic (coding_server.py, lines 437-445)

Added keyword detection for renumber verses requests:

- Triggers: `@renumber-verses`, `/renumber-verses`, `renumber-verses`, `renumber verses`, `renumber verse`, `fix verse numbers`
- Priority: 2nd (after remove comments, before array comments)

### 2. Code Extraction (coding_server.py, lines 482-511)

Implemented code extraction logic that:

- First tries to extract code from markdown blocks (`...`)
- Falls back to extracting variable assignments (e.g., `private let text = [...]`)
- Handles Swift arrays with verse comments

### 3. Processing Logic (coding_server.py, lines 507-511)

- Calls `renumber_verses_with_ai(code_to_fix, model=model)` directly
- Sets `prompt = None` to skip normal Ollama call (function handles it internally)
- Returns cleaned, renumbered code

### 4. Response Handling (coding_server.py, lines 556-563)

- Added check for `prompt is None` to skip redundant Ollama calls
- Pre-generated response is used directly

### 5. Token Calculation Fix (coding_server.py, lines 626-627)

- Updated to handle `prompt = None` case
- `prompt_tokens = len(prompt.split()) if prompt else 0`

### 6. Documentation Updates (README.md)

- Added `@renumber-verses` keyword to chat completions section
- Added example usage with curl
- Updated VS Code Continue custom commands configuration
- Added feature to the main features list

## How to Use

### Via Chat Completions API

```bash
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mixtral:8x7b",
    "messages": [
      {
        "role": "user",
        "content": "@renumber-verses private let text = [\n  /* 1 */ \"First verse\",\n  \"continuation\",\n  /* 2 */ \"Second verse\"\n]"
      }
    ]
  }'
```

### Via VS Code Continue Extension

1. Select your array code
2. Open Continue chat
3. Type: `@renumber-verses` or use the custom command

### Supported Keywords

Any of these keywords will trigger the renumber verses logic:

- `@renumber-verses`
- `/renumber-verses`
- `renumber-verses`
- `renumber verses`
- `renumber verse`
- `fix verse numbers`

## What It Does

The renumber verses feature:

1. Counts the **exact number of strings** in a Swift array
2. Renumbers the `/* number */` comments sequentially from 1
3. Preserves all original text content
4. Maintains proper array formatting
5. Handles multi-line verses correctly

## Example

**Input:**

```swift
private let text = [
  /* 1 */ "First verse",
  "continuation of first",
  /* 2 */ "Second verse",
  /* 5 */ "Third verse"
]
```

**Output:**

```swift
private let text = [
  /* 1 */ "First verse",
  /* 2 */ "continuation of first",
  /* 3 */ "Second verse",
  /* 4 */ "Third verse"
]
```

## Technical Details

### Function Flow

1. User sends message with `@renumber-verses` keyword
2. Server detects keyword and extracts code
3. Calls `renumber_verses_with_ai(code, model)` from `liturgical_processor.py`
4. Function uses AI to count strings and renumber
5. Returns cleaned, renumbered code
6. Server formats response as OpenAI-compatible JSON

### Error Handling

- If code extraction fails, uses entire message
- If renumbering fails, returns error message with "Error:" prefix
- Validates output before returning

### Logging

All operations are logged with `[RENUMBER_VERSES]` prefix for easy debugging.

## Testing

To test the integration:

```bash
# Test via chat completions
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mixtral:8x7b",
    "messages": [
      {"role": "user", "content": "@renumber-verses let x = [\"a\", \"b\", \"c\"]"}
    ]
  }'

# Test via dedicated endpoint (still works)
curl -X POST http://localhost:5000/api/renumber-verses \
  -H "Content-Type: application/json" \
  -d '{"code": "let x = [\"a\", \"b\", \"c\"]"}'
```

## Benefits

1. **Convenience**: Use in VS Code Continue chat without switching to direct API calls
2. **Consistency**: Same keyword pattern as other features (@fix-array-comments, @remove-all-comments)
3. **Flexibility**: Works with both dedicated endpoint and chat completions
4. **Context-Aware**: Automatically detects intent from user message
5. **Clean Integration**: Reuses existing function, minimal code duplication
