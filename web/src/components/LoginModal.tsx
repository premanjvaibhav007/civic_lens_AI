import React, { useState } from "react";
import { X, Shield, Lock, Mail, UserCheck } from "lucide-react";
import { api } from "../api";
import { UserSummary } from "../types";

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLoginSuccess: (user: UserSummary, token: string) => void;
}

export const LoginModal: React.FC<LoginModalProps> = ({ isOpen, onClose, onLoginSuccess }) => {
  if (!isOpen) return null;

  const [email, setEmail] = useState("admin@civiclens.gov");
  const [password, setPassword] = useState("Admin@123456");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    try {
      setIsLoading(true);
      const resp = await api.post("/auth/login", { email, password });
      const { access_token, user } = resp.data.data;
      localStorage.setItem("civiclens_token", access_token);
      localStorage.setItem("civiclens_user", JSON.stringify(user));
      onLoginSuccess(user, access_token);
      onClose();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || "Authentication failed. Check credentials.");
    } finally {
      setIsLoading(false);
    }
  };

  const setPreset = (presetEmail: string, presetPass: string) => {
    setEmail(presetEmail);
    setPassword(presetPass);
    setErrorMsg("");
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white border border-slate-200 rounded-3xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="bg-slate-900 text-white p-6 relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
          <div className="w-12 h-12 bg-emerald-500/20 border border-emerald-500/30 rounded-2xl flex items-center justify-center text-emerald-400 mb-3">
            <Shield className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold">Authority Sign In</h2>
          <p className="text-xs text-slate-400 mt-1">Access the CivicLens Municipal Resolution Portal</p>
        </div>

        {/* Form */}
        <div className="p-6 space-y-4">
          {errorMsg && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl">
              {errorMsg}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-3">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Official Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="officer@civiclens.gov"
                  className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs py-2.5 rounded-xl transition-all shadow-md shadow-slate-900/20"
            >
              {isLoading ? "Verifying Credentials..." : "Authenticate & Enter"}
            </button>
          </form>

          {/* Preset Switcher */}
          <div className="pt-3 border-t border-slate-100 space-y-2">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block">
              Quick One-Click Demo Presets
            </span>
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <button
                type="button"
                onClick={() => setPreset("citizen@civiclens.gov", "Citizen@123456")}
                className="p-2.5 rounded-xl border border-emerald-300 bg-emerald-50/80 hover:bg-emerald-100 hover:border-emerald-400 text-left transition-colors col-span-2"
              >
                <div className="flex items-center justify-between">
                  <p className="font-bold text-emerald-900">👤 Citizen Resident</p>
                  <span className="text-[9px] bg-emerald-200/80 text-emerald-800 px-1.5 py-0.5 rounded-full font-semibold">Civilian Access</span>
                </div>
                <p className="text-[10px] text-emerald-700 mt-0.5">File complaints, track local issues & rate municipal repairs</p>
              </button>

              <button
                type="button"
                onClick={() => setPreset("admin@civiclens.gov", "Admin@123456")}
                className="p-2 rounded-xl border border-slate-200 bg-slate-50 hover:bg-emerald-50 hover:border-emerald-200 text-left transition-colors"
              >
                <p className="font-bold text-slate-800">Admin</p>
                <p className="text-[10px] text-slate-400">Chief Municipal Admin</p>
              </button>

              <button
                type="button"
                onClick={() => setPreset("officer.roads@civiclens.gov", "Officer@123456")}
                className="p-2 rounded-xl border border-slate-200 bg-slate-50 hover:bg-emerald-50 hover:border-emerald-200 text-left transition-colors"
              >
                <p className="font-bold text-slate-800">Roads Officer</p>
                <p className="text-[10px] text-slate-400">Potholes & Pavement</p>
              </button>

              <button
                type="button"
                onClick={() => setPreset("officer.sanitation@civiclens.gov", "Officer@123456")}
                className="p-2 rounded-xl border border-slate-200 bg-slate-50 hover:bg-emerald-50 hover:border-emerald-200 text-left transition-colors"
              >
                <p className="font-bold text-slate-800">Sanitation</p>
                <p className="text-[10px] text-slate-400">Garbage & Dumping</p>
              </button>

              <button
                type="button"
                onClick={() => setPreset("officer.electrical@civiclens.gov", "Officer@123456")}
                className="p-2 rounded-xl border border-slate-200 bg-slate-50 hover:bg-emerald-50 hover:border-emerald-200 text-left transition-colors"
              >
                <p className="font-bold text-slate-800">Electrical</p>
                <p className="text-[10px] text-slate-400">Lighting & Fixtures</p>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
