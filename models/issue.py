from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .repo import Repo

class Issue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    repo_id: int = Field(foreign_key="repo.id")
    title: str
    body: str
    html_url: str
    created_at: datetime

    repo_obj: Optional["Repo"] = Relationship(back_populates="issues")
