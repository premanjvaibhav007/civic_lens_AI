import React, { useState } from "react";
import {
  Search,
  Filter,
  Eye,
  AlertTriangle,
  Clock,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  Layers,
  CheckCircle2
} from "lucide-react";
import { ComplaintListItem, ComplaintStatus, PriorityLevel, UserSummary } from "../types";

interface QueueViewProps {
  complaints: ComplaintListItem[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  onPageChange: (newPage: number) => void;
  onSelectComplaint: (id: string) => void;
  onFilterChange: (filters: { status?: string; priority?: string; search?: string; myComplaintsOnly?: boolean }) => void;
  currentUser?: UserSummary | null;
}

export const QueueView: React.FC<QueueViewProps> = ({
  complaints,
  total,
  page,
  pageSize,
  totalPages,
  onPageChange,
  onSelectComplaint,
  onFilterChange,
  currentUser
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedStatus, setSelectedStatus] = useState<string>("");
  const [selectedPriority, setSelectedPriority] = useState<string>("");
  const [myComplaintsOnly, setMyComplaintsOnly] = useState<boolean>(false);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onFilterChange({
      status: selectedStatus || undefined,
      priority: selectedPriority || undefined,
      search: searchTerm || undefined,
      myComplaintsOnly: myComplaintsOnly || undefined
    });
  };

  const handleStatusClick = (status: string) => {
    const next = selectedStatus === status ? "" : status;
    setSelectedStatus(next);
    onFilterChange({
      status: next || undefined,
      priority: selectedPriority || undefined,
      search: searchTerm || undefined,
      myComplaintsOnly: myComplaintsOnly || undefined
    });
  };

  const toggleMyComplaints = (value: boolean) => {
    setMyComplaintsOnly(value);
    onFilterChange({
      status: selectedStatus || undefined,
      priority: selectedPriority || undefined,
      search: searchTerm || undefined,
      myComplaintsOnly: value || undefined
    });
  };

  const getPriorityBadge = (priority: PriorityLevel) => {
    switch (priority) {
      case "P1":
        return <span className="bg-red-500/15 text-red-700 border border-red-500/30 text-xs px-2.5 py-1 rounded-full font-bold">P1 • CRITICAL</span>;
      case "P2":
        return <span className="bg-orange-500/15 text-orange-700 border border-orange-500/30 text-xs px-2.5 py-1 rounded-full font-semibold">P2 • HIGH</span>;
      case "P3":
        return <span className="bg-amber-500/15 text-amber-700 border border-amber-500/30 text-xs px-2.5 py-1 rounded-full font-semibold">P3 • MEDIUM</span>;
      default:
        return <span className="bg-blue-500/15 text-blue-700 border border-blue-500/30 text-xs px-2.5 py-1 rounded-full font-semibold">P4 • LOW</span>;
    }
  };

  const getStatusBadge = (status: ComplaintStatus) => {
    switch (status) {
      case "SUBMITTED":
        return (
          <span className="inline-flex items-center gap-1.5 bg-slate-100 text-slate-700 text-xs px-2.5 py-1 rounded-full font-medium">
            <Clock className="w-3 h-3 text-slate-500" />
            <span>Awaiting Dispatch</span>
          </span>
        );
      case "ROUTED":
        return (
          <span className="inline-flex items-center gap-1.5 bg-purple-100 text-purple-800 text-xs px-2.5 py-1 rounded-full font-medium">
            <Sparkles className="w-3 h-3 text-purple-600" />
            <span>AI Routed to Dept</span>
          </span>
        );
      case "ASSIGNED":
        return (
          <span className="inline-flex items-center gap-1.5 bg-blue-100 text-blue-800 text-xs px-2.5 py-1 rounded-full font-medium">
            <span>👷 Officer Assigned</span>
          </span>
        );
      case "IN_PROGRESS":
        return (
          <span className="inline-flex items-center gap-1.5 bg-amber-100 text-amber-900 text-xs px-2.5 py-1 rounded-full font-bold border border-amber-300 animate-pulse shadow-sm">
            <span className="w-2 h-2 rounded-full bg-amber-500"></span>
            <span>Authorities Working On-Site</span>
          </span>
        );
      case "RESOLUTION_SUBMITTED":
        return (
          <span className="inline-flex items-center gap-1.5 bg-teal-100 text-teal-900 text-xs px-2.5 py-1 rounded-full font-bold border border-teal-300 shadow-sm">
            <span>📸 Repaired (Review Proof)</span>
          </span>
        );
      case "RESOLVED":
        return (
          <span className="inline-flex items-center gap-1.5 bg-emerald-100 text-emerald-800 text-xs px-2.5 py-1 rounded-full font-bold">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            <span>Verified Resolved</span>
          </span>
        );
      case "REOPENED":
        return <span className="bg-red-100 text-red-800 text-xs px-2.5 py-0.5 rounded-full font-medium">Reopened</span>;
      case "ESCALATED":
        return <span className="bg-rose-100 text-rose-800 text-xs px-2.5 py-0.5 rounded-full font-medium">Escalated</span>;
      default:
        return <span className="bg-slate-100 text-slate-700 text-xs px-2.5 py-0.5 rounded-full font-medium">{status}</span>;
    }
  };

  return (
    <div className="space-y-4">
      {/* Header & Filter Controls */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-slate-900">
              {currentUser?.role === "CITIZEN" ? "Citizen Complaint Tracker" : "Complaint Triage & Assignment Queue"}
            </h1>
            <p className="text-xs text-slate-500">
              {currentUser?.role === "CITIZEN"
                ? "Track live authority response, field crew dispatch, and inspect repair proof."
                : `Showing ${complaints.length} of ${total} registered citizen complaints across municipal grid.`}
            </p>
          </div>

          {/* Search bar */}
          <form onSubmit={handleSearchSubmit} className="flex items-center w-full sm:w-auto">
            <div className="relative w-full sm:w-72">
              <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search ID, title, keyword..."
                className="w-full pl-9 pr-4 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
            </div>
            <button
              type="submit"
              className="ml-2 bg-slate-900 hover:bg-slate-800 text-white text-xs px-3 py-2.5 rounded-xl font-medium transition-colors"
            >
              Search
            </button>
          </form>
        </div>

        {/* Citizen Scope Switcher or Role Notice */}
        {currentUser?.role === "CITIZEN" ? (
          <div className="flex items-center gap-2 p-1.5 bg-slate-100 rounded-xl w-fit">
            <button
              type="button"
              onClick={() => toggleMyComplaints(true)}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                myComplaintsOnly ? "bg-white text-emerald-700 shadow-sm border border-emerald-200" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              👤 My Filed Complaints
            </button>
            <button
              type="button"
              onClick={() => toggleMyComplaints(false)}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                !myComplaintsOnly ? "bg-white text-slate-900 shadow-sm border border-slate-200" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              🌐 All Neighborhood Complaints
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-xs text-slate-600 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-xl w-fit">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span className="font-semibold text-slate-800">Authority Dispatch View:</span>
            <span>Showing live field queue filtered for {currentUser?.department_name || "Municipal Operations"}</span>
          </div>
        )}

        {/* Quick Status Filter Pills */}
        <div className="flex items-center space-x-2 overflow-x-auto pb-1 text-xs">
          <span className="text-slate-400 font-semibold uppercase text-[10px] mr-1">Status:</span>
          {["", "SUBMITTED", "ROUTED", "ASSIGNED", "IN_PROGRESS", "RESOLUTION_SUBMITTED", "RESOLVED", "REOPENED", "ESCALATED"].map((st) => (
            <button
              key={st || "all"}
              onClick={() => handleStatusClick(st)}
              className={`px-3 py-1.5 rounded-full font-medium transition-all whitespace-nowrap ${
                selectedStatus === st
                  ? "bg-slate-900 text-white shadow-sm"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {st ? st.replace("_", " ") : "All Statuses"}
            </button>
          ))}
        </div>
      </div>

      {/* Complaints Table */}
      <div className="bg-white border border-slate-200/80 rounded-2xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50/80 text-slate-600 text-xs uppercase font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3.5 px-4">Complaint ID</th>
                <th className="py-3.5 px-4">Issue Details</th>
                <th className="py-3.5 px-4">Category & AI</th>
                <th className="py-3.5 px-4">Priority</th>
                <th className="py-3.5 px-4">Department</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {complaints.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    No complaints matching the selected filters.
                  </td>
                </tr>
              ) : (
                complaints.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-slate-900 text-xs">
                      {c.complaint_number}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="max-w-xs">
                        <p className="font-semibold text-slate-900 text-sm truncate">{c.title}</p>
                        <p className="text-xs text-slate-500 truncate">{c.address || c.city || "Location mapped"}</p>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center space-x-1.5">
                        <span className="font-medium text-slate-800 text-xs">{c.category_name || "Unclassified"}</span>
                        {c.ai_confidence && (
                          <span
                            className="bg-emerald-50 text-emerald-700 text-[10px] font-bold px-1.5 py-0.5 rounded border border-emerald-200 flex items-center space-x-0.5"
                            title="AI Confidence Score"
                          >
                            <Sparkles className="w-2.5 h-2.5 text-emerald-600" />
                            <span>{Math.round(c.ai_confidence * 100)}%</span>
                          </span>
                        )}
                        {c.is_duplicate && (
                          <span className="bg-amber-100 text-amber-800 text-[10px] font-bold px-1.5 py-0.5 rounded border border-amber-300">
                            Duplicate
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-3.5 px-4">{getPriorityBadge(c.priority)}</td>
                    <td className="py-3.5 px-4 text-slate-600 text-xs">{c.department_name || "Pending Assignment"}</td>
                    <td className="py-3.5 px-4">{getStatusBadge(c.status)}</td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => onSelectComplaint(c.id)}
                        className="bg-slate-100 hover:bg-emerald-50 hover:text-emerald-700 text-slate-700 font-semibold px-3 py-1.5 rounded-lg text-xs transition-colors flex items-center space-x-1 ml-auto border border-slate-200"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        <div className="bg-slate-50 px-4 py-3 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
          <div>
            Showing <span className="font-semibold text-slate-700">{(page - 1) * pageSize + 1}</span> to{" "}
            <span className="font-semibold text-slate-700">{Math.min(page * pageSize, total)}</span> of{" "}
            <span className="font-semibold text-slate-700">{total}</span>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-medium text-slate-700">
              Page {page} of {totalPages || 1}
            </span>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
