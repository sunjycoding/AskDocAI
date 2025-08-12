# app.py - AskDocAI Backend Framework
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

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
    return jsonify({'message': 'Upload endpoint - not implemented yet'})

@app.route('/api/summarize', methods=['POST'])
def summarize_document():
    return jsonify({'message': 'Summarize endpoint - not implemented yet'})

@app.route('/api/ask', methods=['POST'])
def ask_question():
    return jsonify({'message': 'Q&A endpoint - not implemented yet'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)