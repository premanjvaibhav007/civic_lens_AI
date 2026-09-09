import React from "react";
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  TrendingUp,
  Users,
  Copy,
  Flame,
  ArrowUpRight
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  Legend
} from "recharts";
import { AnalyticsDashboard } from "../types";

interface OverviewViewProps {
  data: AnalyticsDashboard | null;
  onNavigateToQueue: () => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({ data, onNavigateToQueue }) => {
  if (!data) {
    return (
      <div className="flex items-center justify-center p-12 text-slate-400">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mr-3"></div>
        Loading municipal overview metrics...
      </div>
    );
  }

  const { metrics, category_distribution, department_performance, trend_last_30_days } = data;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl text-white flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Municipal Command Center</h1>
          <p className="text-slate-400 text-sm mt-1">
            Real-time AI triage, automated jurisdiction routing, and citizen resolution verification
          </p>
        </div>
        <button
          onClick={onNavigateToQueue}
          className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold px-4 py-2.5 rounded-xl transition-all shadow-lg shadow-emerald-500/20 flex items-center space-x-2 text-sm"
        >
          <span>Open Complaint Queue</span>
          <ArrowUpRight className="w-4 h-4" />
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Complaints */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Reported</span>
            <div className="p-2 bg-slate-100 rounded-xl text-slate-600">
              <AlertCircle className="w-5 h-5" />
            </div>
          </div>
          <p className="text-3xl font-bold text-slate-900 mt-2">{metrics.total_complaints}</p>
          <div className="flex items-center space-x-2 text-xs text-slate-500 mt-2">
            <span className="text-emerald-600 font-semibold">{metrics.open_complaints} open</span>
            <span>•</span>
            <span>{metrics.duplicate_count} duplicates detected</span>
          </div>
        </div>

        {/* In Progress */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase tracking-wider">In Progress</span>
            <div className="p-2 bg-amber-50 rounded-xl text-amber-600">
              <Clock className="w-5 h-5" />
            </div>
          </div>
          <p className="text-3xl font-bold text-slate-900 mt-2">{metrics.in_progress}</p>
          <div className="flex items-center space-x-2 text-xs text-slate-500 mt-2">
            <span className="text-amber-600 font-semibold">{metrics.pending_assignment} pending triage</span>
            <span>•</span>
            <span className="text-red-500 font-semibold">{metrics.escalated_complaints} escalated</span>
          </div>
        </div>

        {/* SLA Compliance */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase tracking-wider">SLA Compliance</span>
            <div className="p-2 bg-emerald-50 rounded-xl text-emerald-600">
              <TrendingUp className="w-5 h-5" />
            </div>
          </div>
          <p className="text-3xl font-bold text-slate-900 mt-2">{metrics.sla_compliance_rate}%</p>
          <div className="flex items-center space-x-2 text-xs text-slate-500 mt-2">
            <span>Avg resolution:</span>
            <span className="font-semibold text-slate-700">{metrics.average_resolution_hours} hrs</span>
          </div>
        </div>

        {/* Citizen Satisfaction */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Citizen Rating</span>
            <div className="p-2 bg-blue-50 rounded-xl text-blue-600">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>
          <div className="flex items-baseline space-x-2 mt-2">
            <p className="text-3xl font-bold text-slate-900">{metrics.citizen_satisfaction_score}</p>
            <span className="text-slate-400 text-sm">/ 5.0</span>
          </div>
          <div className="flex items-center space-x-1 text-xs text-amber-500 mt-2">
            {"★".repeat(Math.round(metrics.citizen_satisfaction_score))}
            <span className="text-slate-500 ml-1">Verified resolutions</span>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 30-Day Trend Chart */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-slate-900">30-Day Resolution Velocity</h2>
              <p className="text-xs text-slate-500">Submitted vs Resolved complaints timeline</p>
            </div>
            <span className="text-xs bg-slate-100 text-slate-600 px-2.5 py-1 rounded-full font-medium">
              Daily aggregates
            </span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trend_last_30_days.slice(-14)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748b' }} />
                <YAxis tick={{ fontSize: 10, fill: '#64748b' }} />
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Line type="monotone" dataKey="submitted" stroke="#6366f1" strokeWidth={2} name="New Reports" />
                <Line type="monotone" dataKey="resolved" stroke="#10b981" strokeWidth={2} name="Resolved" />
                <Line type="monotone" dataKey="escalated" stroke="#ef4444" strokeWidth={1.5} strokeDasharray="4 4" name="Escalated" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Breakdown Bar Chart */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-slate-900">Issues by Infrastructure Category</h2>
              <p className="text-xs text-slate-500">AI-classified volume distribution</p>
            </div>
            <span className="text-xs bg-emerald-50 text-emerald-700 px-2.5 py-1 rounded-full font-medium border border-emerald-200">
              Multimodal NLP/Vision
            </span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={category_distribution} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis type="number" tick={{ fontSize: 10, fill: '#64748b' }} />
                <YAxis dataKey="category_name" type="category" width={110} tick={{ fontSize: 10, fill: '#475569' }} />
                <Tooltip />
                <Bar dataKey="count" fill="#16a34a" radius={[0, 6, 6, 0]} name="Complaints" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Department Performance Table Preview */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900">Department Operational Performance</h2>
            <p className="text-xs text-slate-500">Real-time assignment, resolution velocity, and SLA adherence</p>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600 text-xs uppercase font-semibold border-y border-slate-200">
              <tr>
                <th className="py-3 px-4">Department</th>
                <th className="py-3 px-4">Total Assigned</th>
                <th className="py-3 px-4">In Progress</th>
                <th className="py-3 px-4">Resolved</th>
                <th className="py-3 px-4">Avg Turnaround</th>
                <th className="py-3 px-4">SLA Adherence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {department_performance.map((dept) => (
                <tr key={dept.department_id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3.5 px-4 font-semibold text-slate-900">{dept.department_name}</td>
                  <td className="py-3.5 px-4 text-slate-600">{dept.total_assigned}</td>
                  <td className="py-3.5 px-4">
                    <span className="bg-amber-100 text-amber-800 text-xs px-2 py-0.5 rounded-full font-medium">
                      {dept.in_progress_count}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="bg-emerald-100 text-emerald-800 text-xs px-2 py-0.5 rounded-full font-medium">
                      {dept.resolved_count}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-600 font-mono text-xs">{dept.avg_resolution_hours}h</td>
                  <td className="py-3.5 px-4">
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-slate-200 rounded-full h-2 overflow-hidden">
                        <div
                          className={`h-full rounded-full ${dept.sla_compliance_rate >= 90 ? 'bg-emerald-500' : 'bg-amber-500'}`}
                          style={{ width: `${Math.min(100, dept.sla_compliance_rate)}%` }}
                        ></div>
                      </div>
                      <span className="text-xs font-semibold text-slate-700">{dept.sla_compliance_rate}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
