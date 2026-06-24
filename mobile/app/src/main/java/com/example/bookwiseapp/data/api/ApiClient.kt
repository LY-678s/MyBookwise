package com.example.bookwiseapp.data.api

import com.example.bookwiseapp.BuildConfig
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object ApiClient {

    // SERVER_BASE comes from mobile/settings.properties via BuildConfig.
    val SERVER_BASE: String = BuildConfig.SERVER_BASE
    val BASE_URL: String = "$SERVER_BASE/api/"

    var token: String? = null

    fun fullImageUrl(relativePath: String?): String? {
        if (relativePath.isNullOrEmpty()) return null
        return if (relativePath.startsWith("http")) relativePath
        else "$SERVER_BASE$relativePath"
    }

    fun bookCoverUrl(isbn: String, coverImageUrl: String? = null): String? {
        if (isbn.isBlank()) return null
        val path = if (!coverImageUrl.isNullOrBlank() && coverImageUrl.contains("/cover/")) {
            coverImageUrl
        } else {
            "/api/books/$isbn/cover/"
        }
        return fullImageUrl(path)
    }

    private val authInterceptor = Interceptor { chain ->
        val req = chain.request().newBuilder().apply {
            token?.let { addHeader("Authorization", "Token $it") }
        }.build()
        chain.proceed(req)
    }

    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(authInterceptor)
        .addInterceptor(loggingInterceptor)
        .build()

    val service: ApiService = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
        .create(ApiService::class.java)
}
