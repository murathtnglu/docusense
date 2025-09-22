'use client';

import { useState, useRef, useEffect } from 'react';
import { queryAPI } from '@/lib/api';
import { Send, Sparkles, Menu, User, Copy, ThumbsUp, ThumbsDown } from 'lucide-react';
import toast from 'react-hot-toast';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  citations?: any[];
  confidence?: number;
  latency?: number;
}

interface Props {
  collectionId: number;
  onToggleSidebar?: () => void;
  sidebarOpen?: boolean;
}

export default function ChatInterface({ collectionId, onToggleSidebar, sidebarOpen }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await queryAPI.ask({
        collection_id: collectionId,
        question: input,
        top_k: 5,
      });

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.data.answer,
        citations: response.data.citations,
        confidence: response.data.confidence,
        latency: response.data.latency_ms,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      toast.error('Failed to get answer');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied!');
  };

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Header */}
      <div className="h-16 glass-effect border-b border-slate-200/50 flex items-center px-6">
        <button
          onClick={onToggleSidebar}
          className="p-2 hover:bg-slate-100 rounded-lg transition-colors mr-4"
        >
          <Menu className="w-5 h-5 text-slate-600" />
        </button>
        <div className="flex-1">
          <h2 className="text-sm font-semibold text-slate-900">Chat with Documents</h2>
          <p className="text-xs text-slate-500">AI-powered Q&A</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto bg-gradient-to-b from-transparent to-slate-50/50">
        <div className="max-w-4xl mx-auto p-6">
          {messages.length === 0 ? (
            <div className="text-center py-12 animate-slide-up">
              <div className="w-16 h-16 bg-gradient-to-tr from-blue-600 to-cyan-500 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-blue-500/25">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-slate-900 mb-2">Start a conversation</h3>
              <p className="text-slate-600 mb-8 max-w-md mx-auto">
                Ask questions about your documents and get intelligent answers with citations
              </p>
              
              <div className="grid gap-3 max-w-xl mx-auto">
                {[
                  "What are the key points discussed?",
                  "Summarize the main findings",
                  "What conclusions can be drawn?"
                ].map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => setInput(prompt)}
                    className="text-left p-4 bg-white border border-slate-200 rounded-xl hover:border-blue-300 hover:bg-blue-50/50 transition-all group card-hover"
                  >
                    <span className="text-sm text-slate-700 group-hover:text-blue-700">{prompt}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-4 animate-slide-up ${
                    message.type === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {message.type === 'assistant' && (
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-gradient-to-tr from-blue-600 to-cyan-500 rounded-lg flex items-center justify-center shadow-lg">
                        <Sparkles className="w-4 h-4 text-white" />
                      </div>
                    </div>
                  )}
                  
                  <div className={`group relative max-w-2xl ${message.type === 'user' ? 'order-1' : ''}`}>
                    <div
                      className={`px-4 py-3 rounded-2xl ${
                        message.type === 'user'
                          ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg'
                          : 'bg-white border border-slate-200 text-slate-900 shadow-md'
                      }`}
                    >
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                      
                      {message.type === 'assistant' && message.citations && message.citations.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-slate-200">
                          <p className="text-xs font-medium text-slate-500 mb-2">
                            Sources ({message.citations.length})
                          </p>
                          <div className="space-y-1">
                            {message.citations.map((cite, idx) => (
                              <div key={idx} className="text-xs text-slate-600 bg-slate-50 rounded-lg p-2">
                                <span className="font-medium">[{cite.index}]</span> {cite.text}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                    
                    {message.type === 'assistant' && (
                      <div className="absolute -bottom-6 left-0 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2">
                        <button
                          onClick={() => copyToClipboard(message.content)}
                          className="p-1.5 bg-white rounded-lg shadow hover:shadow-md text-slate-400 hover:text-slate-600 transition-all"
                        >
                          <Copy className="w-3 h-3" />
                        </button>
                        <span className="text-xs text-slate-500">
                          {message.confidence && `${(message.confidence * 100).toFixed(0)}% confidence • `}
                          {message.latency}ms
                        </span>
                      </div>
                    )}
                  </div>
                  
                  {message.type === 'user' && (
                    <div className="flex-shrink-0 order-2">
                      <div className="w-8 h-8 bg-gradient-to-tr from-slate-200 to-slate-100 rounded-lg flex items-center justify-center shadow">
                        <User className="w-4 h-4 text-slate-600" />
                      </div>
                    </div>
                  )}
                </div>
              ))}
              
              {loading && (
                <div className="flex gap-4 animate-slide-up">
                  <div className="w-8 h-8 bg-gradient-to-tr from-blue-600 to-cyan-500 rounded-lg flex items-center justify-center shadow-lg">
                    <Sparkles className="w-4 h-4 text-white animate-pulse" />
                  </div>
                  <div className="bg-white border border-slate-200 rounded-2xl px-4 py-3 shadow-md">
                    <div className="flex gap-1.5">
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-slate-200/50 glass-effect p-4">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything about your documents..."
              disabled={loading}
              className="input-primary pr-12"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 btn-primary !px-2 !py-2 !rounded-lg"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}