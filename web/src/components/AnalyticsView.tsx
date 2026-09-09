import React from "react";
import { AnalyticsDashboard } from "../types";
import { BarChart3, TrendingUp, Clock, CheckCircle, ShieldCheck } from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  PieChart,
  Pie,
  Cell
} from "recharts";

const COLORS = ["#16a34a", "#3b82f6", "#f97316", "#ef4444", "#a855f7", "#06b6d4", "#eab308"];

interface AnalyticsViewProps {
  data: AnalyticsDashboard | null;
}

export const AnalyticsView: React.FC<AnalyticsViewProps> = ({ data }) => {
  if (!data) return <div className="p-8 text-center text-slate-400">Loading analytics data...</div>;

  const { metrics, category_distribution, department_performance, trend_last_30_days } = data;

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Municipal SLA & Resolution Analytics</h1>
          <p className="text-xs text-slate-500">Comprehensive departmental turnaround velocity and citizen satisfaction reports</p>
        </div>
        <div className="flex items-center space-x-2 text-xs bg-emerald-50 text-emerald-700 px-3 py-1.5 rounded-xl border border-emerald-200 font-semibold">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>SLA Target: 95.0% Adherence</span>
        </div>
      </div>

      {/* Grid Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Share (Pie) */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
          <h2 className="text-sm font-bold text-slate-900 mb-2">Complaint Category Composition</h2>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={category_distribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={85}
                  paddingAngle={3}
                  dataKey="count"
                  nameKey="category_name"
                  label={({ name, percent }: any) => `${name} (${((percent || 0) * 100).toFixed(0)}%)`}
                >
                  {category_distribution.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Turnaround by Department */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
          <h2 className="text-sm font-bold text-slate-900 mb-2">Average Resolution Time (Hours)</h2>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={department_performance}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="department_name" tick={{ fontSize: 9, fill: '#64748b' }} />
                <YAxis tick={{ fontSize: 10, fill: '#64748b' }} />
                <Tooltip />
                <Bar dataKey="avg_resolution_hours" fill="#3b82f6" radius={[6, 6, 0, 0]} name="Avg Hours" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Detailed Department Performance Grid */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
        <h2 className="text-sm font-bold text-slate-900">SLA Compliance Breakdown</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 uppercase font-semibold border-y border-slate-200">
              <tr>
                <th className="py-3 px-4">Department</th>
                <th className="py-3 px-4">Assigned Tasks</th>
                <th className="py-3 px-4">Resolved on Time</th>
                <th className="py-3 px-4">SLA Violations</th>
                <th className="py-3 px-4">Adherence Rating</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {department_performance.map((d) => (
                <tr key={d.department_id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3 px-4 font-semibold text-slate-900">{d.department_name}</td>
                  <td className="py-3 px-4 text-slate-600">{d.total_assigned}</td>
                  <td className="py-3 px-4 text-emerald-600 font-semibold">{d.resolved_count}</td>
                  <td className="py-3 px-4 text-red-600 font-semibold">0</td>
                  <td className="py-3 px-4 font-bold text-slate-800">{d.sla_compliance_rate}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
