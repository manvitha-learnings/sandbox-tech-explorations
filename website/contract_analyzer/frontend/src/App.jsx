import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { 
  Upload, 
  FileText, 
  AlertTriangle, 
  Calendar, 
  Users, 
  ShieldCheck, 
  MessageSquare, 
  Send, 
  Settings, 
  RefreshCw,
  Clock
} from 'lucide-react';

function App() {
  // Config
  const [backendUrl, setBackendUrl] = useState(
    window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
      ? 'https://contract-analyzer-backend-450158463415.us-central1.run.app'
      : window.location.origin
  );
  const [showConfig, setShowConfig] = useState(false);

  // File Upload & Analysis
  const [file, setFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState(() => {
    const saved = localStorage.getItem('contract_analysis');
    return saved ? JSON.parse(saved) : null;
  });
  const [error, setError] = useState(null);

  // Chat
  const [sessionId, setSessionId] = useState(() => {
    return localStorage.getItem('contract_session_id') || ('session_' + Math.random().toString(36).substring(2, 9));
  });
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState(() => {
    const saved = localStorage.getItem('contract_chat_history');
    return saved ? JSON.parse(saved) : [
      {
        role: 'model',
        text: "Hello! I am your Antigravity Contract Agent. Upload a contract on the left, and I'll be ready to answer any questions or analyze specific clauses for you."
      }
    ];
  });
  const [isChatLoading, setIsChatLoading] = useState(false);
  const chatEndRef = useRef(null);

  // Save states to localStorage
  useEffect(() => {
    if (analysis) {
      localStorage.setItem('contract_analysis', JSON.stringify(analysis));
    } else {
      localStorage.removeItem('contract_analysis');
    }
  }, [analysis]);

  useEffect(() => {
    localStorage.setItem('contract_session_id', sessionId);
  }, [sessionId]);

  useEffect(() => {
    localStorage.setItem('contract_chat_history', JSON.stringify(chatHistory));
  }, [chatHistory]);

  // Auto scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, isChatLoading]);

  // Validate File type and size
  const validateFile = (selectedFile) => {
    setError(null);
    if (!selectedFile) return false;

    const allowedExtensions = /(\.pdf|\.txt)$/i;
    if (!allowedExtensions.exec(selectedFile.name)) {
      setError("Unsupported file type. Only PDF (.pdf) and Text (.txt) files are allowed.");
      return false;
    }

    const maxSize = 5 * 1024 * 1024; // 5 MB
    if (selectedFile.size > maxSize) {
      setError("File size exceeds the maximum limit of 5 MB.");
      return false;
    }

    return true;
  };

  // Handle Drag & Drop
  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (validateFile(droppedFile)) {
        setFile(droppedFile);
      } else {
        setFile(null);
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (validateFile(selectedFile)) {
        setFile(selectedFile);
      } else {
        setFile(null);
        e.target.value = '';
      }
    }
  };

  // Upload and Analyze
  const analyzeContract = async () => {
    if (!file) return;
    if (!validateFile(file)) {
      setFile(null);
      return;
    }
    setIsAnalyzing(true);
    setError(null);
    setAnalysis(null);

    const newSessionId = 'session_' + Math.random().toString(36).substring(2, 9);
    setSessionId(newSessionId);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${backendUrl}/api/analyze`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setAnalysis(response.data);

      // Seed the ADK chat session with the contract context so the agent knows about it
      // We send an initial hidden message to the agent or tell the agent about the contract
      const contractSummaryText = `Here is the contract analysis overview:
- Parties: ${response.data.parties.join(', ')}
- Summary: ${response.data.general_summary}

Please help answer user questions based on this contract.`;

      setChatHistory([
        {
          role: 'model',
          text: `Successfully uploaded and analyzed "${file.name}"! I've extracted the key information. Feel free to ask me any questions about the contract terms, clauses, or obligations.`
        }
      ]);
      
      // Let the agent know about the contract by doing an initial quiet message
      try {
        await axios.post(`${backendUrl}/run`, {
          app_name: 'contract_agent',
          user_id: 'default_user',
          session_id: newSessionId,
          new_message: {
            role: 'user',
            parts: [{ text: `I have uploaded a contract named ${file.name}. Please keep it in mind for our conversation.` }]
          }
        });
      } catch (err) {
        console.warn("Failed to seed session context:", err);
      }

    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'An error occurred during analysis.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Handle Chat Submit
  const handleSendChat = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || isChatLoading) return;

    const userMessage = chatInput;
    setChatInput('');
    setChatHistory(prev => [...prev, { role: 'user', text: userMessage }]);
    setIsChatLoading(true);

    try {
      const response = await axios.post(`${backendUrl}/run`, {
        app_name: 'contract_agent',
        user_id: 'default_user',
        session_id: sessionId,
        new_message: {
          role: 'user',
          parts: [{ text: userMessage }]
        }
      });

      // Extract text content from ADK response events
      const rawEvents = response.data || [];
      const replyText = rawEvents
        .map(event => event.content?.parts?.map(p => p.text).join('') || '')
        .join('');

      setChatHistory(prev => [...prev, { role: 'model', text: replyText || "I've processed your request but didn't receive a response." }]);
    } catch (err) {
      setChatHistory(prev => [...prev, { role: 'model', text: `Error: Failed to connect to agent. ${err.message}` }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const getRiskBadgeColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'high':
        return 'bg-red-50 text-red-700 border-red-200';
      case 'medium':
        return 'bg-yellow-50 text-yellow-700 border-yellow-200';
      case 'low':
        return 'bg-green-50 text-green-700 border-green-200';
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex justify-between items-center shadow-sm">
        <div className="flex items-center gap-3">
          <div className="bg-indigo-600 p-2.5 rounded-xl text-white shadow-md shadow-indigo-100">
            <ShieldCheck size={24} />
          </div>
          <div>
            <h1 className="font-bold text-xl text-slate-800 tracking-tight">Contract Analyzer</h1>
            <p className="text-xs font-medium text-indigo-600">Powered by Antigravity ADK</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button 
            onClick={() => setShowConfig(!showConfig)}
            className="flex items-center gap-1.5 px-3.5 py-2 text-sm font-semibold text-slate-600 hover:text-indigo-600 bg-slate-100 hover:bg-indigo-50 border border-slate-200 hover:border-indigo-100 rounded-xl transition duration-150"
          >
            <Settings size={16} />
            Config
          </button>
        </div>
      </header>

      {/* Backend Config Box */}
      {showConfig && (
        <div className="bg-white border-b border-slate-200 px-6 py-3 shadow-inner transition-all duration-300">
          <div className="max-w-xl flex items-center gap-3">
            <label className="text-sm font-bold text-slate-700 whitespace-nowrap">Backend Server URL:</label>
            <input 
              type="text" 
              value={backendUrl} 
              onChange={(e) => setBackendUrl(e.target.value)}
              className="flex-1 px-3 py-1.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
            />
          </div>
        </div>
      )}

      {/* Main Content Side-by-Side */}
      <main className="flex-1 flex flex-col md:flex-row overflow-hidden">
        {/* Left Side: Upload and Structured Report */}
        <section className="flex-1 p-6 overflow-y-auto flex flex-col gap-6">
          
          {/* File Uploader */}
          <div 
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            className="bg-white border-2 border-dashed border-slate-300 rounded-2xl p-8 text-center hover:border-indigo-500 transition duration-150 flex flex-col items-center justify-center gap-4 bg-gradient-to-b from-white to-slate-50 shadow-sm"
          >
            <div className="bg-indigo-50 p-4 rounded-full text-indigo-600">
              <Upload size={32} />
            </div>
            <div>
              <p className="font-bold text-slate-700">Drag & drop your contract file here</p>
              <p className="text-xs text-slate-400 mt-1">Supports PDF and Text (.pdf, .txt)</p>
            </div>
            
            <div className="flex items-center gap-3">
              <input 
                type="file" 
                id="file-select"
                accept=".pdf,.txt"
                onChange={handleFileChange}
                className="hidden"
              />
              <label 
                htmlFor="file-select" 
                className="px-4 py-2 text-sm font-semibold text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-xl cursor-pointer transition duration-150"
              >
                Browse Files
              </label>
              
              {file && (
                <button 
                  onClick={analyzeContract}
                  disabled={isAnalyzing}
                  className="flex items-center gap-2 px-5 py-2 text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 rounded-xl transition duration-150 shadow-md shadow-indigo-100"
                >
                  {isAnalyzing ? <RefreshCw className="animate-spin" size={16} /> : 'Analyze Contract'}
                </button>
              )}
            </div>

            {file && (
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-600 bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200">
                <FileText size={14} className="text-indigo-600" />
                <span>Selected: {file.name}</span>
              </div>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm font-semibold">
              {error}
            </div>
          )}

          {/* Analysis Results View */}
          {analysis ? (
            <div className="flex flex-col gap-6">
              {/* Summary */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                <h3 className="font-bold text-slate-800 text-lg mb-3">General Summary</h3>
                <p className="text-slate-600 text-sm leading-relaxed">{analysis.general_summary}</p>
              </div>

              {/* Parties & Dates */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Parties */}
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col gap-3">
                  <div className="flex items-center gap-2 font-bold text-slate-800 border-b border-slate-100 pb-2.5">
                    <Users className="text-indigo-600" size={18} />
                    <span>Involved Parties</span>
                  </div>
                  <ul className="text-sm font-medium text-slate-600 flex flex-col gap-2">
                    {analysis.parties.map((party, index) => (
                      <li key={index} className="bg-slate-50 px-3 py-2 rounded-lg border border-slate-100 flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
                        {party}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Dates */}
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col gap-3">
                  <div className="flex items-center gap-2 font-bold text-slate-800 border-b border-slate-100 pb-2.5">
                    <Calendar className="text-indigo-600" size={18} />
                    <span>Key Dates</span>
                  </div>
                  <div className="flex flex-col gap-3.5 mt-1">
                    {analysis.effective_date && (
                      <div className="flex gap-3">
                        <div className="bg-indigo-50 p-2 rounded-lg text-indigo-600 h-fit">
                          <Clock size={16} />
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-slate-400">Effective Date</p>
                          <p className="text-sm font-bold text-slate-700">{analysis.effective_date.date || 'Not explicitly stated'}</p>
                          <p className="text-xs text-slate-500 mt-0.5">{analysis.effective_date.explanation}</p>
                        </div>
                      </div>
                    )}
                    {analysis.expiration_date && (
                      <div className="flex gap-3">
                        <div className="bg-indigo-50 p-2 rounded-lg text-indigo-600 h-fit">
                          <Clock size={16} />
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-slate-400">Expiration Date</p>
                          <p className="text-sm font-bold text-slate-700">{analysis.expiration_date.date || 'Not explicitly stated'}</p>
                          <p className="text-xs text-slate-500 mt-0.5">{analysis.expiration_date.explanation}</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Key Clauses */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                <h3 className="font-bold text-slate-800 text-lg mb-4 border-b border-slate-100 pb-2.5">Important Clauses</h3>
                <div className="flex flex-col gap-5">
                  {analysis.key_clauses.map((clause, idx) => (
                    <div key={idx} className="border border-slate-150 rounded-xl p-4.5 bg-slate-50 hover:bg-white transition duration-150">
                      <div className="flex justify-between items-center mb-2">
                        <h4 className="font-bold text-sm text-indigo-700 bg-indigo-50 border border-indigo-100 px-2.5 py-1 rounded-md h-fit">
                          {clause.clause_name}
                        </h4>
                      </div>
                      <p className="text-slate-600 text-sm font-medium leading-relaxed mb-3">{clause.summary}</p>
                      {clause.raw_text && (
                        <div className="bg-white border border-slate-200 rounded-lg p-3 font-mono text-xs text-slate-500 max-h-24 overflow-y-auto italic">
                          "{clause.raw_text}"
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Obligations */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                <h3 className="font-bold text-slate-800 text-lg mb-4 border-b border-slate-100 pb-2.5">Key Obligations</h3>
                <div className="flex flex-col gap-3">
                  {analysis.obligations.map((item, idx) => (
                    <div key={idx} className="flex gap-3 bg-slate-50 border border-slate-150 p-4 rounded-xl items-start">
                      <span className="text-xs font-bold text-indigo-700 bg-indigo-100 px-2 py-0.5 rounded-md mt-0.5 whitespace-nowrap">
                        {item.party}
                      </span>
                      <p className="text-sm font-medium text-slate-600 leading-relaxed">{item.obligation}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Risk Assessment */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                <h3 className="font-bold text-slate-800 text-lg mb-4 border-b border-slate-100 pb-2.5 flex items-center gap-2">
                  <AlertTriangle className="text-red-500" size={20} />
                  <span>Risk Assessment</span>
                </h3>
                <div className="flex flex-col gap-4">
                  {analysis.risk_assessment.map((risk, idx) => (
                    <div key={idx} className="flex gap-4 p-4 border rounded-xl hover:shadow-sm transition bg-white">
                      <span className={`px-2.5 py-1 text-xs font-bold rounded-lg border h-fit uppercase ${getRiskBadgeColor(risk.severity)}`}>
                        {risk.severity}
                      </span>
                      <div className="flex-1">
                        <h4 className="font-bold text-sm text-slate-800">{risk.risk_type}</h4>
                        <p className="text-slate-500 text-xs mt-1 font-medium">{risk.explanation}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          ) : (
            !isAnalyzing && (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-400 py-12">
                <FileText size={48} strokeWidth={1.5} className="mb-2 text-slate-300" />
                <p className="font-medium">No contract analyzed yet.</p>
                <p className="text-xs mt-1">Upload a PDF or Text file above to start.</p>
              </div>
            )
          )}

          {isAnalyzing && (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-500 py-12 gap-3">
              <RefreshCw className="animate-spin text-indigo-600" size={32} />
              <p className="font-bold">Analyzing contract details...</p>
              <p className="text-xs text-slate-400">Extracting clauses, dates, obligations and risks with Gemini.</p>
            </div>
          )}

        </section>

        {/* Right Side: Agent Chat UI */}
        <section className="w-full md:w-[450px] border-t md:border-t-0 md:border-l border-slate-200 bg-white flex flex-col shadow-inner">
          <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex items-center gap-2">
            <MessageSquare size={18} className="text-indigo-600" />
            <h3 className="font-bold text-slate-800 text-sm">Contract Chat Assistant</h3>
          </div>

          {/* Chat Messages */}
          <div className="flex-1 p-4 overflow-y-auto flex flex-col gap-4">
            {chatHistory.map((msg, index) => (
              <div 
                key={index}
                className={`max-w-[85%] p-3.5 rounded-2xl text-sm leading-relaxed ${
                  msg.role === 'user' 
                    ? 'self-end bg-indigo-600 text-white font-medium rounded-tr-none' 
                    : 'self-start bg-slate-100 text-slate-700 font-medium rounded-tl-none border border-slate-200'
                }`}
              >
                {msg.text}
              </div>
            ))}

            {isChatLoading && (
              <div className="self-start bg-slate-100 border border-slate-200 text-slate-500 max-w-[85%] p-3.5 rounded-2xl rounded-tl-none text-sm flex items-center gap-2 font-medium">
                <RefreshCw size={14} className="animate-spin text-indigo-600" />
                <span>Agent is thinking...</span>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* Chat Input */}
          <form onSubmit={handleSendChat} className="p-4 border-t border-slate-100 flex gap-2">
            <input 
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Ask a question about the contract..."
              className="flex-1 px-4 py-2.5 text-sm border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium"
              disabled={isChatLoading}
            />
            <button 
              type="submit" 
              disabled={isChatLoading || !chatInput.trim()}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-200 text-white disabled:text-slate-400 p-2.5 rounded-xl transition duration-150 shadow-md shadow-indigo-100"
            >
              <Send size={18} />
            </button>
          </form>
        </section>
      </main>
    </div>
  );
}

export default App;
