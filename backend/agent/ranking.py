from typing import List, Dict, Any
from backend.models.schemas import StructuredRequirement, MatchResult
from backend.tools.score import calculate_match_score

def rank_entities(entities: List[Dict[str, Any]], requirement: StructuredRequirement) -> List[MatchResult]:
    """
    Scores, analyzes, and ranks a list of filtered entities.
    Returns sorted MatchResult structures containing calculations, evidence, and risks.
    """
    results = []
    
    for entity in entities:
        # Calculate transparent match score
        score_breakdown = calculate_match_score(entity, requirement)
        
        # Compile evidence
        evidence = {}
        missing_info = []
        risks = []
        
        # Generic rating check
        if entity.get("rating"):
            evidence["rating"] = f"Rated {entity.get('rating')}/5.0 based on client transactions."
        
        # Entity-specific analysis
        if requirement.entity_type == "supplier":
            # Evidence
            evidence["location"] = f"Located in {entity.get('location')}."
            evidence["capacity"] = f"Production capacity is {entity.get('capacity')} units/month."
            evidence["delivery"] = f"Delivers within {entity.get('delivery_days')} days."
            if entity.get("certifications"):
                evidence["certifications"] = f"Certifications held: {', '.join(entity.get('certifications'))}."
                
            # Missing Info
            if not entity.get("email"):
                missing_info.append("email")
            if not entity.get("phone"):
                missing_info.append("phone")
            if entity.get("previous_orders") is None:
                missing_info.append("previous_orders")
                
            # Risks
            if entity.get("capacity", 0) <= 0:
                risks.append("Production capacity is listed as 0 or unknown, indicating potential supply disruption.")
            if not entity.get("email") and not entity.get("phone"):
                risks.append("No active contact details (email or phone) are on record for this supplier.")
            elif not entity.get("email"):
                risks.append("Supplier email contact details are missing.")
            elif not entity.get("phone"):
                risks.append("Supplier phone contact details are missing.")
            if requirement.hard_constraints.minimum_capacity:
                req_cap = requirement.hard_constraints.minimum_capacity
                ent_cap = entity.get("capacity", 0) or 0
                if ent_cap > 0 and ent_cap < req_cap:
                    risks.append(f"Supplier capacity ({ent_cap}) is near the required order size ({req_cap}). Risk of fulfillment delays.")
            if entity.get("rating", 5.0) < 4.0:
                risks.append(f"Supplier rating is {entity.get('rating')}, which is below the target quality threshold.")
                
        elif requirement.entity_type == "professional":
            evidence["skills"] = f"Possesses skills: {', '.join(entity.get('skills', []))}."
            evidence["experience"] = f"Has {entity.get('experience', 0)} years of professional experience."
            
            if not entity.get("experience"):
                missing_info.append("experience")
            if not entity.get("rating"):
                missing_info.append("rating")
                
            if entity.get("experience", 0) < 3:
                risks.append("Professional has less than 3 years of experience. High guidance might be required.")
            if not entity.get("availability"):
                risks.append("Professional availability is currently set to false or restricted.")
                
        elif requirement.entity_type == "opportunity":
            evidence["budget"] = f"Total allocated project budget: ${entity.get('budget')}."
            evidence["deadline"] = f"Project completion deadline: {entity.get('deadline')}."
            
            if not entity.get("budget"):
                missing_info.append("budget")
            if not entity.get("deadline"):
                missing_info.append("deadline")
                
            if entity.get("budget", 0) < 2000:
                risks.append("Project budget is low relative to standard developer rates.")
                
        from backend.tools.search import detect_prompt_injection
        if detect_prompt_injection(entity):
            risks.append(
                "Prompt injection detected in supplier description. "
                "Instruction-like text was ignored during retrieval. "
                "Supplier evaluated only using structured dataset fields."
            )
            
        results.append(MatchResult(
            entity=entity,
            score_breakdown=score_breakdown,
            evidence=evidence,
            missing_information=missing_info,
            risks=risks,
            matched_keywords=entity.get("_matched_keywords", []),
            missing_keywords=entity.get("_missing_keywords", []),
            matched_fields=entity.get("_matched_fields", [])
        ))
        
    # Sort by total score descending, and resolve ties using rating or name/title
    results.sort(
        key=lambda x: (
            -x.score_breakdown.total_score,
            -x.entity.get("rating", 0.0) if x.entity.get("rating") is not None else 0.0,
            x.entity.get("name", x.entity.get("title", ""))
        )
    )
    
    # Deduplicate by business name or opportunity title (keeping the highest-scoring candidate)
    deduplicated_results = []
    seen_names = set()
    for r in results:
        name = r.entity.get("name") or r.entity.get("title")
        if name:
            name_key = str(name).lower().strip()
            if name_key in seen_names:
                continue
            seen_names.add(name_key)
        deduplicated_results.append(r)
        
    if requirement.entity_name:
        filtered_results = []
        name_lower = requirement.entity_name.lower().strip()
        # Find exact match
        for r in deduplicated_results:
            name = r.entity.get("name") or r.entity.get("title")
            if name and name.lower().strip() == name_lower:
                r.score_breakdown.total_score = 100.0
                filtered_results.append(r)
        
        if not filtered_results and deduplicated_results:
            # Fall back to best fuzzy match
            deduplicated_results[0].score_breakdown.total_score = 100.0
            filtered_results.append(deduplicated_results[0])
            
        return filtered_results
        
    return deduplicated_results
