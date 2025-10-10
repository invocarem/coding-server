# src/latin_morphology.py
import re
import json

def create_latin_verb_analysis_prompt(word):
    """Create AI prompt for Latin verb analysis"""
    return f"""Analyze this Latin word as a verb and return ONLY valid JSON:

Word: "{word}"

Respond with EXACTLY this JSON format, no other text:
{{
    "input": "{word}",
    "lemma": "lemma_form",
    "part_of_speech": "verb",
    "conjugation": 1,
    "infinitive": "infinitive_form",
    "perfect": "perfect_form", 
    "supine": "supine_form",
    "future": "future_form",
    "translations": {{
        "en": "english_translation_here",
        "la": "latin_lemma_here"
    }},
    "analysis": {{
        "identified_form": "form_type_here",
        "person": "1|2|3",
        "number": "singular|plural", 
        "tense": "present|future|perfect|imperfect|pluperfect|future_perfect",
        "mood": "indicative|subjunctive|imperative",
        "voice": "active|passive",
        "confidence": "high|medium|low"
    }}
}}

Rules:
- If it's a conjugated form (like 'rigabo'), identify the lemma and all grammatical features
- If it's already a lemma (like 'rigo'), provide all principal parts
- Only include fields you can confidently identify
- For confidence: use 'high' for clear patterns, 'medium' for educated guesses, 'low' for uncertain
- If not a verb, return part_of_speech as "unknown" and conjugation as null"""

def create_latin_noun_analysis_prompt(word):
    """Create AI prompt for Latin noun analysis"""
    return f"""Analyze this Latin word as a noun and return ONLY valid JSON:

Word: "{word}"

Respond with EXACTLY this JSON format, no other text:
{{
    "input": "{word}",
    "lemma": "lemma_form",
    "part_of_speech": "noun",
    "declension": 1,
    "gender": "masculine|feminine|neuter",
    "case": "nominative|genitive|dative|accusative|ablative|vocative",
    "number": "singular|plural",
    "translations": {{
        "en": "english_translation_here",
        "la": "latin_lemma_here"
    }},
    "analysis": {{
        "identified_form": "form_type_here",
        "confidence": "high|medium|low"
    }}
}}"""

def create_general_latin_analysis_prompt(word):
    """Create AI prompt for general Latin word analysis"""
    return f"""Analyze this Latin word and return ONLY valid JSON:

Word: "{word}"

Respond with EXACTLY this JSON format, no other text:
{{
    "input": "{word}",
    "lemma": "lemma_form",
    "part_of_speech": "verb|noun|adjective|adverb|conjunction|preposition|pronoun",
    "conjugation": 1,
    "declension": 1,
    "gender": "masculine|feminine|neuter",
    "infinitive": "infinitive_form",
    "perfect": "perfect_form",
    "future": "future_form",
    "translations": {{
        "en": "english_translation_here",
        "la": "latin_lemma_here"
    }},
    "analysis": {{
        "identified_form": "form_type_here",
        "case": "nominative|genitive|dative|accusative|ablative|vocative",
        "number": "singular|plural",
        "person": "1|2|3",
        "tense": "present|future|perfect|imperfect|pluperfect|future_perfect",
        "mood": "indicative|subjunctive|imperative", 
        "voice": "active|passive",
        "confidence": "high|medium|low"
    }}
}}

Only include fields you can confidently identify. Use null for unknown values."""

def extract_json_from_response(response):
    """Extract JSON from AI response, handling markdown and other formatting"""
    # Remove markdown code blocks
    cleaned = re.sub(r'```json\n?', '', response)
    cleaned = re.sub(r'\n?```', '', cleaned)
    cleaned = cleaned.strip()
    
    # Try to find JSON object
    json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    # If no JSON found, return error structure
    return {
        "input": "unknown",
        "lemma": "unknown",
        "part_of_speech": "unknown",
        "error": "Could not parse AI response as JSON",
        "raw_response": response[:500]  # First 500 chars for debugging
    }

def analyze_latin_word_with_ai(word, model='mistral:7b'):
    """Analyze Latin word using AI"""
    from ollama_client import call_ollama_smart
    
    # Clean the input
    word = word.strip().lower()
    
    # Choose prompt based on likely part of speech
    if looks_like_verb(word):
        prompt = create_latin_verb_analysis_prompt(word)
    elif looks_like_noun(word):
        prompt = create_latin_noun_analysis_prompt(word)
    else:
        prompt = create_general_latin_analysis_prompt(word)
    
    # Call AI
    response = call_ollama_smart(model, prompt)
    
    if response.startswith("Error:"):
        return {
            "input": word,
            "lemma": "unknown",
            "part_of_speech": "unknown",
            "error": response
        }
    
    # Parse the response
    result = extract_json_from_response(response)
    result['input'] = word  # Ensure input is preserved
    result['model_used'] = model
    
    return result

def looks_like_verb(word):
    """Simple heuristic to check if word looks like a verb"""
    verb_endings = ['o', 's', 't', 'mus', 'tis', 'nt', 'bo', 'bis', 'bit', 'bunt', 'vi', 'vit', 'ram', 'rim']
    return any(word.endswith(ending) for ending in verb_endings)

def looks_like_noun(word):
    """Simple heuristic to check if word looks like a noun"""
    noun_endings = ['a', 'us', 'um', 'is', 'es', 'em', 'ibus', 'orum', 'arum']
    return any(word.endswith(ending) for ending in noun_endings)

def analyze_latin_word(word, model='mistral:7b'):
    """Main function to analyze Latin word using AI"""
    return analyze_latin_word_with_ai(word, model)

def analyze_latin_text(text, model='mistral:7b'):
    """Analyze multiple Latin words in text"""
    words = re.findall(r'\b[a-zA-ZāēīōūĀĒĪŌŪ]+\b', text)
    analyses = []
    
    for word in words:
        if len(word) > 2:  # Ignore very short words
            analysis = analyze_latin_word(word, model)
            analyses.append(analysis)
    
    return {
        "original_text": text,
        "word_count": len(analyses),
        "analyses": analyses,
        "model_used": model
    }