import os
import re
import tempfile
import uuid
import streamlit as st
from backend.core import run_full_scan, answer_question
from ingestion import extract_clauses
from fpdf import FPDF


st.set_page_config(page_title="ContractGuard", layout="wide")

# Global styleguide to complement config.toml from Streamlit
st.markdown("""
    <style>
        /* ── Global ── */
        html, body, [class*="css"] {
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        }

        /* ── Sidebar ── */
        [data-testid="stSidebar"] {
            background-color: #F4F4F6;
            border-right: 1px solid #E2E2E8;
        }
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: #4633f6;
        }
        [data-testid="stSidebar"] .stMarkdown p {
            color: #555570;
            font-size: 0.875rem;
        }

        /* ── Divider ── */
        hr {
            border: none;
            border-top: 1px solid #E2E2E8;
        }

        /* ── Buttons ── */
        div.stButton > button {
            background-color: #4633f6;
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            padding: 0.5rem 1.25rem;
            transition: background-color 0.2s ease;
        }
        div.stButton > button:hover {
            background-color: #3322d4;
            color: white;
        }

        /* ── Download button ── */
        div[data-testid="stDownloadButton"] > button {
            background-color: #FFFFFF;
            color: #4633f6;
            border: 1.5px solid #4633f6;
            border-radius: 6px;
            font-weight: 600;
        }
        div[data-testid="stDownloadButton"] > button:hover {
            background-color: #4633f6;
            color: white;
        }

        /* ── File uploader ── */
        [data-testid="stFileUploader"] {
            border: 2px dashed #C8C8D8;
            border-radius: 10px;
            padding: 1rem;
            background-color: #FAFAFC;
        }

        /* ── Chat input ── */
        [data-testid="stChatInput"] textarea {
            border-radius: 8px;
        }

        /* ── Title & subheader ── */
        h1 { color: #1A1A2E; }
        h2, h3 { color: #2E2E4A; }
    </style>
""", unsafe_allow_html=True)

# Initializing streamlit elements
if "clauses" not in st.session_state:
    st.session_state["clauses"] = []
if "report" not in st.session_state:
    st.session_state["report"] = None
if "last_uploaded" not in st.session_state:
    st.session_state["last_uploaded"] = None
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "pdf" not in st.session_state:
    st.session_state["pdf"] = None
if "namespace" not in st.session_state:
    st.session_state["namespace"] = None

# For a clean PDF output
def strip_inline(text: str) -> str:
    """Remove **bold** and *italic* markers from a line of text."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'\1', text)
    return text

# Sanitizing text for the created copy of the PDF report
def sanitize(text: str) -> str:
    text = (text
        .replace(""", '"').replace(""", '"')
        .replace("'", "'").replace("'", "'")
        .replace("–", "-").replace("—", "-")
        .replace("…", "...").replace("•", "*")
        .replace(" ", " ")
        .replace("\U0001f534", "[HIGH]")
        .replace("\U0001f7e0", "[MEDIUM]")
        .replace("\U0001f7e1", "[LOW]")
    )
    return text.encode("latin-1", errors="replace").decode("latin-1")

# Styling the PDF report downloaded
def report_to_pdf(report: str) -> bytes:
    """Create a PDF copy of the generated report"""
    pdf = FPDF()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    for line in report.split("\n"):
        line = sanitize(line.strip())
        try:
            if line.startswith("### "):
                pdf.set_font("Helvetica", "B", 14)
                pdf.multi_cell(0, 8, strip_inline(line[4:]))
            elif line.startswith("#### "):
                pdf.set_font("Helvetica", "B", 12)
                pdf.multi_cell(0, 8, strip_inline(line[5:]))
            elif line.startswith("**"):
                pdf.set_font("Helvetica", "B", 11)
                pdf.multi_cell(0, 7, strip_inline(line))
            elif line.startswith("> "):
                pdf.set_font("Helvetica", "I", 11)
                pdf.multi_cell(0, 7, line[2:])
            elif line.startswith("*") and line.endswith("*"):
                pdf.set_font("Helvetica", "I", 10)
                pdf.multi_cell(0, 6, line[1:-1])
            elif line == "---":
                pdf.ln(3)
            elif line:
                pdf.set_font("Helvetica", size=11)
                pdf.multi_cell(0, 7, strip_inline(line))
            else:
                pdf.ln(3)
        except Exception:
            pass

    return bytes(pdf.output())

# Sidebar
with st.sidebar:
    st.markdown("# ContractGuard ⚖️ ")
    st.markdown("Your trusted **Swedish legal AIsistent**.")
    st.divider()

    st.markdown("### How it works")
    st.markdown("""
        1. 📄 **Upload** your contract PDF
        2. 🔍 **Run Analysis** to scan for risks
        3. 📥 **Download** the report as PDF
        4. 💬 **Ask questions** about the contract
    """)
    st.divider()

    st.markdown("### Status")
    if st.session_state.get("last_uploaded"):
        st.success(f"📎 {st.session_state['last_uploaded']}")
    else:
        st.info("No contract uploaded yet.")

    if st.session_state.get("report"):
        st.success("✅ Analysis complete")

    if st.session_state.get("chat_history"):
        st.markdown(f"💬 **{len(st.session_state['chat_history'])}** message(s) in chat")

    st.divider()
    st.markdown(
        "<p style='font-size:0.75rem; color:#AAAACC;'>ContractGuard is an AI-Powered assistant<br>"
        "to provide guidance and is NOT a substitute<br>"
        "for legal advice.</p>",
        unsafe_allow_html=True
    )

# Main page
st.title("Hej! Welcome to ContractGuard ⚖️")
st.subheader("This is your trusted Swedish legal AIsistent. How may I help you today?")

# Uploading of a PDF document
uploaded_file = st.file_uploader("Upload Contract (PDF)", type="pdf")

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name
    if st.session_state.get("last_uploaded") != uploaded_file.name:
        st.session_state["namespace"] = str(uuid.uuid4())
        with st.spinner("Looking through the document..."):
            st.session_state["clauses"] = extract_clauses(tmp_path, st.session_state["namespace"])
        st.session_state["last_uploaded"] = uploaded_file.name
        st.session_state["report"] = None
        st.session_state["pdf"] = None
    os.unlink(tmp_path)
# If user wants to upload a new document by removing previous file
else:
    st.session_state["clauses"] = []
    st.session_state["report"] = None
    st.session_state["pdf"] = None
    st.session_state["chat_history"] = []
    st.session_state["last_uploaded"] = None
    st.session_state["namespace"] = None

if st.session_state.get("clauses") and not st.session_state.get("report"):
    if st.button("RUN ANALYSIS"):
        try:
            with st.spinner("Analysing your contract..."):
                report = run_full_scan(st.session_state["clauses"])
                st.session_state["report"] = report
                st.session_state["pdf"] = report_to_pdf(report)
                st.session_state["chat_history"] = []
            st.rerun()
        except Exception as e:
            st.error(f"Analysis failed: {e}")

# To clear chat and show only the report
if st.session_state.get("report") and st.session_state.get("chat_history"):
    if st.button("CLEAR CHAT AND SHOW REPORT ONLY"):
        st.session_state["chat_history"] = []
        st.rerun()

# Download button
if st.session_state.get("report"):
    st.divider()
    st.markdown(st.session_state["report"])
    st.download_button(
        label="Download Report",
        data=st.session_state["pdf"],
        file_name="contractguard_report.pdf",
        mime="application/pdf"
    )

# Assistant chat based on report data
if st.session_state.get("report"):
    st.divider()
    st.subheader("Do you have specific questions regarding the contract? Ask away.")

    for exchange in st.session_state["chat_history"]:
        with st.chat_message("user"):
            st.markdown(exchange["question"])
        with st.chat_message("assistant"):
            st.markdown(exchange["answer"])

    if question := st.chat_input("Ask a question about the contract."):
        try:
            with st.spinner("Thinking..."):
                answer = answer_question(question, st.session_state["namespace"])
            st.session_state["chat_history"].append({
                "question": question,
                "answer": answer,
            })
            st.rerun()
        except Exception as e:
            st.error(f"Response failed: {e}")