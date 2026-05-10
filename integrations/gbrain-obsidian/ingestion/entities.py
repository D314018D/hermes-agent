import re

KNOWN_ENTITIES = [
    "Woolworths", "Coles", "Bunnings", "Dan Murphy", "FairPrice",
    "Hanshow", "Hermes", "GBrain", "Obsidian", "CartWise", "BuyBoost"
]

COMMON_WORDS = {
    "After", "And", "Attachments", "Certification", "Confirm", "Customer",
    "Extracted", "For", "From", "Need", "Open", "Put", "References", "Robot",
    "Summary", "Thanks", "The", "This", "To", "Untitled", "Voice"
}

def extract_entities(text: str):
    found = []
    lower = text.lower()
    for entity in KNOWN_ENTITIES:
        if entity.lower() in lower:
            found.append(entity)

    # Simple person-like pattern fallback, e.g. "Ben", "Travis"
    for match in re.findall(r"\b[A-Z][a-z]{2,}\b", text):
        if match not in found and match not in COMMON_WORDS:
            found.append(match)

    return sorted(set(found))
