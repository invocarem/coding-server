# File-Based Code Loading - No JSON Escaping Required! 🎉

## Problem: JSON Escaping is Painful

When embedding Swift code in JSON, you need to escape everything:

```json
{
  "code": "private let text = [\n    /* 1 */ \"First verse\",\n    /* 2 */ \"Second verse\"\n]"
}
```

❌ Every newline becomes `\n`
❌ Every quote becomes `\"`
❌ Hard to read and error-prone
❌ Difficult to edit

## Solution: Use `code_file` Parameter ✨

Just reference a plain Swift file - **no escaping needed!**

---

## Quick Start

### Step 1: Create a Plain Swift File

Create `psalm68.swift` with your code (no escaping!):

```swift
private let text = [
/* 1 */ "Benedictus Dominus die quotidie; prosperum iter faciet nobis Deus salutarium nostrorum.",
/* 2 */ "Deus noster, Deus salvos faciendi; et Domini Domini exitus mortis.",
/* 3 */ "Verumtamen Deus confringet capita inimicorum suorum, verticem capilli perambulantium in delictis suis.",
/* 14 */ "Regna terrae, cantate Deo; psallite Domino.",
/* 15 */ "Psallite Deo, qui ascendit super caelum caeli ad orientem; ",
"ecce dabit voci suae vocem virtutis. Date gloriam Deo super Israel; magnificentia eius et virtus eius in nubibus.",
/* 17 */ "Mirabilis Deus in sanctis suis; Deus Israel, ipse dabit virtutem et fortitudinem plebi suae; benedictus Deus."
]
```

### Step 2: Create Simple Request JSON

Create `psalm_request_simple.json`:

```json
{
  "model": "mixtral:8x7b",
  "messages": [
    {
      "role": "user",
      "content": "renumber verses"
    }
  ],
  "code_file": "psalm68.swift"
}
```

✅ Clean and readable
✅ No escaping needed
✅ Easy to edit

### Step 3: Run the Command

```bash
curl -X POST http://127.0.0.1:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d @psalm_request_simple.json \
  -o output.log
```

**That's it!** The server automatically reads your Swift file.

---

## Comparison: JSON Escaping vs File-Based

### ❌ Old Way: Inline Code (Painful)

```json
{
  "model": "mixtral:8x7b",
  "messages": [
    {
      "role": "user",
      "content": "renumber verses"
    }
  ],
  "code": "private let text = [\n    /* 1 */ \"Benedictus Dominus die quotidie; prosperum iter faciet nobis Deus salutarium nostrorum.\",\n    /* 2 */ \"Deus noster, Deus salvos faciendi; et Domini Domini exitus mortis.\"\n]"
}
```

**Problems:**

- 😫 Must escape every `\n` and `\"`
- 😫 Unreadable
- 😫 Error-prone (missing escape breaks JSON)
- 😫 Hard to maintain

### ✅ New Way: File Reference (Easy!)

**psalm68.swift** (plain Swift, no escaping):

```swift
private let text = [
    /* 1 */ "Benedictus Dominus die quotidie; prosperum iter faciet nobis Deus salutarium nostrorum.",
    /* 2 */ "Deus noster, Deus salvos faciendi; et Domini Domini exitus mortis."
]
```

**psalm_request_simple.json**:

```json
{
  "model": "mixtral:8x7b",
  "messages": [
    {
      "role": "user",
      "content": "renumber verses"
    }
  ],
  "code_file": "psalm68.swift"
}
```

**Benefits:**

- ✅ No escaping needed
- ✅ Readable Swift code
- ✅ Easy to edit in any editor
- ✅ Version control friendly

---

## All Supported Endpoints

Both endpoints now support `code_file`:

### 1. `/v1/chat/completions` (OpenAI-compatible)

```bash
# Using file reference
curl -X POST http://127.0.0.1:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "renumber verses"}],
    "code_file": "psalm68.swift",
    "model": "mixtral:8x7b"
  }'
```

### 2. `/api/renumber-verses` (Dedicated endpoint)

```bash
# Using file reference
curl -X POST http://127.0.0.1:5000/api/renumber-verses \
  -H "Content-Type: application/json" \
  -d '{
    "code_file": "psalm68.swift",
    "model": "mixtral:8x7b"
  }'
```

---

## File Path Options

The server supports both **relative** and **absolute** paths:

### Relative Path (Recommended)

```json
{
  "code_file": "psalm68.swift"
}
```

Looks for file in the current working directory (where you run the server).

### Absolute Path

```json
{
  "code_file": "C:\\code\\github\\coding-server\\psalm68.swift"
}
```

Or on Mac/Linux:

```json
{
  "code_file": "/Users/you/projects/coding-server/psalm68.swift"
}
```

### Subdirectory

```json
{
  "code_file": "psalms/psalm68.swift"
}
```

Relative to current directory.

---

## Complete Examples

### Example 1: Renumber Verses

**Input: psalm68.swift**

```swift
private let psalm68 = [
    /* 1 */ "Benedictus Dominus...",
    /* 2 */ "Deus noster...",
    /* 14 */ "Regna terrae...",     // ❌ Wrong!
    /* 15 */ "Psallite Deo...",
    /* 17 */ "Mirabilis Deus..."    // ❌ Wrong!
]
```

**Request: request.json**

```json
{
  "messages": [{ "role": "user", "content": "renumber verses" }],
  "code_file": "psalm68.swift",
  "model": "mixtral:8x7b"
}
```

**Command:**

```bash
curl -X POST http://127.0.0.1:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d @request.json \
  -o output.log
```

**Output:**

```swift
private let psalm68 = [
    /* 1 */ "Benedictus Dominus...",
    /* 2 */ "Deus noster...",
    /* 3 */ "Regna terrae...",     // ✅ Fixed!
    /* 4 */ "Psallite Deo...",
    /* 5 */ "Mirabilis Deus..."    // ✅ Fixed!
]
```

### Example 2: Remove All Comments

**Input: code.swift**

```swift
let items = [
    /* 1 */ "apple",
    /* 2 */ "banana",
    /* 3 */ "cherry"
]
```

**Request:**

```json
{
  "messages": [{ "role": "user", "content": "remove all comments" }],
  "code_file": "code.swift",
  "model": "mixtral:8x7b"
}
```

**Output:**

```swift
let items = [
    "apple",
    "banana",
    "cherry"
]
```

### Example 3: Fix Array Comments

**Input: array.swift**

```swift
let colors = [
    "red",
    "green",
    "blue"
]
```

**Request:**

```json
{
  "messages": [{ "role": "user", "content": "fix array comments" }],
  "code_file": "array.swift",
  "model": "mixtral:8x7b"
}
```

**Output:**

```swift
let colors = [
    /* 1 */ "red",
    /* 2 */ "green",
    /* 3 */ "blue"
]
```

---

## Best Practices

### ✅ DO:

1. **Keep Swift files clean** - Just pure Swift code, no escaping
2. **Use relative paths** - Easier to share and version control
3. **One file per psalm/text** - Organize by content
4. **Meaningful filenames** - `psalm68.swift`, `psalm150.swift`
5. **Version control your Swift files** - Track changes to liturgical texts

### ❌ DON'T:

1. Don't mix code and prompts in the same file
2. Don't use special characters in filenames
3. Don't forget file extension (use `.swift`)
4. Don't put files outside the project directory (use relative paths)

---

## Error Handling

### File Not Found

**Request:**

```json
{
  "code_file": "nonexistent.swift"
}
```

**Response:**

```json
{
  "error": {
    "message": "Code file not found: nonexistent.swift",
    "type": "invalid_request_error"
  }
}
```

**Fix:** Check file path and ensure file exists.

### Invalid File Path

**Request:**

```json
{
  "code_file": "../../etc/passwd"
}
```

**Response:** Error if file doesn't exist or isn't readable.

**Fix:** Use files in your project directory.

---

## Priority: Multiple Code Sources

If you provide multiple code sources, the server uses this priority:

1. **`code_file`** (highest priority) - Reads from file
2. **`code`** - Uses inline code
3. **`messages.content`** - Extracts from message content

**Example:** If you provide both, `code_file` wins:

```json
{
  "messages": [{ "role": "user", "content": "renumber verses" }],
  "code": "ignored",
  "code_file": "psalm68.swift" // ← This is used
}
```

---

## Organizing Your Files

Recommended structure:

```
coding-server/
├── psalm68.swift           # Plain Swift files
├── psalm150.swift
├── canticle_magnificat.swift
├── requests/
│   ├── renumber_psalm68.json
│   ├── renumber_psalm150.json
│   └── remove_comments.json
└── output/
    └── results.log
```

**Benefits:**

- Clean separation of code and requests
- Easy to maintain and version control
- Reusable Swift files
- Organized outputs

---

## Quick Reference

### All Three Ways to Provide Code

| Method              | Syntax                                  | Best For                          |
| ------------------- | --------------------------------------- | --------------------------------- |
| **File Reference**  | `"code_file": "psalm68.swift"`          | ✅ **Recommended** - No escaping! |
| **Inline Code**     | `"code": "private let text = [...]"`    | Small snippets                    |
| **Message Content** | `"content": "renumber verses: code..."` | Continue integration              |

---

## Summary

🎉 **The `code_file` parameter solves the JSON escaping problem!**

**Before:**

```json
{
  "code": "private let text = [\n    /* 1 */ \"verse\",\n    /* 2 */ \"verse\"\n]"
}
```

😫 Painful escaping

**After:**

```json
{ "code_file": "psalm68.swift" }
```

✅ No escaping needed!

**Your workflow:**

1. Edit Swift files normally (no escaping)
2. Reference file in JSON request
3. Run curl command
4. Get renumbered output

**Simple, clean, and maintainable!** 🚀
