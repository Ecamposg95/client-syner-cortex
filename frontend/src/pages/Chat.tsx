import React, { useEffect, useRef, useState } from 'react';
import { useWorkspaceStore } from '../store/workspaceStore';
import { useChatStore } from '../store/chatStore';
import {
  MessageSquare,
  Plus,
  Send,
  Loader2,
  FileText,
  AlertCircle,
  HelpCircle
} from 'lucide-react';

export const Chat: React.FC = () => {
  const { activeWorkspace } = useWorkspaceStore();
  const { sessions, activeSession, messages, fetchSessions, selectSession, createSession, sendMessage, isSending, isLoading, error } = useChatStore();
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [activeCitation, setActiveCitation] = useState<any>(null);

  useEffect(() => {
    if (activeWorkspace) {
      fetchSessions(activeWorkspace.id);
    }
  }, [activeWorkspace, fetchSessions]);

  useEffect(() => {
    // Scroll to bottom of message list when messages update
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (!activeWorkspace) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6">
        <MessageSquare size={48} className="text-violet-500 mb-4 animate-pulse" />
        <h3 className="text-xl font-bold text-white mb-2">No Workspace Selected</h3>
        <p className="text-sm text-slate-400 max-w-sm">
          Please select or create a project workspace from the sidebar menu to use Cortex Chat.
        </p>
      </div>
    );
  }

  const handleCreateSession = async () => {
    const title = prompt("Enter conversation title:", `Consultation ${sessions.length + 1}`);
    if (title && title.trim()) {
      await createSession(activeWorkspace.id, title.trim());
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isSending) return;

    const textToSend = inputText;
    setInputText('');
    await sendMessage(textToSend);
  };

  const quickPrompts = [
    "What are the main problems of this company?",
    "Identify critical risk vectors.",
    "Give me quick wins to optimize operations.",
    "What recommendations are there for sales?"
  ];

  const handleQuickPromptClick = async (promptText: string) => {
    let session = activeSession;
    if (!session) {
      session = await createSession(activeWorkspace.id, promptText.slice(0, 30) + "...");
    }
    if (session) {
      await sendMessage(promptText);
    }
  };

  return (
    <div className="h-[calc(100vh-140px)] flex gap-6 relative">
      
      {/* SESSIONS LIST SIDEBAR */}
      <div className="w-64 glass-panel rounded-2xl flex flex-col h-full overflow-hidden flex-shrink-0 hidden md:flex">
        <div className="p-4 border-b border-white/5 flex items-center justify-between">
          <h3 className="font-display font-bold text-sm text-white flex items-center space-x-2">
            <MessageSquare size={16} className="text-violet-400" />
            <span>Consultations</span>
          </h3>
          <button
            onClick={handleCreateSession}
            className="p-1 rounded-md bg-white/5 border border-white/5 hover:border-violet-500/30 text-slate-400 hover:text-white transition-colors"
          >
            <Plus size={14} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => selectSession(s)}
              className={`w-full text-left px-3 py-2 text-xs rounded-xl truncate transition-all duration-200 ${
                activeSession && s.id === activeSession.id
                  ? 'bg-gradient-to-r from-violet-600/20 to-indigo-500/10 text-white font-semibold shadow-inner border border-violet-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
              }`}
            >
              {s.title}
            </button>
          ))}
        </div>
      </div>

      {/* MAIN CHAT INTERFACE PANEL */}
      <div className="flex-1 glass-panel rounded-2xl flex flex-col h-full overflow-hidden relative">
        
        {/* CHAT SESSION HEADER */}
        <div className="p-4 border-b border-white/5 flex items-center justify-between">
          <div>
            <h3 className="font-display font-bold text-sm text-white">
              {activeSession ? activeSession.title : 'New Consultation'}
            </h3>
            <p className="text-[10px] text-slate-500 uppercase tracking-widest mt-0.5">
              Cortex RAG Assisted Consulting
            </p>
          </div>
          <div className="md:hidden">
            <button
              onClick={handleCreateSession}
              className="px-2 py-1 rounded-md bg-white/5 border border-white/5 text-[10px] text-slate-300 hover:text-white flex items-center space-x-1"
            >
              <Plus size={10} />
              <span>New Session</span>
            </button>
          </div>
        </div>

        {/* MESSAGES VIEW CONTAINER */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-6 max-w-lg mx-auto">
              <div className="w-12 h-12 rounded-xl bg-violet-600/10 flex items-center justify-center text-violet-400">
                <HelpCircle size={24} />
              </div>
              <div>
                <h4 className="font-semibold text-white">Ask anything about your operations</h4>
                <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                  Syner Cortex will query your uploaded documents semantically to construct a cited response. Select a quick prompt option or enter a custom prompt.
                </p>
              </div>

              {/* QUICK PROMPT LIST */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full pt-4">
                {quickPrompts.map((p, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleQuickPromptClick(p)}
                    className="p-3 text-left rounded-xl bg-white/5 border border-white/5 hover:border-violet-500/20 text-xs text-slate-300 hover:text-white transition-all text-ellipsis overflow-hidden"
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={`flex ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-2xl rounded-2xl p-4 text-sm leading-relaxed ${
                      m.sender === 'user'
                        ? 'bg-violet-600/20 border border-violet-500/20 text-white rounded-br-none'
                        : 'bg-[#0E1524]/60 border border-white/5 text-slate-300 rounded-bl-none'
                    }`}
                  >
                    <div className="cortex-markdown whitespace-pre-line">{m.content}</div>

                    {/* CITATION SOURCES LIST */}
                    {m.sender === 'assistant' && m.sources && m.sources.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-white/5 space-y-1.5">
                        <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest block">
                          Cited Sources
                        </span>
                        <div className="flex flex-wrap gap-2">
                          {m.sources.map((src, sIdx) => (
                            <button
                              key={sIdx}
                              onClick={() => setActiveCitation(src)}
                              className="px-2 py-1 rounded bg-white/5 hover:bg-white/10 text-[10px] text-violet-400 font-semibold border border-white/5 flex items-center space-x-1"
                            >
                              <FileText size={10} />
                              <span>{src.document_name}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              
              {isSending && (
                <div className="flex justify-start">
                  <div className="bg-[#0E1524]/60 border border-white/5 rounded-2xl rounded-bl-none p-4 flex items-center space-x-2 text-slate-400 text-xs">
                    <Loader2 size={14} className="animate-spin" />
                    <span>Analyzing vault files and formulating recommendation...</span>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* INPUT SUBMISSION FIELD */}
        <form onSubmit={handleSend} className="p-4 border-t border-white/5 bg-[#0C1220]/40 flex gap-2">
          <input
            type="text"
            required
            disabled={isSending}
            placeholder={activeSession ? "Ask a question about document assets..." : "Create a consultation session to begin..."}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            className="flex-1 p-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 text-sm disabled:opacity-55"
          />
          <button
            type="submit"
            disabled={!inputText.trim() || isSending}
            className="p-3 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white shadow-glow disabled:opacity-55 transition-all duration-300"
          >
            <Send size={16} />
          </button>
        </form>

        {/* CITATION MODAL DIALOGUE */}
        {activeCitation && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="w-full max-w-lg bg-[#111827] border border-white/10 rounded-2xl p-6 shadow-2xl relative">
              <h3 className="font-display font-bold text-lg text-white mb-2 flex items-center space-x-2">
                <FileText size={18} className="text-violet-400" />
                <span>Source: {activeCitation.document_name}</span>
              </h3>
              
              <div className="p-4 bg-white/5 border border-white/5 rounded-xl text-xs text-slate-300 overflow-y-auto max-h-60 leading-relaxed italic whitespace-pre-wrap">
                "{activeCitation.snippet}"
              </div>

              <div className="flex justify-end pt-4">
                <button
                  onClick={() => setActiveCitation(null)}
                  className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-white rounded-lg bg-white/5 hover:bg-white/10"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

      </div>

    </div>
  );
};
export default Chat;
