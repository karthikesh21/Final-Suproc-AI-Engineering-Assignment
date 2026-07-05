import json
from typing import List
from backend.config import settings
from backend.models.schemas import StructuredRequirement, HardConstraints
from backend.agent.parser import call_ollama
from backend.agent.prompts import SYSTEM_CORRECTOR_PROMPT

def correct_requirement_with_mock(failures: List[str], requirement: StructuredRequirement) -> StructuredRequirement:
    """Fallback corrector that adjusts constraints deterministically based on validation failure text."""
    # Copy requirement to edit
    corrected = requirement.model_copy(deep=True)
    hc = corrected.hard_constraints
    
    # Relax constraints depending on validation error messages
    for fail in failures:
        fail_lower = fail.lower()
        
        # If capacity check failed
        if "capacity" in fail_lower or "units" in fail_lower:
            if hc.minimum_capacity is not None:
                # Relax capacity by 20% or set to next lower threshold
                old_cap = hc.minimum_capacity
                hc.minimum_capacity = max(1000, int(old_cap * 0.8))
                
        # If delivery days check failed
        if "delivery" in fail_lower or "days" in fail_lower:
            if hc.maximum_delivery_days is not None:
                # Relax delivery timeline by 5 days
                hc.maximum_delivery_days = hc.maximum_delivery_days + 5
                
        # If locations constraint is too strict
        if "location" in fail_lower:
            if hc.locations:
                # Expand location list or allow broader region
                if "South India" not in hc.locations:
                    hc.locations.append("South India")
                    
        # If budget constraint is too low
        if "budget" in fail_lower:
            if hc.maximum_budget is not None:
                # Increase budget by 20%
                hc.maximum_budget = hc.maximum_budget * 1.2

    return corrected

def correct_requirement(failures: List[str], requirement: StructuredRequirement) -> StructuredRequirement:
    """
    Invokes the corrector loop. Requests local Qwen to adjust constraints to resolve validation failures.
    Falls back to deterministic rule-based corrections if LLM is unavailable.
    """
    try:
        failures_text = "\n".join([f"- {f}" for f in failures])
        prompt = f"Failures:\n{failures_text}\nOriginal Requirement:\n{requirement.model_dump_json()}"
        
        response_text = call_ollama(prompt, SYSTEM_CORRECTOR_PROMPT)
        clean_text = response_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        
        return StructuredRequirement(**data)
        
    except (ConnectionError, RuntimeError, json.JSONDecodeError, KeyError, ValueError) as e:
        return correct_requirement_with_mock(failures, requirement)
