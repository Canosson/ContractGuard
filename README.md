# ContractGuard ⚖️

An AI-powered Swedish contract law analysis tool. Upload a PDF contract and receive a structured legal risk report, plus a Q&A interface to ask questions about specific clauses.

![ContractGuard screenshot](assets/ContractGuard.png)

## Features

- **Risk analysis** — scans contract clauses and flags HIGH, MEDIUM, and LOW risk items
- **PDF export** — download the generated report as a formatted PDF
- **Q&A chat** — ask follow-up questions about specific clauses, answered using only the contract's content

## Setup

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) for dependency management
- An OpenAI API key
- A Pinecone account and index

### Installation

```bash
git clone https://github.com/Canosson/ContractGuard.git
cd ContractGuard
uv sync
```

### Environment variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
INDEX_NAME=your_pinecone_index_name
```

## Usage

### Streamlit app (recommended)

```bash
streamlit run app.py
```

1. Upload a contract PDF
2. Click **Run Analysis** to generate the risk report
3. Download the report as PDF
4. Use the chat interface to ask questions about the contract

### CLI

```bash
python main.py
```

## Architecture

```
ContractGuard/
├── app.py           # Streamlit UI
├── main.py          # CLI entry point
├── ingestion.py     # PDF parsing, clause extraction, and Pinecone ingestion
├── backend/
│   └── core.py      # LLM interface: run_full_scan() and answer_question()
├── prompt.py        # System prompt assembly
└── flagging.py      # Risk level definitions (HIGH/MEDIUM/LOW) and scoring rubric
```

**Data flow:**
1. `ingestion.py` parses the PDF with `pdfplumber`, splits it into clauses by numbered section headings, embeds them with `text-embedding-3-small`, and stores them in Pinecone.
2. `backend/core.py` runs the full scan by joining all clause texts and passing them to the LLM, or answers questions by retrieving the top-5 relevant clauses via similarity search first.
3. `app.py` manages session state and renders the report and chat interface.

## Dependencies

Managed with `uv`. Key packages:

- `langchain`, `langchain-openai`, `langchain-pinecone` — LLM orchestration and vector store
- `streamlit` — web UI
- `pdfplumber` — PDF parsing
- `fpdf2` — PDF report generation
- `pinecone` — vector database

## Disclaimer

ContractGuard is an AI-powered assistant intended to provide guidance and is **not** a substitute for professional legal advice.
