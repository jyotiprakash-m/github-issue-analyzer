from fastapi import FastAPI, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from contextlib import asynccontextmanager
from core.database import init_db, engine
from core.config import settings
import secrets
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import base64
from sqladmin import Admin, ModelView
# All Model imports
from models import Issue, Repo
from routes import scan_route, analyze_route

security = HTTPBasic()
def basic_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, settings.USERNAME)
    correct_password = secrets.compare_digest(credentials.password, settings.PASSWORD)
    if not (correct_username and correct_password):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid credentials", headers={"WWW-Authenticate": "Basic"})

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield 

app = FastAPI(title="GitHub Issue Analyzer API", lifespan=lifespan, docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory="static"), name="static")

admin = Admin(app=app, engine=engine)

class RepoAdmin(ModelView, model=Repo):
    column_list = ["id", "repo", "issues_fetched", "cached_successfully", "created_at"]

class IssueAdmin(ModelView, model=Issue):
    column_list = ["id", "repo_id", "title", "body", "html_url", "created_at"]
        
admin.add_view(RepoAdmin)
admin.add_view(IssueAdmin)

# Middleware to protect /admin with HTTP Basic auth (SQLite )
class AdminBasicAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith("/admin"):
            auth = request.headers.get("authorization")
            if not auth or not auth.startswith("Basic "):
                return Response(status_code=401, headers={"WWW-Authenticate": "Basic"})
            try:
                token = auth.split(" ", 1)[1]
                decoded = base64.b64decode(token).decode("utf-8")
                username, password = decoded.split(":", 1)
            except Exception:
                return Response(status_code=401, headers={"WWW-Authenticate": "Basic"})

            if not (secrets.compare_digest(username, "admin") and secrets.compare_digest(password, "password")):
                return Response(status_code=401, headers={"WWW-Authenticate": "Basic"})

        return await call_next(request)

app.add_middleware(AdminBasicAuthMiddleware)

# Include user routes
app.include_router(scan_route.router, dependencies=[Depends(basic_auth)])
app.include_router(analyze_route.router, dependencies=[Depends(basic_auth)])

# Root endpoint
@app.get("/")
def read_root(credentials: HTTPBasicCredentials = Depends(security)):
    basic_auth(credentials)
    return {"message": "Welcome to the GitHub Issue Analyzer API"}

@app.get("/docs", include_in_schema=False)
def custom_swagger_ui(credentials: HTTPBasicCredentials = Depends(security)):
    basic_auth(credentials)
    return get_swagger_ui_html(openapi_url="/openapi.json", title=app.title)

@app.get("/redoc", include_in_schema=False)
def custom_redoc(credentials: HTTPBasicCredentials = Depends(security)):
    basic_auth(credentials)
    return get_redoc_html(openapi_url="/openapi.json", title=app.title)

def main():
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config="core/uvicorn_log_config.json"
    )

if __name__ == "__main__":
    main()