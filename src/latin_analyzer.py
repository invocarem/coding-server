# src/latin_analyzer.py
import re

def create_latin_analysis_prompt(text, language="latin"):
    """Create specialized prompt for classical language analysis"""
    return f"""You are an expert in {language} linguistics. Analyze this text grammatically:

"{text}"

Provide a structured analysis with:

WORD ANALYSIS:
- For each word: dictionary form (lemma), grammatical form, translation
- Include: case, number, gender, tense, mood, voice, person as applicable

SYNTAX ANALYSIS:
- Sentence structure and syntax  
- Grammatical constructions used
- Clause relationships

TRANSLATION:
- Literal word-for-word translation
- Fluent English translation

CONTEXT:
- Brief note on usage or context if relevant

Analysis:"""


def create_translation_prompt(text, source_lang, target_lang):
    """Create prompt for translation with analysis"""
    return f"""Translate this {source_lang} text to {target_lang} and provide grammatical analysis:

Text: "{text}"

Provide:
1. Literal translation (word-for-word)
2. Fluent translation (natural English)
3. Word-by-word analysis (lemma, grammatical form, grammar notes)
4. Overall grammatical structure

Translation and Analysis:"""

def extract_latin_words(text):
    """Extract individual Latin words for analysis"""
    # Simple Latin word extraction - you can enhance this
    words = re.findall(r'\b[a-zA-ZāēīōūĀĒĪŌŪ]+\b', text)
    return [word for word in words if len(word) > 1]