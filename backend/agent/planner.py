import json
from typing import List
from backend.config import settings
from backend.models.schemas import StructuredRequirement, ExecutionPlan
from backend.agent.parser import call_ollama
from backend.agent.prompts import SYSTEM_PLANNER_PROMPT

def generate_plan_with_mock(requirement: StructuredRequirement) -> ExecutionPlan:
    """Fallback planner that outputs high-quality deterministic step lists."""
    etype = requirement.entity_type.value
    steps = [
        f"Search {etype}s dataset for matching product keywords and locations",
        f"Inspect individual {etype} records and load complete details",
    ]
    
    # Add filtering steps based on constraints present
    hc = requirement.hard_constraints
    filter_details = []
    if hc.locations:
        filter_details.append(f"locations matching {hc.locations}")
    if hc.certifications:
        filter_details.append(f"certifications matching {hc.certifications}")
    if hc.minimum_capacity:
        filter_details.append(f"minimum capacity >= {hc.minimum_capacity}")
    if hc.maximum_delivery_days:
        filter_details.append(f"delivery time <= {hc.maximum_delivery_days} days")
    if hc.required_skills:
        filter_details.append(f"skills matching {hc.required_skills}")
    if hc.maximum_budget:
        filter_details.append(f"budget <= {hc.maximum_budget}")
        
    if filter_details:
        steps.append(f"Apply hard constraints filtering: {', '.join(filter_details)}")
    else:
        steps.append(f"Filter records according to default filters")
        
    steps.extend([
        f"Rank the eligible {etype}s using transparent weighted match scoring",
        f"Validate the final recommendations against duplicates, factual correctness, and entity exists checks",
        f"Generate professional outreach draft and flag next action for human approval"
    ])
    
    return ExecutionPlan(steps=steps)

def generate_plan(query: str, requirement: StructuredRequirement) -> ExecutionPlan:
    """
    Generates a step-by-step ExecutionPlan for matching.
    Falls back to a rule-based mock planner if Ollama is unavailable or mock mode is active.
    """
    try:
        prompt = f"User Query: \"{query}\"\nStructured Requirement: {requirement.model_dump_json()}"
        response_text = call_ollama(prompt, SYSTEM_PLANNER_PROMPT)
        
        # Clean response text
        clean_text = response_text.replace("```json", "").replace("```", "").strip()
        steps = json.loads(clean_text)
        
        if isinstance(steps, list):
            return ExecutionPlan(steps=steps)
        elif isinstance(steps, dict) and "steps" in steps:
            return ExecutionPlan(steps=steps["steps"])
        else:
            raise ValueError("Ollama plan output format is invalid.")
            
    except (ConnectionError, RuntimeError, json.JSONDecodeError, KeyError, ValueError) as e:
        return generate_plan_with_mock(requirement)
