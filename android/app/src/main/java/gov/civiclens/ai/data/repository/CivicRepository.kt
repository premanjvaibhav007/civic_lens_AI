package gov.civiclens.ai.data.repository

import android.content.Context
import gov.civiclens.ai.data.local.CivicLensDatabase
import gov.civiclens.ai.data.local.ComplaintDraft
import gov.civiclens.ai.data.remote.*
import gov.civiclens.ai.domain.model.*
import kotlinx.coroutines.flow.Flow
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File

class CivicRepository(private val context: Context) {
    private val api = NetworkClient.getService(context)
    private val db = CivicLensDatabase.getInstance(context)
    private val dao = db.complaintDao()

    val localDrafts: Flow<List<ComplaintDraft>> = dao.getAllDrafts()

    suspend fun saveDraft(draft: ComplaintDraft) {
        dao.insertDraft(draft)
    }

    suspend fun deleteDraft(id: String) {
        dao.deleteDraftById(id)
    }

    suspend fun login(email: String, pass: String): Result<UserSummary> {
        return try {
            val resp = api.login(LoginDto(email, pass))
            if (resp.isSuccessful && resp.body()?.data != null) {
                val tokenData = resp.body()!!.data!!
                val prefs = context.getSharedPreferences("civiclens_prefs", Context.MODE_PRIVATE)
                prefs.edit()
                    .putString("auth_token", tokenData.accessToken)
                    .putString("user_id", tokenData.user.id)
                    .putString("user_name", tokenData.user.fullName)
                    .apply()

                Result.success(
                    UserSummary(
                        id = tokenData.user.id,
                        email = tokenData.user.email,
                        fullName = tokenData.user.fullName,
                        phone = tokenData.user.phone,
                        role = tokenData.user.role,
                        badgeScore = tokenData.user.badgeScore
                    )
                )
            } else {
                Result.failure(Exception(resp.body()?.message ?: "Login failed"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun register(name: String, email: String, pass: String, phone: String?, city: String?): Result<UserSummary> {
        return try {
            val resp = api.registerCitizen(RegisterDto(email, pass, name, phone, city))
            if (resp.isSuccessful && resp.body()?.data != null) {
                val tokenData = resp.body()!!.data!!
                val prefs = context.getSharedPreferences("civiclens_prefs", Context.MODE_PRIVATE)
                prefs.edit()
                    .putString("auth_token", tokenData.accessToken)
                    .putString("user_id", tokenData.user.id)
                    .putString("user_name", tokenData.user.fullName)
                    .apply()

                Result.success(
                    UserSummary(
                        id = tokenData.user.id,
                        email = tokenData.user.email,
                        fullName = tokenData.user.fullName,
                        phone = tokenData.user.phone,
                        role = tokenData.user.role,
                        badgeScore = tokenData.user.badgeScore
                    )
                )
            } else {
                Result.failure(Exception(resp.body()?.message ?: "Registration failed"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun submitComplaint(
        title: String,
        description: String?,
        categoryId: String?,
        latitude: Double,
        longitude: Double,
        address: String?,
        city: String?,
        imageFile: File?
    ): Result<ComplaintItem> {
        return try {
            val titlePart = title.toRequestBody("text/plain".toMediaTypeOrNull())
            val descPart = description?.toRequestBody("text/plain".toMediaTypeOrNull())
            val catPart = categoryId?.toRequestBody("text/plain".toMediaTypeOrNull())
            val latPart = latitude.toString().toRequestBody("text/plain".toMediaTypeOrNull())
            val lngPart = longitude.toString().toRequestBody("text/plain".toMediaTypeOrNull())
            val addrPart = address?.toRequestBody("text/plain".toMediaTypeOrNull())
            val cityPart = city?.toRequestBody("text/plain".toMediaTypeOrNull())

            var imagePart: MultipartBody.Part? = null
            if (imageFile != null && imageFile.exists()) {
                val reqFile = imageFile.asRequestBody("image/jpeg".toMediaTypeOrNull())
                imagePart = MultipartBody.Part.createFormData("image", imageFile.name, reqFile)
            }

            val resp = api.submitComplaint(titlePart, descPart, catPart, latPart, lngPart, addrPart, cityPart, imagePart)
            if (resp.isSuccessful && resp.body()?.data != null) {
                val dto = resp.body()!!.data!!
                Result.success(
                    ComplaintItem(
                        id = dto.id,
                        complaintNumber = dto.complaintNumber,
                        title = dto.title,
                        categoryName = dto.categoryName,
                        departmentName = dto.departmentName,
                        status = dto.status,
                        priority = dto.priority,
                        severity = dto.severity,
                        primaryImageUrl = dto.primaryImageUrl,
                        primaryThumbnailUrl = dto.primaryThumbnailUrl,
                        latitude = dto.latitude,
                        longitude = dto.longitude,
                        address = dto.address,
                        city = dto.city,
                        isDuplicate = dto.isDuplicate,
                        aiConfidence = dto.aiConfidence,
                        createdAt = dto.createdAt
                    )
                )
            } else {
                Result.failure(Exception(resp.body()?.message ?: "Failed to submit"))
            }
        } catch (e: Exception) {
            // Save to local drafts for offline recovery
            val draft = ComplaintDraft(
                title = title,
                description = description,
                categoryId = categoryId,
                latitude = latitude,
                longitude = longitude,
                address = address,
                city = city,
                localImagePath = imageFile?.absolutePath,
                isSynced = false
            )
            saveDraft(draft)
            Result.failure(Exception("Network unavailable. Saved as offline draft for automatic background sync."))
        }
    }

    suspend fun getMyComplaints(): Result<List<ComplaintItem>> {
        return try {
            val resp = api.getMyComplaints()
            if (resp.isSuccessful && resp.body()?.data != null) {
                val items = resp.body()!!.data!!.items.map { dto ->
                    ComplaintItem(
                        id = dto.id,
                        complaintNumber = dto.complaintNumber,
                        title = dto.title,
                        categoryName = dto.categoryName,
                        departmentName = dto.departmentName,
                        status = dto.status,
                        priority = dto.priority,
                        severity = dto.severity,
                        primaryImageUrl = dto.primaryImageUrl,
                        primaryThumbnailUrl = dto.primaryThumbnailUrl,
                        latitude = dto.latitude,
                        longitude = dto.longitude,
                        address = dto.address,
                        city = dto.city,
                        isDuplicate = dto.isDuplicate,
                        aiConfidence = dto.aiConfidence,
                        createdAt = dto.createdAt
                    )
                }
                Result.success(items)
            } else {
                Result.failure(Exception("Failed to fetch complaints"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun getNearbyComplaints(lat: Double, lng: Double): Result<List<ComplaintItem>> {
        return try {
            val resp = api.getNearbyComplaints(lat, lng)
            if (resp.isSuccessful && resp.body()?.data != null) {
                val items = resp.body()!!.data!!.map { dto ->
                    ComplaintItem(
                        id = dto.id,
                        complaintNumber = dto.complaintNumber,
                        title = dto.title,
                        categoryName = dto.categoryName,
                        departmentName = dto.departmentName,
                        status = dto.status,
                        priority = dto.priority,
                        severity = dto.severity,
                        primaryImageUrl = dto.primaryImageUrl,
                        primaryThumbnailUrl = dto.primaryThumbnailUrl,
                        latitude = dto.latitude,
                        longitude = dto.longitude,
                        address = dto.address,
                        city = dto.city,
                        isDuplicate = dto.isDuplicate,
                        aiConfidence = dto.aiConfidence,
                        createdAt = dto.createdAt
                    )
                }
                Result.success(items)
            } else {
                Result.failure(Exception("Failed to fetch nearby complaints"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun getComplaintDetail(id: String): Result<ComplaintDetail> {
        return try {
            val resp = api.getComplaintDetail(id)
            if (resp.isSuccessful && resp.body()?.data != null) {
                val dto = resp.body()!!.data!!
                val detail = ComplaintDetail(
                    id = dto.id,
                    complaintNumber = dto.complaintNumber,
                    citizenName = dto.citizenName,
                    categoryName = dto.categoryName,
                    departmentName = dto.departmentName,
                    title = dto.title,
                    description = dto.description,
                    status = dto.status,
                    priority = dto.priority,
                    severity = dto.severity,
                    aiAnalyzed = dto.aiAnalyzed,
                    isDuplicate = dto.isDuplicate,
                    resolutionRating = dto.resolutionRating,
                    citizenFeedback = dto.citizenFeedback,
                    citizenVerified = dto.citizenVerified,
                    primaryImageUrl = dto.images.firstOrNull()?.imageUrl,
                    address = dto.location?.address,
                    latitude = dto.location?.latitude,
                    longitude = dto.location?.longitude,
                    aiAnalysis = dto.aiAnalysis?.let {
                        AIAnalysis(
                            detectedCategory = it.detectedCategory,
                            confidence = it.confidence,
                            predictedSeverity = it.predictedSeverity,
                            predictedPriority = it.predictedPriority,
                            predictedDepartment = it.predictedDepartment,
                            explanationText = it.explanationText,
                            duplicateCandidatesCount = it.duplicateCandidatesCount
                        )
                    },
                    timeline = dto.timeline.map { TimelineItem(it.id, it.newStatus, it.reason, it.createdAt) },
                    resolutionEvidence = dto.resolutionEvidence?.let {
                        ResolutionEvidence(
                            officerName = it.officerName,
                            evidenceImageUrl = it.evidenceImageUrl,
                            completionNote = it.completionNote,
                            completedAt = it.completedAt,
                            aiVisualDiffScore = it.aiVisualDiffScore,
                            aiResolutionConfidence = it.aiResolutionConfidence,
                            aiLikelyResolved = it.aiLikelyResolved
                        )
                    },
                    civicIncidentId = dto.civicIncidentId,
                    civicImpactScore = dto.civicImpactScore,
                    createdAt = dto.createdAt
                )
                Result.success(detail)
            } else {
                Result.failure(Exception("Complaint not found"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun verifyResolution(id: String, isResolved: Boolean, rating: Int?, feedback: String?, reopenReason: String?): Result<Boolean> {
        return try {
            val resp = api.verifyResolution(id, VerificationRequestDto(isResolved, rating, feedback, reopenReason))
            if (resp.isSuccessful) {
                Result.success(true)
            } else {
                Result.failure(Exception("Verification failed"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
