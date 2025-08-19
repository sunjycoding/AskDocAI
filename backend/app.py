# app.py - AskDocAI Backend Framework
from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
import tempfile
import os
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app, origins=['http://127.0.0.1:3000', 'http://127.0.0.1:3000'])

# In-memory storage for demo
documents = {}

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
    return jsonify({'message': 'Summarize endpoint - not implemented yet'})

@app.route('/api/ask', methods=['POST'])
def ask_question():
    return jsonify({'message': 'Q&A endpoint - not implemented yet'})

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)