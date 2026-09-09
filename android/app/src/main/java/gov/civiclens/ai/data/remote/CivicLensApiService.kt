package gov.civiclens.ai.data.remote

import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Response
import retrofit2.http.*

data class ApiResponse<T>(
    val success: Boolean,
    val message: String?,
    val data: T?
)

data class PaginatedData<T>(
    val items: List<T>,
    val total: Int,
    val page: Int,
    val pageSize: Int,
    val totalPages: Int
)

data class LoginDto(val email: String, val password: String)
data class RegisterDto(val email: String, val password: String, val fullName: String, val phone: String?, val city: String?)
data class TokenDto(val accessToken: String, val refreshToken: String, val user: UserDto)
data class UserDto(val id: String, val email: String, val fullName: String, val phone: String?, val role: String, val badgeScore: Int?)

data class ComplaintListItemDto(
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

data class ComplaintDetailDto(
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
    val location: LocationDto?,
    val images: List<ImageDto>,
    val aiAnalysis: AIAnalysisDto?,
    val timeline: List<TimelineDto>,
    val resolutionEvidence: ResolutionEvidenceDto?,
    val civicIncidentId: String? = null,
    val civicImpactScore: Double? = null,
    val createdAt: String
)

data class LocationDto(val latitude: Double, val longitude: Double, val address: String?)
data class ImageDto(val imageUrl: String, val thumbnailUrl: String?)
data class AIAnalysisDto(val detectedCategory: String, val confidence: Double, val predictedSeverity: String, val predictedPriority: String, val predictedDepartment: String?, val explanationText: String?, val duplicateCandidatesCount: Int)
data class TimelineDto(val id: String, val newStatus: String, val reason: String?, val createdAt: String)
data class ResolutionEvidenceDto(
    val officerName: String,
    val evidenceImageUrl: String,
    val completionNote: String,
    val completedAt: String,
    val aiVisualDiffScore: Double? = null,
    val aiResolutionConfidence: Double? = null,
    val aiLikelyResolved: Boolean? = null
)
data class NotificationDto(val id: String, val complaintId: String?, val title: String, val message: String, val notificationType: String, val isRead: Boolean, val createdAt: String)
data class VerificationRequestDto(val isResolved: Boolean, val rating: Int?, val feedback: String?, val reopenReason: String?)

interface CivicLensApiService {
    @POST("auth/login")
    suspend fun login(@Body body: LoginDto): Response<ApiResponse<TokenDto>>

    @POST("auth/register/citizen")
    suspend fun registerCitizen(@Body body: RegisterDto): Response<ApiResponse<TokenDto>>

    @GET("auth/me")
    suspend fun getMe(): Response<ApiResponse<UserDto>>

    @Multipart
    @POST("complaints")
    suspend fun submitComplaint(
        @Part("title") title: RequestBody,
        @Part("description") description: RequestBody?,
        @Part("category_id") categoryId: RequestBody?,
        @Part("latitude") latitude: RequestBody,
        @Part("longitude") longitude: RequestBody,
        @Part("address") address: RequestBody?,
        @Part("city") city: RequestBody?,
        @Part image: MultipartBody.Part?
    ): Response<ApiResponse<ComplaintListItemDto>>

    @GET("complaints")
    suspend fun getMyComplaints(
        @Query("page") page: Int = 1,
        @Query("page_size") pageSize: Int = 20,
        @Query("my_complaints_only") myOnly: Boolean = true
    ): Response<ApiResponse<PaginatedData<ComplaintListItemDto>>>

    @GET("complaints/nearby")
    suspend fun getNearbyComplaints(
        @Query("latitude") latitude: Double,
        @Query("longitude") longitude: Double,
        @Query("radius_meters") radiusMeters: Double = 5000.0
    ): Response<ApiResponse<List<ComplaintListItemDto>>>

    @GET("complaints/{id}")
    suspend fun getComplaintDetail(@Path("id") id: String): Response<ApiResponse<ComplaintDetailDto>>

    @POST("complaints/{id}/verify")
    suspend fun verifyResolution(
        @Path("id") id: String,
        @Body body: VerificationRequestDto
    ): Response<ApiResponse<ComplaintListItemDto>>

    @GET("notifications")
    suspend fun getNotifications(): Response<ApiResponse<List<NotificationDto>>>
}
