import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  TrendingUp,
  AlertTriangle,
  Clock,
  ShieldCheck,
  Building,
  Info,
  Calendar,
  Layers,
  ArrowRight,
  Activity,
  CheckCircle2
} from "lucide-react";
import { api } from "../api";
import { PredictionStatus, InfrastructureAssetItem, UserSummary } from "../types";

interface PredictionViewProps {
  user: UserSummary | null;
}

export const PredictionView: React.FC<PredictionViewProps> = ({ user }) => {
  const [selectedAsset, setSelectedAsset] = useState<InfrastructureAssetItem | null>(null);

  const { data: statusData, isLoading: statusLoading } = useQuery<PredictionStatus>({
    queryKey: ["predictionStatus"],
    queryFn: async () => {
      const res = await api.get("/predictions/status");
      return res.data;
    },
  });

  const { data: assetsData, isLoading: assetsLoading } = useQuery<{
    success: boolean;
    data: {
      items: InfrastructureAssetItem[];
      total: number;
    };
  }>({
    queryKey: ["infrastructureAssets"],
    queryFn: async () => {
      const res = await api.get("/assets?page=1&page_size=20");
      return res.data;
    },
  });

  const assets = assetsData?.data?.items || [];

  const getRiskBadge = (level: string) => {
    switch (level) {
      case "CRITICAL":
        return "bg-red-500/20 text-red-400 border-red-500/30";
      case "HIGH":
        return "bg-amber-500/20 text-amber-400 border-amber-500/30";
      case "MEDIUM":
        return "bg-blue-500/20 text-blue-400 border-blue-500/30";
      default:
        return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
          <TrendingUp className="w-7 h-7 text-emerald-400" />
          Predictive Infrastructure Intelligence
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Machine-assisted failure risk forecasting, seasonal hazard modeling, and preventive infrastructure health monitoring.
        </p>
      </div>

      {/* Honest Data Readiness Banner */}
      <div className="bg-slate-900/90 border border-slate-800 p-5 rounded-2xl space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Activity className={`w-5 h-5 ${statusData?.has_sufficient_data ? "text-emerald-400" : "text-amber-400"}`} />
            <h3 className="text-sm font-bold text-white">Model Readiness & Data Integrity Status</h3>
          </div>
          <span
            className={`text-xs px-2.5 py-1 rounded-full font-mono font-bold border ${
              statusData?.has_sufficient_data
                ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                : "bg-amber-500/20 text-amber-400 border-amber-500/30"
            }`}
          >
            {statusData?.has_sufficient_data ? "ACTIVE FORECASTING" : "LEARNING PHASE"}
          </span>
        </div>

        <p className="text-xs text-slate-300 leading-relaxed">
          {statusData?.message ||
            "Predictive models strictly observe empirical historical complaint clusters. Predictions are never synthesized or fabricated."}
        </p>

        {/* Progress toward 30-day requirement */}
        <div className="space-y-1.5 pt-1">
          <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
            <span>Historical Data Span: {statusData?.days_of_data || 0} days</span>
            <span>Required: {statusData?.minimum_required_days || 30} days</span>
          </div>
          <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-slate-800">
            <div
              className="h-full bg-emerald-500 transition-all"
              style={{
                width: `${Math.min(
                  100,
                  ((statusData?.days_of_data || 0) / (statusData?.minimum_required_days || 30)) * 100
                )}%`,
              }}
            />
          </div>
        </div>
      </div>

      {/* Seasonal Hazard Vulnerability Calendar */}
      <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <Calendar className="w-4 h-4 text-emerald-400" />
          Seasonal Infrastructure Risk Matrix
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs">
          <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-1.5">
            <span className="font-bold text-amber-400 block">Monsoon Season (Jun–Sep)</span>
            <p className="text-slate-400 text-[11px]">
              Drainage blockage, low-lying waterlogging, and asphalt pothole expansion.
            </p>
            <span className="text-[10px] text-slate-500 block">Focus: Drain Desilting & Pump Deployment</span>
          </div>

          <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-1.5">
            <span className="font-bold text-blue-400 block">Post-Monsoon (Oct–Nov)</span>
            <p className="text-slate-400 text-[11px]">
              Subgrade erosion, pothole craters on heavy transit corridors, paver settling.
            </p>
            <span className="text-[10px] text-slate-500 block">Focus: Road Resurfacing & Cold Patching</span>
          </div>

          <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-1.5">
            <span className="font-bold text-indigo-400 block">Winter Fog (Dec–Feb)</span>
            <p className="text-slate-400 text-[11px]">
              Reduced visibility hazards, streetlight failure spikes, traffic sign damage.
            </p>
            <span className="text-[10px] text-slate-500 block">Focus: Luminaire Replacement & Signage</span>
          </div>

          <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-1.5">
            <span className="font-bold text-rose-400 block">Peak Summer (Apr–Jun)</span>
            <p className="text-slate-400 text-[11px]">
              Thermal water pipeline bursts, reservoir pressure drops, garbage combustion risks.
            </p>
            <span className="text-[10px] text-slate-500 block">Focus: Valve Maintenance & Waste Clearance</span>
          </div>
        </div>
      </div>

      {/* Tracked Physical Assets & Health Scores */}
      <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Building className="w-4 h-4 text-emerald-400" />
            Infrastructure Asset Health & Vulnerability Index
          </h3>
          <span className="text-xs text-slate-500 font-mono">{assets.length} registered assets</span>
        </div>

        {assetsLoading ? (
          <div className="py-8 text-center text-slate-500 text-xs">Loading infrastructure assets...</div>
        ) : assets.length === 0 ? (
          <div className="py-8 text-center text-slate-500 text-xs">
            No assets registered. Assets are created via the Administration panel or automated inventory ingestion.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {assets.map((asset) => (
              <div
                key={asset.id}
                onClick={() => setSelectedAsset(asset)}
                className="bg-slate-950 hover:bg-slate-800/60 p-4 rounded-xl border border-slate-800 cursor-pointer transition-all space-y-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="font-mono text-[11px] text-emerald-400 font-bold">
                      {asset.asset_code}
                    </span>
                    <h4 className="text-sm font-semibold text-white mt-0.5 line-clamp-1">
                      {asset.name}
                    </h4>
                  </div>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-md border font-bold ${getRiskBadge(
                      asset.risk_level
                    )}`}
                  >
                    {asset.risk_level}
                  </span>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">Health Score</span>
                    <span className="font-mono font-bold text-slate-200">
                      {Math.round(asset.health_score)}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${
                        asset.health_score >= 75
                          ? "bg-emerald-500"
                          : asset.health_score >= 50
                          ? "bg-amber-500"
                          : "bg-red-500"
                      }`}
                      style={{ width: `${asset.health_score}%` }}
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-800/80">
                  <span>{asset.complaint_count} incidents</span>
                  <span>{asset.repair_count} repairs</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
