import React, { useState, useEffect } from "react";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { Navbar } from "./components/Navbar";
import { Sidebar, TabType } from "./components/Sidebar";
import { OverviewView } from "./components/OverviewView";
import { QueueView } from "./components/QueueView";
import { MapView } from "./components/MapView";
import { AnalyticsView } from "./components/AnalyticsView";
import { AdminConfigView } from "./components/AdminConfigView";
import { IncidentView } from "./components/IncidentView";
import { PredictionView } from "./components/PredictionView";
import { CopilotPanel } from "./components/CopilotPanel";
import { ComplaintDetailModal } from "./components/ComplaintDetailModal";
import { LoginModal } from "./components/LoginModal";
import { ReportIssueModal } from "./components/ReportIssueModal";
import {
  UserSummary,
  ComplaintListItem,
  ComplaintDetail,
  AnalyticsDashboard,
  Department,
  Jurisdiction,
  Category,
  AuditLogItem
} from "./types";
import { api } from "./api";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 5000,
    },
  },
});

function MainDashboard() {
  const [currentTab, setCurrentTab] = useState<TabType>("overview");
  const [currentUser, setCurrentUser] = useState<UserSummary | null>(null);
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);
  const [selectedComplaintId, setSelectedComplaintId] = useState<string | null>(null);

  // Queue query params
  const [queuePage, setQueuePage] = useState(1);
  const [queueFilters, setQueueFilters] = useState<{ status?: string; priority?: string; search?: string }>({});

  // Initialize auth from localStorage or default to Admin demo session
  useEffect(() => {
    const storedUser = localStorage.getItem("civiclens_user");
    const storedToken = localStorage.getItem("civiclens_token");
    if (storedUser && storedToken) {
      try {
        setCurrentUser(JSON.parse(storedUser));
      } catch {
        // Parse error fallback
      }
    } else {
      // Auto login as Chief Admin for instant local dev experience
      api.post("/auth/login", { email: "admin@civiclens.gov", password: "Admin@123456" })
        .then((res) => {
          const { access_token, user } = res.data.data;
          localStorage.setItem("civiclens_token", access_token);
          localStorage.setItem("civiclens_user", JSON.stringify(user));
          setCurrentUser(user);
        })
        .catch(() => {});
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("civiclens_token");
    localStorage.removeItem("civiclens_user");
    setCurrentUser(null);
  };

  // Queries
  const { data: analyticsData, refetch: refetchAnalytics } = useQuery<AnalyticsDashboard>({
    queryKey: ["analyticsDashboard"],
    queryFn: async () => {
      const res = await api.get("/analytics/dashboard");
      return res.data.data;
    },
    enabled: !!currentUser,
  });

  const { data: queueData, refetch: refetchQueue } = useQuery<{
    items: ComplaintListItem[];
    total: number;
    page: number;
    pageSize: number;
    totalPages: number;
  }>({
    queryKey: ["complaintsQueue", queuePage, queueFilters],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.append("page", String(queuePage));
      params.append("page_size", "20");
      if (queueFilters.status) params.append("status", queueFilters.status);
      if (queueFilters.priority) params.append("priority", queueFilters.priority);
      if (queueFilters.search) params.append("search", queueFilters.search);
      if ((queueFilters as any).myComplaintsOnly) params.append("my_complaints_only", "true");

      const res = await api.get(`/complaints?${params.toString()}`);
      return {
        items: res.data.data.items,
        total: res.data.data.total,
        page: res.data.data.page,
        pageSize: res.data.data.page_size,
        totalPages: res.data.data.total_pages,
      };
    },
    enabled: !!currentUser,
  });

  const { data: complaintDetail, refetch: refetchDetail } = useQuery<ComplaintDetail>({
    queryKey: ["complaintDetail", selectedComplaintId],
    queryFn: async () => {
      if (!selectedComplaintId) return null as any;
      const res = await api.get(`/complaints/${selectedComplaintId}`);
      return res.data.data;
    },
    enabled: !!selectedComplaintId,
  });

  const { data: departments = [], refetch: refetchDepts } = useQuery<Department[]>({
    queryKey: ["adminDepartments"],
    queryFn: async () => {
      const res = await api.get("/admin/departments");
      return res.data.data;
    },
    enabled: !!currentUser,
  });

  const { data: jurisdictions = [], refetch: refetchJurisdictions } = useQuery<Jurisdiction[]>({
    queryKey: ["adminJurisdictions"],
    queryFn: async () => {
      const res = await api.get("/admin/jurisdictions");
      return res.data.data;
    },
    enabled: !!currentUser,
  });

  const { data: categories = [], refetch: refetchCategories } = useQuery<Category[]>({
    queryKey: ["adminCategories"],
    queryFn: async () => {
      const res = await api.get("/admin/categories");
      return res.data.data;
    },
    enabled: !!currentUser,
  });

  const { data: auditLogs = [], refetch: refetchAudit } = useQuery<AuditLogItem[]>({
    queryKey: ["adminAuditLogs"],
    queryFn: async () => {
      if (currentUser?.role !== "ADMIN") return [];
      const res = await api.get("/admin/audit-logs");
      return res.data.data.items;
    },
    enabled: currentUser?.role === "ADMIN",
  });

  const refreshAll = () => {
    refetchAnalytics();
    refetchQueue();
    if (selectedComplaintId) refetchDetail();
    refetchDepts();
    refetchJurisdictions();
    refetchCategories();
    refetchAudit();
  };

  const pendingCount = queueData?.items.filter(
    (c) => c.status === "SUBMITTED" || c.status === "ROUTED"
  ).length;

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col font-sans">
      <Navbar
        user={currentUser}
        onLogout={handleLogout}
        onOpenLogin={() => setIsLoginModalOpen(true)}
        onOpenReportIssue={() => {
          if (!currentUser) {
            setIsLoginModalOpen(true);
          } else {
            setIsReportModalOpen(true);
          }
        }}
      />

      <div className="flex-1 flex max-w-7xl w-full mx-auto">
        <Sidebar
          currentTab={currentTab}
          onSelectTab={(tab) => setCurrentTab(tab)}
          user={currentUser}
          pendingCount={pendingCount}
          onToggleCopilot={() => setIsCopilotOpen(true)}
        />

        <main className="flex-1 p-6 overflow-y-auto">
          {currentTab === "overview" && (
            <OverviewView
              data={analyticsData || null}
              onNavigateToQueue={() => setCurrentTab("queue")}
            />
          )}

          {currentTab === "queue" && (
            <QueueView
              complaints={queueData?.items || []}
              total={queueData?.total || 0}
              page={queuePage}
              pageSize={20}
              totalPages={queueData?.totalPages || 1}
              onPageChange={(p) => setQueuePage(p)}
              onSelectComplaint={(id) => setSelectedComplaintId(id)}
              onFilterChange={(f) => {
                setQueueFilters(f);
                setQueuePage(1);
              }}
              currentUser={currentUser}
            />
          )}

          {currentTab === "incidents" && (
            <IncidentView
              user={currentUser}
              onViewComplaintDetail={(id) => setSelectedComplaintId(id)}
            />
          )}

          {currentTab === "map" && (
            <MapView
              complaints={queueData?.items || []}
              onSelectComplaint={(id) => setSelectedComplaintId(id)}
            />
          )}

          {currentTab === "predictions" && <PredictionView user={currentUser} />}

          {currentTab === "analytics" && <AnalyticsView data={analyticsData || null} />}

          {currentTab === "admin" && (
            <AdminConfigView
              departments={departments}
              jurisdictions={jurisdictions}
              categories={categories}
              auditLogs={auditLogs}
              onRefresh={refreshAll}
            />
          )}
        </main>
      </div>

      {/* Complaint Detail Inspection Modal */}
      {selectedComplaintId && (
        <ComplaintDetailModal
          complaint={complaintDetail || null}
          currentUser={currentUser}
          departments={departments}
          onClose={() => setSelectedComplaintId(null)}
          onRefresh={refreshAll}
        />
      )}

      {/* AI Authority Copilot Drawer */}
      <CopilotPanel
        isOpen={isCopilotOpen}
        onClose={() => setIsCopilotOpen(false)}
        onSelectComplaint={(id) => setSelectedComplaintId(id)}
      />

      {/* Login Modal */}
      <LoginModal
        isOpen={isLoginModalOpen}
        onClose={() => setIsLoginModalOpen(false)}
        onLoginSuccess={(user, token) => {
          setCurrentUser(user);
          refreshAll();
        }}
      />

      {/* Citizen Report Issue Modal */}
      <ReportIssueModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        onSuccess={() => {
          refreshAll();
        }}
        userRole={currentUser?.role}
      />
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <MainDashboard />
    </QueryClientProvider>
  );
}
