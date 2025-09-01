# app.py - AskDocAI Backend Framework
from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
import tempfile
import os
import uuid
from datetime import datetime
import requests
from simple_rag import SimplifiedRAG

app = Flask(__name__)
CORS(app, origins=['*'])

# In-memory storage for demo
documents = {}

# Initialize RAG system
try:
    rag = SimplifiedRAG()
    RAG_AVAILABLE = True
except Exception as e:
    print(f"RAG initialization failed: {e}")
    rag = None
    RAG_AVAILABLE = False
    
# Ollama configuration
OLLAMA_MODEL = "qwen2.5:0.5b"

def call_ollama(prompt):
    """Call Ollama API to generate response"""
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': OLLAMA_MODEL,
                'prompt': prompt,
                'stream': False
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json().get('response', '')
    except Exception as e:
        print(f"Ollama error: {e}")
        return None

# Test Ollama connection
def check_ollama():
    try:
        response = requests.get('http://localhost:11434/api/tags')
        if response.status_code == 200:
            return True
    except:
        return False
    return False

OLLAMA_AVAILABLE = check_ollama()
print(f"Ollama status: {'Available' if OLLAMA_AVAILABLE else 'Not Available'}")

def chunk_document(content, chunk_size=1000, overlap=200):
    """Split document into overlapping chunks for better context"""
    chunks = []
    start = 0
    text_length = len(content)
    
    while start < text_length:
        end = start + chunk_size
        chunk = content[start:end]
        chunks.append(chunk)
        start = end - overlap  # Overlap for context continuity
        
    return chunks

@app.route('/')
def home():
    return jsonify({'message': 'AskDocAI Backend is running!'})

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'API is working!'})

@app.route('/api/upload', methods=['POST'])
def upload_document():
    """Upload PDF file for processing"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are supported'}), 400
        
        # Extract content from PDF
        content = extract_pdf_content(file)
        
        if not content:
            return jsonify({'error': 'Could not extract text from PDF'}), 400
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Store document data
        documents[document_id] = {
            'id': document_id,
            'filename': file.filename,
            'content': content,
            'content_length': len(content),
            'created_at': datetime.now().isoformat(),
            'summary': None,
            'qa_history': []
        }

        # Index document with RAG
        if RAG_AVAILABLE and rag:
            rag.index_document(document_id, content)
            print(f"Document {document_id[:8]} indexed in RAG system")
        
        return jsonify({
            'document_id': document_id,
            'message': 'PDF uploaded and processed successfully',
            'filename': file.filename,
            'content_length': len(content),
            'content_preview': content[:200] + '...' if len(content) > 200 else content
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/summarize', methods=['POST'])
def summarize_document():
    """Generate summary for uploaded document using LLM"""
    try:
        data = request.json
        document_id = data.get('document_id')
        
        if not document_id or document_id not in documents:
            return jsonify({'error': 'Document not found'}), 404
        
        doc = documents[document_id]
        # Limit content length to avoid token limits
        content = doc['content'][:2000]
        
        prompt = f"""Summarize the following document in 3-5 clear sentences. Focus on the main ideas and key points.

Document:
{content}

Summary:"""
        
        summary = call_ollama(prompt)
        
        if summary:
            documents[document_id]['summary'] = summary
            return jsonify({
                'document_id': document_id,
                'summary': summary
            }), 200
        else:
            return jsonify({'error': 'Failed to generate summary'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """Answer questions using RAG retrieval"""
    try:
        data = request.json
        document_id = data.get('document_id')
        question = data.get('question')
        
        if not document_id or document_id not in documents:
            return jsonify({'error': 'Document not found'}), 404
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        doc = documents[document_id]
        
        # Use RAG to retrieve relevant chunks
        if RAG_AVAILABLE and rag:
            relevant_chunks = rag.retrieve(document_id, question, top_k=3)
            if relevant_chunks:
                context = '\n\n'.join(relevant_chunks)
                print(f"Retrieved {len(relevant_chunks)} relevant chunks")
            else:
                # Fallback to original method
                context = doc['content'][:2000]
        else:
            # Fallback if RAG not available
            context = doc['content'][:2000]
        
        prompt = f"""Based on the following document excerpts, answer the question accurately.
If the answer is not in the provided text, say so.

Document excerpts:
{context}

Question: {question}

Answer:"""
        
        answer = call_ollama(prompt)
        
        if answer:
            # Store Q&A history
            doc['qa_history'].append({
                'question': question,
                'answer': answer,
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify({
                'document_id': document_id,
                'question': question,
                'answer': answer,
                'method': 'RAG' if RAG_AVAILABLE else 'fallback'
            }), 200
        else:
            return jsonify({'error': 'Failed to generate answer'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents', methods=['GET'])
def list_documents():
    """List all uploaded documents"""
    try:
        doc_list = []
        for doc_id, doc_data in documents.items():
            doc_list.append({
                'id': doc_id,
                'filename': doc_data['filename'],
                'content_length': doc_data['content_length'],
                'created_at': doc_data['created_at'],
                'has_summary': bool(doc_data.get('summary'))
            })
        
        return jsonify({'documents': doc_list}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/document/<document_id>/content', methods=['GET'])
def get_document_content(document_id):
    """Get document content for preview"""
    try:
        if document_id not in documents:
            return jsonify({'error': 'Document not found'}), 404
        
        document_data = documents[document_id]
        
        return jsonify({
            'document_id': document_id,
            'filename': document_data['filename'],
            'content': document_data['content'],
            'content_length': document_data['content_length'],
            'created_at': document_data['created_at']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/document/<document_id>/history', methods=['GET'])
def get_qa_history(document_id):
    """Get Q&A history for a document"""
    try:
        if document_id not in documents:
            return jsonify({'error': 'Document not found'}), 404
        
        doc = documents[document_id]
        return jsonify({
            'document_id': document_id,
            'filename': doc['filename'],
            'qa_history': doc['qa_history'],
            'has_summary': bool(doc.get('summary'))
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def extract_pdf_content(file):
    """Extract text content from PDF file"""
    try:
        content = ""
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            file.save(tmp_file.name)
            tmp_path = tmp_file.name
        
        # Extract text from PDF
        with open(tmp_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Extract text from all pages
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text.strip():  # Only add non-empty pages
                    content += f"\n--- Page {page_num + 1} ---\n"
                    content += page_text + "\n"
        
        # Clean up temporary file
        os.unlink(tmp_path)
        
        # Clean up extracted text
        content = clean_extracted_text(content)
        
        return content if content.strip() else None
        
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return None

def clean_extracted_text(text):
    """Clean and format extracted text"""
    import re
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?;:()\-\'"]+', ' ', text)
    
    # Fix spacing around punctuation
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)
    
    return text.strip()

@app.route('/api/document/<document_id>/download', methods=['GET'])
def download_summary(document_id):
    """Download document summary and Q&A results"""
    try:
        if document_id not in documents:
            return jsonify({'error': 'Document not found'}), 404
        
        doc = documents[document_id]
        
        # Prepare download content
        download_content = f"""Document: {doc['filename']}
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

===============================
DOCUMENT SUMMARY
===============================
{doc.get('summary', 'No summary generated yet.')}

"""
        
        # Add Q&A history if exists
        if doc['qa_history']:
            download_content += """
===============================
QUESTIONS & ANSWERS
===============================
"""
            for i, qa in enumerate(doc['qa_history'], 1):
                download_content += f"""
Q{i}: {qa['question']}
A{i}: {qa['answer']}
---
"""
        
        return jsonify({
            'filename': f"{doc['filename']}_summary.txt",
            'content': download_content
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5050)