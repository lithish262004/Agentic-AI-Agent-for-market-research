

**# 🎯 Agentic AI Agent for Market Research

A lightweight **Agentic RAG-powered AI Agent** that rewrites marketing ad copy with **platform optimization, tone adaptation, and feedback-driven learning**.  
Built with **FastAPI**, **ChromaDB**, **Sentence Transformers**, **Mistral LLM**, and an interactive **Streamlit frontend**.  

---

## 🚀 Features
- FastAPI backend with `/run-agent` and `/submit-feedback`  
- Semantic retrieval using **ChromaDB + Sentence Transformers**  
- **Knowledge Graph** for platform, product category & intent alignment  
- **Feedback & Memory Loop** to adapt over time  
- **Mistral LLM** for natural ad rewriting  
- **Streamlit UI** for easy interaction  

---

## ⚙️ Setup & Run

### 1. Clone Repo
```bash
git clone https://github.com/lithish262004/Agentic-AI-Agent-for-market-research.git
cd Agentic-AI-Agent-for-market-research
2. Install Requirements
bash
Copy code
python -m venv venv
# Activate venv (Windows: venv\Scripts\activate | Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
3. Set API Key
bash
Copy code
# Linux/Mac
export MISTRAL_API_KEY="your_api_key"
# Windows PowerShell
setx MISTRAL_API_KEY "your_api_key"
4. Run Backend
bash
Copy code
uvicorn main:app --reload --port 8000
Test → http://127.0.0.1:8000

5. Run Frontend
bash
Copy code
streamlit run frontend.py
Open → http://localhost:8501


Copy code
**
