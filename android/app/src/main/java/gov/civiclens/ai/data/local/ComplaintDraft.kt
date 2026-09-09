package gov.civiclens.ai.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey
import java.util.UUID

@Entity(tableName = "complaint_drafts")
data class ComplaintDraft(
    @PrimaryKey
    val id: String = UUID.randomUUID().toString(),
    val title: String,
    val description: String?,
    val categoryId: String?,
    val latitude: Double,
    val longitude: Double,
    val accuracyMeters: Float = 0f,
    val address: String?,
    val city: String?,
    val localImagePath: String?,
    val isSynced: Boolean = false,
    val syncAttempts: Int = 0,
    val createdAt: Long = System.currentTimeMillis()
)
