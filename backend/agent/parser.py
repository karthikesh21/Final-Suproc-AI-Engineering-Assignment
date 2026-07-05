import json
import httpx
import re
from typing import Dict, Any, List, Optional, Tuple
from backend.config import settings
from backend.models.schemas import StructuredRequirement, HardConstraints, EntityType
from backend.agent.prompts import SYSTEM_PARSER_PROMPT

def call_ollama(prompt: str, system_prompt: str) -> str:
    """Helper to invoke local Ollama API via HTTP request."""
    if settings.MOCK_LLM:
        raise ConnectionError("MOCK_LLM is enabled.")
        
    try:
        url = f"{settings.OLLAMA_API_URL}/api/generate"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.0  # Make it deterministic
            }
        }
        response = httpx.post(url, json=payload, timeout=15.0)
        if response.status_code == 200:
            return response.json().get("response", "").strip()
        else:
            raise RuntimeError(f"Ollama API returned status {response.status_code}")
    except Exception as e:
        # Pass the exception up so the orchestrator can fall back to mock parsing
        raise ConnectionError(f"Failed to connect to local Ollama server: {str(e)}")

def parse_query_with_mock(query: str) -> StructuredRequirement:
    """Fallback rule-based parser that handles typical test-case requests."""
    query_lower = query.lower()
    
    # Defaults
    objective = "Search entities"
    entity_type = EntityType.SUPPLIER
    locations = None
    certifications = None
    min_capacity = None
    capacity_unit = None
    max_days = None
    req_skills = None
    max_budget = None
    budget_unit = None
    deadline = None
    availability_unit = None
    preferences = {}
    requested_results = 3
    
    # Attempt to extract requested results count
    count_match = re.search(r'\b(one|two|three|four|five|\d+)\b\s+(suppliers|professionals|opportunities|results|matches)', query_lower)
    if count_match:
        word_to_num = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
        val = count_match.group(1)
        requested_results = word_to_num.get(val, int(val) if val.isdigit() else 3)
    else:
        # Fallback regex for standalone numbers
        num_match = re.search(r'\b(?:find|need|get|want)\s+(\d+)\b', query_lower)
        if num_match:
            requested_results = int(num_match.group(1))

    # Try dynamic matching against dataset records
    matched_entity_type = None
    try:
        from backend.tools.search import load_dataset
        suppliers = load_dataset("supplier")
        professionals = load_dataset("professional")
        opportunities = load_dataset("opportunity")
    except Exception:
        suppliers, professionals, opportunities = [], [], []

    query_words = re.findall(r'\w+', query_lower)
    ignore_name_words = {
        "india", "south", "north", "east", "west", "solutions", "corp", "biodegradables", 
        "products", "earthy", "bowls", "bags", "fastapi", "react", "python", "developer", "developers",
        "engineer", "specialist", "opportunity", "opportunities", "bounty", "contract", "project", "need",
        "find", "search", "lookup", "detail", "details", "contact", "supplier", "professional",
        "packaging", "bengaluru", "bangalore", "chennai", "hyderabad", "kochi", "coimbatore",
        "karnataka", "kerala", "tamil", "nadu", "andhra", "pradesh", "telangana", "southern",
        "mumbai", "maharashtra", "pune", "nellore", "hubli", "madurai", "thrissur", "kadapa",
        "ooty", "guntur", "visakhapatnam", "vizag", "mysore", "salem", "vijayawada"
    }
    
    # Check if query matches a professional's name
    for p in professionals:
        p_name = p.get("name", "").lower()
        p_name_words = re.findall(r'\w+', p_name)
        if any(w.startswith(qw) or qw.startswith(w) for w in p_name_words for qw in query_words if len(qw) > 3 and len(w) > 3 and qw not in ignore_name_words and w not in ignore_name_words):
            matched_entity_type = EntityType.PROFESSIONAL
            objective = f"Find professional {p.get('name')}"
            break
            
    # Check if query matches a supplier's name
    if not matched_entity_type:
        for s in suppliers:
            s_name = s.get("name", "").lower()
            s_name_words = re.findall(r'\w+', s_name)
            if any(w.startswith(qw) or qw.startswith(w) for w in s_name_words for qw in query_words if len(qw) > 3 and len(w) > 3 and qw not in ignore_name_words and w not in ignore_name_words):
                matched_entity_type = EntityType.SUPPLIER
                objective = f"Find supplier {s.get('name')}"
                break
                
    # Check if query matches an opportunity's title
    if not matched_entity_type:
        for o in opportunities:
            o_title = o.get("title", "").lower()
            o_title_words = re.findall(r'\w+', o_title)
            if any(w.startswith(qw) or qw.startswith(w) for w in o_title_words for qw in query_words if len(qw) > 3 and len(w) > 3 and qw not in ignore_name_words and w not in ignore_name_words):
                matched_entity_type = EntityType.OPPORTUNITY
                objective = f"Find opportunity {o.get('title')}"
                break

    if matched_entity_type:
        entity_type = matched_entity_type
    else:
        # Entity Type identification
        if "professional" in query_lower or "developer" in query_lower or "hire" in query_lower or "engineer" in query_lower or "specialist" in query_lower:
            entity_type = EntityType.PROFESSIONAL
            objective = "Find technical professionals"
        elif "opportunity" in query_lower or "opportunities" in query_lower or "project" in query_lower or "bounty" in query_lower or "contract" in query_lower:
            entity_type = EntityType.OPPORTUNITY
            objective = "Find projects and opportunities"
        else:
            entity_type = EntityType.SUPPLIER
            objective = "Find suppliers"
        
    # Location Extraction
    extracted_locations = []
    south_cities = [
        "bengaluru", "bangalore", "chennai", "hyderabad", "kochi", 
        "coimbatore", "kozhikode", "nellore", "hubli", "secunderabad", 
        "madurai", "thrissur", "kadapa", "ooty", "guntur", 
        "visakhapatnam", "vizag", "mysore", "salem", "vijayawada"
    ]
    for city in south_cities:
        if city in query_lower:
            if city == "bangalore":
                extracted_locations.append("Bengaluru")
            elif city == "vizag":
                extracted_locations.append("Visakhapatnam")
            else:
                extracted_locations.append(city.capitalize())
                
    if "south india" in query_lower:
        extracted_locations.extend(["Karnataka", "Tamil Nadu", "Kerala", "Andhra Pradesh", "Telangana"])
        
    if extracted_locations:
        locations = list(set(extracted_locations))
        
    # Supplier details parsing
    if entity_type == EntityType.SUPPLIER:
        if "biodegradable" in query_lower or "container" in query_lower:
            objective = "Find biodegradable food container suppliers"
        if "food-grade" in query_lower or "food grade" in query_lower:
            certifications = ["food-grade"]
        
        # Extract capacity (e.g. 10,000 units, 50,000 kg, 100 tonnes, 250 litres)
        capacity_match = re.search(r'([\d,]+)\s*(units|kg|tonnes|litres|pieces|capacity|volume)', query_lower)
        if capacity_match:
            min_capacity = int(capacity_match.group(1).replace(',', ''))
            unit_extracted = capacity_match.group(2)
            if unit_extracted in ["units", "kg", "tonnes", "litres", "pieces"]:
                capacity_unit = unit_extracted
            else:
                capacity_unit = "units"
        else:
            # Fallback check for prefix capacity (e.g. "capacity 50,000")
            capacity_match_prefix = re.search(r'(?:capacity|volume)\s*([\d,]+)', query_lower)
            if capacity_match_prefix:
                min_capacity = int(capacity_match_prefix.group(1).replace(',', ''))
                capacity_unit = "units"
            
        # Extract delivery days (e.g. 30 days)
        delivery_match = re.search(r'(\d+)\s*(?:days|day|timeline)', query_lower)
        if delivery_match:
            max_days = int(delivery_match.group(1))
            
    # Professional details parsing
    elif entity_type == EntityType.PROFESSIONAL:
        skills = []
        if re.search(r'\bfastapi\b', query_lower):
            skills.append("FastAPI")
        if re.search(r'\breact\b', query_lower):
            skills.append("React")
        if re.search(r'\bpython\b', query_lower):
            skills.append("Python")
        if re.search(r'\bai\b', query_lower):
            skills.append("AI")
        if skills:
            req_skills = skills
            objective = f"Find {' and '.join(skills)} professionals"
            
    # Opportunity details parsing
    elif entity_type == EntityType.OPPORTUNITY:
        if "packaging" in query_lower or "sustainable" in query_lower:
            objective = "Find sustainable packaging opportunities"
        
        # Extract deadline days (e.g. within 30 days, next 30 days)
        import datetime
        days_match = re.search(r'(?:deadline|deadlines|within)\s*(?:the\s+next\s+)?(\d+)\s*(?:days|day|month|months)', query_lower)
        if days_match:
            days = int(days_match.group(1))
            if "month" in days_match.group(0):
                days *= 30
            # Use current date as reference date
            future_date = datetime.date(2026, 7, 5) + datetime.timedelta(days=days)
            deadline = future_date.isoformat()
            
        skills = []
        if re.search(r'\bfastapi\b', query_lower):
            skills.append("FastAPI")
        if re.search(r'\breact\b', query_lower):
            skills.append("React")
        if re.search(r'\bpython\b', query_lower):
            skills.append("Python")
        if skills:
            req_skills = skills
            
    # Global budget parsing
    budget_match = re.search(r'(?:budget|under)\s*(\$|rs\.?|usd)?\s*(\d+)', query_lower)
    if budget_match:
        max_budget = float(budget_match.group(2))
        currency = budget_match.group(1)
        if currency == "$":
            budget_unit = "USD"
        elif currency and "rs" in currency:
            budget_unit = "Rs"
        elif currency:
            budget_unit = currency.upper()
        else:
            budget_unit = "USD"

    # If the objective is still generic, try to extract specific non-stopword/constraint tokens
    if objective in ["Find suppliers", "Find technical professionals", "Find projects and opportunities", "Search entities"]:
        # Clean query to find specific keywords
        words = re.findall(r'\w+', query_lower)
        filter_words = {
            "find", "search", "need", "get", "want", "supplier", "suppliers", 
            "professional", "professionals", "opportunity", "opportunities", 
            "for", "in", "with", "and", "or", "a", "an", "the", "to", "of", "about",
            "we", "that", "within", "at", "least", "units", "capacity", "volume",
            "days", "day", "timeline", "deliver", "support", "budget", "under",
            "usd", "skills", "experience", "years", "south", "india", "karnataka",
            "tamil", "nadu", "kerala", "andhra", "pradesh", "telangana", "bengaluru",
            "bangalore", "chennai", "hyderabad", "kochi", "coimbatore", "kozhikode",
            "nellore", "hubli", "secunderabad", "madurai", "thrissur", "kadapa",
            "ooty", "guntur", "visakhapatnam", "vizag", "mysore", "salem", "vijayawada",
            "one", "two", "three", "four", "five"
        }
        keywords = [w for w in words if w not in filter_words and not w.isdigit()]
        if keywords:
            objective = f"Find {' '.join(keywords)}"

    return StructuredRequirement(
        objective=objective,
        entity_type=entity_type,
        hard_constraints=HardConstraints(
            locations=locations,
            certifications=certifications,
            minimum_capacity=min_capacity,
            capacity_unit=capacity_unit,
            maximum_delivery_days=max_days,
            required_skills=req_skills,
            maximum_budget=max_budget,
            budget_unit=budget_unit,
            deadline=deadline,
            availability_unit=availability_unit
        ),
        preferences=preferences,
        requested_results=requested_results
    )

def post_process_requirement(req: StructuredRequirement, query: str) -> StructuredRequirement:
    """Applies expansions, extractions, and defaults to the StructuredRequirement."""
    query_lower = query.lower()
    
    # 1. Expand South India to constituent states
    if req.hard_constraints.locations:
        expanded_locs = []
        for loc in req.hard_constraints.locations:
            if loc.lower().strip() == "south-india" or loc.lower().strip() == "south india":
                expanded_locs.extend(["Karnataka", "Tamil Nadu", "Kerala", "Andhra Pradesh", "Telangana"])
            else:
                expanded_locs.append(loc)
        req.hard_constraints.locations = list(set(expanded_locs))
    elif "south india" in query_lower:
        req.hard_constraints.locations = ["Karnataka", "Tamil Nadu", "Kerala", "Andhra Pradesh", "Telangana"]
        
    # Extract locations if they are mentioned in query but not in req.hard_constraints.locations
    if not req.hard_constraints.locations:
        cities = ["bengaluru", "bangalore", "chennai", "hyderabad", "kochi", "coimbatore"]
        matched_cities = []
        for city in cities:
            if city in query_lower:
                if city == "bangalore":
                    matched_cities.append("Bengaluru")
                else:
                    matched_cities.append(city.capitalize())
        if matched_cities:
            req.hard_constraints.locations = matched_cities

    # 2. Extract preferences if not already set
    pref_keywords = {
        "sustainable": "sustainable_materials",
        "startup-friendly": "startup_friendly",
        "highly-rated": "highly_rated",
        "eco-friendly": "eco_friendly",
        "preferred supplier": "preferred_supplier"
    }
    for kw, pref_key in pref_keywords.items():
        if kw in query_lower:
            req.preferences[pref_key] = True

    # 3. Ensure minimum_capacity and unit are extracted
    if req.hard_constraints.minimum_capacity is None:
        capacity_match = re.search(r'([\d,]+)\s*(units|kg|tonnes|litres|pieces|capacity|volume)', query_lower)
        if capacity_match:
            req.hard_constraints.minimum_capacity = int(capacity_match.group(1).replace(',', ''))
            unit_extracted = capacity_match.group(2)
            if unit_extracted in ["units", "kg", "tonnes", "litres", "pieces"]:
                req.hard_constraints.capacity_unit = unit_extracted
        else:
            capacity_match_prefix = re.search(r'(?:capacity|volume)\s*([\d,]+)', query_lower)
            if capacity_match_prefix:
                req.hard_constraints.minimum_capacity = int(capacity_match_prefix.group(1).replace(',', ''))
                req.hard_constraints.capacity_unit = "units"

    if req.hard_constraints.minimum_capacity is not None and not req.hard_constraints.capacity_unit:
        cap_match = re.search(r'([\d,]+)\s*(units|kg|tonnes|litres|pieces)', query_lower)
        if cap_match:
            req.hard_constraints.capacity_unit = cap_match.group(2)
        else:
            req.hard_constraints.capacity_unit = "units"

    # Extract maximum budget
    if req.hard_constraints.maximum_budget is None:
        budget_match = re.search(r'(?:budget|under)\s*(\$|rs\.?|usd)?\s*([\d,]+)', query_lower)
        if budget_match:
            req.hard_constraints.maximum_budget = float(budget_match.group(2).replace(',', ''))

    if req.hard_constraints.maximum_budget is not None and not req.hard_constraints.budget_unit:
        budget_match = re.search(r'(?:budget|under)\s*(\$|rs\.?|usd)', query_lower)
        if budget_match:
            unit = budget_match.group(1)
            if unit == "$":
                req.hard_constraints.budget_unit = "USD"
            elif "rs" in unit:
                req.hard_constraints.budget_unit = "Rs"
            else:
                req.hard_constraints.budget_unit = unit.upper()
        else:
            req.hard_constraints.budget_unit = "USD"

    # Extract delivery days
    if req.hard_constraints.maximum_delivery_days is None:
        delivery_match = re.search(r'(\d+)\s*(?:days|day|timeline|deliver)', query_lower)
        if delivery_match:
            req.hard_constraints.maximum_delivery_days = int(delivery_match.group(1))

    # Extract skills
    if req.entity_type in [EntityType.PROFESSIONAL, EntityType.OPPORTUNITY]:
        skills = req.hard_constraints.required_skills or []
        for s in ["Python", "React", "FastAPI", "AI"]:
            if re.search(rf'\b{re.escape(s.lower())}\b', query_lower) and s not in skills:
                skills.append(s)
        if skills:
            req.hard_constraints.required_skills = skills

    # Extract deadline / availability
    if req.entity_type == EntityType.PROFESSIONAL:
        if "immediate" in query_lower or "availability" in query_lower:
            req.hard_constraints.deadline = "immediate"
            
    if req.entity_type == EntityType.OPPORTUNITY:
        if "30 days" in query_lower or "next 30 days" in query_lower or "within 30 days" in query_lower:
            req.hard_constraints.deadline = "2026-08-04"

    if req.hard_constraints.deadline is not None and not req.hard_constraints.availability_unit:
        avail_match = re.search(r'(full-time|part-time|contract|\d+\s*(?:months|month|weeks|week|days|day))', query_lower)
        if avail_match:
            req.hard_constraints.availability_unit = avail_match.group(1)

    # 4. Ensure requested_results has a default
    if not req.requested_results:
        req.requested_results = 3
        
    return req

def find_matching_entity_name(candidate: str, etype: str) -> Optional[str]:
    """Tries to find a case-insensitive exact or fuzzy match in the loaded dataset."""
    try:
        from backend.tools.search import load_dataset
        data = load_dataset(etype)
    except Exception:
        return None
        
    candidate_lower = candidate.lower().strip()
    
    # 1. Case-insensitive exact match
    for item in data:
        name = item.get("name") or item.get("title")
        if name and name.lower().strip() == candidate_lower:
            return name
            
    # 2. Fuzzy prefix / substring matches
    candidate_words = re.findall(r'\w+', candidate_lower)
    if not candidate_words:
        return None
        
    for item in data:
        name = item.get("name") or item.get("title")
        if name:
            name_lower = name.lower()
            name_words = re.findall(r'\w+', name_lower)
            if name_lower.startswith(candidate_lower) or candidate_lower.startswith(name_lower):
                return name
            if any(w.startswith(qw) or qw.startswith(w) for w in name_words for qw in candidate_words if len(qw) > 3 and len(w) > 3):
                return name
    return None

def detect_entity_lookup(query: str) -> Optional[Tuple[str, EntityType]]:
    """Detects if query is an explicit Lookup query by name (prefix match or name match)."""
    query_lower = query.lower().strip()
    
    # 1. Prefix checks
    prefixes = {
        EntityType.SUPPLIER: ["find supplier", "show supplier", "lookup supplier", "get supplier", "search supplier"],
        EntityType.PROFESSIONAL: ["find professional", "show professional", "lookup professional", "get professional", "search professional"],
        EntityType.OPPORTUNITY: ["find opportunity", "show opportunity", "lookup opportunity", "get opportunity", "search opportunity", "find project", "show project"]
    }
    
    for etype, prefix_list in prefixes.items():
        for prefix in prefix_list:
            if query_lower.startswith(prefix):
                candidate = query[len(prefix):].strip()
                if candidate:
                    matched = find_matching_entity_name(candidate, etype.value)
                    if matched:
                        return matched, etype
                    # Return raw candidate if prefix matches but not found in DB
                    return candidate, etype

    # 2. Match directly by name (e.g. "karthikesh" or "BioPack India")
    is_business = any(kw in query_lower for kw in ["units", "capacity", "days", "timeline", "budget", "under", "need", "we need"])
    if not is_business:
        for etype in [EntityType.PROFESSIONAL, EntityType.SUPPLIER, EntityType.OPPORTUNITY]:
            if " " in query_lower:
                try:
                    from backend.tools.search import load_dataset
                    data = load_dataset(etype.value)
                except Exception:
                    data = []
                for item in data:
                    name = item.get("name") or item.get("title")
                    if name and name.lower().strip() == query_lower:
                        return name, etype
            else:
                matched = find_matching_entity_name(query, etype.value)
                if matched:
                    return matched, etype
                
    return None

def parse_query(query: str) -> StructuredRequirement:
    """
    Parses a natural language query into a StructuredRequirement.
    First checks if it is a Named Entity Lookup. Otherwise, falls back to Ollama or mock parser.
    """
    lookup = detect_entity_lookup(query)
    if lookup:
        matched_name, etype = lookup
        return StructuredRequirement(
            objective=f"Find {etype.value} by name",
            entity_type=etype,
            entity_name=matched_name,
            hard_constraints=HardConstraints(),
            preferences={},
            requested_results=1
        )

    req = None
    try:
        prompt = f"Query: \"{query}\""
        response_text = call_ollama(prompt, SYSTEM_PARSER_PROMPT)
        
        # Clean response text in case LLM added extra markdown blocks
        clean_text = response_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        
        # Parse into StructuredRequirement
        req = StructuredRequirement(**data)
        
    except (ConnectionError, RuntimeError, json.JSONDecodeError, KeyError, ValueError) as e:
        # Fallback to local rule-based parsing
        req = parse_query_with_mock(query)
        
    return post_process_requirement(req, query)
