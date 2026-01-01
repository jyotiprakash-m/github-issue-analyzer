from sqlmodel import Session, select
from models.issue import Issue
from models.repo import Repo
from core.logger import get_logger
from typing import Dict, Any, List
from datetime import datetime
from openai import OpenAI
from core.config import settings


client = OpenAI(api_key=settings.OPENAI_API_KEY)
logger = get_logger("analyze_service")

MAX_ISSUES_PER_CHUNK = 20  # Adjust based on token limits and issue size

def format_issue(issue: Issue) -> str:
    body = issue.body if len(issue.body) < 500 else issue.body[:500] + "..."
    return (
        f"Issue #{issue.id}\n"
        f"Title: {issue.title}\n"
        f"Body: {body}\n"
        f"URL: {issue.html_url}\n"
        f"Created At: {issue.created_at}\n"
        "---\n"
    )

def chunk_issues(issues: List[Issue], chunk_size: int = MAX_ISSUES_PER_CHUNK) -> List[List[Issue]]:
    return [issues[i:i + chunk_size] for i in range(0, len(issues), chunk_size)]

def analyze_issues_with_llm(prompt: str, issues: List[Issue]) -> str:
    formatted_issues = "".join([format_issue(issue) for issue in issues])
    full_prompt = f"{prompt}\n\nHere are the recent issues:\n{formatted_issues}"
    logger.info("Sending prompt to OpenAI LLM.")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  
            messages=[
                {"role": "system", "content": "You are a helpful assistant for analyzing GitHub issues."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=1024,
            temperature=0.7,
        )
        content = response.choices[0].message.content
        analysis = content.strip() if content else ""
        logger.info("Received analysis from OpenAI.")
        return analysis
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return "Error: Unable to analyze issues with LLM."

def analyze_repo_issues(session: Session, repo_full_name: str, prompt: str) -> Dict[str, Any]:
    repo_obj = session.exec(select(Repo).where(Repo.repo == repo_full_name)).first()
    if not repo_obj:
        logger.error(f"Repo not found in cache: {repo_full_name}")
        return {
            "repo": repo_full_name,
            "analysis": None,
            "error": "Repository not found in cache. Please scan first."
        }
    issues = session.exec(select(Issue).where(Issue.repo_id == repo_obj.id)).all()
    if not issues:
        logger.warning(f"No issues found for repo: {repo_full_name}")
        return {
            "repo": repo_full_name,
            "analysis": None,
            "error": "No issues found for this repository."
        }
    # Chunk issues if needed
    chunks = chunk_issues(list(issues))
    analyses = []
    for chunk in chunks:
        analysis = analyze_issues_with_llm(prompt, chunk)
        analyses.append(analysis)
    # If multiple chunks, summarize the analyses with a final LLM call
    if len(chunks) > 1:
        summary_prompt = (
            f"{prompt}\n\nHere are analyses of different batches of issues:\n"
            + "\n\n".join(analyses) +
            "\n\nPlease provide an overall summary and recommendations based on all the above analyses."
        )
        full_analysis = analyze_issues_with_llm(summary_prompt, [])
    else:
        full_analysis = analyses[0] if analyses else ""
    return {
        "repo": repo_full_name,
        "analysis": full_analysis,
        "error": None
    }