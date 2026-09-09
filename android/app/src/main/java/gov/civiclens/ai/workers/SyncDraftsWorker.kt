package gov.civiclens.ai.workers

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import gov.civiclens.ai.data.local.CivicLensDatabase
import gov.civiclens.ai.data.remote.NetworkClient
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File

class SyncDraftsWorker(
    appContext: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result {
        val db = CivicLensDatabase.getInstance(applicationContext)
        val dao = db.complaintDao()
        val api = NetworkClient.getService(applicationContext)

        val pendingDrafts = dao.getPendingSyncDrafts()
        if (pendingDrafts.isEmpty()) {
            return Result.success()
        }

        for (draft in pendingDrafts) {
            try {
                val titlePart = draft.title.toRequestBody("text/plain".toMediaTypeOrNull())
                val descPart = draft.description?.toRequestBody("text/plain".toMediaTypeOrNull())
                val catPart = draft.categoryId?.toRequestBody("text/plain".toMediaTypeOrNull())
                val latPart = draft.latitude.toString().toRequestBody("text/plain".toMediaTypeOrNull())
                val lngPart = draft.longitude.toString().toRequestBody("text/plain".toMediaTypeOrNull())
                val addrPart = draft.address?.toRequestBody("text/plain".toMediaTypeOrNull())
                val cityPart = draft.city?.toRequestBody("text/plain".toMediaTypeOrNull())

                var imagePart: MultipartBody.Part? = null
                if (!draft.localImagePath.isNullOrEmpty()) {
                    val file = File(draft.localImagePath)
                    if (file.exists()) {
                        val reqFile = file.asRequestBody("image/jpeg".toMediaTypeOrNull())
                        imagePart = MultipartBody.Part.createFormData("image", file.name, reqFile)
                    }
                }

                val resp = api.submitComplaint(titlePart, descPart, catPart, latPart, lngPart, addrPart, cityPart, imagePart)
                if (resp.isSuccessful) {
                    dao.deleteDraft(draft)
                } else {
                    dao.updateDraft(draft.copy(syncAttempts = draft.syncAttempts + 1))
                }
            } catch (e: Exception) {
                dao.updateDraft(draft.copy(syncAttempts = draft.syncAttempts + 1))
            }
        }

        return Result.success()
    }
}
