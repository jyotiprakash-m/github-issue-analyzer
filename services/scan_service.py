import requests
from sqlmodel import Session, select, delete
from models.issue import Issue
from models.repo import Repo
from core.logger import get_logger
from typing import Dict, Any
from datetime import datetime

def fetch_and_cache_issues(session: Session, repo_full_name: str) -> Dict[str, Any]:
    """
    Fetch all open issues from a GitHub repository and cache them locally in the database.
    Returns a summary dict as per assignment spec.
    """
    logger = get_logger("scan_service")
    url = f"https://api.github.com/repos/{repo_full_name}/issues"
    headers = {"Accept": "application/vnd.github+json"}
    response = requests.get(url, headers=headers)
    if response.status_code == 404:
        logger.error(f"Repository not found: {repo_full_name}")
        return {
            "repo": repo_full_name,
            "issues_fetched": 0,
            "cached_successfully": False,
            "error": "Repository not found"
        }
    elif response.status_code != 200:
        logger.error(f"Failed to fetch issues: {response.status_code} {response.text}")
        return {
            "repo": repo_full_name,
            "issues_fetched": 0,
            "cached_successfully": False,
            "error": f"GitHub API error: {response.status_code}"
        }
    issues_data = response.json()
    issues_fetched = 0
    # Create or update Repo entry
    repo_obj = session.exec(select(Repo).where(Repo.repo == repo_full_name)).first()
    if not repo_obj:
        repo_obj = Repo(repo=repo_full_name, issues_fetched=0, cached_successfully=False, created_at=datetime.utcnow())
        session.add(repo_obj)
        session.commit()
        session.refresh(repo_obj)
    else:
        # Remove old issues for this repo (but keep the Repo entry)
        session.exec(delete(Issue).where(Issue.repo_id == int(repo_obj.id))) # type: ignore
    for issue in issues_data:
        # Only cache issues, not PRs
        if "pull_request" in issue:
            continue
        issue_obj = Issue(
            id=issue["id"],
            repo_id=int(repo_obj.id), # type: ignore
            title=issue.get("title", ""),
            body=issue.get("body", ""),
            html_url=issue.get("html_url", ""),
            created_at=datetime.strptime(issue["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        )
        session.add(issue_obj)
        issues_fetched += 1
    repo_obj.issues_fetched = issues_fetched
    repo_obj.cached_successfully = True
    session.commit()
    logger.info(f"Fetched and cached {issues_fetched} issues for {repo_full_name}")
    return {
        "repo": repo_full_name,
        "issues_fetched": issues_fetched,
        "cached_successfully": True
    }
