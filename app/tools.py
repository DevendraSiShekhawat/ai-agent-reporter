# app/tools.py
import os, requests, io
from tavily import TavilyClient
import trafilatura
from pypdf import PdfReader

def web_search_tavily(query, num_results=3):
    """Return list of {'url':..., 'title':..., 'snippet':...} or raise friendly Exception"""
    tavily_api_key = os.getenv("TAVILY_API_KEY")

    if not tavily_api_key:
        raise RuntimeError("TAVILY_API_KEY not set")

    client = TavilyClient(api_key=tavily_api_key)
    results = client.search(query=query, max_results=num_results)

    out = []
    for r in results.get("results", [])[:num_results]:
        out.append({
            "url": r.get("url"),
            "title": r.get("title"),
            "snippet": r.get("content")
        })

    if not out:
        raise RuntimeError("Search returned no results")
    return out


def extract_content_from_url(url, timeout=10):
    """Return extracted text or raise exception indicating reason (blocked, not-html/pdf)."""
    headers = {"User-Agent": "agent-report-bot/1.0 (+https://example.com)"}
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
    except Exception as e:
        raise RuntimeError(f"network_error: {e}")

    if resp.status_code >= 400:
        raise RuntimeError(f"http_error_{resp.status_code}")

    ctype = (resp.headers.get("Content-Type") or "").lower()
    if "application/pdf" in ctype or url.lower().endswith(".pdf"):
        # PDF branch
        try:
            reader = PdfReader(io.BytesIO(resp.content))
            texts = [p.extract_text() or "" for p in reader.pages]
            text = "\n".join(texts)
            return text
        except Exception as e:
            raise RuntimeError(f"pdf_extract_error: {e}")

    # HTML/text branch
    try:
        downloaded = trafilatura.extract(resp.text)
        if not downloaded:
            raise RuntimeError("trafilatura_failed_extract")
        return downloaded
    except Exception as e:
        raise RuntimeError(f"trafilatura_error: {e}")