# Continue Quick Start - 2 Minutes Setup

## ✅ Your Continue Setup Already Works!

**No server changes needed.** Just optimize your Continue config for best results.

---

## 📝 Simplified Continue Configuration

Copy this into your `.continue/config.json`:

```yaml
models:
  - name: local-assistant
    provider: "openai"
    model: "mixtral:8x7b"
    apiBase: "http://127.0.0.1:5000/v1"
    apiKey: "not-needed"
    temperature: 0.1
    default: true
    contextLength: 4096

customCommands:
  - name: "renumber-verses"
    prompt: "@renumber-verses"
    description: "Renumber verse comments sequentially"

  - name: "remove-comments"
    prompt: "@remove-all-comments"
    description: "Remove all comments from code"

  - name: "fix-array"
    prompt: "@fix-array-comments"
    description: "Add sequential comments to array"
```

---

## 🚀 Daily Workflow

### Renumber Verses (Most Common Use Case)

**In VS Code:**

1. **Select your Swift code:**

   ```swift
   private let psalm68 = [
       /* 1 */ "Benedictus Dominus...",
       /* 2 */ "Deus noster...",
       /* 14 */ "Regna terrae...",  // ❌ Wrong number
   ]
   ```

2. **Open Continue:** Press `Cmd+L` (Mac) or `Ctrl+L` (Windows/Linux)

3. **Type command:** `/renumber-verses`

4. **Press Enter** - Done! ✨

**Result:**

```swift
private let psalm68 = [
    /* 1 */ "Benedictus Dominus...",
    /* 2 */ "Deus noster...",
    /* 3 */ "Regna terrae...",  // ✅ Fixed!
]
```

---

## 🎯 All Available Commands

| Command            | What It Does                    | When to Use                               |
| ------------------ | ------------------------------- | ----------------------------------------- |
| `/renumber-verses` | Fix verse numbering (1→2→3→...) | Psalm/liturgical texts with wrong numbers |
| `/remove-comments` | Strip all `/* ... */` comments  | Clean up commented code                   |
| `/fix-array`       | Add `/* 1 */`, `/* 2 */`, etc.  | Number array elements sequentially        |

---

## 💡 Pro Tips

### ✅ DO:

- **Select complete declarations**: Include `private let text = [`
- **Use exact command names**: `/renumber-verses` (not `/renumber` or `/verses`)
- **Select before running**: Highlight code first, then run command

### ❌ DON'T:

- Don't add extra instructions: Just `/renumber-verses` (not `/renumber-verses please fix this`)
- Don't select partial arrays: Include opening `[` and closing `]`
- Don't edit the prompt in customCommands: Keep it simple with just the keyword

---

## 🔍 Behind the Scenes

When you run `/renumber-verses`, Continue sends this to your server:

```json
{
  "model": "mixtral:8x7b",
  "messages": [
    {
      "role": "user",
      "content": "@renumber-verses private let psalm68 = [...]"
    }
  ]
}
```

Your server:

1. Sees the `@renumber-verses` keyword ✅
2. Extracts your Swift code automatically ✅
3. Renumbers the verses ✅
4. Returns clean, formatted code ✅

**You don't need to do anything special - it just works!**

---

## 🐛 Troubleshooting

### Problem: Command not working

**Check:**

```bash
# 1. Is server running?
curl http://127.0.0.1:5000/health
# Should return: {"status": "ok"}

# 2. Check server logs
tail -f server_debug.log
# Look for "[DETECT] Renumber verses request: True"
```

**Fix:**

- Start server: `python src/coding_server.py`
- Verify Continue config has correct `apiBase`
- Try reloading Continue extension

### Problem: Getting chat response instead of code

**Likely cause:** Keyword not detected

**Fix:**

- Use exact keyword: `@renumber-verses` (with @)
- Or use slash command: `/renumber-verses` in Continue
- Check that custom command `prompt` field has: `"@renumber-verses"`

### Problem: Code not being processed

**Likely cause:** Selection issue

**Fix:**

- Select the **entire** variable declaration
- Include: `private let text = [...]` (not just the array)
- Don't select line numbers or extra whitespace

---

## 📊 Performance Tips

### Model Selection

**For Renumber/Remove/Fix operations:**

- `mixtral:8x7b` - Best accuracy, slower (~5-10s)
- `deepseek-coder:6.7b` - Good balance (~3-5s)
- `llama3.1:8b` - Faster but less reliable (~2-3s)

**Recommended:** Use `mixtral:8x7b` for liturgical texts (accuracy matters!)

### Speed Optimization

```yaml
models:
  - name: fast
    model: "deepseek-coder:6.7b"
    temperature: 0.1
    contextLength: 2048 # Smaller = faster for simple tasks

  - name: accurate
    model: "mixtral:8x7b"
    temperature: 0.1
    contextLength: 4096 # Larger for complex texts
    default: true
```

Switch in Continue: Type `@fast` or `@accurate` before your command.

---

## 🎬 Complete Example

**Scenario:** You have a psalm with incorrect verse numbering

**Code:**

```swift
private let psalm68 = [
    /* 1 */ "Benedictus Dominus die quotidie...",
    /* 2 */ "Deus noster, Deus salvos faciendi...",
    /* 3 */ "Verumtamen Deus confringet capita...",
    /* 14 */ "Regna terrae, cantate Deo...",        // ❌ Should be 4
    /* 15 */ "Psallite Deo, qui ascendit...",       // ❌ Should be 5
    /* 17 */ "Mirabilis Deus in sanctis suis..."   // ❌ Should be 6
]
```

**Steps:**

1. Click before `private`, drag to after `]` → Select all
2. `Cmd+L` → Continue opens
3. Type: `/renumber-verses` → Enter
4. Wait 3-10 seconds
5. ✨ Code is replaced with correct numbering

**Result:**

```swift
private let psalm68 = [
    /* 1 */ "Benedictus Dominus die quotidie...",
    /* 2 */ "Deus noster, Deus salvos faciendi...",
    /* 3 */ "Verumtamen Deus confringet capita...",
    /* 4 */ "Regna terrae, cantate Deo...",        // ✅ Fixed!
    /* 5 */ "Psallite Deo, qui ascendit...",       // ✅ Fixed!
    /* 6 */ "Mirabilis Deus in sanctis suis..."   // ✅ Fixed!
]
```

---

## 📚 More Help

- **Detailed Guide:** [CONTINUE_SETUP.md](CONTINUE_SETUP.md)
- **API Examples:** [API_EXAMPLES.md](API_EXAMPLES.md)
- **Quick Reference:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **What's New:** [WHATS_NEW.md](WHATS_NEW.md)

---

## ✅ Summary Checklist

- [ ] Server running: `python src/coding_server.py`
- [ ] Continue config updated with commands above
- [ ] Tested health check: `curl http://127.0.0.1:5000/health`
- [ ] Selected code and ran `/renumber-verses`
- [ ] Got correctly numbered output

**If all checked ✅ - you're ready to go!**
