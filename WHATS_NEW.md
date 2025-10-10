# What's New: Optional `code` Field Support

## TL;DR

✅ **VS Code Continue users: No action needed!** Everything works exactly as before.

✅ **API users: You can now use the cleaner `code` field** (optional, backward compatible).

---

## What Changed?

### Before (Still Works!)

```json
{
  "model": "mixtral:8x7b",
  "messages": [
    {
      "role": "user",
      "content": "renumber verses for the following code: private let text = [...]"
    }
  ]
}
```

### After (New Option!)

```json
{
  "model": "mixtral:8x7b",
  "messages": [
    {
      "role": "user",
      "content": "renumber verses"
    }
  ],
  "code": "private let text = [...]"
}
```

---

## Why This Matters

### Problem We Solved

You had **two different API formats**:

1. `/api/renumber-verses` - Expected `code` field ✅ Clean
2. `/v1/chat/completions` - Expected code in `content` ❌ Mixed with instructions

This was inconsistent and made API calls harder to construct.

### Solution

Now `/v1/chat/completions` accepts **both formats**:

| Format               | Status         | Use Case                         |
| -------------------- | -------------- | -------------------------------- |
| Code in `content`    | ✅ Still works | Continue, backward compatibility |
| Code in `code` field | ✅ New option  | Direct API calls, scripts        |

---

## What You Need to Do

### If You Use VS Code Continue:

**Nothing!** Continue automatically uses the `content` format, which is fully supported.

### If You Use Direct API Calls:

**Optional:** You can now use the cleaner `code` field format for easier JSON construction.

**Your existing scripts still work** - no breaking changes.

---

## Comparison: Old vs. New

### Example: Your psalm_request.json

**Old Format (Still Works):**

```json
{
  "model": "mixtral:8x7b",
  "messages": [
    {
      "role": "user",
      "content": "renumber verses for the following code: private let text = [\n    /* 1 */ \"Benedictus...\",\n    /* 2 */ \"Deus noster...\"\n]"
    }
  ]
}
```

**New Format (Recommended for API):**

```json
{
  "model": "mixtral:8x7b",
  "messages": [
    {
      "role": "user",
      "content": "renumber verses"
    }
  ],
  "code": "private let text = [\n    /* 1 */ \"Benedictus...\",\n    /* 2 */ \"Deus noster...\"\n]"
}
```

---

## Benefits of the New Format

### For API Users:

✅ **Cleaner JSON** - Separate intent from data
✅ **Easier to Construct** - No need to escape code in content string
✅ **More Consistent** - Matches `/api/renumber-verses` format
✅ **Better Logging** - Server logs show clear separation

### For Continue Users:

✅ **No Changes Needed** - Keep using commands as before
✅ **Automatic Handling** - Continue's format is auto-detected
✅ **Full Compatibility** - All features work identically

---

## Technical Details

### How the Server Handles Requests

```python
# Server logic (simplified)
data = request.get_json()
messages = data.get('messages', [])
direct_code = data.get('code', None)  # New!

if direct_code:
    # Use the clean 'code' field
    code_to_process = direct_code
else:
    # Extract code from message content (backward compatible)
    user_message = messages[0]['content']
    code_to_process = extract_code_from_content(user_message)
```

### Supported Operations

All three operations now support both formats:

1. **Renumber Verses** - Fix verse comment numbering
2. **Remove All Comments** - Strip all comments
3. **Fix Array Comments** - Add sequential comments

---

## Migration Guide

### If You Want to Use the New Format:

**Step 1:** Update your request JSON files:

```json
{
  "messages": [{ "role": "user", "content": "<operation-keyword>" }],
  "code": "<your-code-here>",
  "model": "mixtral:8x7b"
}
```

**Step 2:** Use operation keywords:

- `"renumber verses"` or `"@renumber-verses"`
- `"remove all comments"` or `"@remove-all-comments"`
- `"fix array comments"` or `"@fix-array-comments"`

**Step 3:** Test with curl:

```bash
curl -X POST http://127.0.0.1:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d @your_request.json \
  -o output.log
```

### If You Want to Keep Using the Old Format:

**Nothing to change!** Your existing requests work exactly as before.

---

## Files Updated

| File                   | Changes                                             |
| ---------------------- | --------------------------------------------------- |
| `src/coding_server.py` | Added `code` field handling in all three operations |
| `psalm_request.json`   | Updated to use new cleaner format                   |
| `API_EXAMPLES.md`      | Added comprehensive API format examples             |
| `CONTINUE_SETUP.md`    | Detailed Continue configuration guide               |
| `QUICK_REFERENCE.md`   | Quick lookup for all usage patterns                 |
| `README.md`            | Updated Continue section with simplified config     |

---

## Examples

### 1. Renumber Verses (New Format)

```bash
curl -X POST http://127.0.0.1:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "renumber verses"}],
    "code": "private let text = [\n  /* 1 */ \"First\",\n  /* 3 */ \"Second\"\n]",
    "model": "mixtral:8x7b"
  }'
```

### 2. Remove Comments (New Format)

```bash
curl -X POST http://127.0.0.1:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "remove all comments"}],
    "code": "let x = [\n  /* comment */ \"value\"\n]",
    "model": "mixtral:8x7b"
  }'
```

### 3. Continue (No Changes)

```yaml
# .continue/config.json - Works as before!
customCommands:
  - name: "renumber-verses"
    prompt: "@renumber-verses"
```

---

## Questions?

### Q: Do I need to update my Continue configuration?

**A:** No! Continue works perfectly with the existing format.

### Q: Will my existing API scripts break?

**A:** No! The old format (code in `content`) is fully supported.

### Q: Should I migrate to the new format?

**A:** Optional. The new format is cleaner for direct API calls, but migration is not required.

### Q: Can I mix both formats?

**A:** Yes! If you provide both `code` field and code in `content`, the `code` field takes priority.

### Q: What if I don't provide either?

**A:** The server will try to extract code from the content using pattern matching (markdown blocks, variable assignments, etc.).

---

## Summary

🎉 **This is a quality-of-life improvement, not a breaking change.**

- ✅ Continue users: No action needed
- ✅ API users: Optional cleaner format available
- ✅ All existing code: Works without changes
- ✅ Better consistency: `/v1/chat/completions` now more similar to `/api/renumber-verses`

**Your development workflow remains unchanged unless you choose to adopt the new format!**
