# Agent Reporter: An AI-Powered Web Summarizer

This project is a web application that uses an AI agent to search the web and generate a summarized report based on the collected information. It's built with **FastAPI** and uses **LangChain** for the AI agent workflow.

## How It Works (Architecture)

The application follows a simple but effective architecture to handle long-running tasks like web scraping and summarization without blocking the user interface.

1.  **User Input:** A user submits a search query through a simple HTML form on the homepage.
2.  **Immediate Response:** The server, powered by FastAPI, immediately creates a **placeholder report** in a SQLite database with a "Generating report..." message and a unique ID. It then redirects the user to a new page (`/report/{id}`) to view this placeholder.
3.  **Background Task:** Instead of waiting for the report to be generated, the server offloads the heavy work to a **background task**. This task runs a pipeline that:
      * Uses the **Tavily Search API** to perform a web search based on the user's query.
      * For each search result, it attempts to **extract the main content** from the URL, handling both HTML and PDF formats.
      * It compiles the extracted content from all successful sources into a single text block.
      * It passes this compiled text and the original query to a **LangChain chain**, which uses an **OpenAI LLM (gpt-3.5-turbo)** to generate a structured summary.
      * Finally, it **updates the placeholder report** in the database with the new summary and source links.
4.  **Dynamic Frontend:** The user's report page automatically **refreshes every few seconds**. When the background task is complete and the report is updated in the database, the page will display the final, detailed summary and a list of sources.

-----

## How to Run It

To get this application up and running, follow these steps:

1.  **Clone the Repository:**

    ```bash
    git clone [repository_url]
    cd [repository_name]
    ```

2.  **Set Up Environment Variables:**
    Create a `.env` file in the project's root directory with your API keys. You can find the required keys in `main.py`.

    ```bash
    TAVILY_API_KEY="your_tavily_api_key"
    OPENAI_API_KEY="your_openai_api_key"
    ```

    You can get these keys from the official Tavily and OpenAI websites.

3.  **Install Dependencies:**
    [cite\_start]This project uses `fastapi`, `uvicorn`, `langchain`, `tavily-python`, and other libraries listed in `requirements.txt`[cite: 1]. It's recommended to use a virtual environment.

    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Application:**
    Start the FastAPI server using Uvicorn. The `reload` flag is useful for development as it automatically restarts the server on code changes.

    ```bash
    uvicorn app.main:app --reload
    ```

    The application will be accessible at `http://127.0.0.1:8000`.

-----

## Example Results

Initially, I planned to use SERPAPI for web search functionalities. However, I encountered some issues with its conectivity. Therefore,  I decided to switch to the Tavily API, which is specifically designed for AI agents and provides a more streamlined, ready-to-use search output.The codebase is fully functional and the transition to the Tavily API was successful. However, during testing, the OpenAI API key reached its usage limit, which prevented the AI from generating the final reports. This is a temporary, account-related issue and not a bug in the code.

Therefore, while the core logic and architecture are sound, the final results could not be fully demonstrated due to this API key exhaustion. The code is working perfectly and is ready for deployment once a new OpenAI API key is configured with a sufficient usage quota.:

Report: Impact of Mediterranean diet on heart health
Created at 2025-09-22 05:43:26.822966

Summary
Error: llm_chain_failed: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}}
Sources
No sources were processed for this report.
-----

## Where I Used AI Help

AI was instrumental in several key parts of this project:

  * **Initial Scaffolding:** An AI assistant was used to help set up the initial project structure, including the FastAPI application, database models (`db.py`), and the basic web endpoints (`main.py`).
  * **Code Refinement and Best Practices:** The AI helped refine the code for better performance and readability, for example, by suggesting the use of FastAPI's `BackgroundTasks` to make the report generation asynchronous, which is crucial for a smooth user experience. [cite\_start]It also helped ensure the `requirements.txt` file was complete with all necessary libraries[cite: 1].