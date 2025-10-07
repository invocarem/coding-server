# src/code_processor.py
import re

def format_prompt_for_array_comments(code, language="swift"):
    """Enhanced prompt with examples to guide the model"""
    prompt = f"""You are a code formatter. Add sequential /* number */ comments BEFORE each array element.

EXAMPLE INPUT:
private let arr = [
    "First item",
    "Second item",
    "Third item"
]

EXAMPLE OUTPUT:
private let arr = [
    /* 1 */ "First item",
    /* 2 */ "Second item",
    /* 3 */ "Third item"
]

RULES:
- Add /* N */ BEFORE each element (not after)
- Number from 1 sequentially
- Keep exact indentation
- Preserve all text exactly
- Output ONLY the code, no explanations

CODE TO PROCESS:
{code}

OUTPUT:"""
    return prompt

def clean_model_output(output, original_code):
    """Clean and extract the code from model output, preserving variable assignments"""
    if output.startswith("Error:"):
        return output
    
    # Remove markdown code blocks
    cleaned = re.sub(r'```[\w]*\n?', '', output)
    cleaned = re.sub(r'\n?```', '', cleaned)
    cleaned = cleaned.strip()
    
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