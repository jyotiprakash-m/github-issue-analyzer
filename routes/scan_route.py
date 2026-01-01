from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List, Optional
from pydantic import BaseModel
from models import Issue, Repo
from core.database import get_session
from services import scan_service

router = APIRouter(tags=["Scan"])

class ScanRequest(BaseModel):
	repo: str

@router.post("/scan")
def scan_repo(request: ScanRequest, session: Session = Depends(get_session)):
	"""
	Fetch and cache GitHub issues for the given repo.
	"""
	result = scan_service.fetch_and_cache_issues(session, request.repo)
	if not result["cached_successfully"]:
		raise HTTPException(status_code=400, detail="Failed to fetch or cache issues.")
	return result