# test_upload.py - Simple test script for PDF upload
import requests

# API base URL
BASE_URL = "http://127.0.0.1:5000/api"

def test_health():
    """Test if API is running"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print("Health Check:", response.json())
        return response.status_code == 200
    except Exception as e:
        print("Error connecting to API:", e)
        return False

def test_upload_pdf(pdf_path):
    """Test PDF upload"""
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{BASE_URL}/upload", files=files)
            
        print(f"\nUpload Status: {response.status_code}")
        result = response.json()
        print("Upload Response:", result)
        
        if response.status_code == 201:
            return result.get('document_id')
        return None
        
    except FileNotFoundError:
        print(f"Error: PDF file '{pdf_path}' not found!")
        return None
    except Exception as e:
        print("Upload error:", e)
        return None

def test_list_documents():
    """Test document listing"""
    try:
        response = requests.get(f"{BASE_URL}/documents")
        print(f"\nList Documents Status: {response.status_code}")
        print("Documents:", response.json())
    except Exception as e:
        print("List documents error:", e)

def test_get_content(document_id):
    """Test getting document content"""
    if not document_id:
        return
        
    try:
        response = requests.get(f"{BASE_URL}/document/{document_id}/content")
        print(f"\nGet Content Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Content Preview:")
            print(f"Filename: {result['filename']}")
            print(f"Content Length: {result['content_length']}")
            print("First 300 characters:")
            print("-" * 50)
            print(result['content'][:300] + "...")
        else:
            print("Error:", response.json())
            
    except Exception as e:
        print("Get content error:", e)

if __name__ == "__main__":
    print("=== AskDocAI API Test ===")
    
    # Test API connection
    if not test_health():
        print("❌ API is not running! Please start the Flask app first.")
        exit(1)
    
    print("✅ API is running!")
    
    # Test PDF upload
    pdf_file = "test.pdf"  # Change this to your PDF file path
    print(f"\n📄 Testing PDF upload with: {pdf_file}")
    
    document_id = test_upload_pdf(pdf_file)
    
    if document_id:
        print("✅ Upload successful!")
        
        # Test other endpoints
        test_list_documents()
        test_get_content(document_id)
    else:
        print("❌ Upload failed!")
    
    print("\n=== Test Complete ===")

# Alternative test using curl commands
print("""
=== Alternative: Test with curl commands ===

1. Health check:
curl http://127.0.0.1:5000/api/health

2. Upload PDF:
curl -X POST -F "file=@your_file.pdf" http://127.0.0.1:5000/api/upload

3. List documents:
curl http://127.0.0.1:5000/api/documents

4. Get document content (replace DOC_ID):
curl http://127.0.0.1:5000/api/document/DOC_ID/content
""")