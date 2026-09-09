import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  Flame,
  Layers,
  MapPin,
  Clock,
  CheckCircle2,
  Filter,
  Search,
  ChevronRight,
  ShieldAlert,
  ArrowUpRight,
  TrendingUp,
  Activity,
  X
} from "lucide-react";
import { api } from "../api";
import { CivicIncidentItem, PriorityLevel, SeverityLevel, UserSummary } from "../types";

interface IncidentViewProps {
  user: UserSummary | null;
  onViewComplaintDetail?: (id: string) => void;
}

export const IncidentView: React.FC<IncidentViewProps> = ({ user, onViewComplaintDetail }) => {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [minImpact, setMinImpact] = useState<number>(0);
  const [selectedIncident, setSelectedIncident] = useState<CivicIncidentItem | null>(null);
  const [statusUpdateModal, setStatusUpdateModal] = useState(false);
  const [newStatus, setNewStatus] = useState("IN_PROGRESS");
  const [statusReason, setStatusReason] = useState("");

  const { data, isLoading } = useQuery<{
    success: boolean;
    total: number;
    data: CivicIncidentItem[];
  }>({
    queryKey: ["civicIncidents", statusFilter, minImpact],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (statusFilter) params.append("status", statusFilter);
      if (minImpact > 0) params.append("min_impact", String(minImpact));
      const res = await api.get(`/incidents?${params.toString()}`);
      return res.data;
    },
  });

  const { data: incidentReports } = useQuery({
    queryKey: ["incidentReports", selectedIncident?.id],
    queryFn: async () => {
      if (!selectedIncident) return [];
      const res = await api.get(`/incidents/${selectedIncident.id}/reports`);
      return res.data.reports || [];
    },
    enabled: !!selectedIncident,
  });

  const updateStatusMutation = useMutation({
    mutationFn: async ({ id, status, reason }: { id: string; status: string; reason: string }) => {
      const res = await api.patch(`/incidents/${id}/status`, {
        new_status: status,
        reason: reason || "Status updated by authority officer",
      });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["civicIncidents"] });
      setStatusUpdateModal(false);
      setStatusReason("");
      if (selectedIncident) {
        setSelectedIncident({ ...selectedIncident, status: newStatus });
      }
    },
  });

  const incidents = data?.data || [];
  const filtered = incidents.filter((inc) => {
    if (search) {
      const q = search.toLowerCase();
      return (
        inc.title.toLowerCase().includes(q) ||
        inc.incident_number.toLowerCase().includes(q) ||
        (inc.ward && inc.ward.toLowerCase().includes(q))
      );
    }
    return true;
  });

  const getImpactColor = (score: number) => {
    if (score >= 70) return "text-red-400 bg-red-950/40 border-red-800/60";
    if (score >= 45) return "text-amber-400 bg-amber-950/40 border-amber-800/60";
    return "text-emerald-400 bg-emerald-950/40 border-emerald-800/60";
  };

  const getSeverityBadge = (sev: SeverityLevel) => {
    switch (sev) {
      case "CRITICAL":
        return "bg-red-500/20 text-red-400 border-red-500/30";
      case "HIGH":
        return "bg-amber-500/20 text-amber-400 border-amber-500/30";
      case "MEDIUM":
        return "bg-blue-500/20 text-blue-400 border-blue-500/30";
      default:
        return "bg-slate-500/20 text-slate-400 border-slate-500/30";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
            <Layers className="w-7 h-7 text-emerald-400" />
            Civic Incidents Intelligence
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Spatial-temporal clusters aggregating repeated citizen complaints into canonical infrastructure incidents.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 flex items-center gap-2 text-sm text-slate-300">
            <Activity className="w-4 h-4 text-emerald-400 animate-pulse" />
            <span>
              Active Clusters: <strong className="text-white">{data?.total ?? 0}</strong>
            </span>
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-2xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-1 min-w-[260px]">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by incident number, title, ward..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500/50"
            />
          </div>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-emerald-500/50"
            >
              <option value="">All Statuses</option>
              <option value="OPEN">Open</option>
              <option value="ASSIGNED">Assigned</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="RESOLVED">Resolved</option>
              <option value="CLOSED">Closed</option>
            </select>
          </div>

          <div className="flex items-center gap-2 text-sm text-slate-400 bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-800">
            <span>Min Impact:</span>
            <input
              type="range"
              min="0"
              max="90"
              step="10"
              value={minImpact}
              onChange={(e) => setMinImpact(Number(e.target.value))}
              className="w-20 accent-emerald-500"
            />
            <span className="font-mono text-emerald-400 text-xs w-6">{minImpact}+</span>
          </div>
        </div>
      </div>

      {/* Incident Cards / Table */}
      {isLoading ? (
        <div className="text-center py-16 text-slate-400">Loading civic incidents...</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 bg-slate-900/40 border border-slate-800/80 rounded-2xl text-slate-400">
          <Layers className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <p className="font-medium text-slate-300">No civic incidents match your filter.</p>
          <p className="text-xs text-slate-500 mt-1">
            New incidents are automatically generated when citizen complaints are clustered.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {filtered.map((inc) => (
            <div
              key={inc.id}
              onClick={() => setSelectedIncident(inc)}
              className="bg-slate-900/80 border border-slate-800 hover:border-slate-700 p-5 rounded-2xl cursor-pointer transition-all hover:shadow-lg hover:shadow-emerald-950/10 space-y-4 group"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-emerald-400 bg-emerald-950/60 border border-emerald-800/50 px-2 py-0.5 rounded-md">
                      {inc.incident_number}
                    </span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-md border font-medium ${getSeverityBadge(
                        inc.severity
                      )}`}
                    >
                      {inc.severity}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                      {inc.priority}
                    </span>
                  </div>
                  <h3 className="text-base font-semibold text-white mt-2 group-hover:text-emerald-300 transition-colors">
                    {inc.title}
                  </h3>
                </div>

                <div
                  className={`border px-2.5 py-1 rounded-xl text-center flex flex-col items-center shrink-0 ${getImpactColor(
                    inc.civic_impact_score
                  )}`}
                >
                  <div className="flex items-center gap-1">
                    <Flame className="w-3.5 h-3.5" />
                    <span className="font-mono font-bold text-sm">{Math.round(inc.civic_impact_score)}</span>
                  </div>
                  <span className="text-[10px] uppercase tracking-wider font-semibold opacity-80">Impact</span>
                </div>
              </div>

              {/* Stats Bar */}
              <div className="grid grid-cols-3 gap-2 bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80 text-xs">
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase">Reports</span>
                  <span className="font-semibold text-slate-200">{inc.report_count} citizen{inc.report_count > 1 ? "s" : ""}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase">Duplicates</span>
                  <span className="font-semibold text-slate-200">{inc.duplicate_count} merged</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase">Status</span>
                  <span className="font-semibold text-emerald-400">{inc.status}</span>
                </div>
              </div>

              {/* Footer location & department */}
              <div className="flex items-center justify-between text-xs text-slate-400 pt-1 border-t border-slate-800/60">
                <div className="flex items-center gap-1.5 truncate">
                  <MapPin className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  <span className="truncate">{inc.ward || inc.city || "New Delhi Ward"}</span>
                </div>
                <div className="flex items-center gap-1 text-slate-500 group-hover:text-emerald-400 transition-colors font-medium">
                  <span>Inspect</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Incident Detail Drawer / Modal */}
      {selectedIncident && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-xl bg-slate-900 border-l border-slate-800 h-full overflow-y-auto p-6 space-y-6 flex flex-col justify-between animate-in slide-in-from-right duration-200">
            <div className="space-y-6">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-emerald-400 bg-emerald-950/80 border border-emerald-800 px-2 py-0.5 rounded">
                      {selectedIncident.incident_number}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      {selectedIncident.status}
                    </span>
                  </div>
                  <h2 className="text-xl font-bold text-white mt-2">{selectedIncident.title}</h2>
                </div>
                <button
                  onClick={() => setSelectedIncident(null)}
                  className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Civic Impact Score Card */}
              <div className="bg-slate-950 border border-slate-800 rounded-2xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Flame className="w-5 h-5 text-amber-400" />
                    <span className="font-bold text-white text-sm">Civic Impact Analysis</span>
                  </div>
                  <span className="font-mono text-lg font-black text-amber-400">
                    {Math.round(selectedIncident.civic_impact_score)} / 100
                  </span>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-emerald-500 via-amber-500 to-red-500"
                    style={{ width: `${Math.min(100, selectedIncident.civic_impact_score)}%` }}
                  />
                </div>

                {selectedIncident.priority_explanation && (
                  <p className="text-xs text-slate-400 leading-relaxed bg-slate-900/80 p-2.5 rounded-xl border border-slate-800">
                    {selectedIncident.priority_explanation}
                  </p>
                )}
              </div>

              {/* Metadata Grid */}
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <span className="text-slate-500 block">Department</span>
                  <span className="font-semibold text-slate-200">
                    {selectedIncident.department_name || "Municipal Infrastructure"}
                  </span>
                </div>
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <span className="text-slate-500 block">Ward & Location</span>
                  <span className="font-semibold text-slate-200">
                    {selectedIncident.ward || "Ward 101, Central"}
                  </span>
                </div>
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <span className="text-slate-500 block">First Reported</span>
                  <span className="font-semibold text-slate-200">
                    {new Date(selectedIncident.first_reported_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <span className="text-slate-500 block">Citizen Reports</span>
                  <span className="font-semibold text-emerald-400">
                    {selectedIncident.report_count} clustered complaints
                  </span>
                </div>
              </div>

              {/* Clustered Citizen Reports */}
              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-white flex items-center justify-between">
                  <span>Linked Citizen Complaints</span>
                  <span className="text-xs text-slate-500">{incidentReports.length} records</span>
                </h4>

                <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                  {incidentReports.map((item: any) => (
                    <div
                      key={item.complaint_id}
                      onClick={() => {
                        if (onViewComplaintDetail) {
                          onViewComplaintDetail(item.complaint_id);
                        }
                      }}
                      className="bg-slate-950 hover:bg-slate-800/80 p-3 rounded-xl border border-slate-800 cursor-pointer transition-colors flex items-center justify-between"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-semibold text-slate-300">
                            {item.complaint_number}
                          </span>
                          {item.is_canonical && (
                            <span className="text-[10px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-1.5 py-0.2 rounded font-bold">
                              CANONICAL
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-400 mt-1 line-clamp-1">{item.title}</p>
                      </div>
                      <div className="text-right shrink-0">
                        <span className="text-xs text-slate-500 font-mono">
                          {Math.round((item.similarity_score || 1) * 100)}% match
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Officer Action Bar */}
            <div className="pt-4 border-t border-slate-800 flex items-center gap-3">
              <button
                onClick={() => setStatusUpdateModal(true)}
                className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-2.5 rounded-xl text-sm transition-colors shadow-lg shadow-emerald-950/20"
              >
                Transition Status
              </button>
              <button
                onClick={() => setSelectedIncident(null)}
                className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-sm"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Status Transition Modal */}
      {statusUpdateModal && selectedIncident && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 w-full max-w-md p-6 rounded-2xl space-y-4">
            <h3 className="text-lg font-bold text-white">Transition Incident Status</h3>
            <p className="text-xs text-slate-400">
              Updating the incident status will record an immutable entry in the audit trail.
            </p>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">New Status</label>
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="OPEN">OPEN</option>
                  <option value="ASSIGNED">ASSIGNED</option>
                  <option value="IN_PROGRESS">IN_PROGRESS</option>
                  <option value="RESOLVED">RESOLVED</option>
                  <option value="CLOSED">CLOSED</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Reason / Notes</label>
                <textarea
                  rows={3}
                  value={statusReason}
                  onChange={(e) => setStatusReason(e.target.value)}
                  placeholder="e.g. Dispatched maintenance crew to repair culvert"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setStatusUpdateModal(false)}
                className="px-4 py-2 text-sm text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={() =>
                  updateStatusMutation.mutate({
                    id: selectedIncident.id,
                    status: newStatus,
                    reason: statusReason,
                  })
                }
                disabled={updateStatusMutation.isPending}
                className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold rounded-xl disabled:opacity-50"
              >
                {updateStatusMutation.isPending ? "Updating..." : "Confirm Transition"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
