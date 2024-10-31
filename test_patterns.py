import re

def create_bonus(bonus_text):
    # Reformat sentence
    bonus_text = bonus_text.lower().strip("• ").replace(', and ', ', ')

    # Patterns to capture different structures
    patterns = [
        r'(\b\w+(?:\s*\w*)?(?:,\s*\w+(?:\s*\w*)?)*(?:\s*,?\s+|\s+and\s+)?\w+(?:\s*\w*)?)\s+(?:move|are)\s+(-?\d+%)\s+(faster|slower)',
        r'(\b\w+(?:\s*\w*)?(?:,\s*\w+(?:\s*\w*)?)*(?:\s*,?\s+|\s+and\s+)?\w+(?:\s*\w*)?)\s*(?:\(except\s+([\w\s,]+)\))?\s+costs?\s+(-?\d+%?)\s*(less|more|faster|slower|cheaper|none)?\s*(wood|gold|stone|food)?(?:\s+starting in the\s+(dark|feudal|castle|imperial)\s+age)?',
        r'((?:\b\w+\s*\w*\b)(?:[\s,]*and\s+\b\w+\s*\w*)*)\s*(?:\(except\s+([\w\s,]+)\))?\s+([+-]?\d+/?\d*%?)\s*(\w+)?\s*(?:in\s+(dark|feudal|castle|imperial)(?:\s+and\s+(dark|feudal|castle|imperial))*)?',
    ]

    for i, pattern in enumerate(patterns):
        match = re.search(pattern, bonus_text, re.IGNORECASE)
        if match:
            groups = list(match.groups())

            # Separate units by commas and "and"
            units = re.split(r',\s*|\s+and\s+', groups[0]) if groups[0] else []
            groups[0] = units  # Replace with list of units

            # Format exceptions if present
            if groups[1]:
                exceptions = [f"({item.strip()})" for item in re.split(r',\s*|\s+and\s+', groups[1])]
                groups[1] = ', '.join(exceptions)
            
            print(f"Pattern {i}:", tuple(groups))
            break
    else:
        print("No match found.")

# Test example
create_bonus(rf'• Archers, villagers, and infantry are 15% faster')
'''create_bonus('• Buildings cost -50% less wood starting in the Castle Age')
create_bonus('• Buildings (except houses) cost -50% wood starting in the Castle Age')
create_bonus('• Buildings and mule carts cost -50% wood starting in the Castle Age')
create_bonus('• Buildings and mule carts (except houses and town centers) cost -50% wood starting in the Castle Age')
create_bonus('• Buildings, houses, mule carts (except houses, monasteries and town centers) cost -50% wood starting in the Castle Age')'''
#create_bonus("Foot archers, villagers, and archers (except skirmishers) +1 range in Castle and Imperial Age (+2 total)")