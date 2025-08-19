# AskDocAI

A smart document agent for PDF summarization and Q&A.

## Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Frontend
```bash
cd frontend
npm install
npm start
```

### Environment Variables
Create `.env` file in backend folder:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage
1. Backend runs on: http://127.0.0.1:5000
2. Frontend runs on: http://127.0.0.1:3000