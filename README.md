# 📚 AskDocAI

A smart document assistant that helps you understand PDFs and web content through AI-powered summarization and Q&A.

## ✨ Features

- 📄 **PDF Upload & Processing** - Extract and analyze text from PDF documents
- 🌐 **Web Content Extraction** - Import content directly from URLs
- 🤖 **AI Summarization** - Generate concise summaries using local LLM
- 💬 **Interactive Q&A** - Ask questions and get context-aware answers
- 🔍 **RAG-Enhanced Retrieval** - Smart document chunking for accurate responses
- 📊 **Source Citations** - Answers include references to source material
- 💾 **Export Reports** - Download complete analysis with summaries and Q&A history

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 14+
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/sunjycoding/AskDocAI.git
cd AskDocAI
```

### Step 2: Install & Setup Ollama (Local LLM)

Ollama runs AI models locally on your machine.

**For Linux/Mac/WSL/GitHub Codespaces:**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service (keep this running)
ollama serve

# In a new terminal, download a model (choose one):
ollama pull qwen2.5:0.5b    # Smallest, fastest (recommended for testing)
ollama pull gemma:2b        # Good balance
ollama pull llama3.2:3b     # Better quality, slower
```

**For Windows:**
1. Download from [ollama.com](https://ollama.com)
2. Install and run Ollama
3. Open Command Prompt and run: `ollama pull qwen2.5:0.5b`

### Step 3: Setup Backend

```bash
# Navigate to backend folder
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Linux/Mac/WSL:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Run the Flask server
python app.py
```

Backend will start at: `http://localhost:5050`

### Step 4: Setup Frontend

Open a new terminal:

```bash
# Navigate to frontend folder
cd frontend

# Install dependencies
npm install

# Start the React app
npm start
```

Frontend will open at: `http://localhost:3000`

## 📖 How to Use

### 1. Upload a Document
- Click "Upload Document" tab
- Either drag & drop a PDF file OR enter a web URL
- Wait for processing confirmation

### 2. Generate Summary
- Go to "Generate Summary" tab
- Click the "Generate Summary" button
- AI will create a concise overview of your document

### 3. Ask Questions
- Switch to "Ask Questions" tab
- Type your question about the document
- Get AI-powered answers with source references

### 4. Download Results
- Click "Download Summary & Q&A" button in the Ask Questions tab
- Get a complete report with all analyses

## 📁 Project Structure

```
AskDocAI/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── simple_rag.py        # RAG implementation
│   ├── requirements.txt     # Python dependencies
│   └── venv/               # Virtual environment (created during setup)
├── frontend/
│   ├── src/
│   │   └── App.js          # React main component
│   ├── package.json        # Node dependencies
│   └── public/
└── README.md
```

## 🧪 API Endpoints

| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/api/upload` | POST | Upload PDF file | FormData with 'file' |
| `/api/upload-url` | POST | Extract web content | `{"url": "https://example.com"}` |
| `/api/summarize` | POST | Generate summary | `{"document_id": "xxx"}` |
| `/api/ask` | POST | Ask questions | `{"document_id": "xxx", "question": "..."}` |
| `/api/document/{id}/download` | GET | Download report | - |
| `/api/metrics` | GET | System statistics | - |


## 🙏 Acknowledgments

- Ollama for local LLM support
- Flask and React communities
- City University of Seattle

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built with Flask, React, Ollama, and RAG technology**

*Last updated: September 2025*