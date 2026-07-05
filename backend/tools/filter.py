from typing import List, Dict, Any, Optional
from backend.models.schemas import HardConstraints

def filter_by_constraints(entities: List[Dict[str, Any]], constraints: HardConstraints) -> List[Dict[str, Any]]:
    """
    Applies hard constraints to a list of entities.
    Returns only entities that satisfy ALL specified hard constraints.
    Hard constraints must NEVER be ignored.
    """
    filtered_entities = []
    
    for entity in entities:
        is_valid = True
        
        # 1. Location Constraint
        if constraints.locations:
            entity_location = str(entity.get("location", "")).lower()
            location_match = False
            for loc in constraints.locations:
                loc_lower = loc.lower().strip()
                # Handles "South India" alias specifically by mapping to South Indian states
                if loc_lower == "south india":
                    south_states = ["karnataka", "tamil nadu", "kerala", "andhra pradesh", "telangana", "south india"]
                    if any(state in entity_location for state in south_states):
                        location_match = True
                        break
                elif loc_lower in entity_location:
                    location_match = True
                    break
            if not location_match:
                is_valid = False
                continue
                
        # 2. Certifications Constraint (For Suppliers)
        if constraints.certifications and "certifications" in entity:
            entity_certs = [cert.lower().strip() for cert in entity.get("certifications", [])]
            for req_cert in constraints.certifications:
                req_cert_lower = req_cert.lower().strip()
                # Check for substring match in any of the entity certifications
                if not any(req_cert_lower in cert for cert in entity_certs):
                    is_valid = False
                    break
            if not is_valid:
                continue
                
        # 3. Minimum Capacity Constraint (For Suppliers)
        if constraints.minimum_capacity is not None and "capacity" in entity:
            capacity = entity.get("capacity")
            if capacity is None or capacity < constraints.minimum_capacity:
                is_valid = False
                continue
                
        # 4. Maximum Delivery Days Constraint (For Suppliers)
        if constraints.maximum_delivery_days is not None and "delivery_days" in entity:
            delivery_days = entity.get("delivery_days")
            if delivery_days is None or delivery_days > constraints.maximum_delivery_days:
                is_valid = False
                continue
                
        # 5. Required Skills Constraint (For Professionals/Opportunities)
        if constraints.required_skills:
            # Skills field can be "skills" or "required_skills" depending on entity type
            entity_skills = [s.lower().strip() for s in (entity.get("skills") or entity.get("required_skills") or [])]
            for req_skill in constraints.required_skills:
                req_skill_lower = req_skill.lower().strip()
                if not any(req_skill_lower in s for s in entity_skills):
                    is_valid = False
                    break
            if not is_valid:
                continue
                
        # 6. Maximum Budget Constraint (For Opportunities)
        if constraints.maximum_budget is not None:
            budget = entity.get("budget")
            if budget is None or budget > constraints.maximum_budget:
                is_valid = False
                continue
                
        # 7. Deadline / Availability Constraint (Dynamic checks)
        if constraints.deadline:
            # If professional: check availability is True
            if "availability" in entity and not entity.get("availability", True):
                is_valid = False
                continue
            # If opportunity: check deadline string comparisons or presence
            if "deadline" in entity:
                deadline = entity.get("deadline")
                if not deadline or str(deadline) > str(constraints.deadline):
                    is_valid = False
                    continue
                    
        # If all constraints passed, add to list
        if is_valid:
            filtered_entities.append(entity)
            
    return filtered_entities
