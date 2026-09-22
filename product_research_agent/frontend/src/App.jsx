import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { 
  Laptop, 
  Search, 
  Columns, 
  MessageSquare, 
  Send, 
  Settings, 
  RefreshCw,
  AlertCircle,
  TrendingUp,
  Cpu,
  HardDrive,
  CreditCard,
  CheckCircle,
  HelpCircle,
  ChevronRight,
  Sparkles,
  Info,
  ExternalLink
} from 'lucide-react';

function App() {
  // Config
  const [backendUrl, setBackendUrl] = useState(() => {
    // Dynamically fallback to localhost if hosted locally
    return window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
      ? 'http://localhost:8080'
      : window.location.origin;
  });
  const [showConfig, setShowConfig] = useState(false);

  // States
  const [chatInput, setChatInput] = useState('');
  const [sessionId, setSessionId] = useState(() => {
    return localStorage.getItem('product_session_id') || ('sess_' + Math.random().toString(36).substring(2, 9));
  });
  const [chatHistory, setChatHistory] = useState(() => {
    const saved = localStorage.getItem('product_chat_history');
    return saved ? JSON.parse(saved) : [
      {
        role: 'model',
        text: "Hello! I am your Product Research Assistant. I can search, compare, and recommend laptops based on your requirements and budget. Try asking me: \n\n*\"I need a laptop under $1,000 for programming. Find 5 options and recommend the best one.\"*"
      }
    ];
  });
  
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [statusLogs, setStatusLogs] = useState([]);
  
  // Product & Comparison States parsed from agent's tools
  const [searchResults, setSearchResults] = useState(() => {
    const saved = localStorage.getItem('product_search_results');
    return saved ? JSON.parse(saved) : [];
  });
  const [comparisonData, setComparisonData] = useState(() => {
    const saved = localStorage.getItem('product_comparison_data');
    return saved ? JSON.parse(saved) : null;
  });
  const [recommendedLaptop, setRecommendedLaptop] = useState(() => {
    const saved = localStorage.getItem('product_recommended_laptop');
    return saved ? JSON.parse(saved) : null;
  });
  const [activeTab, setActiveTab] = useState('search'); // 'search' | 'compare' | 'recommendation'

  const chatEndRef = useRef(null);

  // Save states to localStorage
  useEffect(() => {
    localStorage.setItem('product_session_id', sessionId);
  }, [sessionId]);

  useEffect(() => {
    localStorage.setItem('product_chat_history', JSON.stringify(chatHistory));
  }, [chatHistory]);

  useEffect(() => {
    localStorage.setItem('product_search_results', JSON.stringify(searchResults));
  }, [searchResults]);

  useEffect(() => {
    if (comparisonData) {
      localStorage.setItem('product_comparison_data', JSON.stringify(comparisonData));
    } else {
      localStorage.removeItem('product_comparison_data');
    }
  }, [comparisonData]);

  useEffect(() => {
    if (recommendedLaptop) {
      localStorage.setItem('product_recommended_laptop', JSON.stringify(recommendedLaptop));
    } else {
      localStorage.removeItem('product_recommended_laptop');
    }
  }, [recommendedLaptop]);

  // Auto scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, isChatLoading]);

  // Reset session
  const handleResetSession = () => {
    const newSess = 'sess_' + Math.random().toString(36).substring(2, 9);
    setSessionId(newSess);
    setChatHistory([
      {
        role: 'model',
        text: "Session reset! How can I help you with your product research today?"
      }
    ]);
    setSearchResults([]);
    setComparisonData(null);
    setRecommendedLaptop(null);
    setStatusLogs([]);
    setActiveTab('search');
  };

  // Helper to parse tool responses from ADK Events
  const parseEventsForProductData = (events) => {
    events.forEach(event => {
      // Inspect event content parts
      if (event.content && event.content.parts) {
        event.content.parts.forEach(part => {
          // 1. Tool execution notifications (status logs)
          if (part.functionCall) {
            const { name, args } = part.functionCall;
            const toolName = name.replace('product_', '');
            if (toolName === 'search_products') {
              setStatusLogs(prev => [...prev, `Searching laptops with criteria: ${JSON.stringify(args)}`]);
            } else if (toolName === 'get_product_details') {
              setStatusLogs(prev => [...prev, `Fetching details for: ${args.product_id}`]);
            } else if (toolName === 'compare_products') {
              setStatusLogs(prev => [...prev, `Comparing selected candidates...`]);
            }
          }

          // 2. Tool response outputs (actual product data)
          if (part.functionResponse) {
            const { name, response } = part.functionResponse;
            const toolName = name.replace('product_', '');
            
            // Extract the result payload (FastMCP wraps return in a 'content' key or similar structure)
            const payload = response.response || response.content || response;
            
            if (toolName === 'search_products') {
              // Try to find the list of products
              let list = [];
              if (Array.isArray(payload)) {
                list = payload;
              } else if (payload && Array.isArray(payload.result)) {
                list = payload.result;
              } else if (payload && typeof payload === 'object') {
                // If it's a FastMCP response wrapping text/json
                try {
                  const data = JSON.parse(payload);
                  if (Array.isArray(data)) list = data;
                } catch (e) {
                  // Fallback
                  if (payload.text) {
                    try {
                      const data = JSON.parse(payload.text);
                      if (Array.isArray(data)) list = data;
                    } catch(err){}
                  }
                }
              }
              
              if (list.length > 0) {
                setSearchResults(list);
                setActiveTab('search');
              }
            } 
            
            else if (toolName === 'compare_products') {
              let compObj = null;
              if (payload && payload.comparison) {
                compObj = payload;
              } else if (payload && typeof payload === 'object') {
                try {
                  const data = JSON.parse(payload);
                  if (data && data.comparison) compObj = data;
                } catch (e) {
                  if (payload.text) {
                    try {
                      const data = JSON.parse(payload.text);
                      if (data && data.comparison) compObj = data;
                    } catch(err){}
                  }
                }
              }
              
              if (compObj) {
                setComparisonData(compObj);
                setActiveTab('compare');
              }
            }
          }
        });
      }
    });
  };

  // Extract recommended product from text response using LLM clues
  const inferRecommendedProduct = (text, products) => {
    if (!products || products.length === 0) return;
    
    // Search for laptop ID or name matching in recommendation text
    let bestMatch = null;
    let maxClues = 0;
    
    products.forEach(p => {
      let clues = 0;
      const nameParts = p.name.toLowerCase().split(' ');
      
      // Look for brand + key name parts in text
      if (text.toLowerCase().includes(p.brand.toLowerCase())) clues += 1;
      nameParts.forEach(part => {
        if (part.length > 2 && text.toLowerCase().includes(part)) {
          clues += 1;
        }
      });
      
      if (clues > maxClues) {
        maxClues = clues;
        bestMatch = p;
      }
    });
    
    if (bestMatch && maxClues > 2) {
      setRecommendedLaptop(bestMatch);
    }
  };

  // Send Chat Message
  const handleSendChat = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || isChatLoading) return;

    const userMsg = chatInput;
    setChatInput('');
    setChatHistory(prev => [...prev, { role: 'user', text: userMsg }]);
    setIsChatLoading(true);
    setStatusLogs(['Initiating ADK Agent turn...']);

    try {
      const response = await axios.post(`${backendUrl}/run`, {
        app_name: 'product_agent',
        user_id: 'default_user',
        session_id: sessionId,
        new_message: {
          role: 'user',
          parts: [{ text: userMsg }]
        }
      });

      const rawEvents = response.data || [];
      
      // Parse any product data from the execution events
      parseEventsForProductData(rawEvents);

      // Extract text content from final response events
      const replyText = rawEvents
        .map(event => event.content?.parts?.map(p => p.text).join('') || '')
        .join('');

      const cleanReplyText = replyText || "I have analyzed the laptops using the MCP tools but didn't return a text summary. Please check the results tab.";
      
      setChatHistory(prev => [...prev, { role: 'model', text: cleanReplyText }]);
      
      // Infer recommendation from text
      inferRecommendedProduct(cleanReplyText, searchResults);

    } catch (err) {
      console.error("Error communicating with ADK agent:", err);
      setChatHistory(prev => [...prev, { 
        role: 'model', 
        text: `Error: Failed to connect to backend agent. Make sure the FastAPI app is running at ${backendUrl}.\n\nDetails: ${err.message}` 
      }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
      {/* Header */}
      <header className="bg-slate-950 border-b border-slate-800 px-6 py-4 flex justify-between items-center shadow-lg">
        <div className="flex items-center gap-3">
          <div className="bg-cyan-600 p-2.5 rounded-xl text-white shadow-md shadow-cyan-900/50">
            <Laptop size={24} className="animate-pulse" />
          </div>
          <div>
            <h1 className="font-bold text-xl text-slate-100 tracking-tight">AI Product Research Assistant</h1>
            <p className="text-xs font-semibold text-cyan-400">Google ADK Agent & Model Context Protocol</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button 
            onClick={handleResetSession}
            className="px-3.5 py-2 text-sm font-semibold text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl transition duration-150"
          >
            Reset Session
          </button>
          <button 
            onClick={() => setShowConfig(!showConfig)}
            className="flex items-center gap-1.5 px-3.5 py-2 text-sm font-semibold text-slate-300 hover:text-cyan-400 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl transition duration-150"
          >
            <Settings size={16} />
            Config
          </button>
        </div>
      </header>

      {/* Backend Config Box */}
      {showConfig && (
        <div className="bg-slate-950 border-b border-slate-800 px-6 py-3 shadow-inner transition-all duration-300">
          <div className="max-w-xl flex items-center gap-3">
            <label className="text-sm font-bold text-slate-300 whitespace-nowrap">Backend Agent URL:</label>
            <input 
              type="text" 
              value={backendUrl} 
              onChange={(e) => setBackendUrl(e.target.value)}
              className="flex-1 px-3 py-1.5 text-sm bg-slate-900 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-cyan-500 font-mono"
            />
          </div>
        </div>
      )}

      {/* Main Split-Screen Layout */}
      <main className="flex-1 flex flex-col md:flex-row overflow-hidden">
        
        {/* Left Side: Conversational Chat */}
        <section className="w-full md:w-1/2 flex flex-col border-r border-slate-800 bg-slate-900/50">
          {/* Chat Headers */}
          <div className="px-6 py-3 border-b border-slate-800 bg-slate-950/40 flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-300">
              <MessageSquare size={16} className="text-cyan-400" />
              <span>Agent Conversation</span>
            </div>
            {isChatLoading && (
              <span className="flex items-center gap-1.5 text-xs text-cyan-400">
                <RefreshCw size={12} className="animate-spin" />
                Thinking...
              </span>
            )}
          </div>

          {/* Messages Window */}
          <div className="flex-1 p-6 overflow-y-auto flex flex-col gap-4">
            {chatHistory.map((msg, index) => (
              <div 
                key={index} 
                className={`flex flex-col max-w-[85%] ${msg.role === 'user' ? 'self-end items-end' : 'self-start items-start'}`}
              >
                <div 
                  className={`px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-line shadow-md ${
                    msg.role === 'user' 
                      ? 'bg-cyan-600 text-white rounded-tr-none' 
                      : 'bg-slate-800 text-slate-100 border border-slate-700/50 rounded-tl-none'
                  }`}
                >
                  {msg.text}
                </div>
                <span className="text-[10px] text-slate-500 mt-1 font-semibold">
                  {msg.role === 'user' ? 'You' : 'ADK Agent'}
                </span>
              </div>
            ))}
            
            {/* Status logs / tool invocation tracking */}
            {isChatLoading && statusLogs.length > 0 && (
              <div className="bg-slate-950/50 border border-slate-800/80 rounded-xl p-3.5 self-start w-full max-w-md my-2 flex flex-col gap-1.5">
                <div className="flex items-center gap-1.5 text-[11px] font-bold text-cyan-400 uppercase tracking-wider mb-1">
                  <Sparkles size={12} />
                  <span>Agent Execution Trace</span>
                </div>
                {statusLogs.map((log, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs text-slate-400 font-mono">
                    <ChevronRight size={12} className="text-cyan-500 mt-0.5 shrink-0" />
                    <span>{log}</span>
                  </div>
                ))}
              </div>
            )}
            
            <div ref={chatEndRef} />
          </div>

          {/* Input Box */}
          <form onSubmit={handleSendChat} className="p-4 border-t border-slate-800 bg-slate-950/60 flex gap-2">
            <input 
              type="text" 
              value={chatInput} 
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Ask for laptop recommendations..."
              disabled={isChatLoading}
              className="flex-1 px-4 py-3 rounded-xl bg-slate-900 border border-slate-700 text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500 disabled:opacity-55"
            />
            <button 
              type="submit"
              disabled={isChatLoading || !chatInput.trim()}
              className="px-4.5 py-3 bg-cyan-600 hover:bg-cyan-700 disabled:bg-slate-800 disabled:text-slate-500 rounded-xl font-bold transition duration-150 flex items-center justify-center shadow-lg"
            >
              <Send size={18} />
            </button>
          </form>
        </section>

        {/* Right Side: Visual Product Catalog & Details */}
        <section className="w-full md:w-1/2 flex flex-col bg-slate-950">
          
          {/* Tab Navigation */}
          <div className="flex border-b border-slate-800 bg-slate-950">
            <button 
              onClick={() => setActiveTab('search')}
              className={`flex-1 py-3.5 text-sm font-bold flex items-center justify-center gap-2 border-b-2 transition ${
                activeTab === 'search' 
                  ? 'border-cyan-500 text-cyan-400 bg-slate-900/30' 
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Search size={16} />
              <span>Search Results ({searchResults.length})</span>
            </button>
            <button 
              onClick={() => setActiveTab('compare')}
              disabled={!comparisonData}
              className={`flex-1 py-3.5 text-sm font-bold flex items-center justify-center gap-2 border-b-2 transition ${
                !comparisonData ? 'opacity-35 cursor-not-allowed' : ''
              } ${
                activeTab === 'compare' 
                  ? 'border-cyan-500 text-cyan-400 bg-slate-900/30' 
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Columns size={16} />
              <span>Comparison Spec Matrix</span>
            </button>
            <button 
              onClick={() => setActiveTab('recommendation')}
              disabled={!recommendedLaptop}
              className={`flex-1 py-3.5 text-sm font-bold flex items-center justify-center gap-2 border-b-2 transition ${
                !recommendedLaptop ? 'opacity-35 cursor-not-allowed' : ''
              } ${
                activeTab === 'recommendation' 
                  ? 'border-cyan-500 text-cyan-400 bg-slate-900/30' 
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <CheckCircle size={16} />
              <span>Best Choice</span>
            </button>
          </div>

          {/* Active View Content */}
          <div className="flex-1 p-6 overflow-y-auto">
            
            {/* SEARCH RESULTS TAB */}
            {activeTab === 'search' && (
              <div className="flex flex-col gap-5">
                {searchResults.length === 0 ? (
                  <div className="text-center py-16 flex flex-col items-center justify-center gap-3">
                    <Laptop size={48} className="text-slate-700" />
                    <p className="font-bold text-slate-500">No products fetched yet.</p>
                    <p className="text-xs text-slate-600 max-w-xs">Ask the agent to find options for you, and the laptops will display here.</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 gap-4">
                    {searchResults.map((product) => (
                      <div 
                        key={product.id} 
                        className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-cyan-500/50 transition duration-150 shadow-md relative"
                      >
                        {/* Header info */}
                        <div className="flex justify-between items-start gap-4 mb-2">
                          <div>
                            <span className="text-[10px] font-bold uppercase tracking-wider bg-cyan-900/40 text-cyan-400 px-2.5 py-0.5 rounded-full border border-cyan-800/30">
                              {product.brand}
                            </span>
                            <h3 className="font-bold text-lg text-slate-100 mt-1">{product.name}</h3>
                          </div>
                          <span className="text-xl font-black text-cyan-400 font-mono">
                            ${product.price.toFixed(2)}
                          </span>
                        </div>

                        {/* Description */}
                        <p className="text-xs text-slate-400 mb-4 font-medium">{product.description}</p>

                        {/* Specs grid */}
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-slate-950/40 p-3 rounded-lg border border-slate-850 mb-4">
                          <div className="flex items-center gap-2 text-xs">
                            <Cpu size={14} className="text-cyan-500" />
                            <span className="text-slate-400 font-semibold truncate" title={product.specs.CPU}>
                              {product.specs.CPU}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 text-xs">
                            <Cpu size={14} className="text-cyan-500" />
                            <span className="text-slate-400 font-semibold truncate" title={product.specs.RAM}>
                              {product.specs.RAM}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 text-xs">
                            <HardDrive size={14} className="text-cyan-500" />
                            <span className="text-slate-400 font-semibold truncate" title={product.specs.Storage}>
                              {product.specs.Storage}
                            </span>
                          </div>
                        </div>

                        {/* Pros / Cons preview */}
                        <div className="flex flex-col gap-1.5 mb-4">
                          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Pros</div>
                          <div className="flex flex-wrap gap-1">
                            {product.pros.slice(0, 2).map((pro, index) => (
                              <span key={index} className="text-[10px] font-semibold bg-emerald-950/40 text-emerald-400 px-2 py-0.5 rounded border border-emerald-900/30">
                                ✓ {pro}
                              </span>
                            ))}
                          </div>
                        </div>

                        {/* Product Link */}
                        {product.url && (
                          <div className="pt-3 border-t border-slate-800/60 mt-3">
                            <a 
                              href={product.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300 font-bold transition"
                            >
                              <span>View Product Page</span>
                              <ExternalLink size={12} />
                            </a>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* COMPARISON TAB */}
            {activeTab === 'compare' && comparisonData && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
                <div className="p-4 border-b border-slate-800 bg-slate-950 flex items-center justify-between">
                  <h3 className="font-bold text-slate-200 text-sm">Specification Comparison Table</h3>
                  <span className="text-xs bg-slate-800 text-slate-400 px-2.5 py-1 rounded font-bold">
                    {comparisonData.products?.length || 0} Candidates
                  </span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-slate-950/60 border-b border-slate-800 text-xs text-slate-400 font-bold">
                        <th className="p-3.5 font-bold uppercase tracking-wider">Specification</th>
                        {comparisonData.products?.map((p, idx) => (
                          <th key={idx} className="p-3.5 font-bold text-cyan-400 border-l border-slate-800 w-[30%]">
                            {p.name}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 text-xs">
                      {Object.keys(comparisonData.comparison).map((specName) => {
                        const values = comparisonData.comparison[specName];
                        return (
                          <tr key={specName} className="hover:bg-slate-850/30 transition">
                            <td className="p-3.5 font-bold text-slate-300 bg-slate-950/20">{specName}</td>
                            {comparisonData.products?.map((p, idx) => {
                              const val = values[p.name];
                              return (
                                <td key={idx} className="p-3.5 border-l border-slate-800 text-slate-400">
                                  {Array.isArray(val) ? (
                                    <ul className="list-disc pl-3 flex flex-col gap-1">
                                      {val.map((item, idy) => <li key={idy}>{item}</li>)}
                                    </ul>
                                  ) : specName === 'Product Page' ? (
                                    <a 
                                      href={val} 
                                      target="_blank" 
                                      rel="noopener noreferrer"
                                      className="inline-flex items-center gap-1 text-cyan-400 hover:text-cyan-300 font-bold transition"
                                    >
                                      <span>View Page</span>
                                      <ExternalLink size={10} />
                                    </a>
                                  ) : (
                                    <span className={specName === 'Price' ? 'text-cyan-400 font-extrabold text-sm' : ''}>
                                      {val}
                                    </span>
                                  )}
                                </td>
                              );
                            })}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* RECOMMENDATION TAB */}
            {activeTab === 'recommendation' && recommendedLaptop && (
              <div className="bg-slate-900 border-2 border-cyan-500 rounded-2xl p-6 shadow-2xl relative overflow-hidden bg-gradient-to-br from-slate-900 to-slate-950">
                <div className="absolute top-0 right-0 bg-cyan-500 text-slate-950 font-black text-[10px] uppercase tracking-wider px-6 py-2 rotate-45 translate-x-7 translate-y-3">
                  Recommended
                </div>

                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle className="text-emerald-500" size={24} />
                  <span className="text-xs font-bold text-cyan-400 uppercase tracking-widest">Assistant Selection</span>
                </div>

                <h2 className="text-2xl font-black text-slate-100 leading-tight mb-1">{recommendedLaptop.name}</h2>
                <p className="text-sm font-bold text-slate-400 mb-4">{recommendedLaptop.brand} Laptop</p>

                <div className="text-3xl font-black text-cyan-400 font-mono mb-4">
                  ${recommendedLaptop.price.toFixed(2)}
                </div>

                <p className="text-sm text-slate-300 leading-relaxed mb-6 bg-slate-950/40 p-4 rounded-xl border border-slate-850">
                  {recommendedLaptop.description}
                </p>

                {/* Product CTA */}
                {recommendedLaptop.url && (
                  <div className="mb-6">
                    <a 
                      href={recommendedLaptop.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 px-5 py-3 bg-cyan-600 hover:bg-cyan-700 text-slate-950 font-black rounded-xl shadow-lg transition duration-150 text-xs uppercase tracking-wider"
                    >
                      <span>View Official Product Page</span>
                      <ExternalLink size={14} />
                    </a>
                  </div>
                )}

                {/* Technical specifications */}
                <h3 className="font-bold text-sm text-slate-200 mb-3 flex items-center gap-1.5">
                  <Info size={16} className="text-cyan-500" />
                  <span>Technical Specifications</span>
                </h3>
                <div className="grid grid-cols-2 gap-4 bg-slate-950/60 p-4 rounded-xl border border-slate-850 mb-6">
                  {Object.keys(recommendedLaptop.specs).map(key => (
                    <div key={key} className="text-xs">
                      <span className="text-slate-500 font-bold">{key}:</span>
                      <p className="text-slate-300 mt-0.5 font-medium">{recommendedLaptop.specs[key]}</p>
                    </div>
                  ))}
                </div>

                {/* Pros and Cons */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div>
                    <h4 className="text-xs font-black text-emerald-400 uppercase tracking-wider mb-2">✓ Key Pros for Coders</h4>
                    <ul className="flex flex-col gap-1.5 text-xs text-slate-300 font-medium">
                      {recommendedLaptop.pros.map((pro, index) => (
                        <li key={index} className="flex gap-2 items-start">
                          <span className="text-emerald-500 font-bold mt-0.5">✓</span>
                          <span>{pro}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="text-xs font-black text-rose-400 uppercase tracking-wider mb-2">✗ Cons / Trade-offs</h4>
                    <ul className="flex flex-col gap-1.5 text-xs text-slate-300 font-medium">
                      {recommendedLaptop.cons.map((con, index) => (
                        <li key={index} className="flex gap-2 items-start">
                          <span className="text-rose-500 font-bold mt-0.5">✗</span>
                          <span>{con}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

          </div>
        </section>

      </main>
    </div>
  );
}

export default App;
