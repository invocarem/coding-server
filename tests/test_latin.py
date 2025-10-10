import sys
import os
import json

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from latin_morphology import analyze_latin_word

# Test the function directly
result = analyze_latin_word("rigo")
print(json.dumps(result, indent=2))
