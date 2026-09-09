package gov.civiclens.ai.data.local

import androidx.room.*
import kotlinx.coroutines.flow.Flow

@Dao
interface ComplaintDao {
    @Query("SELECT * FROM complaint_drafts ORDER BY createdAt DESC")
    fun getAllDrafts(): Flow<List<ComplaintDraft>>

    @Query("SELECT * FROM complaint_drafts WHERE isSynced = 0 ORDER BY createdAt ASC")
    suspend fun getPendingSyncDrafts(): List<ComplaintDraft>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertDraft(draft: ComplaintDraft)

    @Update
    suspend fun updateDraft(draft: ComplaintDraft)

    @Delete
    suspend fun deleteDraft(draft: ComplaintDraft)

    @Query("DELETE FROM complaint_drafts WHERE id = :id")
    suspend fun deleteDraftById(id: String)
}
