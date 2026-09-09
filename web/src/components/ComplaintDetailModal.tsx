import React, { useState } from "react";
import {
  X,
  Sparkles,
  MapPin,
  Calendar,
  User,
  Shield,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Upload,
  Send,
  Building,
  Copy,
  Layers,
  ArrowRight
} from "lucide-react";
import { ComplaintDetail, UserSummary, Department } from "../types";
import { api, getMediaUrl } from "../api";

interface ComplaintDetailModalProps {
  complaint: ComplaintDetail | null;
  currentUser: UserSummary | null;
  departments: Department[];
  onClose: () => void;
  onRefresh: () => void;
}

export const ComplaintDetailModal: React.FC<ComplaintDetailModalProps> = ({
  complaint,
  currentUser,
  departments,
  onClose,
  onRefresh
}) => {
  if (!complaint) return null;

  const [activeTab, setActiveTab] = useState<"overview" | "timeline" | "resolution" | "duplicates">("overview");
  
  // Status update state
  const [newStatus, setNewStatus] = useState<string>("");
  const [statusReason, setStatusReason] = useState<string>("");
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);

  // Assignment state
  const [selectedDept, setSelectedDept] = useState<string>(complaint.department_id || "");
  const [assignmentRemarks, setAssignmentRemarks] = useState<string>("");
  const [isAssigning, setIsAssigning] = useState(false);

  // Resolution evidence state
  const [completionNote, setCompletionNote] = useState<string>("");
  const [evidenceFile, setEvidenceFile] = useState<File | null>(null);
  const [isSubmittingEvidence, setIsSubmittingEvidence] = useState(false);

  // Comment state
  const [commentText, setCommentText] = useState<string>("");
  const [isPostingComment, setIsPostingComment] = useState(false);

  const handleStatusChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newStatus) return;
    try {
      setIsUpdatingStatus(true);
      await api.patch(`/complaints/${complaint.id}/status`, {
        new_status: newStatus,
        reason: statusReason || undefined
      });
      onRefresh();
      setNewStatus("");
      setStatusReason("");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Status update failed");
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  const handleAssign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDept) return;
    try {
      setIsAssigning(true);
      await api.post(`/complaints/${complaint.id}/assign`, {
        department_id: selectedDept,
        remarks: assignmentRemarks || undefined
      });
      onRefresh();
      setAssignmentRemarks("");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Assignment failed");
    } finally {
      setIsAssigning(false);
    }
  };

  const handleResolutionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!completionNote || !evidenceFile) {
      alert("Please provide both an evidence photo and completion remarks.");
      return;
    }
    try {
      setIsSubmittingEvidence(true);
      const formData = new FormData();
      formData.append("completion_note", completionNote);
      formData.append("evidence_image", evidenceFile);

      await api.post(`/complaints/${complaint.id}/resolution`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      alert("Resolution evidence uploaded! Verification request dispatched to citizen.");
      onRefresh();
      setCompletionNote("");
      setEvidenceFile(null);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Evidence upload failed");
    } finally {
      setIsSubmittingEvidence(false);
    }
  };

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!commentText.trim()) return;
    try {
      setIsPostingComment(true);
      await api.post(`/complaints/${complaint.id}/comments`, {
        comment_text: commentText
      });
      setCommentText("");
      onRefresh();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to post comment");
    } finally {
      setIsPostingComment(false);
    }
  };

  const primaryImage = complaint.images.find((i) => i.is_primary) || complaint.images[0];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white border border-slate-200 rounded-2xl shadow-2xl w-full max-w-5xl max-h-[92vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <span className="font-mono bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs px-2.5 py-1 rounded-lg font-bold">
              {complaint.complaint_number}
            </span>
            <div>
              <h2 className="text-base font-bold truncate max-w-lg text-white">{complaint.title}</h2>
              <p className="text-xs text-slate-400">Reported by {complaint.citizen_name} • {new Date(complaint.created_at).toLocaleString()}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="bg-slate-50 border-b border-slate-200 px-6 flex items-center space-x-6 text-sm">
          <button
            onClick={() => setActiveTab("overview")}
            className={`py-3 font-semibold border-b-2 transition-all ${
              activeTab === "overview" ? "border-emerald-600 text-emerald-700" : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            Overview & AI Analysis
          </button>
          <button
            onClick={() => setActiveTab("timeline")}
            className={`py-3 font-semibold border-b-2 transition-all ${
              activeTab === "timeline" ? "border-emerald-600 text-emerald-700" : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            Lifecycle Timeline ({complaint.timeline.length})
          </button>
          <button
            onClick={() => setActiveTab("resolution")}
            className={`py-3 font-semibold border-b-2 transition-all ${
              activeTab === "resolution" ? "border-emerald-600 text-emerald-700" : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            Resolution Evidence
          </button>
          {complaint.duplicate_candidates.length > 0 && (
            <button
              onClick={() => setActiveTab("duplicates")}
              className={`py-3 font-semibold border-b-2 transition-all flex items-center space-x-1.5 ${
                activeTab === "duplicates" ? "border-emerald-600 text-emerald-700" : "border-transparent text-slate-500 hover:text-slate-900"
              }`}
            >
              <span>Duplicate Candidates</span>
              <span className="bg-amber-100 text-amber-800 text-xs px-1.5 py-0.2 rounded-full font-bold">
                {complaint.duplicate_candidates.length}
              </span>
            </button>
          )}
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {activeTab === "overview" && (
            <div className="space-y-5">
              {/* Live Authority Work Progress Status Card */}
              <div className={`p-4 rounded-2xl border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-sm ${
                complaint.status === "IN_PROGRESS"
                  ? "bg-amber-50/90 border-amber-300 text-amber-950"
                  : complaint.status === "RESOLUTION_SUBMITTED"
                  ? "bg-teal-50 border-teal-300 text-teal-950"
                  : complaint.status === "RESOLVED"
                  ? "bg-emerald-50 border-emerald-300 text-emerald-950"
                  : "bg-blue-50/80 border-blue-200 text-blue-950"
              }`}>
                <div className="flex items-center space-x-3">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                    complaint.status === "IN_PROGRESS"
                      ? "bg-amber-500 text-white animate-pulse"
                      : complaint.status === "RESOLUTION_SUBMITTED"
                      ? "bg-teal-600 text-white"
                      : complaint.status === "RESOLVED"
                      ? "bg-emerald-600 text-white"
                      : "bg-blue-600 text-white"
                  }`}>
                    {complaint.status === "IN_PROGRESS" ? (
                      <span className="text-lg">🚧</span>
                    ) : complaint.status === "RESOLVED" ? (
                      <CheckCircle2 className="w-5 h-5" />
                    ) : complaint.status === "RESOLUTION_SUBMITTED" ? (
                      <Sparkles className="w-5 h-5" />
                    ) : (
                      <Clock className="w-5 h-5" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-bold">
                        {complaint.status === "IN_PROGRESS" && "Authorities Are Actively Working On-Site"}
                        {complaint.status === "RESOLUTION_SUBMITTED" && "Repairs Completed by Authorities — Citizen Review Pending"}
                        {complaint.status === "RESOLVED" && "Work Complete & Officially Verified"}
                        {complaint.status === "ROUTED" && `Assigned to ${complaint.department_name || "Department"}`}
                        {complaint.status === "ASSIGNED" && `Crew Assigned by ${complaint.department_name || "Department"}`}
                        {complaint.status === "SUBMITTED" && "Complaint Ingested — Scheduled for Authority Dispatch"}
                        {complaint.status === "REOPENED" && "Complaint Reopened — Authority Review Required"}
                        {complaint.status === "ESCALATED" && "Escalated to Executive Municipal Cell"}
                      </h4>
                      <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full font-bold bg-white/80 border border-current">
                        {complaint.status.replace("_", " ")}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 mt-0.5">
                      {complaint.status === "IN_PROGRESS" && "Municipal field repair crew has acknowledged this complaint and is actively deployed on-site."}
                      {complaint.status === "RESOLUTION_SUBMITTED" && "An officer has uploaded photographic proof of repair. Please inspect the 'Resolution Evidence' tab."}
                      {complaint.status === "RESOLVED" && "This complaint has been formally inspected, repaired, and confirmed closed."}
                      {complaint.status === "ROUTED" && `Autonomous AI routed this issue to ${complaint.department_name || "the municipality"} based on visual severity.`}
                      {complaint.status === "SUBMITTED" && "Your report is in the priority dispatch queue awaiting crew assignment."}
                    </p>
                  </div>
                </div>

                {/* Quick Action Button for Officers or Citizens */}
                <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
                  {currentUser && (currentUser.role === "OFFICER" || currentUser.role === "ADMIN") && complaint.status !== "RESOLVED" && (
                    <button
                      onClick={() => {
                        if (complaint.status !== "IN_PROGRESS") {
                          setNewStatus("IN_PROGRESS");
                          setStatusReason("Field crew dispatched to site");
                        } else {
                          setActiveTab("resolution");
                        }
                      }}
                      className="bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold px-3 py-2 rounded-xl transition-all shadow-sm flex items-center gap-1.5 cursor-pointer"
                    >
                      {complaint.status === "IN_PROGRESS" ? "📸 Submit Repair Photo" : "👷 Start Work (Mark In Progress)"}
                    </button>
                  )}
                  {complaint.status === "RESOLUTION_SUBMITTED" && (
                    <button
                      onClick={() => setActiveTab("resolution")}
                      className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold px-3 py-2 rounded-xl transition-all shadow-sm flex items-center gap-1 cursor-pointer"
                    >
                      <span>Verify Repair Now</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left Column: Media & Location (5 cols) */}
              <div className="lg:col-span-5 space-y-4">
                <div className="bg-slate-100 rounded-xl overflow-hidden border border-slate-200 aspect-video flex items-center justify-center relative">
                  {primaryImage ? (
                    <img
                      src={getMediaUrl(primaryImage.image_url)}
                      alt="Complaint Evidence"
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        // Fallback image preview if file not found locally
                        (e.target as HTMLElement).style.display = 'none';
                      }}
                    />
                  ) : (
                    <div className="text-slate-400 text-xs flex flex-col items-center">
                      <Layers className="w-8 h-8 mb-1" />
                      <span>No Photo Attached</span>
                    </div>
                  )}
                  <span className="absolute bottom-2 left-2 bg-slate-900/80 backdrop-blur-md text-white text-[10px] px-2 py-0.5 rounded font-mono">
                    Citizen Photo Evidence
                  </span>
                </div>

                {/* Location Box */}
                {complaint.location && (
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-1 text-xs">
                    <div className="flex items-center text-slate-800 font-semibold space-x-1">
                      <MapPin className="w-4 h-4 text-emerald-600" />
                      <span>Location Coordinates</span>
                    </div>
                    <p className="text-slate-600">{complaint.location.address || "Address not geocoded"}</p>
                    <p className="font-mono text-slate-500 text-[11px]">
                      GPS: {complaint.location.latitude.toFixed(5)}, {complaint.location.longitude.toFixed(5)}
                    </p>
                    {complaint.jurisdiction_info && (
                      <p className="text-slate-700 font-medium pt-1 border-t border-slate-200">
                        Jurisdiction: {complaint.jurisdiction_info}
                      </p>
                    )}
                  </div>
                )}

                {/* Authority Action: Assign Officer */}
                <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-3">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                    Department & Officer Triage
                  </h3>
                  <form onSubmit={handleAssign} className="space-y-2">
                    <div>
                      <label className="text-[11px] text-slate-500 font-medium">Department</label>
                      <select
                        value={selectedDept}
                        onChange={(e) => setSelectedDept(e.target.value)}
                        className="w-full text-xs p-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-emerald-500"
                      >
                        <option value="">Select Department</option>
                        {departments.map((d) => (
                          <option key={d.id} value={d.id}>
                            {d.name} ({d.code})
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="text-[11px] text-slate-500 font-medium">Internal Notes</label>
                      <input
                        type="text"
                        value={assignmentRemarks}
                        onChange={(e) => setAssignmentRemarks(e.target.value)}
                        placeholder="e.g. Dispatched to Zone 3 crew"
                        className="w-full text-xs p-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none"
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={isAssigning}
                      className="w-full bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold py-2 rounded-lg transition-colors"
                    >
                      {isAssigning ? "Assigning..." : "Update Assignment"}
                    </button>
                  </form>
                </div>
              </div>

              {/* Right Column: AI Analysis & Details (7 cols) */}
              <div className="lg:col-span-7 space-y-4">
                {/* Description */}
                <div>
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Description</h3>
                  <p className="text-sm text-slate-800 mt-1 bg-slate-50 p-3 rounded-xl border border-slate-100">
                    {complaint.description || "No text description provided."}
                  </p>
                </div>

                {/* AI Analysis Card */}
                {complaint.ai_analysis && (
                  <div className="bg-gradient-to-br from-emerald-950 via-slate-900 to-slate-900 text-white border border-emerald-500/30 rounded-2xl p-5 shadow-lg space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Sparkles className="w-5 h-5 text-emerald-400" />
                        <h3 className="font-bold text-sm text-white">Multimodal AI Triage Report</h3>
                      </div>
                      <span className="text-[10px] font-mono bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded-full">
                        Latency: {Math.round(complaint.ai_analysis.inference_latency_ms)}ms
                      </span>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-800 text-xs">
                      <div className="bg-slate-800/80 p-2 rounded-xl">
                        <span className="text-slate-400 text-[10px] block">Detected Issue</span>
                        <span className="font-bold text-emerald-300">{complaint.ai_analysis.detected_category}</span>
                      </div>
                      <div className="bg-slate-800/80 p-2 rounded-xl">
                        <span className="text-slate-400 text-[10px] block">Confidence</span>
                        <span className="font-bold text-white">{Math.round(complaint.ai_analysis.confidence * 100)}%</span>
                      </div>
                      <div className="bg-slate-800/80 p-2 rounded-xl">
                        <span className="text-slate-400 text-[10px] block">Severity</span>
                        <span className="font-bold text-amber-400">{complaint.severity}</span>
                      </div>
                      <div className="bg-slate-800/80 p-2 rounded-xl">
                        <span className="text-slate-400 text-[10px] block">Priority</span>
                        <span className="font-bold text-red-400">{complaint.priority}</span>
                      </div>
                    </div>

                    {complaint.ai_analysis.explanation_text && (
                      <div className="bg-slate-800/50 p-3 rounded-xl text-xs text-slate-300 border border-slate-700/50">
                        <span className="text-emerald-400 font-semibold block mb-0.5">Decision Rationale:</span>
                        {complaint.ai_analysis.explanation_text}
                      </div>
                    )}
                  </div>
                )}

                {/* Change Status Form */}
                <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-3">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Update Complaint Status</h3>
                  <form onSubmit={handleStatusChange} className="space-y-2">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      <select
                        value={newStatus}
                        onChange={(e) => setNewStatus(e.target.value)}
                        className="text-xs p-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none"
                      >
                        <option value="">Select New Status</option>
                        <option value="IN_PROGRESS">IN_PROGRESS</option>
                        <option value="ESCALATED">ESCALATED</option>
                        <option value="REJECTED">REJECTED</option>
                        <option value="DUPLICATE">DUPLICATE</option>
                      </select>
                      <input
                        type="text"
                        value={statusReason}
                        onChange={(e) => setStatusReason(e.target.value)}
                        placeholder="Reason for change..."
                        className="text-xs p-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none"
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={isUpdatingStatus || !newStatus}
                      className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold px-4 py-2 rounded-lg transition-colors"
                    >
                      {isUpdatingStatus ? "Updating..." : "Commit Status Change"}
                    </button>
                  </form>
                </div>
              </div>
            </div>
          </div>
          )}

          {/* Timeline Tab */}
          {activeTab === "timeline" && (
            <div className="space-y-4">
              <h3 className="text-sm font-bold text-slate-900">Official Lifecycle State History</h3>
              <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
                {complaint.timeline.map((item, idx) => (
                  <div key={item.id} className="relative group">
                    <div className="absolute -left-6 top-1 w-3.5 h-3.5 rounded-full bg-emerald-500 border-2 border-white shadow-sm"></div>
                    <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 text-xs space-y-1">
                      <div className="flex items-center justify-between font-semibold text-slate-900">
                        <span>Status Changed: {item.new_status}</span>
                        <span className="text-slate-400 font-mono text-[10px]">
                          {new Date(item.created_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-slate-600">{item.reason || "Automatic state transition"}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Resolution Evidence Tab */}
          {activeTab === "resolution" && (
            <div className="space-y-6">
              {complaint.resolution_evidence ? (
                <div className="bg-emerald-50/50 border border-emerald-200 rounded-2xl p-5 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2 text-emerald-800 font-bold">
                      <CheckCircle2 className="w-5 h-5" />
                      <span>Resolution Evidence On Record</span>
                    </div>
                    {complaint.resolution_evidence.ai_visual_diff_score !== undefined && (
                      <div className="flex items-center gap-2">
                        <span className="text-xs bg-emerald-100 text-emerald-800 border border-emerald-300 font-mono font-bold px-2.5 py-1 rounded-lg">
                          AI Diff: {Math.round(complaint.resolution_evidence.ai_visual_diff_score)}%
                        </span>
                        <span className="text-xs bg-slate-900 text-white font-mono font-semibold px-2 py-1 rounded-lg">
                          {complaint.resolution_evidence.ai_likely_resolved ? "VERIFIED REPAIR" : "FLAGGED"}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Side by Side: Before & After Photos */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider block">
                        Before Repair (Citizen Report)
                      </span>
                      <div className="aspect-video bg-slate-100 rounded-xl overflow-hidden border border-slate-200">
                        {complaint.images && complaint.images.length > 0 ? (
                          <img
                            src={getMediaUrl(complaint.images[0].image_url)}
                            alt="Before"
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-slate-400 text-xs">
                            No citizen photo attached
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="space-y-1.5">
                      <span className="text-[11px] font-bold text-emerald-700 uppercase tracking-wider block">
                        After Repair (Officer Evidence)
                      </span>
                      <div className="aspect-video bg-slate-100 rounded-xl overflow-hidden border border-emerald-300 ring-2 ring-emerald-500/20">
                        <img
                          src={getMediaUrl(complaint.resolution_evidence.evidence_image_url)}
                          alt="After Repair Evidence"
                          className="w-full h-full object-cover"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Evidence Metadata & Citizen Feedback */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 border-t border-emerald-200/80 text-xs text-slate-700">
                    <div className="space-y-1.5">
                      <p>
                        <strong className="text-slate-900">Submitted By:</strong> {complaint.resolution_evidence.officer_name}
                      </p>
                      <p>
                        <strong className="text-slate-900">Timestamp:</strong>{" "}
                        {new Date(complaint.resolution_evidence.completed_at).toLocaleString()}
                      </p>
                      <p>
                        <strong className="text-slate-900">Officer Note:</strong> {complaint.resolution_evidence.completion_note}
                      </p>
                    </div>

                    <div>
                      {complaint.citizen_verified !== undefined ? (
                        <div className="bg-white p-3 rounded-xl border border-emerald-200 space-y-1">
                          <strong className="text-slate-900 block">Citizen Verification:</strong>
                          {complaint.citizen_verified ? (
                            <span className="text-emerald-700 font-bold block">
                              ★ Confirmed Resolved ({complaint.resolution_rating || 5}/5 stars)
                            </span>
                          ) : (
                            <span className="text-red-600 font-bold block">Rejected / Reopened</span>
                          )}
                          {complaint.citizen_feedback && (
                            <p className="italic text-slate-600">"{complaint.citizen_feedback}"</p>
                          )}
                        </div>
                      ) : (
                        <div className="bg-amber-50 border border-amber-200 p-3 rounded-xl text-amber-800">
                          <strong className="block">Pending Citizen Confirmation</strong>
                          <p className="text-[11px] mt-0.5">Notification dispatched to citizen mobile app for resolution sign-off.</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4 max-w-xl">
                  <h3 className="text-sm font-bold text-slate-900">Submit Work Completion Evidence</h3>
                  <p className="text-xs text-slate-500">
                    Upload an after-repair photo and completion note. A verification request will automatically be sent to the reporting citizen.
                  </p>
                  <form onSubmit={handleResolutionSubmit} className="space-y-3">
                    <div>
                      <label className="text-xs font-medium text-slate-700 block mb-1">After-Repair Photograph</label>
                      <input
                        type="file"
                        accept="image/*"
                        onChange={(e) => setEvidenceFile(e.target.files?.[0] || null)}
                        className="text-xs file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-slate-700 block mb-1">Completion Note / Work Summary</label>
                      <textarea
                        rows={3}
                        value={completionNote}
                        onChange={(e) => setCompletionNote(e.target.value)}
                        placeholder="Detail the repair actions taken, materials used, and final restored state..."
                        className="w-full text-xs p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none"
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={isSubmittingEvidence || !completionNote || !evidenceFile}
                      className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold px-4 py-2.5 rounded-xl transition-all shadow-md shadow-emerald-600/20 flex items-center space-x-2"
                    >
                      <Upload className="w-4 h-4" />
                      <span>{isSubmittingEvidence ? "Uploading..." : "Submit Resolution & Request Verification"}</span>
                    </button>
                  </form>
                </div>
              )}
            </div>
          )}

          {/* Duplicates Tab */}
          {activeTab === "duplicates" && (
            <div className="space-y-4">
              <h3 className="text-sm font-bold text-slate-900">AI-Detected Candidate Duplicates</h3>
              <p className="text-xs text-slate-500">
                Spatial-temporal duplicate candidates within 200m radius evaluated using image embeddings and text token similarity.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {complaint.duplicate_candidates.map((dup) => (
                  <div key={dup.id} className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-xs space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-slate-800">{dup.candidate_complaint_number}</span>
                      <span className="bg-amber-100 text-amber-800 font-bold px-2 py-0.5 rounded-full text-[10px]">
                        {Math.round(dup.similarity_score * 100)}% Similarity
                      </span>
                    </div>
                    <p className="font-semibold text-slate-900">{dup.candidate_title}</p>
                    <div className="grid grid-cols-3 gap-2 text-[10px] text-slate-500 bg-white p-2 rounded-lg border border-slate-100 font-mono">
                      <div>Geo: {dup.geo_distance_meters}m</div>
                      <div>Text: {Math.round(dup.text_similarity * 100)}%</div>
                      <div>Status: {dup.candidate_status}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
