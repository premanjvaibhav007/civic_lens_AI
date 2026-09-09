package gov.civiclens.ai.domain.model

data class UserSummary(
    val id: String,
    val email: String,
    val fullName: String,
    val phone: String?,
    val role: String,
    val badgeScore: Int? = null
)

data class ComplaintItem(
    val id: String,
    val complaintNumber: String,
    val title: String,
    val categoryName: String?,
    val departmentName: String?,
    val status: String,
    val priority: String,
    val severity: String,
    val primaryImageUrl: String?,
    val primaryThumbnailUrl: String?,
    val latitude: Double?,
    val longitude: Double?,
    val address: String?,
    val city: String?,
    val isDuplicate: Boolean,
    val aiConfidence: Double?,
    val createdAt: String
)

data class AIAnalysis(
    val detectedCategory: String,
    val confidence: Double,
    val predictedSeverity: String,
    val predictedPriority: String,
    val predictedDepartment: String?,
    val explanationText: String?,
    val duplicateCandidatesCount: Int
)

data class TimelineItem(
    val id: String,
    val newStatus: String,
    val reason: String?,
    val createdAt: String
)

data class ResolutionEvidence(
    val officerName: String,
    val evidenceImageUrl: String,
    val completionNote: String,
    val completedAt: String,
    val aiVisualDiffScore: Double? = null,
    val aiResolutionConfidence: Double? = null,
    val aiLikelyResolved: Boolean? = null
)

data class ComplaintDetail(
    val id: String,
    val complaintNumber: String,
    val citizenName: String,
    val categoryName: String?,
    val departmentName: String?,
    val title: String,
    val description: String?,
    val status: String,
    val priority: String,
    val severity: String,
    val aiAnalyzed: Boolean,
    val isDuplicate: Boolean,
    val resolutionRating: Int?,
    val citizenFeedback: String?,
    val citizenVerified: Boolean?,
    val primaryImageUrl: String?,
    val address: String?,
    val latitude: Double?,
    val longitude: Double?,
    val aiAnalysis: AIAnalysis?,
    val timeline: List<TimelineItem>,
    val resolutionEvidence: ResolutionEvidence?,
    val civicIncidentId: String? = null,
    val civicImpactScore: Double? = null,
    val createdAt: String
)

data class NotificationItem(
    val id: String,
    val complaintId: String?,
    val title: String,
    val message: String,
    val notificationType: String,
    val isRead: Boolean,
    val createdAt: String
)
