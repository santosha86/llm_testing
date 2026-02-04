import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Bot, ChevronLeft, MessageSquare, RotateCcw, Send, Truck, FileText, Users, TrendingUp, Download, HelpCircle, Database, Clock, BookOpen } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { ChatMessage, DisambiguationOption, ClarificationOption, VisualizationConfig } from '../types';
import { API_BASE_URL } from '../constants';
import DataVisualization from './DataVisualization';

// Icon mapping for dynamic icons from API
const ICON_MAP: Record<string, React.FC<{ size?: number; className?: string }>> = {
  Truck,
  FileText,
  Users,
  TrendingUp,
};

interface CategoryData {
  id: string;
  label: string;
  icon: string;
  queries: string[];
}

const ChatWidget: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const [categories, setCategories] = useState<CategoryData[]>([]);
  const [isLoadingCategories, setIsLoadingCategories] = useState(true);
  const [sessionId] = useState(() => {
    // crypto.randomUUID requires secure context (HTTPS)
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    // Fallback for HTTP contexts
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  });
  const [streamingContent, setStreamingContent] = useState('');
  const [streamingPhase, setStreamingPhase] = useState('');
  const chatEndRef = useRef<HTMLDivElement>(null);
  const activeReaderRef = useRef<ReadableStreamDefaultReader<Uint8Array> | null>(null);

  // Cleanup active stream on unmount
  useEffect(() => {
    return () => {
      if (activeReaderRef.current) {
        activeReaderRef.current.cancel();
        activeReaderRef.current = null;
      }
    };
  }, []);

  // Fetch categories from API
  useEffect(() => {
    const controller = new AbortController();

    const fetchCategories = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/categories`, {
          signal: controller.signal,
          headers: {
            'ngrok-skip-browser-warning': 'true'
          }
        });
        if (response.ok) {
          const data = await response.json();
          setCategories(data);
        }
      } catch (error) {
        if (error instanceof Error && error.name !== 'AbortError') {
          console.error('Failed to fetch categories:', error);
        }
      } finally {
        if (!controller.signal.aborted) {
          setIsLoadingCategories(false);
        }
      }
    };
    fetchCategories();

    return () => controller.abort();
  }, []);

  // Auto-scroll to bottom when messages or streaming content changes
  useEffect(() => {
    if (messages.length > 0 || streamingContent || streamingPhase) {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [messages, isTyping, streamingContent, streamingPhase]);

  const getCurrentTime = useCallback(() => {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }, []);

  const handleSendMessage = useCallback(async (text: string, forcedRoute?: string) => {
    if (!text.trim()) return;

    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: getCurrentTime()
    };

    setMessages(prev => [...prev, newMessage]);
    setInputValue('');
    setSelectedCategory(null);
    setIsTyping(true);
    setStreamingContent('');
    setStreamingPhase('');

    try {
      let route = forcedRoute;

      // Step 1: Get route classification (skip if route is forced from clarification)
      if (!route) {
        const routeResponse = await fetch(`${API_BASE_URL}/api/route`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'ngrok-skip-browser-warning': 'true'
          },
          body: JSON.stringify({ query: text, session_id: sessionId }),
        });

        if (!routeResponse.ok) throw new Error('Route API request failed');
        const routeData = await routeResponse.json();
        route = routeData.route;
      }

      if (route === 'sql' || route === 'csv') {
        // Step 2a: SQL/CSV queries - use non-streaming endpoint
        const response = await fetch(`${API_BASE_URL}/api/query`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'ngrok-skip-browser-warning': 'true'
          },
          body: JSON.stringify({ query: text, session_id: sessionId, route: route }),
        });

        if (!response.ok) throw new Error('API request failed');

        const data = await response.json();
        setIsTyping(false);

        const botMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.content,
          timestamp: getCurrentTime(),
          originalQuery: text,
          metadata: {
            responseTime: data.response_time,
            sources: data.sources,
            tableData: data.table_data,
            sqlQuery: data.sql_query,
            needsDisambiguation: data.needs_disambiguation,
            disambiguationOptions: data.disambiguation_options,
            needsClarification: data.needs_clarification,
            clarificationMessage: data.clarification_message,
            clarificationOptions: data.clarification_options,
            visualization: data.visualization
          }
        };
        setMessages(prev => [...prev, botMessage]);

      } else if (route === 'clarify') {
        // Step 2b: Clarification needed - run workflow to get clarification options
        const response = await fetch(`${API_BASE_URL}/api/query`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'ngrok-skip-browser-warning': 'true'
          },
          body: JSON.stringify({ query: text, session_id: sessionId }),
        });

        if (!response.ok) throw new Error('API request failed');

        const data = await response.json();
        setIsTyping(false);

        const botMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.content,
          timestamp: getCurrentTime(),
          originalQuery: text,
          metadata: {
            responseTime: data.response_time,
            sources: data.sources,
            needsClarification: data.needs_clarification,
            clarificationMessage: data.clarification_message,
            clarificationOptions: data.clarification_options
          }
        };
        setMessages(prev => [...prev, botMessage]);

      } else {
        // Step 2b: PDF queries - use streaming endpoint
        const response = await fetch(`${API_BASE_URL}/api/query/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'ngrok-skip-browser-warning': 'true'
          },
          body: JSON.stringify({ query: text, session_id: sessionId, route: route }),
        });

        if (!response.ok) throw new Error('API request failed');

        const reader = response.body?.getReader();
        activeReaderRef.current = reader || null;
        const decoder = new TextDecoder();
        let accumulatedContent = '';
        let finalMetadata: any = null;

        if (reader) {
          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6));

                  if (data.phase && !data.done) {
                    // Update phase indicator
                    if (data.phase === 'planning') {
                      setStreamingPhase('Planning...');
                    } else if (data.phase === 'retrieval') {
                      setStreamingPhase('Retrieving documents...');
                    } else if (data.phase === 'reasoning') {
                      setStreamingPhase('Analyzing...');
                    } else if (data.phase === 'answer') {
                      setStreamingPhase('');
                      accumulatedContent += data.content;
                      setStreamingContent(accumulatedContent);
                    }
                  } else if (data.done) {
                    finalMetadata = data;
                    if (data.content && !accumulatedContent) {
                      accumulatedContent = data.content;
                    }
                  }
                } catch (e) {
                  // Ignore parse errors for incomplete chunks
                }
              }
            }
          }
          } finally {
            activeReaderRef.current = null;
          }
        }

        setIsTyping(false);
        setStreamingContent('');
        setStreamingPhase('');

        const botMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: accumulatedContent || finalMetadata?.content || 'No response',
          timestamp: getCurrentTime(),
          metadata: {
            responseTime: finalMetadata?.response_time || '0s',
            sources: finalMetadata?.sources || ['System'],
            tableData: finalMetadata?.table_data,
            sqlQuery: finalMetadata?.sql_query
          }
        };
        setMessages(prev => [...prev, botMessage]);
      }

    } catch (error) {
      console.error('Failed to get response:', error);
      setIsTyping(false);
      setStreamingContent('');
      setStreamingPhase('');

      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '**Error:** Unable to connect to the server. Please make sure the backend is running.',
        timestamp: getCurrentTime(),
        metadata: {
          responseTime: "0s",
          sources: ["Error"]
        }
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  }, [sessionId, getCurrentTime]);

  const handleClearChat = useCallback(async () => {
    setMessages([]);
    setSelectedCategory(null);
    setStreamingContent('');
    setStreamingPhase('');

    // Clear server session memory
    try {
      await fetch(`${API_BASE_URL}/api/session/clear`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true'
        },
        body: JSON.stringify({ session_id: sessionId })
      });
    } catch (error) {
      console.error('Failed to clear session:', error);
    }
  }, [sessionId]);

  const handleDownloadCSV = useCallback((tableData: { columns: string[]; rows: any[][] }) => {
    const csvRows: string[] = [];

    // Header
    csvRows.push(tableData.columns.map(col => `"${col}"`).join(','));

    // Data rows (ALL rows)
    tableData.rows.forEach(row => {
      csvRows.push(row.map(cell => {
        const value = cell !== null ? String(cell) : '';
        return `"${value.replace(/"/g, '""')}"`;
      }).join(','));
    });

    // UTF-8 BOM for Excel compatibility with Arabic
    const BOM = '\uFEFF';
    const csvContent = BOM + csvRows.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = `query_results_${Date.now()}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, []);

  return (
    <div className="flex flex-col h-[700px] w-full bg-gradient-to-b from-[#1a1a2e] to-[#16213e] rounded-3xl overflow-hidden shadow-2xl border border-indigo-500/20">
      
      {/* Header */}
      <div className="bg-gradient-to-r from-[#0f3460] to-[#16213e] p-4 flex items-center justify-center gap-3 border-b border-indigo-500/20 relative z-10 shrink-0">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
          <Bot className="text-white w-6 h-6" />
        </div>
        <div className="text-center">
          <h2 className="text-white font-semibold text-sm tracking-wide">SPB Conversational Chatbot</h2>
          <div className="flex items-center justify-center gap-1.5 text-[11px] text-indigo-300">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse-soft"></span>
            <span>Online • {getCurrentTime()}</span>
          </div>
        </div>
      </div>

      {/* Chat Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar bg-[#1a1a2e]/50">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-start text-center py-4 px-2">
            <div className="w-14 h-14 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center mb-4 shadow-xl shadow-indigo-500/20">
              <Bot className="text-white w-7 h-7" />
            </div>
            <h3 className="text-white font-bold text-lg mb-1">How can I help you today?</h3>
            <p className="text-slate-400 text-xs mb-4 max-w-xs mx-auto">Ask questions about dispatch, waybills, contractors, and routes</p>

            <div className="w-full transition-all duration-300">
               {isLoadingCategories ? (
                 <div className="flex items-center justify-center p-4">
                   <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                 </div>
               ) : !selectedCategory ? (
                 /* Top Level Categories */
                 <div className="grid grid-cols-2 gap-2">
                    {categories.map(cat => {
                      const IconComponent = ICON_MAP[cat.icon] || Truck;
                      return (
                        <button
                          key={cat.id}
                          onClick={() => setSelectedCategory(cat.id)}
                          className="flex flex-col items-center p-3 bg-[#16213e] border border-indigo-500/20 rounded-xl hover:bg-indigo-600/20 hover:border-indigo-500/50 hover:shadow-lg transition-all group"
                        >
                           <div className="p-2 bg-indigo-500/10 rounded-lg mb-2 group-hover:bg-indigo-500/20 transition-colors">
                              <IconComponent size={20} className="text-indigo-400 group-hover:text-white" />
                           </div>
                           <span className="text-xs font-semibold text-slate-200 group-hover:text-white">{cat.label}</span>
                        </button>
                      );
                    })}
                 </div>
               ) : (
                 /* Sub Questions */
                 <div className="bg-[#16213e] border border-indigo-500/20 rounded-xl overflow-hidden shadow-xl">
                    <div className="flex items-center justify-between p-3 border-b border-indigo-500/10 bg-[#0f3460]/50">
                       <div className="flex items-center gap-2">
                          <div className="p-1.5 bg-indigo-500/10 rounded-md">
                             {(() => {
                                const cat = categories.find(c => c.id === selectedCategory);
                                const IconComponent = cat ? ICON_MAP[cat.icon] || Truck : Truck;
                                return <IconComponent size={14} className="text-indigo-400" />;
                             })()}
                          </div>
                          <span className="text-xs font-semibold text-white">
                             {categories.find(c => c.id === selectedCategory)?.label}
                          </span>
                       </div>
                       <button
                         onClick={() => setSelectedCategory(null)}
                         className="flex items-center gap-1 text-xs text-slate-400 hover:text-white px-2 py-1 hover:bg-white/5 rounded-md transition-colors"
                       >
                          <ChevronLeft size={12} /> Back
                       </button>
                    </div>
                    <div className="p-2 space-y-1.5">
                       {categories.find(c => c.id === selectedCategory)?.queries.map((q, idx) => (
                         <button
                           key={idx}
                           onClick={() => handleSendMessage(q)}
                           className="w-full text-left p-2.5 rounded-lg text-xs bg-indigo-500/5 border border-indigo-500/10 text-slate-300 hover:bg-indigo-500/20 hover:text-white hover:border-indigo-500/30 transition-all flex items-start gap-2 group"
                         >
                            <MessageSquare size={14} className="mt-0.5 shrink-0 text-indigo-400/70 group-hover:text-indigo-400" />
                            <span>{q}</span>
                         </button>
                       ))}
                    </div>
                 </div>
               )}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div 
              key={msg.id} 
              className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div 
                className={`max-w-[85%] rounded-2xl p-4 shadow-lg ${
                  msg.role === 'user' 
                    ? 'bg-gradient-to-br from-indigo-600 to-purple-600 text-white rounded-br-sm' 
                    : 'bg-[#16213e] border border-indigo-500/20 text-slate-200 rounded-bl-sm'
                }`}
              >
                {msg.role === 'assistant' ? (
                   <div className="prose prose-invert prose-p:text-sm prose-li:text-sm prose-headings:text-sm prose-strong:text-indigo-300 max-w-none">
                     <ReactMarkdown
                       remarkPlugins={[remarkGfm]}
                       rehypePlugins={[rehypeRaw]}
                       components={{
                         table: ({node, ...props}) => (
                           <div className="overflow-x-auto my-3">
                             <table className="w-full text-xs border-collapse border border-indigo-500/30" {...props} />
                           </div>
                         ),
                         thead: ({node, ...props}) => (
                           <thead className="bg-indigo-500/20" {...props} />
                         ),
                         th: ({node, ...props}) => (
                           <th className="px-3 py-2 text-left text-indigo-300 font-semibold border border-indigo-500/20 whitespace-nowrap" {...props} />
                         ),
                         td: ({node, ...props}) => (
                           <td className="px-3 py-2 border border-indigo-500/20 text-slate-300" {...props} />
                         ),
                       }}
                     >
                       {msg.content}
                     </ReactMarkdown>

                     {/* Visualization */}
                     {msg.metadata?.visualization?.should_visualize && msg.metadata?.tableData && (
                       <DataVisualization
                         visualization={msg.metadata.visualization}
                         tableData={msg.metadata.tableData}
                       />
                     )}

                     {/* Table Data (shown if no visualization or toggled to table view) */}
                     {msg.metadata?.tableData && msg.metadata.tableData.rows.length > 0 && !msg.metadata?.visualization?.should_visualize && (
                       <div className="mt-3 overflow-x-auto">
                         <table className="w-full text-[11px] border-collapse">
                           <thead>
                             <tr className="bg-indigo-500/20">
                               {msg.metadata.tableData.columns.map((col, i) => (
                                 <th key={i} className="px-2 py-1.5 text-left text-indigo-300 font-semibold border border-indigo-500/20 whitespace-nowrap">
                                   {col}
                                 </th>
                               ))}
                             </tr>
                           </thead>
                           <tbody>
                             {msg.metadata.tableData.rows.slice(0, 50).map((row, rowIdx) => (
                               <tr key={rowIdx} className="hover:bg-indigo-500/10">
                                 {row.map((cell, cellIdx) => (
                                   <td key={cellIdx} className="px-2 py-1 border border-indigo-500/10 text-slate-300">
                                     {cell !== null ? String(cell) : '-'}
                                   </td>
                                 ))}
                               </tr>
                             ))}
                           </tbody>
                         </table>
                         {msg.metadata.tableData.rows.length > 50 && (
                           <p className="text-[10px] text-slate-400 mt-2">
                             Showing 50 of {msg.metadata.tableData.rows.length} rows (CSV download includes all rows)
                           </p>
                         )}
                       </div>
                     )}

                     {/* Disambiguation Options */}
                     {msg.metadata?.needsDisambiguation && msg.metadata.disambiguationOptions && (
                       <div className="mt-3 pt-3 border-t border-indigo-500/20">
                         <div className="flex items-center gap-2 mb-2">
                           <HelpCircle size={14} className="text-amber-400" />
                           <span className="text-xs text-amber-300 font-medium">Please select an option:</span>
                         </div>
                         <div className="flex flex-wrap gap-2">
                           {msg.metadata.disambiguationOptions.map((option, idx) => (
                             <button
                               key={idx}
                               onClick={() => handleSendMessage(option.value)}
                               className="flex flex-col items-start p-2.5 bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 hover:border-indigo-500/50 rounded-lg transition-all group"
                             >
                               <span className="text-xs font-semibold text-indigo-300 group-hover:text-white">
                                 {option.display}
                               </span>
                               {option.description && (
                                 <span className="text-[10px] text-slate-400 group-hover:text-slate-300 mt-0.5">
                                   {option.description}
                                 </span>
                               )}
                             </button>
                           ))}
                         </div>
                       </div>
                     )}

                     {/* Clarification Options - Route Selection */}
                     {msg.metadata?.needsClarification && msg.metadata.clarificationOptions && (
                       <div className="mt-3 pt-3 border-t border-indigo-500/20">
                         <div className="flex items-center gap-2 mb-3">
                           <HelpCircle size={14} className="text-cyan-400" />
                           <span className="text-xs text-cyan-300 font-medium">Please select a data source:</span>
                         </div>
                         <div className="grid grid-cols-1 gap-2">
                           {msg.metadata.clarificationOptions.map((option, idx) => {
                             const iconMap: Record<string, React.FC<{ size?: number; className?: string }>> = {
                               sql: Database,
                               csv: Clock,
                               pdf: BookOpen
                             };
                             const IconComponent = iconMap[option.value] || Database;
                             return (
                               <button
                                 key={idx}
                                 onClick={() => handleSendMessage(msg.originalQuery || msg.content, option.value)}
                                 className="flex items-center gap-3 p-3 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 hover:border-cyan-500/50 rounded-lg transition-all group text-left"
                               >
                                 <div className="p-2 bg-cyan-500/20 rounded-lg group-hover:bg-cyan-500/30">
                                   <IconComponent size={18} className="text-cyan-400 group-hover:text-cyan-300" />
                                 </div>
                                 <div className="flex flex-col">
                                   <span className="text-sm font-semibold text-cyan-300 group-hover:text-white">
                                     {option.label}
                                   </span>
                                   {option.description && (
                                     <span className="text-[11px] text-slate-400 group-hover:text-slate-300">
                                       {option.description}
                                     </span>
                                   )}
                                 </div>
                               </button>
                             );
                           })}
                         </div>
                       </div>
                     )}

                     {msg.metadata && !msg.metadata.needsDisambiguation && !msg.metadata.needsClarification && (
                       <div className="mt-3 pt-2 border-t border-white/10 flex flex-wrap items-center gap-2 text-[10px]">
                         <span className="bg-indigo-500/20 text-indigo-300 px-2 py-1 rounded-md">
                           ⏱️ {msg.metadata.responseTime}
                         </span>
                         <span className="bg-slate-700 text-slate-300 px-2 py-1 rounded-md">
                           📊 {msg.metadata.sources.join(', ')}
                         </span>
                         {msg.metadata.tableData && msg.metadata.tableData.rows.length > 0 && (
                           <button
                             onClick={() => handleDownloadCSV(msg.metadata!.tableData!)}
                             className="flex items-center gap-1 bg-green-500/20 hover:bg-green-500/30 text-green-300 hover:text-white px-2 py-1 rounded-md transition-colors border border-green-500/30"
                           >
                             <Download size={12} />
                             CSV
                           </button>
                         )}
                       </div>
                     )}
                   </div>
                ) : (
                  <p className="text-sm whitespace-pre-wrap break-words">{msg.content}</p>
                )}
              </div>
            </div>
          ))
        )}
        {/* Streaming content display */}
        {(streamingContent || streamingPhase) && (
          <div className="flex w-full justify-start">
            <div className="max-w-[85%] rounded-2xl p-4 shadow-lg bg-[#16213e] border border-indigo-500/20 text-slate-200 rounded-bl-sm">
              {streamingPhase && (
                <div className="flex items-center gap-2 text-indigo-300 text-sm mb-2">
                  <span className="w-2 h-2 bg-indigo-400 rounded-full animate-pulse"></span>
                  {streamingPhase}
                </div>
              )}
              {streamingContent && (
                <div className="prose prose-invert prose-sm max-w-none">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeRaw]}
                    components={{
                      table: ({node, ...props}) => (
                        <div className="overflow-x-auto my-3">
                          <table className="w-full text-xs border-collapse border border-indigo-500/30" {...props} />
                        </div>
                      ),
                      thead: ({node, ...props}) => (
                        <thead className="bg-indigo-500/20" {...props} />
                      ),
                      th: ({node, ...props}) => (
                        <th className="px-3 py-2 text-left text-indigo-300 font-semibold border border-indigo-500/20 whitespace-nowrap" {...props} />
                      ),
                      td: ({node, ...props}) => (
                        <td className="px-3 py-2 border border-indigo-500/20 text-slate-300" {...props} />
                      ),
                    }}
                  >
                    {streamingContent}
                  </ReactMarkdown>
                </div>
              )}
            </div>
          </div>
        )}
        {/* Typing indicator (shown when loading but no streaming content yet) */}
        {isTyping && !streamingContent && !streamingPhase && (
           <div className="flex w-full justify-start">
              <div className="bg-[#16213e] border border-indigo-500/20 text-slate-200 rounded-2xl rounded-bl-sm p-4 shadow-lg flex gap-1 items-center h-10">
                <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></span>
                <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce delay-100"></span>
                <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce delay-200"></span>
              </div>
           </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-3 bg-[#16213e] border-t border-indigo-500/20 shrink-0">
        <div className="flex gap-2 items-center">
           {/* Clear Button */}
           <button 
             onClick={handleClearChat}
             title="Clear Chat"
             className="w-10 h-10 flex items-center justify-center rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20 hover:text-red-300 transition-colors"
           >
             <RotateCcw size={16} />
           </button>

           <div className="flex-1 relative">
             <textarea
               value={inputValue}
               onChange={(e) => {
                 setInputValue(e.target.value);
                 // Auto-resize: reset height then set to scrollHeight
                 e.target.style.height = 'auto';
                 e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
               }}
               onKeyDown={(e) => {
                 if (e.key === 'Enter' && !e.shiftKey) {
                   e.preventDefault();
                   handleSendMessage(inputValue);
                   // Reset height after sending
                   e.currentTarget.style.height = 'auto';
                 }
               }}
               placeholder="Type your message... (Shift+Enter for new line)"
               rows={1}
               className="w-full min-h-[40px] max-h-[120px] pl-4 pr-10 py-2 rounded-xl bg-indigo-900/20 border border-indigo-500/30 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 transition-all resize-none overflow-y-auto"
             />
           </div>

           <button 
             onClick={() => handleSendMessage(inputValue)}
             className="w-10 h-10 flex items-center justify-center rounded-xl bg-gradient-to-br from-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-500/30 hover:shadow-indigo-500/50 hover:scale-105 transition-all"
           >
             <Send size={16} className="ml-0.5" />
           </button>
        </div>
      </div>
    </div>
  );
};

export default ChatWidget;