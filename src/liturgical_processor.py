import re
import json
import logging
from ollama_client import call_ollama_smart
from code_processor import clean_model_output
logger = logging.getLogger(__name__)

def renumber_verses_with_ai(code, model="mixtral:8x7b"):
    """Ultra-simple prompt that might actually work"""
    prompt = f"""

You are an expert Swift code formatter.
Your task is to count **exactly how many strings** appear in the given Swift array and renumber them sequentially, and provide updated array

### RULES
1. Do not generate Swift function code to format the array.
2. Do not merge or split string in the array.
3. The Comment /* number */ before any string is misleading, don't use it to count
4. The `.` or `;` inside the string is misleading, don't use it to count
5. The blank line inside the array do not count 1
6, For array in swift, the spliter is comma, so a string that ends with double quote and one comma followed should c
ount 1
7. The last string (that ends with double quote `"` which followed with `]` with no comma) should count 1.
8. In the output, every string should start with a /* number */ comment
9. Every 5 strings, insert a blank line to make it easier to read.
10. No explanations, notes, but markdown code block only.

### EXAMPLE
** INPUT **
private let text = [
  /* 1 */ "string a",
   "string b",
  /* 2 */ "string c"

]


** Expected OUTPUT **
```
private let text = [
  /* 1 */ "string a",
  /* 2 */ "string b",
  /* 3 */ "string c",
]

### Now, process this input    
{code}

"""
    logger.info(f"[RENUMBER] ollama {model}")
    result = call_ollama_smart(model, prompt)

    logger.info(f"[RENUMBER] Received response from Ollama")
    logger.debug(f"[RENUMBER] Raw response length: {len(result)} chars")
    logger.debug(f"[RENUMBER] Raw response first 200 chars: {result[:200]}")
    logger.debug(f"[RENUMBER] Raw response last 200 chars: {result[-200:]}")

    return clean_model_output(result, code)


def parse_verses_from_array(code):
    """Extract verses from Swift array code"""
    # Find all string literals in the array
    string_matches = re.findall(r'"(.*?)"(?=\s*,?\s*(?:\/\*|\n|$))', code, re.DOTALL)
    return [match for match in string_matches if match.strip()]

def analyze_verse_structure_with_ai(verses):
    """Use AI to understand verse boundaries and semantics"""
    verses_text = "\n".join([f"{i+1}. {verse}" for i, verse in enumerate(verses)])
    
    prompt = f"""
Analyze these Latin psalm verses and identify proper verse boundaries. 
Some verses may span multiple string literals in the code array.

VERSES:
{verses_text}

Return JSON analysis with this structure:
{{
    "verse_boundaries": [
        {{
            "verse_number": 1,
            "content": "full verse text",
            "array_lines": [0]  // indices of array elements that form this verse
        }}
    ],
    "total_complete_verses": 17,
    "notes": "any observations about verse structure"
}}

Focus on:
1. Semantic completeness - each verse should make sense as a complete thought
2. Liturgical structure - verses should follow proper psalm division
3. Multi-line verses - identify which array lines belong together
"""
    
    try:
        response = call_ollama_smart("deepseek-coder:6.7b", prompt)
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return create_fallback_analysis(verses)
    except:
        return create_fallback_analysis(verses)

def create_fallback_analysis(verses):
    """Fallback analysis when AI fails"""
    return {
        "verse_boundaries": [
            {
                "verse_number": i + 1,
                "content": verse,
                "array_lines": [i]
            } for i, verse in enumerate(verses)
        ],
        "total_complete_verses": len(verses),
        "notes": "Used fallback analysis - each array line treated as separate verse"
    }

def adjust_verses_to_count(verses, analysis, target_count):
    """Restructure verses to target count using AI guidance"""
    current_structure = json.dumps(analysis['verse_boundaries'], indent=2)
    
    prompt = f"""
Restructure these {len(analysis['verse_boundaries'])} Latin psalm verses into exactly {target_count} verses 
following proper liturgical division. PRESERVE ALL TEXT CONTENT - do not remove or add any Latin text.

CURRENT STRUCTURE:
{current_structure}

TARGET: {target_count} verses

Return JSON with the new structure:
{{
    "new_verses": [
        {{
            "verse_number": 1,
            "content": "full reconstructed verse text",
            "source_lines": [0, 1]  // which original array lines were used
        }}
    ],
    "explanation": "how verses were restructured"
}}

RULES:
1. Preserve ALL original Latin text
2. Create exactly {target_count} verses
3. Maintain semantic coherence
4. Follow typical psalm verse length patterns
5. Split long verses or merge short ones appropriately
"""
    
    try:
        response = call_ollama_smart("deepseek-coder:6.7b", prompt)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return create_adjusted_fallback(verses, target_count)
    except:
        return create_adjusted_fallback(verses, target_count)

def create_adjusted_fallback(verses, target_count):
    """Fallback when verse adjustment fails"""
    return {
        "new_verses": [
            {"verse_number": i+1, "content": verse, "source_lines": [i]} 
            for i, verse in enumerate(verses)
        ],
        "explanation": "AI adjustment failed - using original structure"
    }