import React, { useState, useRef, useEffect } from "react";
import {
  Bot,
  Send,
  X,
  Sparkles,
  Database,
  CheckCircle2,
  Clock,
  ChevronRight,
  ShieldCheck,
  AlertCircle
} from "lucide-react";
import { api } from "../api";
import { CopilotQueryResponse } from "../types";

interface CopilotPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectComplaint?: (id: string) => void;
}

interface Message {
  role: "user" | "assistant";
  text: string;
  intent?: string;
  sourceRecords?: Array<Record<string, any>>;
  queryTimeMs?: number;
  timestamp: string;
}

const QUICK_PROMPTS = [
  "Show critical open potholes in New Delhi",
  "Which incidents are approaching SLA deadline?",
  "Check recurring drainage issues in Ward 101",
  "How is the Roads Department performing?",
];

export const CopilotPanel: React.FC<CopilotPanelProps> = ({
  isOpen,
  onClose,
  onSelectComplaint,
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      text: "Hello, Officer. I am your CivicLens Authority Copilot. Ask me about active civic incidents, SLA breach risks, recurring infrastructure hotspots, or department workloads. All my answers are grounded in real database records.",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  if (!isOpen) return null;

  const handleSend = async (queryText?: string) => {
    const text = (queryText || input).trim();
    if (!text || isLoading) return;

    const userMsg: Message = {
      role: "user",
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await api.post("/copilot/query", { query: text });
      const data: CopilotQueryResponse = res.data;

      const botMsg: Message = {
        role: "assistant",
        text: data.answer,
        intent: data.intent,
        sourceRecords: data.source_records,
        queryTimeMs: data.query_time_ms,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const errorMsg: Message = {
        role: "assistant",
        text:
          err.response?.data?.detail ||
          "I encountered an issue querying the database. Please verify your connection or try again.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-lg bg-slate-900 border-l border-slate-800 h-full flex flex-col justify-between shadow-2xl animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white shadow-md shadow-emerald-950/50">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white flex items-center gap-1.5">
                AI Authority Copilot
                <span className="text-[10px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-1.5 py-0.2 rounded font-bold">
                  GROUNDED
                </span>
              </h2>
              <p className="text-[11px] text-slate-400">Strictly grounded on active database records</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 text-sm">
          {messages.map((m, idx) => (
            <div
              key={idx}
              className={`flex flex-col ${m.role === "user" ? "items-end" : "items-start"}`}
            >
              <div
                className={`max-w-[90%] p-3.5 rounded-2xl ${
                  m.role === "user"
                    ? "bg-emerald-600 text-white rounded-tr-none shadow-md shadow-emerald-950/20"
                    : "bg-slate-950 border border-slate-800 text-slate-200 rounded-tl-none space-y-2.5"
                }`}
              >
                <p className="whitespace-pre-line leading-relaxed text-xs sm:text-sm">{m.text}</p>

                {/* Source records cited */}
                {m.sourceRecords && m.sourceRecords.length > 0 && (
                  <div className="pt-2 border-t border-slate-800 space-y-1.5">
                    <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider flex items-center gap-1">
                      <Database className="w-3 h-3 text-emerald-400" />
                      Cited Database Records ({m.sourceRecords.length})
                    </span>
                    <div className="space-y-1 max-h-36 overflow-y-auto pr-1">
                      {m.sourceRecords.map((rec, rIdx) => (
                        <div
                          key={rIdx}
                          onClick={() => {
                            if (rec.id && onSelectComplaint) {
                              onSelectComplaint(rec.id);
                            }
                          }}
                          className="bg-slate-900 p-2 rounded-lg text-xs hover:bg-slate-800/80 cursor-pointer border border-slate-800 flex items-center justify-between"
                        >
                          <div className="truncate pr-2">
                            <span className="font-mono text-emerald-400 font-semibold mr-2 text-[11px]">
                              {rec.incident_number || rec.complaint_number || `#${rIdx + 1}`}
                            </span>
                            <span className="text-slate-300">{rec.title || rec.name}</span>
                          </div>
                          <ChevronRight className="w-3 h-3 text-slate-500 shrink-0" />
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
                  <span>{m.timestamp}</span>
                  {m.queryTimeMs !== undefined && <span>{m.queryTimeMs}ms query time</span>}
                </div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-950 border border-slate-800 p-3 rounded-2xl rounded-tl-none w-max">
              <Sparkles className="w-4 h-4 text-emerald-400 animate-spin" />
              <span>Querying database and aggregating evidence...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Prompts Bar */}
        <div className="px-4 py-2 bg-slate-950/40 border-t border-slate-800/60 overflow-x-auto flex items-center gap-2 no-scrollbar">
          {QUICK_PROMPTS.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(prompt)}
              className="text-[11px] bg-slate-800/60 hover:bg-slate-800 text-slate-300 hover:text-white px-2.5 py-1 rounded-lg border border-slate-700/60 whitespace-nowrap transition-colors shrink-0"
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <div className="p-3 border-t border-slate-800 bg-slate-950">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask Copilot about civic issues, SLA status, ward trends..."
              className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="p-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl disabled:opacity-40 transition-colors shrink-0"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
          <div className="flex items-center justify-between text-[10px] text-slate-500 mt-2 px-1">
            <span className="flex items-center gap-1">
              <ShieldCheck className="w-3 h-3 text-emerald-500" />
              RBAC Verified
            </span>
            <span>Ground Truth Policy: No fabricated metrics</span>
          </div>
        </div>
      </div>
    </div>
  );
};
