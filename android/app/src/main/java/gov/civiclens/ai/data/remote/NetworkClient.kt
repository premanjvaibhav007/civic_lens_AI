package gov.civiclens.ai.data.remote

import android.content.Context
import android.content.SharedPreferences
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object NetworkClient {
    // 10.0.2.2 points to host machine localhost in standard Android emulator
    private const val BASE_URL = "http://10.0.2.2:8000/api/v1/"
    private var apiService: CivicLensApiService? = null

    fun getService(context: Context): CivicLensApiService {
        return apiService ?: synchronized(this) {
            val prefs: SharedPreferences = context.getSharedPreferences("civiclens_prefs", Context.MODE_PRIVATE)

            val authInterceptor = Interceptor { chain ->
                val original = chain.request()
                val token = prefs.getString("auth_token", null)
                val builder = original.newBuilder()
                if (!token.isNullOrEmpty()) {
                    builder.header("Authorization", "Bearer $token")
                }
                chain.proceed(builder.build())
            }

            val logging = HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            }

            val okHttpClient = OkHttpClient.Builder()
                .addInterceptor(authInterceptor)
                .addInterceptor(logging)
                .connectTimeout(30, TimeUnit.SECONDS)
                .readTimeout(30, TimeUnit.SECONDS)
                .writeTimeout(30, TimeUnit.SECONDS)
                .build()

            val retrofit = Retrofit.Builder()
                .baseUrl(BASE_URL)
                .client(okHttpClient)
                .addConverterFactory(GsonConverterFactory.create())
                .build()

            val service = retrofit.create(CivicLensApiService::class.java)
            apiService = service
            service
        }
    }
}
