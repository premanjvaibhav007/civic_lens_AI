package gov.civiclens.ai

import android.app.Application
import androidx.work.*
import gov.civiclens.ai.workers.SyncDraftsWorker
import java.util.concurrent.TimeUnit

class CivicLensApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        setupPeriodicSyncWorker()
    }

    private fun setupPeriodicSyncWorker() {
        val constraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build()

        val syncWorkRequest = PeriodicWorkRequestBuilder<SyncDraftsWorker>(15, TimeUnit.MINUTES)
            .setConstraints(constraints)
            .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 1, TimeUnit.MINUTES)
            .build()

        WorkManager.getInstance(this).enqueueUniquePeriodicWork(
            "SyncCivicLensDrafts",
            ExistingPeriodicWorkPolicy.KEEP,
            syncWorkRequest
        )
    }
}
