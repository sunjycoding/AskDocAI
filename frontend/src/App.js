import React, { useState } from 'react';
import { Upload, FileText, MessageCircle, Download, Loader2, CheckCircle, AlertCircle } from 'lucide-react';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadedDoc, setUploadedDoc] = useState(null);
  const [summary, setSummary] = useState('');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('upload');

  // Real API call to backend
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setLoading(true);
      
      try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('http://127.0.0.1:5000/api/upload', {
          method: 'POST',
          body: formData,
        });
        
        if (response.ok) {
          const data = await response.json();
          setUploadedDoc({
            id: data.document_id,
            filename: data.filename,
            content_length: data.content_length,
            created_at: new Date().toISOString(),
            content_preview: data.content_preview
          });
          setActiveTab('summary');
          alert('Document uploaded successfully!');
        } else {
          const errorData = await response.json();
          alert(`Upload failed: ${errorData.error}`);
        }
      } catch (error) {
        console.error('Upload error:', error);
        alert(`Network error: ${error.message}. Please make sure the backend is running on http://127.0.0.1:5000`);
      } finally {
        setLoading(false);
      }
    } else {
      alert('Please select a PDF file');
    }
  };

  const generateSummary = async () => {
    if (!uploadedDoc) return;
    
    setLoading(true);
    try {
      const response = await fetch(`http://127.0.0.1:5000/api/document/${uploadedDoc.id}/content`, {
        method: 'GET',
      });
      
      if (response.ok) {
        const data = await response.json();
        setSummary(data.content); // 直接把提取的内容设置为summary
      } else {
        const errorData = await response.json();
        alert(`Failed to get document content: ${errorData.error}`);
      }
    } catch (error) {
      console.error('Error fetching document content:', error);
      alert('Network error occurred while fetching document content.');
    } finally {
      setLoading(false);
    }
  };

  const askQuestion = async () => {
    if (!question.trim() || !uploadedDoc) return;
    
    setLoading(true);
    setTimeout(() => {
      setAnswer(`Based on the uploaded document "${uploadedDoc.filename}", here's the answer to your question:

**Question**: ${question}

**Answer**: According to the document, this topic is covered in Section 3.2. The key points include:

1. The methodology follows established best practices in the field
2. Implementation requires careful consideration of data quality and preprocessing steps
3. Performance metrics should be evaluated using cross-validation techniques

**Source References**: This information can be found on pages 15-18 of the document, specifically in the sections discussing implementation strategies and evaluation methods.

*Note: This is a demo response. In the full implementation, answers would be generated using RAG (Retrieval-Augmented Generation) with actual document content.*`);
      setLoading(false);
    }, 2000);
  };

  const TabButton = ({ id, label, icon: Icon, isActive, onClick }) => (
    <button
      onClick={() => onClick(id)}
      className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
        isActive
          ? 'bg-blue-600 text-white shadow-lg transform scale-105'
          : 'bg-white text-gray-600 hover:bg-gray-50 hover:text-blue-600 shadow-md'
      }`}
    >
      <Icon size={20} />
      <span>{label}</span>
    </button>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-3 rounded-xl">
                <FileText size={24} />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">AskDocAI</h1>
                <p className="text-sm text-gray-600">Smart Document Assistant</p>
              </div>
            </div>
            <div className="text-sm text-gray-500">
              Demo Version
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Navigation Tabs */}
        <div className="flex space-x-4 mb-8">
          <TabButton
            id="upload"
            label="Upload Document"
            icon={Upload}
            isActive={activeTab === 'upload'}
            onClick={setActiveTab}
          />
          <TabButton
            id="summary"
            label="Generate Summary"
            icon={FileText}
            isActive={activeTab === 'summary'}
            onClick={setActiveTab}
          />
          <TabButton
            id="qa"
            label="Ask Questions"
            icon={MessageCircle}
            isActive={activeTab === 'qa'}
            onClick={setActiveTab}
          />
        </div>

        {/* Content Area */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-lg p-6">
              {/* Upload Tab */}
              {activeTab === 'upload' && (
                <div className="space-y-6">
                  <h2 className="text-2xl font-bold text-gray-800 mb-4">Upload Your Document</h2>
                  
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
                    <Upload size={48} className="mx-auto text-gray-400 mb-4" />
                    <div className="space-y-2">
                      <p className="text-lg font-medium text-gray-700">
                        Drop your PDF file here or click to browse
                      </p>
                      <p className="text-sm text-gray-500">
                        Supported format: PDF (max 50MB)
                      </p>
                    </div>
                    <input
                      type="file"
                      accept=".pdf"
                      onChange={handleFileUpload}
                      className="mt-4"
                    />
                  </div>

                  {loading && (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="animate-spin text-blue-600 mr-3" size={24} />
                      <span className="text-lg text-gray-600">
                        {uploadedDoc ? 'Processing your document...' : 'Uploading and processing your document...'}
                      </span>
                    </div>
                  )}

                  {uploadedDoc && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <div className="flex items-center space-x-3">
                        <CheckCircle className="text-green-600" size={24} />
                        <div>
                          <h3 className="font-semibold text-green-800">Document Uploaded Successfully!</h3>
                          <p className="text-sm text-green-600">
                            {uploadedDoc.filename} ({uploadedDoc.content_length} characters)
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Summary Tab */}
              {activeTab === 'summary' && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h2 className="text-2xl font-bold text-gray-800">Document Summary</h2>
                    {uploadedDoc && !summary && (
                      <button
                        onClick={generateSummary}
                        disabled={loading}
                        className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center space-x-2"
                      >
                        {loading ? <Loader2 className="animate-spin" size={16} /> : <FileText size={16} />}
                        <span>{loading ? 'Generating...' : 'Generate Summary'}</span>
                      </button>
                    )}
                  </div>

                  {!uploadedDoc && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <div className="flex items-center space-x-3">
                        <AlertCircle className="text-yellow-600" size={24} />
                        <p className="text-yellow-800">Please upload a document first to generate a summary.</p>
                      </div>
                    </div>
                  )}

                  {summary && (
                    <div className="bg-gray-50 rounded-lg p-6 max-h-96 overflow-y-auto">
                      <div className="prose max-w-none">
                        <div className="whitespace-pre-wrap text-gray-800 leading-relaxed text-sm">
                          {summary}
                        </div>
                      </div>
                      <div className="mt-4 pt-4 border-t">
                        <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2">
                          <Download size={16} />
                          <span>Download Summary</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Q&A Tab */}
              {activeTab === 'qa' && (
                <div className="space-y-6">
                  <h2 className="text-2xl font-bold text-gray-800">Ask Questions</h2>

                  {!uploadedDoc && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <div className="flex items-center space-x-3">
                        <AlertCircle className="text-yellow-600" size={24} />
                        <p className="text-yellow-800">Please upload a document first to ask questions.</p>
                      </div>
                    </div>
                  )}

                  {uploadedDoc && (
                    <div className="space-y-4">
                      <div className="flex space-x-4">
                        <input
                          type="text"
                          placeholder="Ask a question about your document..."
                          value={question}
                          onChange={(e) => setQuestion(e.target.value)}
                          className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          onKeyPress={(e) => e.key === 'Enter' && askQuestion()}
                        />
                        <button
                          onClick={askQuestion}
                          disabled={loading || !question.trim()}
                          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center space-x-2"
                        >
                          {loading ? <Loader2 className="animate-spin" size={16} /> : <MessageCircle size={16} />}
                          <span>{loading ? 'Asking...' : 'Ask'}</span>
                        </button>
                      </div>

                      {answer && (
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                          <div className="whitespace-pre-line text-gray-800 leading-relaxed">
                            {answer}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Document Info */}
            {uploadedDoc && (
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Document Info</h3>
                <div className="space-y-3 text-sm">
                  <div>
                    <span className="font-medium text-gray-600">Filename:</span>
                    <p className="text-gray-800">{uploadedDoc.filename}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-600">Size:</span>
                    <p className="text-gray-800">{uploadedDoc.content_length} characters</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-600">Uploaded:</span>
                    <p className="text-gray-800">{new Date(uploadedDoc.created_at).toLocaleString()}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Quick Actions */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Quick Actions</h3>
              <div className="space-y-3">
                <button className="w-full text-left px-4 py-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                  <div className="font-medium text-gray-800">Sample Questions</div>
                  <div className="text-sm text-gray-600">View example questions</div>
                </button>
                <button className="w-full text-left px-4 py-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                  <div className="font-medium text-gray-800">Export Results</div>
                  <div className="text-sm text-gray-600">Download Q&A history</div>
                </button>
                <button className="w-full text-left px-4 py-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                  <div className="font-medium text-gray-800">Clear Session</div>
                  <div className="text-sm text-gray-600">Start over with new document</div>
                </button>
              </div>
            </div>

            {/* System Status */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">System Status</h3>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-gray-600">Backend API: Online</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                  <span className="text-sm text-gray-600">AI Service: Demo Mode</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-gray-600">File Storage: Ready</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;