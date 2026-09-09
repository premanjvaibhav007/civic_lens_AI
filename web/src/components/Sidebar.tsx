import React from "react";
import {
  LayoutDashboard,
  ListTodo,
  Layers,
  MapPin,
  TrendingUp,
  BarChart3,
  Building2,
  Bot,
  Sparkles
} from "lucide-react";
import { UserSummary } from "../types";

export type TabType = "overview" | "queue" | "incidents" | "map" | "predictions" | "analytics" | "admin";

interface SidebarProps {
  currentTab: TabType;
  onSelectTab: (tab: TabType) => void;
  user: UserSummary | null;
  pendingCount?: number;
  onToggleCopilot?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  user,
  pendingCount = 0,
  onToggleCopilot,
}) => {
  const navItems: Array<{ id: TabType; label: string; icon: any; badge?: number; adminOnly?: boolean }> = [
    { id: "overview", label: "Executive Overview", icon: LayoutDashboard },
    { id: "queue", label: "Complaint Queue", icon: ListTodo, badge: pendingCount },
    { id: "incidents", label: "Civic Incidents", icon: Layers },
    { id: "map", label: "GIS Live Heatmap", icon: MapPin },
    { id: "predictions", label: "Risk & Forecasting", icon: TrendingUp },
    { id: "analytics", label: "SLA & Performance", icon: BarChart3 },
    { id: "admin", label: "Administration & Rules", icon: Building2, adminOnly: true },
  ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between p-4 min-h-[calc(100vh-4rem)]">
      <div className="space-y-1">
        <div className="px-3 py-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Navigation
        </div>
        {navItems.map((item) => {
          if (item.adminOnly && user && user.role !== "ADMIN") return null;
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                isActive
                  ? "bg-emerald-600/15 text-emerald-400 border border-emerald-500/30 shadow-sm"
                  : "text-slate-300 hover:bg-slate-800/80 hover:text-white"
              }`}
            >
              <div className="flex items-center space-x-3">
                <Icon className={`w-5 h-5 ${isActive ? "text-emerald-400" : "text-slate-400"}`} />
                <span>{item.label}</span>
              </div>
              {item.badge !== undefined && item.badge > 0 && (
                <span className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs px-2 py-0.5 rounded-full font-bold">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* AI Copilot Quick Action */}
      {onToggleCopilot && (
        <div className="pt-2">
          <button
            onClick={onToggleCopilot}
            className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white p-3 rounded-xl text-xs font-bold flex items-center justify-between shadow-lg shadow-emerald-950/40 transition-all border border-emerald-400/30 group"
          >
            <div className="flex items-center gap-2">
              <Bot className="w-4 h-4 group-hover:scale-110 transition-transform" />
              <span>AI Authority Copilot</span>
            </div>
            <Sparkles className="w-3.5 h-3.5 text-emerald-200" />
          </button>
        </div>
      )}

      {/* System info badge */}
      <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-3 text-xs text-slate-400 space-y-1 mt-3">
        <div className="flex items-center justify-between font-semibold text-slate-300">
          <span>AI Engine</span>
          <span className="text-emerald-400 font-mono text-[10px] bg-emerald-950/80 px-1.5 py-0.5 rounded border border-emerald-500/30">
            ONLINE
          </span>
        </div>
        <p className="text-[11px] text-slate-400">Model: CivicLens Intelligence v2.0</p>
        <p className="text-[10px] text-slate-500">Latency: ~180ms • SLA target: 95%</p>
      </div>
    </aside>
  );
};
