# src/latin_morphology.py
import re
import json

def analyze_latin_verb(word):
    """
    Analyze a Latin verb and return structured morphological data
    Supports both lemmas and conjugated forms
    """
    
    # Common Latin verb patterns
    verb_patterns = {
        'first_conj': {
            'infinitive': r'are$',
            'present_1sg': r'o$',
            'present_2sg': r'as$',
            'present_3sg': r'at$',
            'future_1sg': r'abo$',
            'future_2sg': r'abis$', 
            'future_3sg': r'abit$',
            'perfect_1sg': r'avi$',
            'perfect_3sg': r'avit$'
        },
        'second_conj': {
            'infinitive': r'ēre$',
            'present_1sg': r'eō$',
            'future_1sg': r'ēbo$',
            'perfect_1sg': r'ui$'
        },
        'third_conj': {
            'infinitive': r'ere$',
            'present_1sg': r'o$',
            'future_1sg': r'am$',
            'perfect_1sg': r'si$|xi$'
        },
        'fourth_conj': {
            'infinitive': r'īre$',
            'present_1sg': r'io$',
            'future_1sg': r'iam$',
            'perfect_1sg': r'ivi$'
        }
    }
    
    # Common Latin verbs database (you can expand this)
    verb_database = {
        'rigo': {
            'lemma': 'rigo',
            'conjugation': 1,
            'infinitive': 'rigare',
            'present_1sg': 'rigo',
            'present_2sg': 'rigas', 
            'present_3sg': 'rigat',
            'future_1sg': 'rigabo',
            'future_2sg': 'rigabis',
            'future_3sg': 'rigabit',
            'perfect_1sg': 'rigavi',
            'perfect_3sg': 'rigavit',
            'supine': 'rigatum',
            'translations': {
                'en': 'drench, water, irrigate',
                'la': 'rigo'
            }
        },
        'amo': {
            'lemma': 'amo',
            'conjugation': 1,
            'infinitive': 'amare',
            'future_1sg': 'amabo',
            'perfect_1sg': 'amavi',
            'translations': {
                'en': 'love, like',
                'la': 'amo'
            }
        },
        'moneo': {
            'lemma': 'moneo', 
            'conjugation': 2,
            'infinitive': 'monēre',
            'future_1sg': 'monēbo',
            'perfect_1sg': 'monui',
            'translations': {
                'en': 'warn, advise',
                'la': 'moneo'
            }
        }
    }
    
    # First, check if it's a known verb in our database
    if word in verb_database:
        return create_verb_response(verb_database[word], 'lemma')
    
    # If not, try to analyze the form
    analysis = analyze_verb_form(word, verb_patterns, verb_database)
    if analysis:
        return analysis
    
    # If we can't analyze it automatically, use Ollama for analysis
    return analyze_with_ollama(word)

def analyze_verb_form(word, patterns, database):
    """Analyze verb form to find lemma and conjugation"""
    
    # Check for future tense forms
    if word.endswith('bo'):  # First conjugation future
        lemma = word[:-2] + 'o'
        if lemma in database:
            return create_verb_response(database[lemma], 'future_1sg', word)
    
    elif word.endswith('bis'):  # Future 2nd person
        lemma = word[:-3] + 'o'
        if lemma in database:
            return create_verb_response(database[lemma], 'future_2sg', word)
    
    elif word.endswith('bit'):  # Future 3rd person  
        lemma = word[:-3] + 'o'
        if lemma in database:
            return create_verb_response(database[lemma], 'future_3sg', word)
    
    # Check for perfect tense
    elif word.endswith('vi'):  # First conjugation perfect
        lemma = word[:-2] + 'o'
        if lemma in database:
            return create_verb_response(database[lemma], 'perfect_1sg', word)
    
    elif word.endswith('vit'):  # Perfect 3rd person
        lemma = word[:-3] + 'o' 
        if lemma in database:
            return create_verb_response(database[lemma], 'perfect_3sg', word)
    
    return None

def create_verb_response(verb_data, form_type, input_form=None):
    """Create standardized verb response"""
    response = {
        "input": input_form or verb_data['lemma'],
        "lemma": verb_data['lemma'],
        "part_of_speech": "verb",
        "conjugation": verb_data['conjugation'],
        "infinitive": verb_data['infinitive'],
        "perfect": verb_data.get('perfect_1sg', ''),
        "future": verb_data.get('future_1sg', ''),
        "translations": verb_data['translations'],
        "analysis": {
            "input_form": input_form or "lemma",
            "identified_form": form_type,
            "confidence": "high"
        }
    }
    
    # Add specific form information
    if input_form and form_type in verb_data:
        response['identified_as'] = {
            "form": form_type,
            "value": verb_data[form_type]
        }
    
    return response

def analyze_with_ollama(word):
    """Use Ollama to analyze unknown Latin words"""
    prompt = f"""Analyze this Latin word and provide JSON output: "{word}"

Respond ONLY with valid JSON in this exact format:
{{
    "input": "{word}",
    "lemma": "lemma_form",
    "part_of_speech": "verb|noun|adjective|etc",
    "conjugation": 1,
    "infinitive": "infinitive_form", 
    "perfect": "perfect_form",
    "future": "future_form",
    "translations": {{
        "en": "english translation",
        "la": "latin translation"
    }},
    "analysis": {{
        "input_form": "identified_form_type",
        "confidence": "high|medium|low"
    }}
}}

If it's not a verb, set conjugation to null.
Only include fields you can confidently identify."""

    # This would call your Ollama function
    # For now, return a placeholder
    return {
        "input": word,
        "lemma": "unknown",
        "part_of_speech": "unknown",
        "conjugation": None,
        "infinitive": "",
        "perfect": "",
        "future": "", 
        "translations": {
            "en": "unknown",
            "la": "unknown"
        },
        "analysis": {
            "input_form": "unknown",
            "confidence": "low",
            "note": "Requires Ollama analysis"
        }
    }

def analyze_latin_word(word):
    """Main function to analyze any Latin word"""
    # Clean the input
    word = word.strip().lower()
    
    # First try verb analysis
    result = analyze_latin_verb(word)
    
    # If not a verb or unknown, expand to other parts of speech
    if result['lemma'] == 'unknown':
        # You can add noun, adjective analysis here
        result = analyze_with_ollama(word)
    
    return result