"""
Topic Validator for WIT Library Chatbot.
Enforces strict library-only validation before calling the LLM.
Rejects unrelated questions with the exact mandated refusal message.
Handles ambiguous questions by prompting for clarification.
Permits library-related topics across all 10 categories.
"""

import re
from typing import Tuple, Dict, Any, Optional

EXACT_REFUSAL_MESSAGE = (
    "I'm sorry, but I don't answer questions unrelated to the library. "
    "I only answer questions about library-related topics, such as books, authors, "
    "library hours, borrowing policies, and library services. How can I help you with the library today?"
)

# 1. Polite Conversational Patterns
GREETING_PATTERNS = [
    r"^(hi|hello|hey|good\s+(morning|afternoon|evening|day)|kumusta|yo|greetings)[\s!.]*$",
    r"^(hello|hi|hey)\s+(there|bot|assistant|librarian)[\s!.]*$",
]

GOODBYE_PATTERNS = [
    r"^(bye|goodbye|see\s+you|cya|take\s+care|farewell|paalam)[\s!.]*$",
    r"^(that['’]?s\s+all|i['’]?m\s+done|talk\s+to\s+you\s+later)[\s!.]*$",
]

THANKS_PATTERNS = [
    r"^(thanks|thank\s+you|thank\s+you\s+very\s+much|salamat|maraming\s+salamat)[\s!.]*$",
    r"^(thanks|thank\s+you)\s+for\s+(the\s+help|your\s+help|helping)[\s!.]*$",
]

CAPABILITIES_PATTERNS = [
    r"(what\s+can\s+you\s+do|who\s+are\s+you|what\s+do\s+you\s+do|help\s+me\s+with\s+library|your\s+capabilities)",
]

# 2. Strong Unrelated Patterns (Immediate reject unless genuine library topic is also present)
UNRELATED_PATTERNS = [
    # Math calculations & equations
    r"\b(solve|calculate|compute|derivative|integral|equation)\b",
    r"\b\d+\s*[\+\-\*\/]\s*\d+",
    r"\b(pythagorean|algebraic|trigonometry|matrix\s+multiplication)\b",
    
    # Programming & Code writing prompts
    r"\b(write|create|debug|code|script)\s+(a\s+)?(python|java|c\+\+|javascript|html|css|sql|react|node|bash|powershell|c#|php|rust|ruby)\s+(program|code|script|function|app|class|algorithm)\b",
    r"\b(print\(|console\.log|function\(\)|def\s+[a-zA-Z_]|#include\s+<)",
    r"\b(how\s+to\s+code|how\s+to\s+program|leetcode|binary\s+search\s+tree|bubble\s+sort)\b",
    
    # Weather, food ordering, cooking
    r"\b(weather|temperature|forecast|rain\s+today|sunny\s+today)\b",
    r"\b(order\s+(food|pizza|burger|groceries|lunch|dinner|meal)|delivery|deliver\s+food|jollibee|mcdonalds)\b",
    r"\b(recipe|how\s+to\s+cook|ingredients\s+for|bake\s+a\s+cake|recipe\s+for)\b",
    
    # Entertainment, Pop Culture, Gaming, Sports
    r"\b(play\s+(minecraft|roblox|fortnite|valorant|dota|genshin|pubg|fifa))\b",
    r"\b(who\s+won\s+the\s+(game|match|super\s+bowl|world\s+cup|nba|championship))\b",
    r"\b(movie\s+review|box\s+office|celebrity\s+gossip|hollywood|netflix\s+series)\b",
    
    # Politics, Health/Medical diagnostics
    r"\b(who\s+to\s+vote\s+for|political\s+party|presidential\s+election|who\s+is\s+the\s+president\s+of)\b",
    r"\b(diagnose\s+my|symptoms\s+of|cure\s+for|medical\s+advice|medicine\s+for)\b",
]

# 3. Explicit Library & Academic Keywords / Patterns (All 10 Categories)
LIBRARY_KEYWORD_PATTERNS = {
    "library_hours": [
        r"\b(hours?|open|opens|close|closes|closing|schedule|operating|saturday|sunday|weekend|holiday|holidays)\b",
        r"\b(time\s+does\s+the\s+library|when\s+is\s+the\s+library\s+open)\b",
    ],
    "borrowing": [
        r"\b(borrow|borrowing|loan|loaned|lend|lending|keep\s+a\s+book|check\s*out|renew|renewal|renewing)\b",
        r"\b(return|returning|book\s*drop|due\s*date|how\s+many\s+books|how\s+long\s+can\s+i\s+keep)\b",
    ],
    "penalties": [
        r"\b(fine|fines|penalty|penalties|overdue|late\s+return|late\s+fee|lost\s+book|damaged\s+book|pay\s+a\s+penalty)\b",
        r"\b(what\s+happens\s+if\s+a\s+book\s+is\s+late|overdue\s+policy)\b",
    ],
    "library_card": [
        r"\b(library\s+card|student\s+id|id\s+card|membership|register|registration|account|identification|matriculation)\b",
        r"\b(do\s+i\s+need\s+my\s+student\s+id|how\s+can\s+i\s+get\s+a\s+library\s+card)\b",
    ],
    "catalog_availability": [
        r"\b(available|availability|in\s+stock|copy|copies|on\s+the\s+shelf|catalog|catalogue|opac|call\s+number|dewey|shelf\s+location)\b",
        r"\b(search\s+for\s+books?|find\s+a\s+book|look\s+up\s+a\s+book|where\s+can\s+i\s+search)\b",
        r"\b(reserve|reservation|hold|placed?\s+on\s+hold)\b",
    ],
    "citation_help": [
        r"\b(cite|citation|citing|apa|mla|ieee|chicago|reference\s+list|bibliography|referencing|in-text\s+citation)\b",
        r"\b(how\s+do\s+i\s+cite|cite\s+a\s+website|citation\s+help|citation\s+style)\b",
    ],
    "research_academic_assistance": [
        r"\b(research|academic\s+sources?|academic\s+journals?|scholarly|peer-reviewed|journal\s+articles?|journals?\s+online|thesis|theses|dissertation|database\s+search|boolean\s+search|literature\s+review)\b",
        r"\b(find\s+academic|search\s+for\s+journals?|how\s+(can|do)\s+i\s+find\s+journals?|research\s+materials?)\b",
    ],
    "book_information": [
        r"\b(book|books|novel|novels|author|authors|writer|writers|literature|textbook|textbooks|biography|isbn|genre|summary|plot|who\s+wrote|publisher|publication)\b",
        r"\b(pride\s+and\s+prejudice|shakespeare|george\s+orwell|1984|great\s+gatsby|to\s+kill\s+a\s+mockingbird|iliad|odyssey|noli\s+me\s+tangere|el\s+filibusterismo|jose\s+rizal)\b",
    ],
    "book_recommendations": [
        r"\b(recommend|recommendation|recommendations|suggest|suggestion|suggestions|good\s+reads?|reading\s+list|similar\s+books?)\b",
    ],
    "facilities_services": [
        r"\b(facilities|facility|study\s+area|study\s+room|reading\s+room|computer|computers|printer|printing|print|scan|scanning|photocopy|photocopying|wifi|wi-fi|internet)\b",
        r"\b(librarian|reference\s+desk|circulation\s+desk|where\s+is\s+the\s+library|library\s+location|library\s+address|located|address)\b",
        r"\b(does\s+the\s+library\s+have|library\s+have|library\s+provides?|library\s+offer)\b",
    ],
    "digital_resources": [
        r"\b(e-book|ebook|ebooks|audiobook|audiobooks|online\s+journal|student\s+portal|remote\s+access|electronic\s+resources|digital\s+resources?)\b",
        r"\b(access\s+(the\s+)?library.?s?\s+digital|digital\s+access|access\s+from\s+home|library\s+from\s+home|online\s+resources?|library\s+resources?\s+from\s+home)\b",
    ],
    "rules_policies": [
        r"\b(rule|rules|policy|policies|conduct|code\s+of\s+conduct|silence|quiet|bag\s+deposit|dress\s+code)\b",
        r"\b(can\s+(i|we)\s+(eat|drink|bring\s+food)|food\s+and\s+drinks?|no\s+food|allowed\s+to\s+eat)\b",
    ],
}

# Ambiguous single-word or short generic queries
AMBIGUOUS_QUERIES = {
    "help": "I'd be happy to help! Could you specify what library service or information you need (such as book search, hours, borrowing rules, or citation help)?",
    "info": "Are you looking for WIT Library hours, borrowing policies, facilities, or assistance finding books?",
    "information": "Are you looking for WIT Library hours, borrowing policies, facilities, or assistance finding books?",
    "where is it": "Could you please clarify what you're looking for? Are you looking for the library campus location, a specific facility, or book call number?",
    "where is it?": "Could you please clarify what you're looking for? Are you looking for the library campus location, a specific facility, or book call number?",
    "can you help me": "Certainly! How can I help you today? Are you looking for books, citation formatting, library hours, or borrowing limits?",
    "can you help me?": "Certainly! How can I help you today? Are you looking for books, citation formatting, library hours, or borrowing limits?",
    "how do i do that": "Could you clarify which library procedure you need help with, such as getting a library card, renewing a book, or citing a source?",
    "how do i do that?": "Could you clarify which library procedure you need help with, such as getting a library card, renewing a book, or citing a source?",
    "books": "Are you looking to search for books in the catalog, get book recommendations, or learn about borrowing rules?",
    "hours": "Are you asking about the operating hours of the WIT Library? We are open Monday-Friday 8:00 AM-6:00 PM and Saturday 9:00 AM-1:00 PM.",
}

# Explicit terms that signify a genuine library-domain context
GENUINE_LIBRARY_INDICATORS = [
    r"\b(library|book|books|author|novel|reading|catalog|circulation|borrow|loan|overdue|fine|fines|dewey|citation|apa|mla|thesis|librarian)\b"
]

def validate_user_query(query: str) -> Dict[str, Any]:
    """
    Validate whether a user question is library-related.
    Returns a dict with:
        status: 'ACCEPTED' | 'REJECTED' | 'AMBIGUOUS' | 'CONVERSATIONAL'
        intent: matched intent string
        answer: pre-computed answer if REJECTED, AMBIGUOUS, or CONVERSATIONAL
        is_mixed: bool indicating if both library and unrelated content were detected
    """
    raw_query = query.strip()
    lowered = raw_query.lower()

    if not raw_query:
        return {
            "status": "AMBIGUOUS",
            "intent": "ambiguous",
            "answer": "Please enter a question or topic related to the WIT Library, books, research, or library services.",
            "is_mixed": False,
        }

    # Check for direct ambiguous short phrases
    clean_punct = re.sub(r"[^\w\s]", "", lowered).strip()
    if lowered in AMBIGUOUS_QUERIES or clean_punct in AMBIGUOUS_QUERIES:
        clarification = AMBIGUOUS_QUERIES.get(lowered) or AMBIGUOUS_QUERIES.get(clean_punct)
        return {
            "status": "AMBIGUOUS",
            "intent": "ambiguous",
            "answer": clarification,
            "is_mixed": False,
        }

    # Check for conversational courtesy intents
    for p in GREETING_PATTERNS:
        if re.search(p, lowered):
            return {
                "status": "CONVERSATIONAL",
                "intent": "greeting",
                "answer": "Hello! Welcome to the WIT Library Chatbot. How can I assist you with library services, books, or research today?",
                "is_mixed": False,
            }

    for p in GOODBYE_PATTERNS:
        if re.search(p, lowered):
            return {
                "status": "CONVERSATIONAL",
                "intent": "goodbye",
                "answer": "Goodbye! Have a productive study session. Feel free to ask if you need help with the library again.",
                "is_mixed": False,
            }

    for p in THANKS_PATTERNS:
        if re.search(p, lowered):
            return {
                "status": "CONVERSATIONAL",
                "intent": "thanks",
                "answer": "You're very welcome! Let me know if there's anything else I can help you with regarding the library.",
                "is_mixed": False,
            }

    for p in CAPABILITIES_PATTERNS:
        if re.search(p, lowered):
            return {
                "status": "CONVERSATIONAL",
                "intent": "bot_capabilities",
                "answer": (
                    "I am the WIT Library Chatbot. I can assist you with library hours, location, "
                    "borrowing and return policies, overdue fines, library card registration, "
                    "catalog search guidance, research and citation assistance (APA, MLA), and book recommendations."
                ),
                "is_mixed": False,
            }

    # Check for Unrelated Patterns first
    unrelated_detected = False
    for un_pat in UNRELATED_PATTERNS:
        if re.search(un_pat, lowered):
            unrelated_detected = True
            break

    # Match Library Categories
    detected_intents = []
    for intent_name, patterns in LIBRARY_KEYWORD_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, lowered):
                detected_intents.append(intent_name)
                break

    has_genuine_library_indicator = any(re.search(ind, lowered) for ind in GENUINE_LIBRARY_INDICATORS)

    # If unrelated pattern was detected:
    if unrelated_detected:
        # If there is also genuine library context, it's a MIXED query
        if detected_intents and has_genuine_library_indicator:
            primary_intent = detected_intents[0]
            return {
                "status": "ACCEPTED",
                "intent": primary_intent,
                "answer": None,
                "is_mixed": True,
            }
        else:
            # Entirely unrelated -> REJECT immediately without calling LLM
            return {
                "status": "REJECTED",
                "intent": "fallback",
                "answer": EXACT_REFUSAL_MESSAGE,
                "is_mixed": False,
            }

    # Pure library intents detected
    if detected_intents:
        # Map to classic test intent names if applicable
        if "library_hours" in detected_intents:
            primary_intent = "library_hours"
        elif "borrowing" in detected_intents:
            primary_intent = "borrowing"
        elif "penalties" in detected_intents:
            primary_intent = "penalties"
        elif "library_card" in detected_intents:
            primary_intent = "library_card"
        elif "catalog_availability" in detected_intents:
            primary_intent = "catalog_availability"
        elif "citation_help" in detected_intents:
            primary_intent = "citation_help"
        else:
            primary_intent = detected_intents[0]

        return {
            "status": "ACCEPTED",
            "intent": primary_intent,
            "answer": None,
            "is_mixed": False,
        }

    # Check if query is extremely vague / ambiguous single word or short phrase
    words = [w for w in re.findall(r"\w+", lowered) if len(w) > 1]
    if len(words) <= 2:
        return {
            "status": "AMBIGUOUS",
            "intent": "ambiguous",
            "answer": (
                f"Could you please clarify your question about '{raw_query}'? "
                "For example, are you searching for books, research materials, or information on WIT Library services?"
            ),
            "is_mixed": False,
        }

    # General query with no library connection -> REJECTED
    return {
        "status": "REJECTED",
        "intent": "fallback",
        "answer": EXACT_REFUSAL_MESSAGE,
        "is_mixed": False,
    }
