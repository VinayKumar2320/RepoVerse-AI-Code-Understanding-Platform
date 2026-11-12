'use client';

import React, { useState } from 'react';
import { useRepoStore } from '../../store/useRepoStore';
import { api } from '../../services/api';
import { QuestionResponse } from '../../types';
import { MessageSquare, Send, Bot, User, FileText, CheckCircle2, ShieldAlert } from 'lucide-react';

interface ChatMessage {
  sender: 'user' | 'assistant';
  text: string;
  citations?: any[];
  mode?: string;
}

export const AskRepositoryChat: React.FC = () => {
  const { currentRepo, experienceLevel, setSelectedFile } = useRepoStore();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      sender: 'assistant',
      text: `Hello! I am RepoVerse AI. I provide source-grounded answers about ${currentRepo?.name || 'this repository'} backed by verified AST symbols, call traces, and file citations. How can I help you understand this codebase?`,
    },
  ]);
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);

  const handleSend = async (questionText?: string) => {
    const q = questionText || input;
    if (!q.trim() || !currentRepo || loading) return;

    setMessages((prev) => [...prev, { sender: 'user', text: q }]);
    setInput('');
    setLoading(true);

    try {
      const res: QuestionResponse = await api.askQuestion(currentRepo.id, q, experienceLevel);
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: res.answer,
          citations: res.citations,
          mode: res.mode_used,
        },
      ]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: `Error retrieving grounded answer: ${e.message}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const starterQuestions = [
    'Where is authentication implemented?',
    'What does this repository do?',
    'Where does execution begin?',
    'Which modules are most central?',
  ];

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-140px)] flex flex-col bg-slate-900 border border-slate-800 rounded-xl overflow-hidden py-2">
      {/* Chat Messages Log */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex items-start space-x-3 ${
              msg.sender === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {msg.sender === 'assistant' && (
              <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center text-white shrink-0 shadow">
                <Bot className="w-4 h-4" />
              </div>
            )}

            <div
              className={`max-w-2xl rounded-xl p-4 text-xs leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-brand-600 text-white rounded-tr-none'
                  : 'bg-slate-950 border border-slate-800 text-slate-200 rounded-tl-none'
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.text}</p>

              {/* Engine Mode Badge */}
              {msg.mode && (
                <div className="mt-2 text-[10px] text-slate-500 flex items-center space-x-1">
                  <span>Engine:</span>
                  <span className="font-mono text-indigo-400">
                    {msg.mode === 'deterministic_engine' ? 'Deterministic Graph Knowledge Engine' : 'LLM Grounded'}
                  </span>
                </div>
              )}

              {/* Citations List */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-800 space-y-1.5">
                  <span className="text-[10px] uppercase font-bold text-slate-500 block">
                    Source Citations
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {msg.citations.map((c, idx) => (
                      <button
                        key={idx}
                        onClick={() => setSelectedFile(c.file_path, c.start_line)}
                        className="px-2 py-0.5 bg-slate-900 hover:bg-slate-800 rounded text-[11px] font-mono text-brand-400 border border-slate-700/60 flex items-center space-x-1 transition"
                      >
                        <FileText className="w-3 h-3 text-slate-500" />
                        <span>{c.file_path}:{c.start_line}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {msg.sender === 'user' && (
              <div className="w-8 h-8 rounded-lg bg-slate-700 flex items-center justify-center text-white shrink-0">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex items-center space-x-2 text-slate-400 text-xs italic pl-11">
            <Bot className="w-3.5 h-3.5 animate-spin" />
            <span>Retrieving verified code symbols and generating response...</span>
          </div>
        )}
      </div>

      {/* Starter Questions */}
      <div className="px-5 py-2 flex flex-wrap gap-2 border-t border-slate-800/60 bg-slate-950/40">
        {starterQuestions.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(q)}
            className="text-[11px] text-slate-400 bg-slate-950 hover:text-slate-200 hover:bg-slate-800 border border-slate-800 rounded-full px-3 py-1 transition"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Chat Input Bar */}
      <div className="p-4 bg-slate-950 border-t border-slate-800 flex items-center space-x-2">
        <input
          type="text"
          placeholder={`Ask about ${currentRepo?.name || 'this repo'} at ${experienceLevel} level...`}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-brand-500"
        />
        <button
          onClick={() => handleSend()}
          disabled={loading || !input.trim()}
          className="p-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white rounded-lg transition"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
