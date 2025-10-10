# Solution Summary: File-Based Code Loading

## Your Problem

> "I still think provide 'code' in JSON is not an easy task, because it has many \n and \", I prefer send a file with plain text"

**You're absolutely right!** JSON escaping is painful:

```json
{
  "code": "private let text = [\n    /* 1 */ \"verse\",\n    /* 2 */ \"verse\"\n]"
}
```

😫 Every newline → `\n`
😫 Every quote → `\"`
😫 Unreadable and error-prone

---

## The Solution

### ✨ New `code_file` Parameter

Now you can reference plain Swift files directly - **no JSON escaping needed!**

---

## How It Works

### Step 1: Create Plain Swift File

Create `psalm68.swift`:

```swift
private let text = [
/* 1 */ "Benedictus Dominus die quotidie; prosperum iter faciet nobis Deus salutarium nostrorum.",
/* 2 */ "Deus noster, Deus salvos faciendi; et Domini Domini exitus mortis.",
/* 14 */ "Regna terrae, cantate Deo; psallite Domino.",
/* 15 */ "Psallite Deo, qui ascendit super caelum caeli ad orientem; ",
"ecce dabit voci suae vocem virtutis. Date gloriam Deo super Israel; magnificentia eius et virtus eius in nubibus.",
/* 17 */ "Mirabilis Deus in sanctis suis; Deus Israel, ipse dabit virtutem et fortitudinem plebi suae; benedictus Deus."
]
```

✅ **Plain Swift - no escaping!**

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

✅ **Clean and readable!**

### Step 3: Run Command

```bash
curl -X POST http://127.0.0.1:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d @psalm_request_simple.json \
  -o output.log
```

✅ **Simple curl command!**

---

## What We Changed

### 1. Server Updates (`src/coding_server.py`)

Added `code_file` support to both endpoints:

**`/v1/chat/completions`:**

- Now reads code from file if `code_file` is provided
- Supports both relative and absolute paths
- Proper error handling for missing files

**`/api/renumber-verses`:**

- Also supports `code_file` parameter
- Consistent behavior across endpoints

### 2. Example Files Created

**`psalm68.swift`** - Plain Swift code (no escaping)
**`psalm_request_simple.json`** - Simple request using `code_file`

### 3. Documentation Created

**`FILE_BASED_USAGE.md`** - Complete guide for file-based usage

- Detailed examples
- Best practices
- Error handling
- File organization tips

**Updated existing docs:**

- `README.md` - Highlights new file-based approach
- `API_EXAMPLES.md` - Added file-based format as #1 recommendation
- `QUICK_REFERENCE.md` - Updated with file-based examples

---

## Three Ways to Provide Code (Priority Order)

The server now accepts code in three ways:

| Priority | Method          | Parameter            | Example                        |
| -------- | --------------- | -------------------- | ------------------------------ |
| **1st**  | File reference  | `code_file`          | `"code_file": "psalm68.swift"` |
| **2nd**  | Inline code     | `code`               | `"code": "private let..."`     |
| **3rd**  | Message content | `messages[].content` | Continue uses this             |

If multiple are provided, `code_file` takes precedence.

---

## Comparison: Before vs After

### ❌ Before (Inline Code - Painful)

```json
{
  "model": "mixtral:8x7b",
  "messages": [
    {
      "role": "user",
      "content": "renumber verses"
    }
  ],
  "code": "private let text = [\n/* 1 */ \"Benedictus Dominus die quotidie; prosperum iter faciet nobis Deus salutarium nostrorum.\",\n/* 2 */ \"Deus noster, Deus salvos faciendi; et Domini Domini exitus mortis.\",\n/* 14 */ \"Regna terrae, cantate Deo; psallite Domino.\"\n]"
}
```

**Problems:**

- 😫 Must escape `\n` and `\"`
- 😫 Unreadable
- 😫 Error-prone
- 😫 Hard to edit

### ✅ After (File-Based - Easy!)

**psalm68.swift:**

```swift
private let text = [
/* 1 */ "Benedictus Dominus die quotidie; prosperum iter faciet nobis Deus salutarium nostrorum.",
/* 2 */ "Deus noster, Deus salvos faciendi; et Domini Domini exitus mortis.",
/* 14 */ "Regna terrae, cantate Deo; psallite Domino."
]
```

**request.json:**

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

- ✅ No escaping
- ✅ Readable
- ✅ Easy to edit
- ✅ Version control friendly

---

## Supported Endpoints

Both endpoints now support `code_file`:

### 1. `/v1/chat/completions` (OpenAI-compatible)

```bash
curl -X POST http://127.0.0.1:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "renumber verses"}],
    "code_file": "psalm68.swift",
    "model": "mixtral:8x7b"
  }'
```

### 2. `/api/renumber-verses` (Dedicated)

```bash
curl -X POST http://127.0.0.1:5000/api/renumber-verses \
  -H "Content-Type: application/json" \
  -d '{
    "code_file": "psalm68.swift",
    "model": "mixtral:8x7b"
  }'
```

---

## File Path Support

### Relative Path (Recommended)

```json
{
  "code_file": "psalm68.swift"
}
```

Looks for file relative to where you run the server.

### Absolute Path

```json
{
  "code_file": "C:\\code\\github\\coding-server\\psalm68.swift"
}
```

Full path to file.

### Subdirectory

```json
{
  "code_file": "psalms/psalm68.swift"
}
```

Organized in folders.

---

## Benefits

### For You

1. ✅ **No JSON escaping** - Edit plain Swift files
2. ✅ **Easier to maintain** - Use any editor
3. ✅ **Version control** - Track changes to liturgical texts
4. ✅ **Reusable** - Same file for multiple operations
5. ✅ **Less error-prone** - No escaping mistakes

### Backward Compatible

- ✅ Old `code` field still works
- ✅ Continue extension unchanged
- ✅ All existing scripts work
- ✅ No breaking changes

---

## Quick Start

### Simplest Example

```bash
# 1. Create Swift file
cat > test.swift << 'EOF'
private let text = [
    /* 1 */ "First",
    /* 14 */ "Wrong number"
]
EOF

# 2. Create request
cat > request.json << 'EOF'
{
  "messages": [{"role": "user", "content": "renumber verses"}],
  "code_file": "test.swift",
  "model": "mixtral:8x7b"
}
EOF

# 3. Run
curl -X POST http://127.0.0.1:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d @request.json
```

---

## Documentation Files

All documentation updated:

| File                    | Purpose                                |
| ----------------------- | -------------------------------------- |
| **FILE_BASED_USAGE.md** | 📘 Complete guide for file-based usage |
| **API_EXAMPLES.md**     | Updated with file-based examples       |
| **README.md**           | Highlights new feature                 |
| **QUICK_REFERENCE.md**  | Quick lookup with file examples        |
| **SOLUTION_SUMMARY.md** | This file - summary of changes         |

---

## Error Handling

### File Not Found

```json
{
  "error": {
    "message": "Code file not found: psalm68.swift",
    "type": "invalid_request_error"
  }
}
```

**Fix:** Check file path exists.

### File Read Error

```json
{
  "error": {
    "message": "Error reading code file: Permission denied",
    "type": "invalid_request_error"
  }
}
```

**Fix:** Check file permissions.

---

## Summary

🎉 **Problem solved!**

**Before:**

- JSON escaping was painful
- Had to escape every `\n` and `\"`
- Code was unreadable in JSON

**After:**

- Reference plain Swift files with `code_file`
- No escaping needed
- Clean, maintainable, version-controllable

**Your workflow:**

1. Create `.swift` file with plain code
2. Reference it in JSON request
3. Run curl command
4. ✨ Done!

**No more JSON escaping headaches!** 🚀
