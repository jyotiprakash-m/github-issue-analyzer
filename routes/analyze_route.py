from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from pydantic import BaseModel
from core.database import get_session
from services import analyze_service

router = APIRouter(tags=["Analyze"])

class AnalyzeRequest(BaseModel):
    repo: str
    prompt: str

@router.post("/analyze")
def analyze_repo(request: AnalyzeRequest, session: Session = Depends(get_session)):
    """
    Analyze cached GitHub issues for the given repo using a natural-language prompt and LLM.
    Returns: {"analysis": "<LLM-generated text here>"}
    """
    result = analyze_service.analyze_repo_issues(session, request.repo, request.prompt)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return {"analysis": result["analysis"]}