# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the Streamlit app
streamlit run app.py

# Run the CLI version
python main.py

# Add a dependency
uv add <package>

# Remove a dependency
uv remove <package>
```

## Architecture

ContractGuard is a Swedish contract law AI analysis tool. A user uploads a PDF contract and receives a structured legal risk report, plus a Q&A interface to ask questions about specific clauses.

### Data flow

1. **Ingestion** (`ingestion.py`): A PDF is opened with `pdfplumber`, split into clause segments via regex on numbered section headings, enriched with a context prefix, embedded with OpenAI `text-embedding-3-small`, and stored in a Pinecone vector store.

2. **Analysis** (`backend/core.py`): `run_full_scan()` joins all clause texts and sends them to the LLM with the system prompt. `answer_question()` retrieves the top-5 relevant clauses from Pinecone via similarity search, then passes them as context to the LLM.

3. **Prompting** (`prompt.py` + `flagging.py`): The system prompt is assembled at import time. `flagging.py` defines the three risk levels (HIGH/MEDIUM/LOW) and injects the scoring rubric into the prompt via `build_risk_scoring_prompt()`.

4. **UI** (`app.py`): Streamlit app with session state managing `clauses`, `report`, `last_uploaded`, and `chat_history`. Ingestion only runs when a new file is detected (compared by filename). The report is rendered as markdown and downloadable as PDF via `fpdf2`.

### Key constraints

- **Pinecone index**: The vector store is shared across sessions. Uploading a new contract adds to the existing index rather than replacing it — clauses from previous contracts persist in Pinecone between runs.
- **PDF path in core.py**: `PDF_PATH` in `backend/core.py` is hardcoded for CLI use via `main.py`. The Streamlit app bypasses this and passes the temp file path directly.
- **Font handling in PDF export**: `fpdf2` uses Helvetica (Latin-1 only). All text must pass through `sanitize()` in `app.py` before being written to the PDF, or it will crash on Unicode characters (curly quotes, em dashes, emojis) that the LLM commonly outputs.
- **`st.set_page_config`** must be the first Streamlit call in `app.py`.
- **Never name a file `streamlit.py`** — it shadows the `streamlit` library on import.

### Environment variables required

- `OPENAI_API_KEY`
- `PINECONE_API_KEY`
- `INDEX_NAME` (Pinecone index name)
