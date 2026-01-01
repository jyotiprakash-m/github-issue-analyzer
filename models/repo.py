from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone

if TYPE_CHECKING:
    from .issue import Issue

class Repo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    repo: str = Field(unique=True)
    issues_fetched: int
    cached_successfully: bool
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    issues: List["Issue"] = Relationship(back_populates="repo_obj")
