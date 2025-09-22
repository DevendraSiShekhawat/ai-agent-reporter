# app/main.py
import os
import json
from fastapi import FastAPI, Request, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.db import init_db, SessionLocal, Report
from app.agent_runner import run_query_pipeline
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv, find_dotenv

# Load .env file
load_dotenv(find_dotenv())

# Check required API keys
# Updated the required key from SERPAPI_API_KEY to TAVILY_API_KEY
required_keys = ["TAVILY_API_KEY", "OPENAI_API_KEY"]
missing_keys = [key for key in required_keys if not os.getenv(key)]

if missing_keys:
    raise RuntimeError(f"Missing environment variables: {', '.join(missing_keys)}")

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
def startup():
    init_db()


def run_and_save_report(query: str, report_id: int):
    """
    Runs the agent pipeline and saves the final report.
    This function is run in the background.
    """
    db = SessionLocal()
    try:
        result = run_query_pipeline(query)

        if "error" in result:
            summary = f"Error: {result['error']}"
            links_json = "[]"
        else:
            summary = result["summary"]
            sources_meta = result["sources"]
            # Convert sources to a simple format for storage
            links = [{"url": s["url"], "title": s["title"], "status": s["status"]} for s in sources_meta]
            links_json = json.dumps(links)

        report = db.query(Report).filter(Report.id == report_id).first()
        if report:
            report.summary = summary
            report.links_json = links_json
            if "raw" in result and result["raw"]:
                report.raw = result["raw"][:50000] # store a truncated version of the raw content
            db.commit()

    except Exception as e:
        db.rollback()
        report = db.query(Report).filter(Report.id == report_id).first()
        if report:
            report.summary = f"An unexpected error occurred: {str(e)}"
            db.commit()
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    db = SessionLocal()
    reports = db.query(Report).order_by(Report.created_at.desc()).limit(50).all()
    db.close()
    return templates.TemplateResponse("index.html", {"request": request, "reports": reports})


@app.post("/generate", response_class=RedirectResponse)
def generate_report(background_tasks: BackgroundTasks, request: Request, query: str = Form(...)):
    if not query:
        db = SessionLocal()
        reports = db.query(Report).order_by(Report.created_at.desc()).limit(50).all()
        db.close()
        return templates.TemplateResponse("index.html", {"request": request, "error": "Query cannot be empty.", "reports": reports})

    db = SessionLocal()
    try:
        # 1. Create a placeholder report immediately to get an ID
        placeholder_report = Report(
            query=query,
            summary="Generating report, please wait...", # Placeholder text
            links_json="[]"
        )
        db.add(placeholder_report)
        db.commit()
        db.refresh(placeholder_report)
        report_id = placeholder_report.id

        # 2. Add the long-running job to the background
        background_tasks.add_task(run_and_save_report, query, report_id)

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

    # 3. Redirect the user to the report page immediately
    return RedirectResponse(url=f"/report/{report_id}", status_code=303)


@app.get("/report/{report_id}", response_class=HTMLResponse)
def view_report(request: Request, report_id: int):
    db = SessionLocal()
    try:
        r = db.query(Report).filter(Report.id == report_id).first()
        if not r:
            raise HTTPException(status_code=404, detail="Report not found")
        
        sources = json.loads(r.links_json) if r.links_json else []
        return templates.TemplateResponse("report.html", {"request": request, "report": r, "sources": sources})
    finally:
        db.close()