import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, X, Send, Bot, User } from 'lucide-react';
import api from '../api';

const AgentChat = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { id: 1, role: 'agent', content: 'Hello! I am your Autonomous Financial Brain. Ask me anything about your revenue, cash flow, or expenses.' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { id: Date.now(), role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await api.post('/finance/agent/chat/', { query: userMessage.content });
      const agentMessage = { id: Date.now() + 1, role: 'agent', content: res.data.response };
      setMessages((prev) => [...prev, agentMessage]);
    } catch (error) {
      console.error('Error querying agent:', error);
      const errorMessage = { 
        id: Date.now() + 1, 
        role: 'agent', 
        content: error.response?.data?.error || 'System anomaly detected. I am currently offline or unable to process that request.' 
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* Floating Action Button */}
      <button
        onClick={() => setIsOpen(true)}
        className={`fixed bottom-6 right-6 p-4 rounded-full bg-brand-600 text-white shadow-lg shadow-brand-500/20 hover:bg-brand-500 transition-all z-40 animate-fade-in ${isOpen ? 'scale-0' : 'scale-100'}`}
      >
        <MessageSquare size={24} />
      </button>

      {/* Chat Window */}
      <div className={`fixed bottom-6 right-6 w-96 h-[32rem] glass-card flex flex-col z-50 transition-all duration-300 transform origin-bottom-right ${isOpen ? 'scale-100 opacity-100' : 'scale-0 opacity-0 pointer-events-none'}`}>
        {/* Header */}
        <div className="p-4 border-b border-slate-700/50 flex justify-between items-center bg-dark-800/80 rounded-t-2xl">
          <div className="flex items-center gap-3">
            <div className="bg-brand-500/20 p-2 rounded-lg text-brand-500">
              <Bot size={20} />
            </div>
            <div>
              <h3 className="font-bold text-white text-sm">AMSS Agent</h3>
              <p className="text-xs text-brand-400 flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-brand-400 animate-pulse"></span>
                Online (Llama 3)
              </p>
            </div>
          </div>
          <button onClick={() => setIsOpen(false)} className="text-slate-400 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Message Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-dark-900/50 custom-scrollbar">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.role === 'agent' && (
                <div className="w-8 h-8 rounded-full bg-brand-500/20 flex items-center justify-center text-brand-500 flex-shrink-0">
                  <Bot size={16} />
                </div>
              )}
              
              <div className={`max-w-[75%] rounded-2xl px-4 py-2 text-sm ${
                msg.role === 'user' 
                  ? 'bg-brand-600 text-white rounded-tr-sm' 
                  : 'bg-dark-800 text-slate-200 border border-slate-700/50 rounded-tl-sm'
              }`}>
                {msg.content}
              </div>

              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-slate-400 flex-shrink-0">
                  <User size={16} />
                </div>
              )}
            </div>
          ))}
          {isLoading && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 rounded-full bg-brand-500/20 flex items-center justify-center text-brand-500 flex-shrink-0">
                <Bot size={16} />
              </div>
              <div className="max-w-[75%] rounded-2xl px-4 py-3 bg-dark-800 border border-slate-700/50 rounded-tl-sm flex items-center gap-1">
                <span className="w-2 h-2 bg-brand-500 rounded-full animate-bounce"></span>
                <span className="w-2 h-2 bg-brand-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                <span className="w-2 h-2 bg-brand-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <form onSubmit={handleSend} className="p-4 border-t border-slate-700/50 bg-dark-800/80 rounded-b-2xl">
          <div className="relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about your finances..."
              className="w-full bg-dark-900 border border-slate-700 rounded-xl pl-4 pr-12 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/50 text-white"
              disabled={isLoading}
            />
            <button 
              type="submit" 
              disabled={isLoading || !input.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-brand-600 rounded-lg text-white hover:bg-brand-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send size={16} />
            </button>
          </div>
        </form>
      </div>
    </>
  );
};

export default AgentChat;
