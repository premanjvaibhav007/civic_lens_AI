export type UserRole = "CITIZEN" | "OFFICER" | "ADMIN";

export type ComplaintStatus =
  | "DRAFT"
  | "SUBMITTED"
  | "AI_ANALYZING"
  | "AI_VERIFIED"
  | "ROUTED"
  | "ASSIGNED"
  | "IN_PROGRESS"
  | "RESOLUTION_SUBMITTED"
  | "CITIZEN_VERIFICATION"
  | "RESOLVED"
  | "REJECTED"
  | "DUPLICATE"
  | "ESCALATED"
  | "REOPENED";

export type PriorityLevel = "P1" | "P2" | "P3" | "P4";
export type SeverityLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface UserSummary {
  id: string;
  email: string;
  full_name: string;
  phone?: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  badge_score?: number;
  department_id?: string;
  department_name?: string;
  badge_number?: string;
  designation?: string;
}

export interface ComplaintListItem {
  id: string;
  complaint_number: string;
  title: string;
  category_name?: string;
  department_name?: string;
  status: ComplaintStatus;
  priority: PriorityLevel;
  severity: SeverityLevel;
  primary_image_url?: string;
  primary_thumbnail_url?: string;
  latitude?: number;
  longitude?: number;
  address?: string;
  city?: string;
  is_duplicate: boolean;
  ai_confidence?: number;
  created_at: string;
  updated_at: string;
}

export interface LocationDetail {
  id: string;
  latitude: number;
  longitude: number;
  accuracy_meters: number;
  address?: string;
  landmark?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  is_manual_adjusted: boolean;
}

export interface ImageDetail {
  id: string;
  image_url: string;
  thumbnail_url?: string;
  file_size_bytes: number;
  mime_type: string;
  is_primary: boolean;
  captured_at: string;
}

export interface AIAnalysisDetail {
  id: string;
  model_name: string;
  model_version: string;
  detected_category: string;
  confidence: number;
  predicted_severity: SeverityLevel;
  predicted_priority: PriorityLevel;
  predicted_department?: string;
  duplicate_candidates_count: number;
  contributing_factors?: Record<string, any>;
  explanation_text?: string;
  inference_latency_ms: number;
  created_at: string;
}

export interface StatusHistoryItem {
  id: string;
  previous_status?: ComplaintStatus;
  new_status: ComplaintStatus;
  reason?: string;
  created_at: string;
}

export interface CommentItem {
  id: string;
  user_id: string;
  user_name: string;
  user_role: string;
  is_official: boolean;
  comment_text: string;
  created_at: string;
}

export interface ResolutionEvidenceDetail {
  id: string;
  officer_name: string;
  evidence_image_url: string;
  evidence_thumbnail_url?: string;
  completion_note: string;
  completed_at: string;
  visual_similarity_score?: number;
  ai_visual_diff_score?: number;
  ai_resolution_confidence?: number;
  ai_likely_resolved?: boolean;
}

export interface DuplicateCandidateItem {
  id: string;
  candidate_complaint_id: string;
  candidate_complaint_number: string;
  candidate_title: string;
  candidate_status: ComplaintStatus;
  candidate_image_url?: string;
  similarity_score: number;
  image_similarity: number;
  text_similarity: number;
  geo_distance_meters: number;
  status: string;
}

export interface ComplaintDetail {
  id: string;
  complaint_number: string;
  citizen_id: string;
  citizen_name: string;
  category_id?: string;
  category_name?: string;
  department_id?: string;
  department_name?: string;
  jurisdiction_id?: string;
  jurisdiction_info?: string;
  assigned_officer_id?: string;
  assigned_officer_name?: string;
  title: string;
  description?: string;
  status: ComplaintStatus;
  priority: PriorityLevel;
  severity: SeverityLevel;
  ai_analyzed: boolean;
  ai_status: string;
  is_duplicate: boolean;
  duplicate_of_id?: string;
  duplicate_score: number;
  requires_manual_verification: boolean;
  resolution_rating?: number;
  citizen_feedback?: string;
  citizen_verified?: boolean;
  reopened_count: number;
  sla_deadline?: string;
  location?: LocationDetail;
  images: ImageDetail[];
  ai_analysis?: AIAnalysisDetail;
  timeline: StatusHistoryItem[];
  comments: CommentItem[];
  resolution_evidence?: ResolutionEvidenceDetail;
  duplicate_candidates: DuplicateCandidateItem[];
  created_at: string;
  updated_at: string;
}

export interface AnalyticsDashboard {
  metrics: {
    total_complaints: number;
    open_complaints: number;
    pending_assignment: number;
    in_progress: number;
    resolution_submitted: number;
    resolved_complaints: number;
    escalated_complaints: number;
    duplicate_count: number;
    average_resolution_hours: number;
    sla_compliance_rate: number;
    citizen_satisfaction_score: number;
  };
  category_distribution: Array<{
    category_name: string;
    count: number;
    percentage: number;
  }>;
  department_performance: Array<{
    department_id: string;
    department_name: string;
    total_assigned: number;
    resolved_count: number;
    in_progress_count: number;
    avg_resolution_hours: number;
    sla_compliance_rate: number;
  }>;
  trend_last_30_days: Array<{
    date: string;
    submitted: number;
    resolved: number;
    escalated: number;
  }>;
  geo_hotspots: Array<{
    latitude: number;
    longitude: number;
    intensity: number;
    complaint_count: number;
    category_name: string;
    city: string;
  }>;
}

export interface Department {
  id: string;
  name: string;
  code: string;
  description?: string;
  contact_email?: string;
  contact_phone?: string;
  is_active: boolean;
  officer_count: number;
  active_complaints_count: number;
  created_at: string;
}

export interface Jurisdiction {
  id: string;
  city: string;
  zone: string;
  ward: string;
  is_active: boolean;
  created_at: string;
}

export interface Category {
  id: string;
  name: string;
  code: string;
  description?: string;
  default_department_id?: string;
  default_department_name?: string;
  default_priority: PriorityLevel;
  default_severity: SeverityLevel;
  icon_name: string;
  is_active: boolean;
  created_at: string;
}

export interface AuditLogItem {
  id: string;
  user_id?: string;
  user_name?: string;
  action: string;
  entity_name: string;
  entity_id: string;
  old_value_json?: any;
  new_value_json?: any;
  ip_address?: string;
  created_at: string;
}

export interface CivicIncidentItem {
  id: string;
  incident_number: string;
  title: string;
  status: string;
  severity: SeverityLevel;
  priority: PriorityLevel;
  civic_impact_score: number;
  report_count: number;
  duplicate_count: number;
  recurrence_count: number;
  centroid_lat?: number;
  centroid_lng?: number;
  ward?: string;
  city?: string;
  category_code?: string;
  department_name?: string;
  first_reported_at: string;
  last_updated_at: string;
  impact_breakdown?: {
    safety?: number;
    population?: number;
    traffic?: number;
    persistence?: number;
    recurrence?: number;
    total?: number;
    explanation?: string;
  };
  priority_explanation?: string;
}

export interface InfrastructureAssetItem {
  id: string;
  asset_code: string;
  asset_type: string;
  name: string;
  description?: string;
  latitude?: number;
  longitude?: number;
  address?: string;
  health_score: number;
  risk_score: number;
  risk_level: string;
  complaint_count: number;
  repair_count: number;
  is_recurrent: boolean;
  ai_recommendation?: string;
}

export interface PredictionStatus {
  has_sufficient_data: boolean;
  days_of_data: number;
  total_incidents: number;
  minimum_required_days: number;
  message: string;
}

export interface CopilotQueryResponse {
  answer: string;
  intent: string;
  source_records: Array<Record<string, any>>;
  data_caveat?: string;
  query_time_ms: number;
}
