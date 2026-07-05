import logging
from typing import Dict, Any, List
from backend.config import settings
from backend.models.schemas import (
    AgentResponse, StructuredRequirement, ExecutionPlan, 
    MatchResult, ValidationStatus, NextAction
)
from backend.agent.parser import parse_query
from backend.agent.planner import generate_plan
from backend.agent.ranking import rank_entities
from backend.agent.validator import correct_requirement
from backend.tools.search import search_entities
from backend.tools.filter import filter_by_constraints
from backend.tools.validation import validate_recommendations
from backend.tools.outreach import draft_outreach

logger = logging.getLogger("suproc_agent")

def run_agent_workflow(query: str) -> AgentResponse:
    """
    Orchestrates the entire Suproc Agent lifecycle.
    Executes: Parser -> Planner -> Search -> Details -> Filter -> Score -> Validate -> Correction -> Response.
    """
    logger.info(f"Starting agent workflow for query: {query}")
    
    # 1. Parse natural language into structured requirements
    requirement = parse_query(query)
    logger.info(f"Parsed requirements: {requirement.model_dump_json()}")
    
    # 2. Generate the execution plan
    plan = generate_plan(query, requirement)
    logger.info(f"Generated execution plan: {plan.steps}")
    
    attempt = 1
    max_attempts = settings.MAX_CORRECTION_ATTEMPTS
    validation = None
    matches = []
    
    while attempt <= max_attempts:
        logger.info(f"Executing workflow iteration {attempt}/{max_attempts}")
        
        # 3. Search entities in JSON dataset
        raw_results = search_entities(requirement.entity_type.value, requirement.objective, entity_name=requirement.entity_name)
        
        # 4. Filter hard constraints
        filtered = filter_by_constraints(raw_results, requirement.hard_constraints)
        
        # 5. Calculate match scores and rank candidates
        ranked = rank_entities(filtered, requirement)
        
        # Take the top N requested results
        matches = ranked[:requirement.requested_results]
        
        # 6. Validate recommendations
        validation = validate_recommendations(matches, requirement, attempt)
        logger.info(f"Validation status for attempt {attempt}: success={validation.success}")
        
        if validation.success:
            break
            
        # 7. Self-correction loop: Modify constraints if validation failed and attempts remain
        if attempt < max_attempts:
            logger.warning(f"Validation failed. Retrying self-correction. Failures: {validation.failures}")
            requirement = correct_requirement(validation.failures, requirement)
            logger.info(f"Self-corrected requirement: {requirement.model_dump_json()}")
            
        attempt += 1
        
    # 8. Draft outreach message using final matched list
    outreach_msg = None
    if matches:
        raw_matched_entities = [m.entity for m in matches]
        outreach_msg = draft_outreach(raw_matched_entities, requirement)
        
    # 9. Formulate recommended next action and require human approval
    entity_ids_str = ", ".join([m.entity.get("id", "N/A") for m in matches])
    if requirement.entity_name:
        next_action_desc = "Named supplier successfully verified.\nAwaiting human approval before transmitting outreach communication."
    else:
        next_action_desc = f"Awaiting human approval to transmit outreach enquiry to {requirement.entity_type.value}(s): {entity_ids_str}."
    if not matches:
        next_action_desc = "No matching entities found. Review requirement inputs and broaden constraint search."
        
    next_action = NextAction(
        description=next_action_desc,
        awaiting_approval=True
    )
    
    return AgentResponse(
        requirement=requirement,
        plan=plan,
        matches=matches,
        validation=validation or ValidationStatus(success=False, failures=["Agent processing failed"], attempts=attempt),
        next_action=next_action,
        outreach_message=outreach_msg
    )
