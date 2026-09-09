import React from "react";
import { Shield, Bell, User, LogOut, CheckCircle2, AlertTriangle, Layers, PlusCircle } from "lucide-react";
import { UserSummary } from "../types";

interface NavbarProps {
  user: UserSummary | null;
  onLogout: () => void;
  onOpenLogin: () => void;
  onOpenReportIssue: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ user, onLogout, onOpenLogin, onOpenReportIssue }) => {
  return (
    <header className="bg-slate-900 text-white border-b border-slate-800 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="bg-gradient-to-tr from-emerald-500 to-teal-400 p-2 rounded-xl shadow-lg shadow-emerald-500/20">
            <Shield className="w-6 h-6 text-slate-950 font-bold" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg tracking-tight text-white">CivicLens</span>
              <span className="bg-emerald-500/20 text-emerald-400 text-xs px-2 py-0.5 rounded-full font-semibold border border-emerald-500/30">
                {user?.role === "CITIZEN" ? "Citizen Portal" : "AI Authority Portal"}
              </span>
            </div>
            <p className="text-xs text-slate-400">Municipal Infrastructure Resolution Grid</p>
          </div>
        </div>

        {/* Right Action / Profile */}
        <div className="flex items-center space-x-3">
          {/* File Complaint Action Button */}
          <button
            onClick={onOpenReportIssue}
            className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs px-3.5 py-2 rounded-xl transition-all shadow-md shadow-emerald-500/20 flex items-center space-x-1.5 cursor-pointer"
            title="Submit a new civic complaint to municipal authorities"
          >
            <PlusCircle className="w-4 h-4 text-slate-950" />
            <span className="hidden sm:inline">File Complaint</span>
            <span className="sm:hidden">Report</span>
          </button>

          {user ? (
            <div className="flex items-center space-x-3">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-medium text-white">{user.full_name}</p>
                <div className="flex items-center justify-end space-x-1.5">
                  <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                  <p className="text-xs text-slate-400 font-mono">
                    {user.role} {user.department_name ? `• ${user.department_name}` : ""}
                  </p>
                </div>
              </div>
              <div className="bg-slate-800 border border-slate-700 p-2 rounded-full text-slate-300">
                <User className="w-5 h-5" />
              </div>
              <button
                onClick={onLogout}
                className="p-2 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
                title="Sign out"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          ) : (
            <button
              onClick={onOpenLogin}
              className="bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-all border border-slate-700 flex items-center space-x-2 cursor-pointer"
            >
              <User className="w-4 h-4" />
              <span>Sign In</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
