import json
import re
from typing import List, Dict, Any
from backend.config import settings

def load_dataset(entity_type: str) -> List[Dict[str, Any]]:
    """Loads the dataset file based on the entity type."""
    file_map = {
        "supplier": "suppliers.json",
        "professional": "professionals.json",
        "opportunity": "opportunities.json"
    }
    
    filename = file_map.get(entity_type.lower())
    if not filename:
        raise ValueError(f"Invalid entity type: {entity_type}")
        
    filepath = settings.DATASET_DIR / filename
    if not filepath.exists():
        return []
        
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def is_instruction_phrase(text: str) -> bool:
    if not text:
        return False
    t_lower = text.lower()
    injection_indicators = [
        "ignore all", "ignore constraint", "ignore check", "override", 
        "rank first", "rank sup-", "system instruction", "system prompt",
        "act as", "you are", "ignore the above", "ignore the below",
        "do not check", "bypass"
    ]
    return any(indicator in t_lower for indicator in injection_indicators)

def detect_prompt_injection(entity: Dict[str, Any]) -> bool:
    for k, v in entity.items():
        if isinstance(v, str):
            if is_instruction_phrase(v):
                return True
        elif isinstance(v, list):
            for x in v:
                if isinstance(x, str) and is_instruction_phrase(x):
                    return True
    return False

def clean_entity_text(val: Any) -> Any:
    """If a field contains prompt injection, we ignore it during search/ranking."""
    if isinstance(val, str):
        if is_instruction_phrase(val):
            return ""
        return val
    elif isinstance(val, list):
        return [clean_entity_text(x) for x in val if clean_entity_text(x)]
    return val

def get_stem(word: str) -> str:
    w = word.lower().strip()
    if w.endswith("s") and not w.endswith("ss"):
        w = w[:-1]
    for suffix in ["es", "ed", "ing", "er", "ers", "able", "ability", "grade"]:
        if w.endswith(suffix) and len(w) - len(suffix) >= 4:
            w = w[:-len(suffix)]
    return w

SYNONYMS = {
    "biodegradable": ["compostable", "eco-friendly", "sustainable", "green", "organic", "pla"],
    "compostable": ["biodegradable", "eco-friendly", "sustainable", "green"],
    "eco-friendly": ["biodegradable", "compostable", "sustainable", "green"],
    "sustainable": ["biodegradable", "compostable", "eco-friendly", "green"],
    "green": ["biodegradable", "compostable", "eco-friendly", "sustainable"],
    "food-grade": ["food grade", "fda", "clean", "safe", "iso-22000"],
    "container": ["box", "cup", "packaging", "pack", "wrap", "wrapper", "bag"],
    "packaging": ["container", "box", "cup", "wrap", "wrapper", "bag"],
    "professional": ["developer", "engineer", "specialist", "expert"],
    "developer": ["professional", "engineer", "specialist", "expert"],
    "engineer": ["professional", "developer", "specialist", "expert"],
    "fastapi": ["python", "backend", "api"],
    "react": ["javascript", "frontend", "web"],
    "python": ["fastapi", "backend", "api"],
    "javascript": ["react", "frontend", "web"]
}

def is_synonym(w1: str, w2: str) -> bool:
    w1_clean, w2_clean = w1.lower().strip(), w2.lower().strip()
    if w1_clean == w2_clean:
        return True
    if w1_clean in SYNONYMS and w2_clean in SYNONYMS[w1_clean]:
        return True
    if w2_clean in SYNONYMS and w1_clean in SYNONYMS[w2_clean]:
        return True
    return False

def search_entities(entity_type: str, query_str: str, entity_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Search JSON dataset for matches based on keyword queries or direct entity name lookups.
    Uses tokenization, punctuation removal, and stopwords filtering.
    Matches entities that have at least one overlapping keyword with the query.
    If entity_name is provided, retrieves the matching record directly by name.
    """
    entities = load_dataset(entity_type)
    
    if entity_name:
        name_lower = entity_name.lower().strip()
        # 1. Exact match
        exact_matches = []
        for e in entities:
            name = e.get("name") or e.get("title")
            if name and name.lower().strip() == name_lower:
                exact_matches.append(e)
        if exact_matches:
            return exact_matches
            
        # 2. Fuzzy prefix / substring matches
        fuzzy_matches = []
        for e in entities:
            name = e.get("name") or e.get("title")
            if name:
                name_val = name.lower()
                if name_lower in name_val or name_val in name_lower:
                    fuzzy_matches.append(e)
        if fuzzy_matches:
            return fuzzy_matches
            
        # 3. Word matches
        word_matches = []
        query_words = re.findall(r'\w+', name_lower)
        for e in entities:
            name = e.get("name") or e.get("title")
            if name:
                name_words = re.findall(r'\w+', name.lower())
                if any(w.startswith(qw) or qw.startswith(w) for w in name_words for qw in query_words if len(qw) > 3 and len(w) > 3):
                    word_matches.append(e)
        return word_matches

    if not query_str or query_str.strip() == "":
        return entities
        
    # Punctuation cleaning and tokenization
    raw_tokens = re.findall(r'\w+', query_str.lower())
    
    stopwords = {
        "find", "search", "need", "get", "want", "supplier", "suppliers", 
        "professional", "professionals", "opportunity", "opportunities", 
        "for", "in", "with", "and", "a", "an", "the", "to", "of", "about",
        "please", "company", "we", "need"
    }
    
    query_keywords = [token for token in raw_tokens if token not in stopwords]
    
    if not query_keywords:
        return entities
        
    results = []
    for entity in entities:
        # Build search fields (filtering out prompt injections)
        search_fields = []
        
        if entity_type == "supplier":
            search_fields.append(clean_entity_text(entity.get("name", "")))
            search_fields.append(clean_entity_text(entity.get("location", "")))
            search_fields.append(clean_entity_text(entity.get("industry", "")))
            search_fields.extend(clean_entity_text(entity.get("products", [])))
        elif entity_type == "professional":
            search_fields.append(clean_entity_text(entity.get("name", "")))
            search_fields.append(clean_entity_text(entity.get("location", "")))
            search_fields.extend(clean_entity_text(entity.get("skills", [])))
        elif entity_type == "opportunity":
            search_fields.append(clean_entity_text(entity.get("title", "")))
            search_fields.append(clean_entity_text(entity.get("location", "")))
            search_fields.extend(clean_entity_text(entity.get("required_skills", [])))
            
        entity_text = " ".join([str(field) for field in search_fields if field])
        entity_tokens = set(re.findall(r'\w+', entity_text.lower()))
        
        # Calculate weighted keyword relevance
        total_relevance = 0.0
        matched_kws = []
        
        for kw in query_keywords:
            kw_score = 0
            is_matched = False
            for token in entity_tokens:
                if kw == token:
                    kw_score = max(kw_score, 5)
                    is_matched = True
                elif get_stem(kw) == get_stem(token):
                    kw_score = max(kw_score, 3)
                    is_matched = True
                elif is_synonym(kw, token):
                    kw_score = max(kw_score, 2)
                    is_matched = True
            
            if is_matched:
                matched_kws.append(kw)
                total_relevance += kw_score
                
        # Determine which fields matched
        matched_flds = []
        for field_name in ["products", "certifications", "location", "capacity", "rating", "skills", "required_skills", "title"]:
            if field_name in entity:
                val = entity[field_name]
                if not val:
                    continue
                val_str = str(val).lower()
                if any(kw in val_str or get_stem(kw) in val_str or any(is_synonym(kw, token) for token in re.findall(r'\w+', val_str)) for kw in matched_kws):
                    matched_flds.append(field_name)
                    
        # Only retain entities with relevance score >= 5
        if total_relevance >= 5:
            # Clone entity to avoid mutating database shared caches
            entity_copy = dict(entity)
            entity_copy["_matched_keywords"] = list(set(matched_kws))
            entity_copy["_missing_keywords"] = list(set(kw for kw in query_keywords if kw not in matched_kws))
            entity_copy["_matched_fields"] = list(set(matched_flds))
            results.append(entity_copy)
            
    return results
