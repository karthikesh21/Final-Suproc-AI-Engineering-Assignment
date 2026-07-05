from typing import List, Dict, Any
from backend.models.schemas import StructuredRequirement

def draft_outreach(entities: List[Dict[str, Any]], requirement: StructuredRequirement) -> str:
    """
    Generates a professional outreach email template for procurement, recruitment, or project proposals.
    Constructs the message dynamically using entity details and structured requirements.
    """
    if not entities:
        return "No recommendations available to draft outreach messages for."
        
    entity_names = ", ".join([e.get("name", "Unknown") for e in entities])
    entity_ids = ", ".join([e.get("id", "Unknown") for e in entities])
    
    if requirement.entity_name:
        etype_label = requirement.entity_type.value.capitalize()
        return f"""{etype_label} Lookup Result

Selected {etype_label}
{entity_names}

Lookup Type
Explicit {etype_label} Search

Reason for Selection
Exact {etype_label.lower()} name matched the dataset.
The {etype_label.lower()} passed validation and is awaiting human approval before any business action."""
    
    if requirement.entity_type == "supplier":
        # Supplier procurement inquiry
        capacity_str = f"{requirement.hard_constraints.minimum_capacity} units" if requirement.hard_constraints.minimum_capacity else "bulk quantity"
        timeline_str = f"within {requirement.hard_constraints.maximum_delivery_days} days" if requirement.hard_constraints.maximum_delivery_days else "the standard timeline"
        certs_str = ", ".join(requirement.hard_constraints.certifications) if requirement.hard_constraints.certifications else "industry standard"
        
        email_body = f"""Subject: Request for Quotation: {requirement.objective.capitalize()} - Suproc Business Network

Dear Sales Team,

We are contacting you on behalf of a procurement request on the Suproc Business Network. We are looking to engage with qualified suppliers for:

- Requirement: {requirement.objective}
- Target Volume: {capacity_str}
- Required Timeline: Deliver {timeline_str}
- Required Certifications: {certs_str}

Based on our system search, we have identified your company, representing:
{entity_names} (IDs: {entity_ids})
as a potential match for this order. We noted that you support similar capabilities and operate from locations in {", ".join(list(set(e.get("location", "") for e in entities)))}.

Could you please confirm:
1. Your current capacity and lead time to fulfill an initial order of {capacity_str}?
2. Your compliance with the required certifications ({certs_str})?
3. A ballpark price quotation for the requested quantity?

We look forward to your prompt response.

Best regards,

Procurement Agent
Suproc Business Network
"""
        return email_body.strip()
        
    elif requirement.entity_type == "professional":
        # Professional hiring inquiry
        skills_str = ", ".join(requirement.hard_constraints.required_skills) if requirement.hard_constraints.required_skills else "relevant skills"
        email_body = f"""Subject: Collaboration Opportunity: {requirement.objective.capitalize()} - Suproc Network

Dear candidate(s),

We are reaching out to you regarding a professional engagement opportunity on the Suproc Business Network matching your background.

We are currently looking for qualified professionals with experience in:
- Domain/Role: {requirement.objective}
- Core Skills: {skills_str}

Based on your profile, we have identified:
{entity_names} (IDs: {entity_ids})
as prime candidates for this project.

Could you please let us know:
1. Your availability to take on a new contract/role starting within the next few weeks?
2. Your standard rate/salary expectations for this engagement?
3. Your experience with {skills_str}?

Please let us know if you're interested, and we can set up a short alignment call.

Best regards,

Talent Acquisition Specialist
Suproc Business Network
"""
        return email_body.strip()
        
    elif requirement.entity_type == "opportunity":
        # Opportunity bid proposal
        budget_str = f"${requirement.hard_constraints.maximum_budget}" if requirement.hard_constraints.maximum_budget else "the specified budget"
        email_body = f"""Subject: Proposal for Project: {requirement.objective.capitalize()} - Suproc Network

Dear Project Coordinator,

We are writing to express interest in the business opportunity published on the Suproc Network:

- Opportunity: {requirement.objective}
- Project details: {entity_names} (IDs: {entity_ids})
- Target Budget: {budget_str}

Our team of professionals has the required skills and certifications matching your project requirements. We would love to submit a formal bid proposal.

Could you please share:
1. The detailed Request for Proposal (RFP) document?
2. The submission guidelines and final timeline for vendor selections?
3. The contact person for subsequent technical questions?

We are prepared to deploy resources and look forward to participating in your selection process.

Best regards,

Business Development Director
Suproc Business Network
"""
        return email_body.strip()
        
    return "Unsupported entity type for outreach generation."
