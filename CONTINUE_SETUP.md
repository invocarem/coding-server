# VS Code Continue Extension Setup

## Configuration for Renumber Verses

Add this to your Continue configuration file (`.continue/config.json` or `config.yaml`):

### Recommended Configuration

```yaml
name: Local Coding Agent
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
    description: "Renumber verse comments sequentially (1, 2, 3...)"

  - name: "fix-array-comments"
    prompt: "@fix-array-comments"
    description: "Add sequential comments to array elements"

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

### Method 1: Using Custom Commands (Recommended)

1. **Select your Swift array code** in VS Code:

   ```swift
   private let text = [
       /* 1 */ "First verse",
       /* 3 */ "Second verse",
       /* 2 */ "Third verse"
   ]
   ```

2. **Open Continue** (usually with `Cmd+L` or `Ctrl+L`)

3. **Type the command**: `/renumber-verses`

4. **Press Enter** - Continue will automatically:
   - Send your selected code
   - Include the `@renumber-verses` keyword
   - Return the renumbered code

### Method 2: Using Chat (Manual)

1. **Select your code** in VS Code

2. **Open Continue chat**

3. **Type**: `@renumber-verses` (followed by Enter, or just highlight and use context)

4. Continue will include your selected code automatically

### Method 3: Direct Prompt (Inline)

1. **Select code**

2. **In Continue chat, type**:

   ```
   @renumber-verses
   ```

3. Continue will use the selected code from your editor

## How It Works Behind the Scenes

When you use Continue, it sends a request like this:

```json
{
  "model": "mixtral:8x7b",
  "messages": [
    {
      "role": "user",
      "content": "@renumber-verses private let text = [\n  /* 1 */ \"verse\",\n  /* 3 */ \"verse\"\n]"
    }
  ]
}
```

Your server:

1. ✅ Detects the `@renumber-verses` keyword
2. ✅ Extracts the Swift code automatically
3. ✅ Renumbers the verses sequentially
4. ✅ Returns clean, formatted code

## Trigger Keywords

Your server recognizes these keywords in the content:

| Keyword                | Variants                                                  | Function                |
| ---------------------- | --------------------------------------------------------- | ----------------------- |
| `@renumber-verses`     | `renumber-verses`, `renumber verses`, `fix verse numbers` | Renumber verse comments |
| `@remove-all-comments` | `remove-all-comments`, `remove all comments`              | Strip all comments      |
| `@fix-array-comments`  | `fix-array-comments`, `add sequential comments`           | Add array numbering     |

## Tips for Best Results

### ✅ DO:

- Select the **entire variable declaration** including `private let text = [`
- Use the exact trigger keywords (`@renumber-verses`)
- Keep the prompt simple - let the server do the work

### ❌ DON'T:

- Add extra instructions after the keyword (the server ignores them)
- Select only part of the array
- Mix multiple operations in one request

## Example Workflow

**Before:**

```swift
private let psalm68 = [
    /* 1 */ "Benedictus Dominus...",
    /* 2 */ "Deus noster...",
    /* 3 */ "Verumtamen Deus...",
    /* 14 */ "Regna terrae...",  // Wrong number!
    /* 15 */ "Psallite Deo...",
    /* 17 */ "Mirabilis Deus..."  // Wrong number!
]
```

**Steps:**

1. Select entire array (including `private let psalm68 = [`)
2. Open Continue (`Cmd+L`)
3. Type: `/renumber-verses`
4. Press Enter

**After:**

```swift
private let psalm68 = [
    /* 1 */ "Benedictus Dominus...",
    /* 2 */ "Deus noster...",
    /* 3 */ "Verumtamen Deus...",
    /* 4 */ "Regna terrae...",  // ✅ Fixed!
    /* 5 */ "Psallite Deo...",
    /* 6 */ "Mirabilis Deus..."  // ✅ Fixed!
]
```

## Troubleshooting

### Issue: Continue not connecting to server

**Solution:**

```bash
# Make sure your server is running:
python src/coding_server.py

# Check server health:
curl http://127.0.0.1:5000/health
```

### Issue: Code not being detected

**Solution:**

- Ensure you selected the code before running the command
- Try including the `private let` declaration
- Check that your array has the proper Swift syntax

### Issue: Getting raw chat response instead of formatted code

**Solution:**

- Make sure you're using the exact keyword: `@renumber-verses` (with the @)
- Check server logs to see if keyword was detected
- Try using `/renumber-verses` (with slash) in Continue commands

## Advanced: Multiple Models

You can configure multiple models for different tasks:

```yaml
models:
  - name: fast-model
    provider: "openai"
    model: "deepseek-coder:6.7b"
    apiBase: "http://127.0.0.1:5000/v1"
    apiKey: "not-needed"
    default: true

  - name: powerful-model
    provider: "openai"
    model: "mixtral:8x7b"
    apiBase: "http://127.0.0.1:5000/v1"
    apiKey: "not-needed"
```

Switch models in Continue by typing `@fast-model` or `@powerful-model` before your command.

## Summary

✨ **Your current Continue setup works perfectly!** No changes needed to the server or Continue configuration. The `code` field we added is just an optional convenience for direct API calls.

The key is using the trigger keywords (`@renumber-verses`, `@remove-all-comments`, etc.) and selecting your code before running the command.
