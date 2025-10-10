# API Usage Examples

## Overview

The `/v1/chat/completions` endpoint now supports **three flexible formats** for code operations:

1. **File-Based Format** (⭐ Recommended!) - No JSON escaping needed
2. **Direct Code Format** - Code in `code` field
3. **OpenAI-Compatible Format** - Traditional message-based approach

All formats are fully supported and can be used interchangeably.

---

## File-Based Format (⭐ Best! No Escaping!)

This format lets you reference plain Swift files - **no JSON escaping required!**

### Renumber Verses

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
  "messages": [
    {
      "role": "user",
      "content": "renumber verses"
    }
  ],
  "code_file": "psalm68.swift"
}
```

**Step 3:** Run curl:

```bash
curl -X POST http://127.0.0.1:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d @request.json \
  -o output.log
```

**Benefits:**

- ✅ No `\n` or `\"` escaping needed
- ✅ Edit code in any editor
- ✅ Clean and readable
- ✅ Version control friendly

📖 **See [FILE_BASED_USAGE.md](FILE_BASED_USAGE.md) for complete guide.**

---

## Direct Code Format (New! ✨)

This format allows you to pass code directly via the `code` field, making requests cleaner and easier to construct.

### Renumber Verses

```json
{
  "model": "mixtral:8x7b",
  "messages": [
    {
      "role": "user",
      "content": "renumber verses"
    }
  ],
  "code": "private let text = [\n    /* 1 */ \"First verse\",\n    /* 3 */ \"Second verse\",\n    /* 2 */ \"Third verse\"\n]"
}
```

**Curl Example:**

```bash
curl -X POST http://127.0.0.1:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d @psalm_request.json \
  -o output.log
```

### Remove All Comments

```json
{
  "model": "mixtral:8x7b",
  "messages": [
    {
      "role": "user",
      "content": "remove all comments"
    }
  ],
  "code": "private let text = [\n    /* 1 */ \"First verse\",\n    /* 2 */ \"Second verse\"\n]"
}
```

### Fix Array Comments

```json
{
  "model": "mixtral:8x7b",
  "messages": [
    {
      "role": "user",
      "content": "fix array comments"
    }
  ],
  "code": "let items = [\n    \"First\",\n    \"Second\",\n    \"Third\"\n]"
}
```

---

## OpenAI-Compatible Format (Traditional)

This format embeds the code within the message content, following OpenAI's API conventions.

### Renumber Verses

```json
{
  "model": "mixtral:8x7b",
  "messages": [
    {
      "role": "user",
      "content": "renumber verses for the following code: private let text = [\n    /* 1 */ \"First verse\",\n    /* 3 */ \"Second verse\"\n]"
    }
  ]
}
```

### Remove All Comments

```json
{
  "model": "mixtral:8x7b",
  "messages": [
    {
      "role": "user",
      "content": "remove all comments from: private let text = [\n    /* 1 */ \"First verse\"\n]"
    }
  ]
}
```

---

## Dedicated Endpoint: `/api/renumber-verses`

For the most straightforward approach, use the dedicated endpoint:

```json
{
  "code": "private let text = [\n    /* 1 */ \"First verse\",\n    /* 3 */ \"Second verse\"\n]",
  "model": "mixtral:8x7b"
}
```

**Curl Example:**

```bash
curl -X POST http://127.0.0.1:5000/api/renumber-verses \
  -H "Content-Type: application/json" \
  -d '{"code": "private let text = [...]", "model": "mixtral:8x7b"}' \
  -o output.json
```

---

## Comparison

| Feature               | File-Based (`code_file`)    | Direct Code (`code`)        | OpenAI (`content`) | `/api/renumber-verses`   |
| --------------------- | --------------------------- | --------------------------- | ------------------ | ------------------------ |
| **Code Source**       | 📁 Plain file (`.swift`)    | 📝 JSON field (escaped)     | 📝 Message content | 📁 File or JSON field    |
| **Escaping Needed**   | ✅ None! Plain Swift        | ⚠️ Yes (`\n`, `\"`)         | ⚠️ Yes             | ✅ None with `code_file` |
| **Ease of Use**       | ⭐⭐⭐⭐⭐ Easiest          | ⭐⭐⭐⭐ Easy               | ⭐⭐⭐ Moderate    | ⭐⭐⭐⭐⭐ Easiest       |
| **Maintainability**   | ⭐⭐⭐⭐⭐ Best             | ⭐⭐⭐ Good                 | ⭐⭐ Fair          | ⭐⭐⭐⭐⭐ Best          |
| **OpenAI Compatible** | ✅ Yes                      | ✅ Yes                      | ✅ Yes             | ❌ No                    |
| **Operations**        | All (renumber, remove, fix) | All (renumber, remove, fix) | All                | Only renumber            |
| **Streaming Support** | ✅ Yes                      | ✅ Yes                      | ✅ Yes             | ❌ No                    |

---

## Supported Operations

All three formats support these operations via `/v1/chat/completions`:

### 1. Renumber Verses

**Keywords:** `renumber verses`, `renumber-verses`, `fix verse numbers`, `fix comment`

Renumbers verse comments sequentially (1, 2, 3, ...).

### 2. Remove All Comments

**Keywords:** `remove all comments`, `remove-all-comments`, `delete comment`, `strip comment`

Removes all comments from the code.

### 3. Fix Array Comments

**Keywords:** `fix array comments`, `fix-array-comments`, `add sequential comment`, `number comment`

Adds sequential comments to array elements.

---

## Recommendation

### 🏆 Best Choice: File-Based Format (`code_file`)

✨ **Use `code_file` for the ultimate experience:**

- ✅ **No JSON escaping** - Edit plain Swift files
- ✅ **Most readable** - Clean code in your editor
- ✅ **Easy to maintain** - Version control friendly
- ✅ **Reusable** - Same file for multiple requests
- ✅ **Less error-prone** - No escaping mistakes

**Example:**

```json
{
  "messages": [{ "role": "user", "content": "renumber verses" }],
  "code_file": "psalm68.swift",
  "model": "mixtral:8x7b"
}
```

### 2nd Choice: Direct Code Format (`code`)

Use when:

- Code is small
- Generated programmatically
- Quick one-off requests

### 3rd Choice: OpenAI Format (backward compatible)

- Automatically used by Continue extension
- Traditional OpenAI API format
- Code embedded in message content

---

## VS Code Continue Extension Compatibility

✅ **Continue works perfectly without any changes!**

Continue automatically uses the OpenAI-compatible format (code embedded in `content`), which is fully supported. When you use Continue:

1. **Select your code** in VS Code
2. **Use the command**: `/renumber-verses` or `/fix-array-comments`
3. Continue sends: `{"messages": [{"role": "user", "content": "@renumber-verses <your-code>"}]}`
4. The server automatically extracts and processes your code

**📖 See [CONTINUE_SETUP.md](CONTINUE_SETUP.md) for detailed Continue setup and usage guide.**

### Continue vs Direct API

| Aspect          | Continue Extension          | Direct API (curl)              |
| --------------- | --------------------------- | ------------------------------ |
| **Format**      | OpenAI compatible (content) | Can use `code` field (cleaner) |
| **Usage**       | Select code + command       | Construct JSON manually        |
| **Convenience** | ⭐⭐⭐⭐⭐ Automatic        | ⭐⭐⭐ Manual                  |
| **Flexibility** | Limited to Continue UI      | Full control over request      |

**Bottom line:** Use Continue for daily work in VS Code, use direct API calls for automation/scripting.
