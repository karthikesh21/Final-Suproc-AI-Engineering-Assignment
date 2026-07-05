import re
from typing import Dict, Any, List
from backend.models.schemas import StructuredRequirement, ScoreBreakdown

def tokenize(text: str) -> set:
    """Helper to tokenize and lowercase text for Jaccard similarity."""
    if not text:
        return set()
    return set(re.findall(r'\w+', text.lower()))

def calculate_match_score(entity: Dict[str, Any], requirement: StructuredRequirement) -> ScoreBreakdown:
    """
    Calculates a transparent, weighted match score (0-100%) for an entity against requirements.
    Weights:
      - Product/Skill Relevance: 30%
      - Location Suitability: 20%
      - Hard Constraint Compliance: 25%
      - Capacity/Availability: 15%
      - Reputation/Rating: 10%
    """
    if requirement.entity_name:
        return ScoreBreakdown(
            product_relevance=30.0,
            location_suitability=20.0,
            constraint_compliance=25.0,
            capacity_availability=15.0,
            reputation_rating=10.0,
            total_score=100.0,
            calculation_explanation="100% score for explicit Named Entity Lookup match."
        )

    # Category 1: Relevance Score
    relevance_score = 0.0
    objective_tokens = tokenize(requirement.objective)
    
    from backend.tools.search import is_instruction_phrase, get_stem, is_synonym
    
    relevance_lines = []
    
    if requirement.entity_type == "supplier":
        raw_products = entity.get("products", [])
        entity_products = [p for p in raw_products if not is_instruction_phrase(p)]
        product_tokens = set()
        for prod in entity_products:
            product_tokens.update(tokenize(prod))
            
        if objective_tokens:
            intersection = objective_tokens.intersection(product_tokens)
            union = objective_tokens.union(product_tokens)
            overlap_ratio = len(intersection) / len(union) if union else 0.0
            relevance_score = min(30.0, overlap_ratio * 30.0 * 2.0)
            if relevance_score > 0.0:
                relevance_score = min(30.0, relevance_score + 20.0)
        else:
            relevance_score = 0.0
            
        # Display details
        stopwords = {"find", "search", "need", "get", "want", "supplier", "suppliers", "professional", "professionals", "opportunity", "opportunities", "for", "in", "with", "and", "a", "an", "the", "to", "of", "about", "please", "company"}
        obj_kws = [w for w in re.findall(r'\w+', requirement.objective.lower()) if w not in stopwords]
        
        relevance_lines.append("Product / Skill Relevance (30%)")
        relevance_lines.append("Objective Keywords")
        matched_count = 0
        for kw in obj_kws:
            is_matched = False
            for tok in product_tokens:
                if kw == tok or get_stem(kw) == get_stem(tok) or is_synonym(kw, tok):
                    is_matched = True
                    break
            if is_matched:
                matched_count += 1
                relevance_lines.append(f"✓ {kw}")
            else:
                relevance_lines.append(f"✗ {kw}")
        relevance_lines.append("")
        relevance_lines.append("Supplier Products")
        for prod in entity_products:
            relevance_lines.append(f"✓ {prod}")
        relevance_lines.append("")
        relevance_lines.append(f"Matched Keywords: {matched_count} / {len(obj_kws) if obj_kws else 1}")
        relevance_lines.append(f"Awarded Score: {relevance_score:.1f} / 30")
        
    elif requirement.entity_type == "professional":
        req_skills = set(s.lower().strip() for s in (requirement.hard_constraints.required_skills or []))
        entity_skills = set(s.lower().strip() for s in entity.get("skills", []))
        
        if req_skills:
            intersection = req_skills.intersection(entity_skills)
            overlap_ratio = len(intersection) / len(req_skills)
            relevance_score = overlap_ratio * 30.0
            if relevance_score > 0.0:
                relevance_score = min(30.0, relevance_score + 20.0)
        else:
            relevance_score = 30.0
            
        relevance_lines.append("Product / Skill Relevance (30%)")
        relevance_lines.append("Objective Keywords")
        for skill in req_skills:
            status = "✓" if skill in entity_skills else "✗"
            relevance_lines.append(f"{status} {skill}")
        relevance_lines.append("")
        relevance_lines.append("Professional Skills")
        for skill in entity_skills:
            relevance_lines.append(f"✓ {skill}")
        relevance_lines.append("")
        relevance_lines.append(f"Matched Keywords: {len(req_skills.intersection(entity_skills))} / {len(req_skills) if req_skills else 1}")
        relevance_lines.append(f"Awarded Score: {relevance_score:.1f} / 30")
        
    elif requirement.entity_type == "opportunity":
        req_skills = set(s.lower().strip() for s in (requirement.hard_constraints.required_skills or []))
        entity_skills = set(s.lower().strip() for s in entity.get("required_skills", []))
        
        if req_skills:
            intersection = req_skills.intersection(entity_skills)
            overlap_ratio = len(intersection) / len(req_skills)
            relevance_score = overlap_ratio * 30.0
            if relevance_score > 0.0:
                relevance_score = min(30.0, relevance_score + 20.0)
        else:
            relevance_score = 30.0
            
        relevance_lines.append("Product / Skill Relevance (30%)")
        relevance_lines.append("Objective Keywords")
        for skill in req_skills:
            status = "✓" if skill in entity_skills else "✗"
            relevance_lines.append(f"{status} {skill}")
        relevance_lines.append("")
        relevance_lines.append("Opportunity Skills")
        for skill in entity_skills:
            relevance_lines.append(f"✓ {skill}")
        relevance_lines.append("")
        relevance_lines.append(f"Matched Keywords: {len(req_skills.intersection(entity_skills))} / {len(req_skills) if req_skills else 1}")
        relevance_lines.append(f"Awarded Score: {relevance_score:.1f} / 30")

    # Category 2: Location Suitability
    location_score = 0.0
    entity_location = str(entity.get("location", "")).lower()
    location_lines = []
    location_lines.append("Location Suitability (20%)")
    location_lines.append(f"User Requirement: {', '.join(requirement.hard_constraints.locations) if requirement.hard_constraints.locations else 'None'}")
    
    if requirement.hard_constraints.locations:
        has_south_india = any(loc.lower().strip() == "south-india" or loc.lower().strip() == "south india" for loc in requirement.hard_constraints.locations)
        if has_south_india:
            location_lines.append("Expanded States:")
            for s in ["Karnataka", "Tamil Nadu", "Kerala", "Andhra Pradesh", "Telangana"]:
                location_lines.append(f"  {s}")
                
        matched_locs = []
        for loc in requirement.hard_constraints.locations:
            loc_lower = loc.lower().strip()
            if loc_lower == "south india" or loc_lower == "south-india":
                south_states = ["karnataka", "tamil nadu", "kerala", "andhra pradesh", "telangana"]
                if any(state in entity_location for state in south_states):
                    location_score = 20.0
                    matched_locs.append("South India")
                    break
            elif loc_lower in entity_location:
                location_score = 20.0
                matched_locs.append(loc)
                break
                
        location_lines.append(f"Supplier Location: {entity.get('location')}")
        if location_score > 0:
            location_lines.append(f"Result: Matches {'South India' if has_south_india else ', '.join(matched_locs)}")
        else:
            location_lines.append("Result: Location mismatch")
        location_lines.append(f"Awarded Score: {location_score:.1f} / 20")
    else:
        location_score = 20.0
        location_lines.append("No location constraint supplied.")
        location_lines.append("Default Score: 20/20")

    # Category 3: Constraint Compliance
    constraint_score = 25.0
    failures = []
    constraint_lines = []
    constraint_lines.append("Constraint Compliance (25%)")
    
    constraints = requirement.hard_constraints
    has_any = False
    
    if requirement.entity_type == "supplier":
        if constraints.minimum_capacity is not None:
            has_any = True
            cap = entity.get("capacity", 0) or 0
            status = "PASS" if cap >= constraints.minimum_capacity else "FAIL"
            if status == "FAIL":
                failures.append(f"Capacity {cap} < Minimum {constraints.minimum_capacity}")
            constraint_lines.extend([
                "Minimum Capacity",
                f"  Required: {constraints.minimum_capacity} units",
                f"  Supplier: {cap} units",
                f"  Result: {status}"
            ])
        if constraints.maximum_delivery_days is not None:
            has_any = True
            days = entity.get("delivery_days", 999) or 999
            status = "PASS" if days <= constraints.maximum_delivery_days else "FAIL"
            if status == "FAIL":
                failures.append(f"Delivery days {days} > Maximum {constraints.maximum_delivery_days}")
            constraint_lines.extend([
                "Delivery",
                f"  Required: {constraints.maximum_delivery_days} days",
                f"  Supplier: {days} days",
                f"  Result: {status}"
            ])
        if constraints.certifications:
            has_any = True
            entity_certs = [c.lower() for c in entity.get("certifications", [])]
            for cert in constraints.certifications:
                status = "PASS" if any(cert.lower() in ec for ec in entity_certs) else "FAIL"
                if status == "FAIL":
                    failures.append(f"Missing certification: {cert}")
                constraint_lines.extend([
                    f"{cert} Certification",
                    f"  Required: Yes",
                    f"  Supplier: {', '.join(entity.get('certifications', [])) or 'None'}",
                    f"  Result: {status}"
                ])
                
    elif requirement.entity_type == "professional":
        if constraints.required_skills:
            has_any = True
            entity_skills = [s.lower() for s in entity.get("skills", [])]
            for skill in constraints.required_skills:
                status = "PASS" if any(skill.lower() in es for es in entity_skills) else "FAIL"
                if status == "FAIL":
                    failures.append(f"Missing skill: {skill}")
                constraint_lines.extend([
                    f"Skill Match: {skill}",
                    f"  Required: Yes",
                    f"  Professional: {', '.join(entity.get('skills', [])) or 'None'}",
                    f"  Result: {status}"
                ])
                
    elif requirement.entity_type == "opportunity":
        if constraints.maximum_budget is not None:
            has_any = True
            budget = entity.get("budget", 999999) or 999999
            status = "PASS" if budget <= constraints.maximum_budget else "FAIL"
            if status == "FAIL":
                failures.append(f"Budget {budget} > Maximum {constraints.maximum_budget}")
            constraint_lines.extend([
                "Maximum Budget Limit",
                f"  Required: Under ${constraints.maximum_budget}",
                f"  Opportunity: ${budget}",
                f"  Result: {status}"
            ])
        if constraints.required_skills:
            has_any = True
            entity_skills = [s.lower() for s in entity.get("required_skills", [])]
            for skill in constraints.required_skills:
                status = "PASS" if any(skill.lower() in es for es in entity_skills) else "FAIL"
                if status == "FAIL":
                    failures.append(f"Missing required skill: {skill}")
                constraint_lines.extend([
                    f"Skill Match: {skill}",
                    f"  Required: Yes",
                    f"  Opportunity: {', '.join(entity.get('required_skills', [])) or 'None'}",
                    f"  Result: {status}"
                ])
                
    if failures:
        constraint_score = 18.0 if len(failures) == 1 else 0.0
    else:
        constraint_score = 25.0
        
    if not has_any:
        constraint_lines.append("No hard constraints specified.")
    constraint_lines.append(f"Awarded Score: {constraint_score:.1f} / 25")

    # Category 4: Capacity / Availability
    capacity_score = 0.0
    capacity_lines = []
    capacity_lines.append("Capacity / Availability (15%)")
    
    if requirement.entity_type == "supplier":
        capacity = entity.get("capacity", 0) or 0
        min_cap = requirement.hard_constraints.minimum_capacity
        
        if min_cap:
            if capacity >= min_cap:
                capacity_score = 15.0
            else:
                capacity_score = (capacity / min_cap) * 15.0
            capacity_lines.extend([
                f"Required Capacity: {min_cap} units",
                f"Supplier Capacity: {capacity} units",
                f"Available: {'Immediate' if entity.get('availability', True) else 'Unavailable'}"
            ])
        else:
            if capacity > 0:
                capacity_score = 15.0
            else:
                capacity_score = 5.0
            capacity_lines.extend([
                "Required Capacity: None specified",
                f"Supplier Capacity: {capacity} units",
                f"Available: {'Immediate' if entity.get('availability', True) else 'Unavailable'}"
            ])
            
    elif requirement.entity_type == "professional":
        available = entity.get("availability", False)
        if available:
            capacity_score = 15.0
        else:
            capacity_score = 0.0
        capacity_lines.append(f"Professional Availability: {'Immediate' if available else 'Unavailable'}")
        
    elif requirement.entity_type == "opportunity":
        budget = entity.get("budget", 0) or 0
        max_budget = requirement.hard_constraints.maximum_budget
        
        if max_budget:
            if budget <= max_budget:
                capacity_score = 15.0
            else:
                capacity_score = max(0.0, (1.0 - (budget - max_budget)/max_budget) * 15.0)
            capacity_lines.extend([
                f"Opportunity Budget: ${budget}",
                f"Limit Constraints: ${max_budget}"
            ])
        else:
            capacity_score = 15.0
            capacity_lines.append(f"Opportunity Budget: ${budget}")
            
    capacity_lines.append(f"Awarded Score: {capacity_score:.1f} / 15")

    # Category 5: Reputation
    reputation_lines = []
    reputation_lines.append("Reputation (10%)")
    rating = entity.get("rating")
    if rating is not None:
        rating_score = (rating / 5.0) * 10.0
    else:
        rating_score = 5.0
        
    reputation_lines.extend([
        f"Rating: {rating or 0.0} / 5",
        f"Previous Successful Projects: {entity.get('previous_orders') or entity.get('completed_projects') or 0}"
    ])
    reputation_lines.append(f"Awarded Score: {rating_score:.1f} / 10")

    # Final score
    total_score = relevance_score + location_score + constraint_score + capacity_score + rating_score
    total_score = round(min(100.0, max(0.0, total_score)), 2)
    
    final_lines = []
    final_lines.append("Final Score Calculation")
    final_lines.append(f"Product Relevance: {relevance_score:.1f}")
    final_lines.append(f"+ Location: {location_score:.1f}")
    final_lines.append(f"+ Constraint Compliance: {constraint_score:.1f}")
    final_lines.append(f"+ Capacity: {capacity_score:.1f}")
    final_lines.append(f"+ Reputation: {rating_score:.1f}")
    final_lines.append(f"= {total_score:.1f} / 100")

    full_explanation = "\n\n".join([
        "\n".join(relevance_lines),
        "\n".join(location_lines),
        "\n".join(constraint_lines),
        "\n".join(capacity_lines),
        "\n".join(reputation_lines),
        "\n".join(final_lines)
    ])
    
    return ScoreBreakdown(
        product_relevance=round(relevance_score, 2),
        location_suitability=round(location_score, 2),
        constraint_compliance=round(constraint_score, 2),
        capacity_availability=round(capacity_score, 2),
        reputation_rating=round(rating_score, 2),
        total_score=total_score,
        calculation_explanation=full_explanation
    )
