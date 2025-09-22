# app/agent_runner.py
import os
from langchain_openai import ChatOpenAI                     # Corrected import
from langchain_core.prompts import PromptTemplate             # Corrected import
from langchain_core.output_parsers import StrOutputParser   # New import for parsing output

from app.tools import web_search_tavily, extract_content_from_url

OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# This instantiation is now correct with the new import
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

SUMMARY_PROMPT = PromptTemplate(
    input_variables=["query", "sources"],
    template=(
        "You are an assistant that MUST produce a short structured report for the user query:\n\n"
        "{query}\n\n"
        "Here are the extracted source texts (each source is labeled). Create:\n"
        "1) A short title\n2) A 5-bullet key-points summary (concise)\n"
        "3) A one-paragraph synthesis\n4) A list of source links with a short one-line note per link.\n\n"
        "Use the content only from the provided sources. If a source was skipped state it.\n\nSOURCES:\n{sources}\n\nReport:"
    )
)

# This is the new, modern way to create a chain using LangChain Expression Language (LCEL)
# It's more flexible and replaces the deprecated LLMChain
summary_chain = SUMMARY_PROMPT | llm | StrOutputParser()


def run_query_pipeline(query: str, max_sources=3):
    """
    1) call web_search tool (returns list of sources)
    2) call extract_content for each source (skip if fails)
    3) compile sources text and call the summary_chain to produce final structured report
    4) return dict with summary, sources metadata
    """
    try:
        search_results = web_search_tavily(query, num_results=max_sources)
    except Exception as e:
        return {"error": f"search_failed: {e}"}

    collected = []
    for r in search_results:
        url = r.get("url")
        try:
            text = extract_content_from_url(url)
            # limit stored raw to safe size
            collected.append({"url": url, "title": r.get("title"), "snippet": r.get("snippet"), "text": text[:15000], "status": "ok"})
        except Exception as e:
            collected.append({"url": url, "title": r.get("title"), "snippet": r.get("snippet"), "text": "", "status": str(e)})

    # create sources string for the LLM
    sources_combined = ""
    for i, s in enumerate(collected, 1):
        sources_combined += f"Source {i} URL: {s['url']}\nStatus: {s['status']}\nSnippet: {s.get('snippet')}\n\n"
        if s["status"] == "ok":
            sources_combined += f"Text:\n{s['text']}\n\n---\n\n"
            
    # if no sources were collected, return a graceful error
    if not any(s["status"] == "ok" for s in collected):
        return {"error": f"No usable content could be extracted from search results."}

    try:
        summary_raw = summary_chain.invoke({"query": query, "sources": sources_combined})
        return {"summary": summary_raw, "sources": collected}
    except Exception as e:
        return {"error": f"llm_chain_failed: {e}"}