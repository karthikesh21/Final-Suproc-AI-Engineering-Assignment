from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from backend.models.schemas import AgentRequest, AgentResponse
from backend.agent.workflow import run_agent_workflow
from backend.config import settings
import httpx
import uvicorn

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Suproc Agent - Local Agentic Search, Matching & Verification System Backend",
    version="1.0.0"
)

# CORS Configuration for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local development, allow all origins. Can narrow to ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "config": {
            "model": settings.OLLAMA_MODEL,
            "mock_llm": settings.MOCK_LLM
        }
    }

@app.get("/status")
def get_status():
    ollama_online = False
    available_models = []
    try:
        response = httpx.get(f"{settings.OLLAMA_API_URL}/api/tags", timeout=1.0)
        if response.status_code == 200:
            ollama_online = True
            models_info = response.json().get("models", [])
            available_models = [m.get("name") for m in models_info]
    except Exception:
        pass
        
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "ollama_online": ollama_online,
        "configured_model": settings.OLLAMA_MODEL,
        "available_models": available_models,
        "fallback_active": not ollama_online or settings.OLLAMA_MODEL not in available_models
    }

@app.post("/agent", response_model=AgentResponse)
def execute_agent(request: AgentRequest):
    """
    Main agent endpoint. Takes a natural language query,
    executes the agent workflow and returns matches, scoring, validation status and outreach details.
    """
    if not request.query or request.query.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty."
        )
        
    try:
        response = run_agent_workflow(request.query)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during workflow execution: {str(e)}"
        )

# For running backend directly
if __name__ == "__main__":
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
