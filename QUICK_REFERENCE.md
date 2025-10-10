# Quick Reference Guide

## ✨ Good News: No Changes Needed for VS Code Continue!

Your server already works perfectly with Continue. Just use the trigger keywords in your prompts.

---

## 🎯 Four Ways to Use This Server

### 1️⃣ File-Based API (🏆 Best for API Calls - No Escaping!)

**Best for:** Direct API calls, scripts, automation

**No JSON escaping needed!**

```bash
# Step 1: Create plain Swift file
echo 'private let text = [
  /* 1 */ "First",
  /* 14 */ "Wrong number"
]' > psalm68.swift

# Step 2: Create simple request
echo '{
  "messages": [{"role": "user", "content": "renumber verses"}],
  "code_file": "psalm68.swift",
  "model": "mixtral:8x7b"
}' > request.json

# Step 3: Run
curl -X POST http://127.0.0.1:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d @request.json
```

**Advantages:**

- ✅ No `\n` or `\"` escaping
- ✅ Edit code in any editor
- ✅ Version control friendly
- ✅ Reusable files

📖 **See [FILE_BASED_USAGE.md](FILE_BASED_USAGE.md)**

---

### 2️⃣ VS Code Continue (Easiest for Daily Coding)

**Setup Once:**

```yaml
# .continue/config.json
models:
  - name: local-coding-assistant
    provider: "openai"
    model: "mixtral:8x7b"
    apiBase: "http://127.0.0.1:5000/v1"
    apiKey: "not-needed"

customCommands:
  - name: "renumber-verses"
    prompt: "@renumber-verses"
```

**Daily Use:**

1. Select code in VS Code
2. Open Continue (`Cmd+L`)
3. Type: `/renumber-verses`
4. ✨ Done!

---

### 3️⃣ Direct API with `code` Field (Inline Code)

**Best for:** Scripts, automation, external tools

```bash
curl -X POST http://127.0.0.1:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "renumber verses"}],
    "code": "private let text = [...your swift code...]",
    "model": "mixtral:8x7b"
  }'
```

**Advantages:**

- ✅ Clean separation of intent vs. data
- ✅ Easier to construct JSON
- ✅ Similar to `/api/renumber-verses` format

---

### 4️⃣ Dedicated Endpoint (Original)

**Best for:** Single-purpose scripts

```bash
curl -X POST http://127.0.0.1:5000/api/renumber-verses \
  -H "Content-Type: application/json" \
  -d '{
    "code": "private let text = [...]",
    "model": "mixtral:8x7b"
  }'
```

---

## 🔑 Trigger Keywords

All keywords work in Continue and API calls:

| Operation              | Keywords                                                            | Example                                                                     |
| ---------------------- | ------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| **Renumber Verses**    | `@renumber-verses`<br>`renumber verses`<br>`fix verse numbers`      | Continue: `/renumber-verses`<br>API: `"content": "renumber verses"`         |
| **Remove Comments**    | `@remove-all-comments`<br>`remove all comments`<br>`strip comments` | Continue: `/remove-all-comments`<br>API: `"content": "remove all comments"` |
| **Fix Array Comments** | `@fix-array-comments`<br>`fix array comments`<br>`number comments`  | Continue: `/fix-array-comments`<br>API: `"content": "fix array comments"`   |

---

## 📊 Which Method Should I Use?

```
Working in VS Code daily?
    → Use Continue Extension ⭐⭐⭐⭐⭐

Making API calls / Have Swift files?
    → Use File-Based (code_file) ⭐⭐⭐⭐⭐ (No escaping!)

Building automation/scripts with inline code?
    → Use Direct API with 'code' field ⭐⭐⭐⭐

Need simplest curl command?
    → Use Dedicated Endpoint (/api/renumber-verses) ⭐⭐⭐
```

---

## 🚀 Complete Example: Renumber Verses

### Input Swift Code:

```swift
private let psalm68 = [
    /* 1 */ "Benedictus Dominus...",
    /* 2 */ "Deus noster...",
    /* 14 */ "Regna terrae...",     // ❌ Wrong!
    /* 15 */ "Psallite Deo...",
    /* 17 */ "Mirabilis Deus..."    // ❌ Wrong!
]
```

### Using File-Based API (Recommended for API):

1. Save code to `psalm68.swift` (no escaping!)
2. Create `request.json`:
   ```json
   {
     "messages": [{ "role": "user", "content": "renumber verses" }],
     "code_file": "psalm68.swift",
     "model": "mixtral:8x7b"
   }
   ```
3. Run: `curl -X POST http://127.0.0.1:5000/v1/chat/completions -H "Content-Type: application/json" -d @request.json`

### Using Continue (Recommended for VS Code):

1. Select the entire array
2. `Cmd+L` → `/renumber-verses` → Enter
3. ✨ Done!

### Using Inline Code API:

```bash
curl -X POST http://127.0.0.1:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "renumber verses"}],
    "code": "private let psalm68 = [...code above...]",
    "model": "mixtral:8x7b"
  }'
```

### Output:

```swift
private let psalm68 = [
    /* 1 */ "Benedictus Dominus...",
    /* 2 */ "Deus noster...",
    /* 3 */ "Regna terrae...",     // ✅ Fixed!
    /* 4 */ "Psallite Deo...",
    /* 5 */ "Mirabilis Deus..."    // ✅ Fixed!
]
```

---

## 🔧 Server Status

```bash
# Check if server is running
curl http://127.0.0.1:5000/health

# Start server
python src/coding_server.py

# View server logs
tail -f server_debug.log
```

---

## 📚 Documentation Links

- **[CONTINUE_SETUP.md](CONTINUE_SETUP.md)** - Detailed Continue setup and troubleshooting
- **[API_EXAMPLES.md](API_EXAMPLES.md)** - All API formats and examples
- **[README.md](README.md)** - Full project documentation
- **[RENUMBER_VERSES_INTEGRATION.md](RENUMBER_VERSES_INTEGRATION.md)** - Technical details

---

## 💡 Pro Tips

### For Continue Users:

- ✅ Always select the **entire variable declaration** (include `private let text = [`)
- ✅ Use simple commands: `/renumber-verses` (don't add extra instructions)
- ✅ Check server logs if commands aren't working

### For API Users:

- ✅ Use the new `code` field for cleaner requests
- ✅ Old format still works - no breaking changes
- ✅ Can pass code in either `code` field or `messages.content`

### For All Users:

- ✅ Server auto-detects code in markdown blocks (\`\`\`swift ... \`\`\`)
- ✅ Server auto-extracts variable assignments
- ✅ Keywords are case-insensitive
- ✅ Both `/keyword` and `@keyword` formats work
