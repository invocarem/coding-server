# src/code_processor.py
import re

def format_prompt_for_remove_all_comments(code, language="swift"):
    """Prompt to remove ALL comments from code"""
    prompt = f"""You are a code formatter. Remove ALL comments completely from the code.

EXAMPLE INPUT:
private let text = [
    /* 1 */ "First item",
    /* 2 */ "Second item", /* Keep reading */
    /* 3 */ "Third item"
]

EXAMPLE OUTPUT:
private let text = [
    "First item",
    "Second item",
    "Third item"
]

RULES:
- Remove ALL /* ... */ style comments completely
- Remove ALL // style comments completely
- Do NOT convert /* */ to // - just remove them entirely
- Remove both number comments /* N */ and text comments /* text */
- Keep exact indentation and spacing
- Preserve all code exactly (only remove comments)
- OUTPUT: Wrap the code in Markdown code block, no explanations

CODE TO PROCESS:
{code}

OUTPUT:"""
    return prompt

def format_prompt_for_array_comments(code, language="swift"):
    """Enhanced prompt with examples to guide the model"""
    prompt = f"""You are a code formatter. Provide sequential /* number */ comments BEFORE each array element.

EXAMPLE INPUT:
private let arr = [
    /* 1 */ "First item",
    /* 2 */ "Second item",
    "Third item",
    /* 3 */ "Fourth item"
]

EXAMPLE OUTPUT:
private let arr = [
    /* 1 */ "First item",
    /* 2 */ "Second item",
    /* 3 */ "Third item"
    /* 4 */ "Fourth item"
]

RULES:
- Provide /* N */ BEFORE each element (N is from 1 sequentially)
- The last comment /* N */ should be the array length.
- IMPORTANT: Preserve all items exactly
- OUTPUT: Wrap the code in Markdown code block, no explanations

CODE TO PROCESS:
{code}

OUTPUT:"""
    return prompt

def clean_model_output(output, original_code):
    """Clean and extract the code from model output, preserving variable assignments"""
    if output.startswith("Error:"):
        return output
    
    # Keep markdown code blocks for better display in VS Code/Continue
    # cleaned = re.sub(r'```[\w]*\n?', '', output)
    # cleaned = re.sub(r'\n?```', '', cleaned)
    cleaned = output.strip()
    
    # Remove special tokens that Ollama sometimes generates
    # Pattern: <｜token｜> or <|token|> or similar special markers
    cleaned = re.sub(r'<[｜|][^｜|>]+[｜|]>', '', cleaned)
    cleaned = re.sub(r'<\|[^|>]+\|>', '', cleaned)
    
    # Remove any lines that don't look like code
    lines = cleaned.split('\n')
    code_lines = []
    for line in lines:
        # Skip lines with special characters or non-code content
        if any(char in line for char in ['<｜', '｜>', '<|', '|>']):
            continue
        # Skip empty explanatory lines
        if line.strip() and not line.strip().startswith(('Corrected', 'Output', 'Result', '---')):
            code_lines.append(line)
    
    cleaned = '\n'.join(code_lines)
    
    # Validate that comments are in the right position (before strings, not after)
    # Pattern: "string" /* N */ should be /* N */ "string"
    cleaned = re.sub(r'("(?:[^"\\]|\\.)*")\s*(\/\*\s*\d+\s*\*\/)', r'\2 \1', cleaned)
    
    # If the output looks like just an array but original had a variable assignment,
    # reconstruct the full assignment
    if cleaned.startswith('[') and '=' in original_code:
        # Extract the variable assignment part from original
        var_match = re.match(r'^([^=]+=)\s*\[', original_code, re.DOTALL)
        if var_match:
            var_part = var_match.group(1).strip()
            return f"{var_part} {cleaned}"
    
    return cleaned

def clean_removed_comments_output(output, original_code):
    """Clean output from comment removal, ensuring all comments are truly removed"""
    # First apply standard cleaning
    cleaned = clean_model_output(output, original_code)
    
    if cleaned.startswith("Error:"):
        return cleaned
    
    # Extract code from markdown blocks to work with it
    code_only = re.sub(r'```[\w]*\n?', '', cleaned)
    code_only = re.sub(r'\n?```', '', code_only)
    code_only = code_only.strip()
    
    # Force remove any remaining /* ... */ style comments
    code_only = re.sub(r'/\*.*?\*/', '', code_only)
    
    # Force remove any remaining // style comments (to end of line)
    code_only = re.sub(r'//.*$', '', code_only, flags=re.MULTILINE)
    
    # Clean up extra whitespace that might be left behind
    lines = code_only.split('\n')
    cleaned_lines = [line.rstrip() for line in lines]  # Remove trailing whitespace
    code_only = '\n'.join(cleaned_lines)
    
    # Re-wrap in markdown if original had it
    if '```' in cleaned:
        # Extract language tag if present
        lang_match = re.search(r'```(\w+)', cleaned)
        lang = lang_match.group(1) if lang_match else 'swift'
        return f"```{lang}\n{code_only}\n```"
    
    return code_only