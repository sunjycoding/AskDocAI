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

metrics = {
    'total_uploads': 0,
    'total_summaries': 0,
    'total_questions': 0,
    'avg_response_time': []
}

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
        
        metrics['total_uploads'] += 1

        return jsonify({
            'document_id': document_id,
            'message': 'PDF uploaded and processed successfully',
            'filename': file.filename,
            'content_length': len(content),
            'content_preview': content[:200] + '...' if len(content) > 200 else content
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/upload-url', methods=['POST'])
def upload_from_url():
    """Extract content from web URL"""
    try:
        from urllib.parse import urlparse
        import re
        
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Fetch webpage content
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if response.status_code != 200:
            return jsonify({'error': f'Failed to fetch URL: {response.status_code}'}), 400
        
        # Simple HTML text extraction
        text = response.text
        # Remove script and style elements
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        # Remove HTML tags
        text = re.sub('<[^<]+?>', ' ', text)
        # Clean whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        if not text or len(text) < 100:
            return jsonify({'error': 'Could not extract enough text from URL'}), 400
        
        # Create document entry
        document_id = str(uuid.uuid4())
        domain = urlparse(url).netloc
        
        documents[document_id] = {
            'id': document_id,
            'filename': f"Web: {domain}",
            'content': text[:10000],  # Limit to 10000 chars
            'content_length': len(text),
            'created_at': datetime.now().isoformat(),
            'summary': None,
            'qa_history': [],
            'source_type': 'web',
            'source_url': url
        }
        
        # Index with RAG if available
        if RAG_AVAILABLE and rag:
            rag.index_document(document_id, text[:10000])
            print(f"Web content {document_id[:8]} indexed in RAG system")
        
        # Update metrics
        metrics['total_uploads'] += 1
        
        return jsonify({
            'document_id': document_id,
            'message': 'Web content extracted successfully',
            'url': url,
            'domain': domain,
            'content_length': len(text),
            'content_preview': text[:200] + '...' if len(text) > 200 else text
        }), 201
        
    except requests.Timeout:
        return jsonify({'error': 'URL request timed out'}), 408
    except Exception as e:
        return jsonify({'error': f'Failed to extract web content: {str(e)}'}), 500

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
            
            metrics['total_summaries'] += 1

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
    """Answer questions about the document using relevant chunks"""
    try:
        data = request.json
        document_id = data.get('document_id')
        question = data.get('question')
        
        if not document_id or document_id not in documents:
            return jsonify({'error': 'Document not found'}), 404
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        doc = documents[document_id]
        
        # Track which chunks were used
        used_chunks = []
        
        # Use RAG to retrieve relevant chunks
        if RAG_AVAILABLE and rag:
            relevant_chunks = rag.retrieve(document_id, question, top_k=3)
            if relevant_chunks:
                context = '\n\n'.join(relevant_chunks)
                used_chunks = relevant_chunks[:2]  # Save first 2 chunks as sources
                print(f"Retrieved {len(relevant_chunks)} relevant chunks")
            else:
                context = doc['content'][:2000]
                used_chunks = [doc['content'][:500]]  # Use beginning as source
        else:
            context = doc['content'][:2000]
            used_chunks = [doc['content'][:500]]
        
        # Updated prompt to include citation instruction
        prompt = f"""Based on the following document excerpts, answer the question accurately.
Include specific references to the information source when possible.

Document excerpts:
{context}

Question: {question}

Answer (cite the document when referencing specific information):"""
        
        answer = call_ollama(prompt)
        
        if answer:
            # Build source reference
            source_info = {
                'document': doc['filename'],
                'type': doc.get('source_type', 'pdf'),
                'url': doc.get('source_url', None),
                'excerpt': used_chunks[0][:200] + '...' if used_chunks else None
            }
            
            # Store Q&A history with source
            doc['qa_history'].append({
                'question': question,
                'answer': answer,
                'sources': source_info,
                'timestamp': datetime.now().isoformat()
            })
            
            # Update metrics
            metrics['total_questions'] += 1
            
            return jsonify({
                'document_id': document_id,
                'question': question,
                'answer': answer,
                'source_reference': f"Source: {doc['filename']}",
                'source_details': source_info,
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
    """Download document summary and Q&A results with sources"""
    try:
        if document_id not in documents:
            return jsonify({'error': 'Document not found'}), 404
        
        doc = documents[document_id]
        
        # Prepare download content with better formatting
        download_content = f"""===============================
ASKDOCAI DOCUMENT ANALYSIS REPORT
===============================

Document: {doc['filename']}
Type: {doc.get('source_type', 'PDF').upper()}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'URL: ' + doc.get('source_url', '') if doc.get('source_url') else ''}

===============================
DOCUMENT SUMMARY
===============================
{doc.get('summary', 'No summary generated yet.')}

"""
        
        # Add Q&A history with sources
        if doc['qa_history']:
            download_content += """===============================
QUESTIONS & ANSWERS WITH SOURCES
===============================
"""
            for i, qa in enumerate(doc['qa_history'], 1):
                download_content += f"""
Question {i}: {qa['question']}

Answer: {qa['answer']}

Source: {qa.get('sources', {}).get('document', 'Unknown')}
Timestamp: {qa['timestamp']}
---
"""
        
        # Add metrics summary
        download_content += f"""
===============================
DOCUMENT METRICS
===============================
Total Questions Asked: {len(doc['qa_history'])}
Document Size: {doc['content_length']} characters
Analysis Method: {'RAG-enhanced' if RAG_AVAILABLE else 'Direct extraction'}
"""
        
        return jsonify({
            'filename': f"{doc['filename'].replace(':', '').replace('/', '_')}_analysis.txt",
            'content': download_content
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get system performance metrics"""
    return jsonify({
        'total_uploads': metrics['total_uploads'],
        'total_summaries': metrics['total_summaries'],
        'total_questions': metrics['total_questions'],
        'documents_in_memory': len(documents),
        'rag_enabled': RAG_AVAILABLE,
        'model_used': OLLAMA_MODEL if 'OLLAMA_MODEL' in globals() else 'none'
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5050)