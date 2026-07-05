from pydantic import BaseModel, Field, EmailStr
from typing import List, Dict, Any, Optional
from enum import Enum

class EntityType(str, Enum):
    SUPPLIER = "supplier"
    PROFESSIONAL = "professional"
    OPPORTUNITY = "opportunity"

class AgentRequest(BaseModel):
    query: str = Field(..., description="Natural language query from user describing business requirements")

class HardConstraints(BaseModel):
    locations: Optional[List[str]] = Field(default=None, description="Allowed locations/states/cities")
    certifications: Optional[List[str]] = Field(default=None, description="Required certifications (e.g. food-grade, ISO)")
    minimum_capacity: Optional[int] = Field(default=None, description="Minimum production or team capacity")
    capacity_unit: Optional[str] = Field(default=None, description="Unit of capacity (e.g., units, kg, tonnes, etc.)")
    maximum_delivery_days: Optional[int] = Field(default=None, description="Maximum days to deliver orders")
    required_skills: Optional[List[str]] = Field(default=None, description="Required skills/technologies")
    maximum_budget: Optional[float] = Field(default=None, description="Maximum allowed budget")
    budget_unit: Optional[str] = Field(default=None, description="Unit of budget (e.g., USD, Rs, etc.)")
    deadline: Optional[str] = Field(default=None, description="Deadline or availability timeframe requirement")
    availability_unit: Optional[str] = Field(default=None, description="Unit of availability timeframe")

class StructuredRequirement(BaseModel):
    objective: str = Field(..., description="Extracted objective of the query")
    entity_type: EntityType = Field(..., description="Target entity type being searched")
    entity_name: Optional[str] = Field(default=None, description="Name of the specific entity to look up (if any)")
    hard_constraints: HardConstraints = Field(default_factory=HardConstraints, description="Hard constraints extracted from user request")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="Soft preferences and nice-to-haves")
    requested_results: int = Field(default=3, description="Number of results requested by the user")

class ExecutionPlan(BaseModel):
    steps: List[str] = Field(default_factory=list, description="Execution steps generated before matching")

# Entity schemas representing items stored in the JSON dataset
class Supplier(BaseModel):
    id: str
    name: str
    location: str
    products: List[str]
    capacity: Optional[int] = None
    delivery_days: Optional[int] = None
    certifications: List[str] = Field(default_factory=list)
    rating: Optional[float] = None
    availability: bool
    email: Optional[str] = None
    phone: Optional[str] = None
    industry: Optional[str] = None
    previous_orders: Optional[int] = None

class Professional(BaseModel):
    id: str
    name: str
    skills: List[str]
    experience: Optional[int] = None  # in years
    location: str
    availability: bool
    rating: Optional[float] = None

class Opportunity(BaseModel):
    id: str
    title: str
    required_skills: List[str]
    budget: Optional[float] = None
    deadline: Optional[str] = None
    location: str

class ScoreBreakdown(BaseModel):
    product_relevance: float = Field(..., description="Score for matching product categories or skills (out of 30%)")
    location_suitability: float = Field(..., description="Score for location match (out of 20%)")
    constraint_compliance: float = Field(..., description="Score for hard constraint checks (out of 25%)")
    capacity_availability: float = Field(..., description="Score for capacity or availability checks (out of 15%)")
    reputation_rating: float = Field(..., description="Score for entity rating/feedback (out of 10%)")
    total_score: float = Field(..., description="Total matching score (0.0 to 100.0)")
    calculation_explanation: str = Field(..., description="Step-by-step breakdown of how the score was calculated")

class MatchResult(BaseModel):
    entity: Dict[str, Any] = Field(..., description="Raw entity details from the database")
    score_breakdown: ScoreBreakdown = Field(..., description="Transparent match score breakdown")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Factual evidence backing constraints and ratings")
    missing_information: List[str] = Field(default_factory=list, description="Dataset fields missing for this entity")
    risks: List[str] = Field(default_factory=list, description="Any potential risks or ambiguities identified")
    matched_keywords: List[str] = Field(default_factory=list, description="List of query keywords found in this entity")
    missing_keywords: List[str] = Field(default_factory=list, description="List of query keywords not found in this entity")
    matched_fields: List[str] = Field(default_factory=list, description="List of fields where keywords matched")

class ValidationStatus(BaseModel):
    success: bool = Field(..., description="True if recommendations satisfy all validation rules")
    failures: List[str] = Field(default_factory=list, description="Factual error or constraint validation failures")
    verification_evidence: List[str] = Field(default_factory=list, description="Checks passed with evidence")
    corrected_in_loop: bool = Field(default=False, description="True if self-correction was executed")
    attempts: int = Field(default=1, description="Number of attempts taken during correction loop")

class NextAction(BaseModel):
    description: str = Field(..., description="Recommended action statement")
    awaiting_approval: bool = Field(default=True, description="Always True; waits for human approval")

class AgentResponse(BaseModel):
    requirement: StructuredRequirement
    plan: ExecutionPlan
    matches: List[MatchResult]
    validation: ValidationStatus
    next_action: NextAction
    outreach_message: Optional[str] = None
