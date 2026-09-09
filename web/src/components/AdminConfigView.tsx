import React, { useState } from "react";
import { Department, Jurisdiction, Category, AuditLogItem } from "../types";
import { Building2, MapPin, Tag, GitFork, Shield, Plus, Check } from "lucide-react";
import { api } from "../api";

interface AdminConfigViewProps {
  departments: Department[];
  jurisdictions: Jurisdiction[];
  categories: Category[];
  auditLogs: AuditLogItem[];
  onRefresh: () => void;
}

export const AdminConfigView: React.FC<AdminConfigViewProps> = ({
  departments,
  jurisdictions,
  categories,
  auditLogs,
  onRefresh
}) => {
  const [subTab, setSubTab] = useState<"depts" | "jurisdictions" | "categories" | "audit">("depts");

  // Form states
  const [newDeptName, setNewDeptName] = useState("");
  const [newDeptCode, setNewDeptCode] = useState("");
  const [newDeptEmail, setNewDeptEmail] = useState("");
  const [isCreatingDept, setIsCreatingDept] = useState(false);

  const [newJurCity, setNewJurCity] = useState("New Delhi");
  const [newJurZone, setNewJurZone] = useState("");
  const [newJurWard, setNewJurWard] = useState("");
  const [isCreatingJur, setIsCreatingJur] = useState(false);

  const handleCreateDept = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDeptName || !newDeptCode) return;
    try {
      setIsCreatingDept(true);
      await api.post("/admin/departments", {
        name: newDeptName,
        code: newDeptCode.toUpperCase(),
        contact_email: newDeptEmail || undefined
      });
      setNewDeptName("");
      setNewDeptCode("");
      setNewDeptEmail("");
      onRefresh();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to create department");
    } finally {
      setIsCreatingDept(false);
    }
  };

  const handleCreateJur = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newJurCity || !newJurZone || !newJurWard) return;
    try {
      setIsCreatingJur(true);
      await api.post("/admin/jurisdictions", {
        city: newJurCity,
        zone: newJurZone,
        ward: newJurWard
      });
      setNewJurZone("");
      setNewJurWard("");
      onRefresh();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to create jurisdiction");
    } finally {
      setIsCreatingJur(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">System Administration & Routing Configuration</h1>
          <p className="text-xs text-slate-500">Configure authority departments, jurisdictional boundaries, and audit logging</p>
        </div>
      </div>

      {/* Sub Tabs */}
      <div className="flex items-center space-x-2 text-xs border-b border-slate-200 pb-2">
        <button
          onClick={() => setSubTab("depts")}
          className={`px-4 py-2 rounded-xl font-semibold transition-all flex items-center space-x-2 ${
            subTab === "depts" ? "bg-slate-900 text-white shadow-sm" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
          }`}
        >
          <Building2 className="w-4 h-4" />
          <span>Departments ({departments.length})</span>
        </button>
        <button
          onClick={() => setSubTab("jurisdictions")}
          className={`px-4 py-2 rounded-xl font-semibold transition-all flex items-center space-x-2 ${
            subTab === "jurisdictions" ? "bg-slate-900 text-white shadow-sm" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
          }`}
        >
          <MapPin className="w-4 h-4" />
          <span>Jurisdictions ({jurisdictions.length})</span>
        </button>
        <button
          onClick={() => setSubTab("categories")}
          className={`px-4 py-2 rounded-xl font-semibold transition-all flex items-center space-x-2 ${
            subTab === "categories" ? "bg-slate-900 text-white shadow-sm" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
          }`}
        >
          <Tag className="w-4 h-4" />
          <span>Categories ({categories.length})</span>
        </button>
        <button
          onClick={() => setSubTab("audit")}
          className={`px-4 py-2 rounded-xl font-semibold transition-all flex items-center space-x-2 ${
            subTab === "audit" ? "bg-slate-900 text-white shadow-sm" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
          }`}
        >
          <Shield className="w-4 h-4" />
          <span>Audit Logs ({auditLogs.length})</span>
        </button>
      </div>

      {/* Departments SubTab */}
      {subTab === "depts" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 uppercase font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">Code</th>
                  <th className="py-3 px-4">Department Name</th>
                  <th className="py-3 px-4">Contact</th>
                  <th className="py-3 px-4">Officers</th>
                  <th className="py-3 px-4">Active Tasks</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {departments.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-slate-800">{d.code}</td>
                    <td className="py-3 px-4 font-semibold text-slate-900">{d.name}</td>
                    <td className="py-3 px-4 text-slate-500">{d.contact_email || "N/A"}</td>
                    <td className="py-3 px-4 text-slate-700">{d.officer_count}</td>
                    <td className="py-3 px-4 font-semibold text-amber-600">{d.active_complaints_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Add Department Form */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
            <h2 className="text-sm font-bold text-slate-900">Add New Department</h2>
            <form onSubmit={handleCreateDept} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Department Name</label>
                <input
                  type="text"
                  value={newDeptName}
                  onChange={(e) => setNewDeptName(e.target.value)}
                  placeholder="e.g. Parks & Gardens Division"
                  className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none"
                />
              </div>
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Code</label>
                <input
                  type="text"
                  value={newDeptCode}
                  onChange={(e) => setNewDeptCode(e.target.value)}
                  placeholder="e.g. PARKS"
                  className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none"
                />
              </div>
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Contact Email</label>
                <input
                  type="email"
                  value={newDeptEmail}
                  onChange={(e) => setNewDeptEmail(e.target.value)}
                  placeholder="parks@civiclens.gov"
                  className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none"
                />
              </div>
              <button
                type="submit"
                disabled={isCreatingDept || !newDeptName || !newDeptCode}
                className="w-full bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white font-semibold py-2.5 rounded-xl transition-colors"
              >
                {isCreatingDept ? "Saving..." : "Create Department"}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Jurisdictions SubTab */}
      {subTab === "jurisdictions" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 uppercase font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">City</th>
                  <th className="py-3 px-4">Zone</th>
                  <th className="py-3 px-4">Ward</th>
                  <th className="py-3 px-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {jurisdictions.map((j) => (
                  <tr key={j.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-4 font-semibold text-slate-900">{j.city}</td>
                    <td className="py-3 px-4 text-slate-700">{j.zone}</td>
                    <td className="py-3 px-4 font-mono text-slate-600">{j.ward}</td>
                    <td className="py-3 px-4">
                      <span className="bg-emerald-50 text-emerald-700 font-semibold px-2 py-0.5 rounded-full border border-emerald-200">
                        Active
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
            <h2 className="text-sm font-bold text-slate-900">Add Jurisdiction Ward</h2>
            <form onSubmit={handleCreateJur} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">City</label>
                <input
                  type="text"
                  value={newJurCity}
                  onChange={(e) => setNewJurCity(e.target.value)}
                  className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none"
                />
              </div>
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Zone</label>
                <input
                  type="text"
                  value={newJurZone}
                  onChange={(e) => setNewJurZone(e.target.value)}
                  placeholder="e.g. South Zone"
                  className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none"
                />
              </div>
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Ward Name / Code</label>
                <input
                  type="text"
                  value={newJurWard}
                  onChange={(e) => setNewJurWard(e.target.value)}
                  placeholder="e.g. Ward 108 - Saket"
                  className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none"
                />
              </div>
              <button
                type="submit"
                disabled={isCreatingJur || !newJurZone || !newJurWard}
                className="w-full bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white font-semibold py-2.5 rounded-xl transition-colors"
              >
                {isCreatingJur ? "Saving..." : "Create Ward"}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Categories SubTab */}
      {subTab === "categories" && (
        <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 uppercase font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Category Name</th>
                <th className="py-3 px-4">Code</th>
                <th className="py-3 px-4">Default Department</th>
                <th className="py-3 px-4">Baseline Severity</th>
                <th className="py-3 px-4">Baseline Priority</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {categories.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3 px-4 font-semibold text-slate-900">{c.name}</td>
                  <td className="py-3 px-4 font-mono text-slate-600">{c.code}</td>
                  <td className="py-3 px-4 text-slate-700">{c.default_department_name || "General"}</td>
                  <td className="py-3 px-4">
                    <span className="font-bold text-amber-600">{c.default_severity}</span>
                  </td>
                  <td className="py-3 px-4 font-bold text-slate-800">{c.default_priority}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Audit Logs SubTab */}
      {subTab === "audit" && (
        <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 uppercase font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Actor</th>
                <th className="py-3 px-4">Action</th>
                <th className="py-3 px-4">Entity</th>
                <th className="py-3 px-4">Delta / Context</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {auditLogs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3 px-4 font-mono text-slate-500 text-[11px]">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td className="py-3 px-4 font-semibold text-slate-900">{log.user_name || "System"}</td>
                  <td className="py-3 px-4">
                    <span className="bg-slate-100 font-mono text-[10px] text-slate-800 px-2 py-0.5 rounded border border-slate-200">
                      {log.action}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-medium text-slate-700">{log.entity_name}</td>
                  <td className="py-3 px-4 font-mono text-[10px] text-slate-500 max-w-xs truncate">
                    {JSON.stringify(log.new_value_json || {})}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
