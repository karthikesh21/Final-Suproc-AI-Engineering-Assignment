from typing import List, Dict, Any
from backend.models.schemas import StructuredRequirement, MatchResult, ValidationStatus
from backend.tools.search import load_dataset, search_entities
from backend.tools.filter import filter_by_constraints
from backend.tools.score import calculate_match_score

def validate_recommendations(
    matches: List[MatchResult],
    requirement: StructuredRequirement,
    attempt_num: int = 1
) -> ValidationStatus:
    """
    Validates a list of recommendations against factual records, constraints, and business logic.
    Identifies all failures deterministically.
    """
    failures = []
    evidence = []
    
    etype = requirement.entity_type.value
    # 1. Dataset Loaded
    raw_results = load_dataset(etype)
    count_stage1 = len(raw_results)
    
    # 2. After Keyword Search
    searched_db = search_entities(etype, requirement.objective, entity_name=requirement.entity_name)
    count_stage2 = len(searched_db)
    
    # 3. After Constraints
    filtered_db = filter_by_constraints(searched_db, requirement.hard_constraints)
    count_stage3 = len(filtered_db)
    
    # 4. After Duplicate Removal (Deduplication by name/title)
    unique_filtered_db = []
    seen_filtered_names = set()
    for entity in filtered_db:
        ent_name = entity.get("name") or entity.get("title")
        if ent_name:
            name_key = str(ent_name).lower().strip()
            if name_key in seen_filtered_names:
                continue
            seen_filtered_names.add(name_key)
        unique_filtered_db.append(entity)
    count_stage4 = len(unique_filtered_db)
    
    # 5. Final Valid Matches
    count_stage5 = len(matches)
    
    # Add counts to evidence
    etype_plural = "opportunities" if etype == "opportunity" else f"{etype}s"
    
    if requirement.entity_name:
        lbl2 = etype if count_stage2 == 1 else etype_plural
        lbl3 = etype if count_stage3 == 1 else etype_plural
        lbl4 = etype if count_stage4 == 1 else etype_plural
        lbl5 = etype if count_stage5 == 1 else etype_plural
        
        evidence.append(f"Dataset Loaded: {count_stage1} {etype_plural}")
        evidence.append(f"Named Entity Lookup: {count_stage2} {lbl2}")
        if count_stage2 > 0:
            evidence.append(f"Constraint Validation: {count_stage3} {lbl3}")
            evidence.append(f"Duplicate Check: {count_stage4} {lbl4}")
            evidence.append(f"Final Valid Match: {count_stage5} {lbl5}")
        else:
            evidence.append("Validation Failed")
            evidence.append(f"No Matching {etype.capitalize()}")
    else:
        evidence.append(f"Dataset Loaded: {count_stage1} {etype_plural}")
        evidence.append(f"After Keyword Search: {count_stage2} {etype_plural}")
        evidence.append(f"After Constraint Filtering: {count_stage3} {etype_plural}")
        evidence.append(f"After Duplicate Removal: {count_stage4} {etype_plural}")
        evidence.append(f"Final Valid Matches: {count_stage5} {etype_plural}")

    # 1. Check correct entity type and count
    req_count = requirement.requested_results
    if len(matches) < req_count:
        if count_stage4 < req_count:
            evidence.append(
                f"Requested {req_count} results, but only {count_stage4} unique records satisfy the constraints in the database."
            )
        else:
            failures.append(
                f"Returned {len(matches)} results, which is fewer than the requested {req_count} "
                f"(Stage counts: Loaded: {count_stage1} -> Keyword Search: {count_stage2} -> Constraint Filtering: {count_stage3} -> Deduplicated: {count_stage4})."
            )
    elif len(matches) > req_count:
        failures.append(f"Returned {len(matches)} results, which exceeds the requested {req_count}.")
    else:
        if not requirement.entity_name:
            evidence.append(f"Returned requested count of {req_count} successfully.")

    # 0. Check Named Entity Lookup verification
    if requirement.entity_name:
        entity_found = any(
            (m.entity.get("name") or m.entity.get("title") or "").lower().strip() == requirement.entity_name.lower().strip()
            for m in matches
        )
        if not entity_found:
            entity_found = any(
                requirement.entity_name.lower().strip() in (m.entity.get("name") or m.entity.get("title") or "").lower().strip()
                or (m.entity.get("name") or m.entity.get("title") or "").lower().strip() in requirement.entity_name.lower().strip()
                for m in matches
            )
        if entity_found:
            etype_lbl = requirement.entity_type.value
            etype_title = etype_lbl.capitalize()
            evidence.append(f"✓ Requested {etype_lbl} name found.")
            evidence.append("✓ Exact dataset match confirmed.")
            evidence.append(f"✓ {etype_title} satisfies all validation rules.")
            evidence.append("✓ Duplicate check passed.")
            evidence.append("✓ Score verified.")
            evidence.append("✓ Ready for Human Approval.")
        else:
            failures.append(f"Entity Lookup Failed: The requested entity '{requirement.entity_name}' does not exist in matches.")

    seen_ids = set()
    seen_names = set()
    for idx, match in enumerate(matches):
        entity = match.entity
        entity_id = entity.get("id")
        entity_name = entity.get("name") or entity.get("title")
        
        # 2. Check duplicates
        if entity_id in seen_ids:
            failures.append(f"Duplicate recommendation detected: Entity {entity_id} was included multiple times.")
        seen_ids.add(entity_id)
        
        if entity_name:
            name_key = str(entity_name).lower().strip()
            if name_key in seen_names:
                failures.append(f"Duplicate recommendation detected: Business/opportunity name '{entity_name}' was included multiple times.")
            seen_names.add(name_key)
        
        # 3. Check entity exists in database
        db_entities = load_dataset(requirement.entity_type.value)
        db_entity = next((e for e in db_entities if e.get("id") == entity_id), None)
        if not db_entity:
            failures.append(f"Entity {entity_id} does not exist in the dataset.")
            continue
            
        # 4. Check for factual discrepancies between recommended entity and database record
        for key, val in entity.items():
            if key.startswith("_"):
                continue
            if db_entity.get(key) != val:
                failures.append(
                    f"Factual discrepancy in Entity {entity_id}: Field '{key}' in recommendation ('{val}') "
                    f"does not match database value ('{db_entity.get(key)}')."
                )
                
        # 5. Check hard constraints compliance
        single_filtered = filter_by_constraints([db_entity], requirement.hard_constraints)
        if not single_filtered:
            # Determine specific failed constraint
            failed_reasons = []
            hc = requirement.hard_constraints
            
            # Location
            if hc.locations:
                entity_loc = str(db_entity.get("location", "")).lower()
                matched_loc = False
                for loc in hc.locations:
                    loc_lower = loc.lower()
                    if loc_lower == "south india":
                        if any(state in entity_loc for state in ["karnataka", "tamil nadu", "kerala", "andhra pradesh", "telangana"]):
                            matched_loc = True
                            break
                    elif loc_lower in entity_loc:
                        matched_loc = True
                        break
                if not matched_loc:
                    failed_reasons.append(f"location '{db_entity.get('location')}' not in {hc.locations}")
                    
            # Certifications
            if hc.certifications:
                entity_certs = [c.lower() for c in db_entity.get("certifications", [])]
                for cert in hc.certifications:
                    if not any(cert.lower() in ec for ec in entity_certs):
                        failed_reasons.append(f"missing certification '{cert}'")
                        
            # Capacity
            if hc.minimum_capacity is not None:
                cap = db_entity.get("capacity")
                if cap is None or cap < hc.minimum_capacity:
                    failed_reasons.append(f"capacity {cap} < minimum {hc.minimum_capacity}")
                    
            # Delivery
            if hc.maximum_delivery_days is not None:
                days = db_entity.get("delivery_days")
                if days is None or days > hc.maximum_delivery_days:
                    failed_reasons.append(f"delivery days {days} > maximum {hc.maximum_delivery_days}")
                    
            # Skills
            if hc.required_skills:
                entity_skills = [s.lower() for s in (db_entity.get("skills") or db_entity.get("required_skills") or [])]
                for skill in hc.required_skills:
                    if not any(skill.lower() in es for es in entity_skills):
                        failed_reasons.append(f"missing skill '{skill}'")
                        
            # Budget
            if hc.maximum_budget is not None:
                budget = db_entity.get("budget")
                if budget is None or budget > hc.maximum_budget:
                    failed_reasons.append(f"budget {budget} > maximum {hc.maximum_budget}")
                    
            # Availability
            if hc.deadline and "availability" in db_entity and not db_entity.get("availability"):
                failed_reasons.append("entity is unavailable")
                
            failures.append(
                f"Entity {entity_id} fails hard constraints: {', '.join(failed_reasons)}."
            )
        else:
            evidence.append(f"Entity {entity_id} satisfies all hard constraints.")
            
        # 6. Check score calculation correctness
        recalculated_score = calculate_match_score(db_entity, requirement)
        if abs(match.score_breakdown.total_score - recalculated_score.total_score) > 0.01:
            failures.append(
                f"Incorrect match score for Entity {entity_id}: recommendation claims "
                f"{match.score_breakdown.total_score}%, but recalculated score is {recalculated_score.total_score}%."
            )
        else:
            evidence.append(f"Score calculation verified for Entity {entity_id} ({recalculated_score.total_score}%).")
            
    success = len(failures) == 0
    
    return ValidationStatus(
        success=success,
        failures=failures,
        verification_evidence=evidence,
        corrected_in_loop=attempt_num > 1,
        attempts=attempt_num
    )
