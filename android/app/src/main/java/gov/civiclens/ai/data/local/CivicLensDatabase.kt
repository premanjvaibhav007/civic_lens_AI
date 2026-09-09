package gov.civiclens.ai.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(entities = [ComplaintDraft::class], version = 1, exportSchema = false)
abstract class CivicLensDatabase : RoomDatabase() {
    abstract fun complaintDao(): ComplaintDao

    companion object {
        @Volatile
        private var INSTANCE: CivicLensDatabase? = null

        fun getInstance(context: Context): CivicLensDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    CivicLensDatabase::class.java,
                    "civiclens_local.db"
                ).build()
                INSTANCE = instance
                instance
            }
        }
    }
}
